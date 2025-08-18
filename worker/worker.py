#!/usr/bin/env python3
# ============================================================================
# WORKER DE MONITOREO AUTOMÁTICO DE ALERTAS DE VUELOS
# ============================================================================
# Proceso en background que:
# 1. Revisa alertas activas cada 15 minutos
# 2. Busca vuelos usando RapidAPI Kiwi.com 
# 3. Envía notificaciones si encuentra precios objetivo
# 4. Guarda historial de precios automáticamente
# ============================================================================

import os
import sys
import time
import logging
import requests
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

# Configurar logging PRIMERO
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/worker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Agregar el path del backend para importar modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
try:
    from flights_api import FlightSearchAPI
    logger.info("✅ FlightSearchAPI importada correctamente")
except ImportError as e:
    logger.error(f"❌ Error importando flights_api: {e}")
    FlightSearchAPI = None

class FlightAlertWorker:
    """
    Worker para monitoreo automático de alertas de vuelos
    """

    def __init__(self, flights_api):
        self.db_config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'vuelos'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'password')
        }
        
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.check_interval_minutes = int(os.getenv('WORKER_INTERVAL_MINUTES', '15'))
        self.flights_api = flights_api
        
        logger.info(f"🤖 Worker iniciado - Intervalo: {self.check_interval_minutes} minutos")
        
    def get_db_connection(self):
        """Obtener conexión a PostgreSQL"""
        try:
            conn = psycopg2.connect(**self.db_config)
            return conn
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            return None
    
    def get_active_alerts(self) -> List[Dict]:
        """Obtener todas las alertas activas"""
        conn = self.get_db_connection()
        if not conn:
            return []
        
        try:
            cursor = conn.cursor()
            query = """
                SELECT a.id, a.user_id, a.origin, a.destination, 
                       a.date_from, a.date_to, a.price_target_cents, 
                       a.max_stops, a.created_at, u.telegram_id
                FROM alerts a
                JOIN users u ON a.user_id = u.id
                WHERE a.active = TRUE
                  AND a.date_from >= CURRENT_DATE
                ORDER BY a.created_at ASC
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            alerts = []
            for row in results:
                alerts.append({
                    'id': row[0],
                    'user_id': row[1],
                    'origin': row[2],
                    'destination': row[3],
                    'date_from': row[4].strftime('%d/%m/%Y') if row[4] else None,
                    'date_to': row[5].strftime('%d/%m/%Y') if row[5] else None,
                    'price_target_cents': row[6],
                    'max_stops': row[7],
                    'created_at': row[8],
                    'telegram_id': row[9]
                })
            
            logger.info(f"📊 Encontradas {len(alerts)} alertas activas")
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo alertas: {e}")
            return []
        finally:
            conn.close()
    
    def search_flights_for_alert(self, alert: Dict) -> Dict[str, Any]:
        """Buscar vuelos para una alerta específica"""
        try:
            logger.info(f"🔍 Buscando vuelos para alerta {alert['id']}: {alert['origin']} → {alert['destination']}")

            if not self.flights_api:
                logger.error("❌ flights_api no está disponible")
                return {
                    'success': False,
                    'error': 'FlightSearchAPI no disponible',
                    'flights': [],
                    'total_results': 0
                }

            # Usar la API de vuelos ya configurada
            result = self.flights_api.search_flights(
                origin=alert['origin'],
                destination=alert['destination'],
                date_from=alert['date_from'],
                return_from=alert.get('date_to'),
                limit=5
            )

            if result.get('success') and result.get('flights'):
                logger.info(f"✅ Encontrados {len(result['flights'])} vuelos para alerta {alert['id']}")
                return result
            else:
                logger.warning(f"⚠️ No se encontraron vuelos para alerta {alert['id']}")
                return result

        except Exception as e:
            logger.error(f"❌ Error buscando vuelos para alerta {alert['id']}: {e}")
            return {
                'success': False,
                'error': str(e),
                'flights': [],
                'total_results': 0
            }
    
    def save_search_snapshot(self, alert_id: int, price_cents: int, flight_details: Dict):
        """Guardar snapshot de búsqueda en BD"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO search_snapshots (alert_id, price_cents, found_at, details)
                VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                alert_id,
                price_cents,
                datetime.now(),
                json.dumps(flight_details)
            ))
            
            conn.commit()
            logger.info(f"💾 Snapshot guardado para alerta {alert_id}: {price_cents/100:.2f}€")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error guardando snapshot: {e}")
            return False
        finally:
            conn.close()
    
    def check_recent_notification(self, alert_id: int) -> bool:
        """Verificar si ya se envió una notificación reciente (últimas 24h)"""
        conn = self.get_db_connection()
        if not conn:
            return True  # Por seguridad, asumir que sí se envió
        
        try:
            cursor = conn.cursor()
            
            query = """
                SELECT COUNT(*) FROM notifications_sent
                WHERE alert_id = %s
                  AND sent_at >= %s
            """
            
            yesterday = datetime.now() - timedelta(days=1)
            cursor.execute(query, (alert_id, yesterday))
            
            count = cursor.fetchone()[0]
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Error verificando notificaciones recientes: {e}")
            return True
        finally:
            conn.close()
    
    def save_notification_sent(self, alert_id: int, price_cents: int):
        """Registrar que se envió una notificación"""
        conn = self.get_db_connection()
        if not conn:
            return False
        
        try:
            cursor = conn.cursor()
            
            query = """
                INSERT INTO notifications_sent (alert_id, price_cents, sent_at)
                VALUES (%s, %s, %s)
            """
            
            cursor.execute(query, (alert_id, price_cents, datetime.now()))
            conn.commit()
            
            logger.info(f"📬 Notificación registrada para alerta {alert_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error registrando notificación: {e}")
            return False
        finally:
            conn.close()
    
    def send_telegram_notification(self, telegram_id: int, alert: Dict, flight: Dict):
        """Enviar notificación por Telegram"""
        if not self.telegram_bot_token:
            logger.warning("⚠️ No hay token de Telegram configurado")
            return False
        
        try:
            price_euros = flight['price_euros']
            target_euros = alert['price_target_cents'] / 100
            
            message = f"🎉 **¡ALERTA DE VUELO ENCONTRADO!** ✈️\n\n"
            message += f"**Ruta:** {alert['origin']} → {alert['destination']}\n"
            message += f"**Fecha:** {alert['date_from']}\n"
            message += f"**Precio encontrado:** {price_euros:.2f}€\n"
            message += f"**Tu objetivo:** {target_euros:.2f}€\n"
            message += f"**Aerolínea:** {', '.join(flight['airlines'])}\n"
            message += f"**Duración:** {flight['flight_duration']}\n"
            message += f"**Escalas:** {flight['stops']}\n\n"
            message += f"🔗 **[RESERVAR AHORA]({flight['booking_link']})**\n\n"
            message += f"💡 *Precio encontrado por tu alerta automática*"
            
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': telegram_id,
                'text': message,
                'parse_mode': 'Markdown',
                'disable_web_page_preview': False
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"📱 Notificación enviada a usuario {telegram_id}")
                return True
            else:
                logger.error(f"❌ Error enviando notificación: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error enviando notificación por Telegram: {e}")
            return False
    
    def process_alert(self, alert: Dict):
        """Procesar una alerta individual"""
        alert_id = alert['id']
        target_price_cents = alert['price_target_cents']
        
        logger.info(f"🔄 Procesando alerta {alert_id} - Objetivo: {target_price_cents/100:.2f}€")
        
        # 1. Buscar vuelos
        search_result = self.search_flights_for_alert(alert)
        
        if not search_result.get('success') or not search_result.get('flights'):
            logger.warning(f"⚠️ No hay vuelos disponibles para alerta {alert_id}")
            return
        
        flights = search_result['flights']
        
        # 2. Encontrar el vuelo más barato
        cheapest_flight = min(flights, key=lambda f: f.get('price_euros', 999))
        cheapest_price_cents = int(cheapest_flight['price_euros'] * 100)
        
        # 3. Guardar snapshot siempre
        self.save_search_snapshot(alert_id, cheapest_price_cents, cheapest_flight)
        
        # 4. Verificar si cumple objetivo de precio
        if cheapest_price_cents <= target_price_cents:
            logger.info(f"🎯 ¡PRECIO OBJETIVO ALCANZADO! Alerta {alert_id}: {cheapest_price_cents/100:.2f}€ <= {target_price_cents/100:.2f}€")
            
            # 5. Verificar si ya se envió notificación reciente
            if self.check_recent_notification(alert_id):
                logger.info(f"📬 Ya se envió notificación reciente para alerta {alert_id}")
                return
            
            # 6. Enviar notificación
            if self.send_telegram_notification(alert['telegram_id'], alert, cheapest_flight):
                # 7. Registrar notificación enviada
                self.save_notification_sent(alert_id, cheapest_price_cents)
                logger.info(f"✅ Alerta {alert_id} procesada y notificación enviada")
            else:
                logger.error(f"❌ Error enviando notificación para alerta {alert_id}")
        else:
            logger.info(f"💰 Precio actual {cheapest_price_cents/100:.2f}€ > objetivo {target_price_cents/100:.2f}€ (alerta {alert_id})")
    
    def run_check_cycle(self):
        """Ejecutar un ciclo completo de verificación"""
        logger.info("🔄 Iniciando ciclo de verificación de alertas")
        
        start_time = datetime.now()
        
        # Obtener alertas activas
        alerts = self.get_active_alerts()
        
        if not alerts:
            logger.info("😴 No hay alertas activas para procesar")
            return
        
        # Procesar cada alerta
        processed_count = 0
        notifications_sent = 0
        
        for alert in alerts:
            try:
                self.process_alert(alert)
                processed_count += 1
                
                # Pequeño delay entre alertas para no saturar la API
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error procesando alerta {alert['id']}: {e}")
        
        elapsed_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Ciclo completado: {processed_count} alertas procesadas en {elapsed_time:.1f}s")
    
    def run(self):
        """Ejecutar el worker principal"""
        logger.info("🚀 Worker de alertas de vuelos iniciado")
        logger.info(f"⏰ Intervalo de verificación: {self.check_interval_minutes} minutos")
        
        while True:
            try:
                self.run_check_cycle()
                
                # Esperar hasta el siguiente ciclo
                logger.info(f"💤 Esperando {self.check_interval_minutes} minutos hasta el próximo ciclo...")
                time.sleep(self.check_interval_minutes * 60)
                
            except KeyboardInterrupt:
                logger.info("⏹️ Worker detenido por usuario")
                break
            except Exception as e:
                logger.error(f"💥 Error inesperado en worker: {e}")
                logger.info("🔄 Reintentando en 5 minutos...")
                time.sleep(300)  # 5 minutos


def main():
    """Función principal"""
    # Cargar variables de entorno desde .env si existe
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logger.info(f"📁 Variables de entorno cargadas desde {env_path}")
        logger.info(f"RAPIDAPI_KEY detectada: {os.getenv('RAPIDAPI_KEY')}")

    # Verificar variables críticas
    if not os.getenv('RAPIDAPI_KEY'):
        logger.error("❌ RAPIDAPI_KEY no configurada")
        return

    if not os.getenv('TELEGRAM_BOT_TOKEN'):
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN no configurado - no se enviarán notificaciones")

    # Instanciar FlightSearchAPI después de cargar .env
    flights_api = FlightSearchAPI() if FlightSearchAPI else None

    # Iniciar worker
    worker = FlightAlertWorker(flights_api)
    worker.run()

if __name__ == "__main__":
    main()
