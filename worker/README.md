# 🤖 Worker de Alertas de Vuelos

Sistema de monitoreo automático que verifica alertas de vuelos cada 15 minutos y envía notificaciones cuando encuentra precios objetivo.

## 📋 Funcionalidades

- **🔄 Monitoreo Automático**: Revisa alertas activas cada 15 minutos
- **✈️ Búsqueda de Vuelos**: Integración con RapidAPI Kiwi.com (300 búsquedas/mes gratis)
- **📱 Notificaciones Telegram**: Envío automático cuando se cumple precio objetivo
- **💾 Historial**: Guarda snapshots de precios para análisis
- **🚫 Anti-spam**: No envía múltiples notificaciones en 24h por la misma alerta

## ⚙️ Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en esta carpeta y añade tus credenciales y configuración necesarias.

### 2. Dependencias

```bash
# Instalar dependencias Python
pip3 install requests psycopg2-binary python-dotenv
```

### 3. Base de Datos

Asegúrate de que PostgreSQL esté ejecutándose y la base de datos `vuelos` o como la quieras llamar esté creada con las tablas necesarias.

## 🚀 Uso

### Inicio Automático (Recomendado)

```bash
# Usar script de inicio
./start_worker.sh
```

### Inicio Manual

```bash
# Ejecutar directamente
python3 worker.py
```

## 📊 Monitoreo

### Logs del Worker

```bash
# Ver logs en tiempo real
tail -f logs/worker.log

# o logs del sistema
tail -f /tmp/worker.log
```

### Estado de Alertas

El worker registra en los logs:
- ✅ Alertas procesadas correctamente
- 🎯 Precios objetivo alcanzados
- 📱 Notificaciones enviadas
- ❌ Errores de conexión o API

## 🔧 Arquitectura

```
worker.py
├── FlightAlertWorker
│   ├── get_active_alerts()      # Obtiene alertas de PostgreSQL
│   ├── search_flights_for_alert() # Busca vuelos vía RapidAPI
│   ├── save_search_snapshot()   # Guarda historial en BD
│   ├── send_telegram_notification() # Envía alertas por Telegram
│   └── process_alert()          # Procesa una alerta individual
└── run_check_cycle()            # Ejecuta ciclo cada 15 minutos
```

## 📱 Formato de Notificaciones

```
🎉 ¡ALERTA DE VUELO ENCONTRADO! ✈️

Ruta: MAD → BCN
Fecha: 15/01/2024
Precio encontrado: 53.00€
Tu objetivo: 60.00€
Aerolínea: Iberia Airlines
Duración: 1h 30m
Escalas: 0

🔗 [RESERVAR AHORA](https://booking-link)

💡 Precio encontrado por tu alerta automática
```


## 📈 Optimización

### Intervalo de Verificación

```bash
# Cambiar intervalo en .env
WORKER_INTERVAL_MINUTES=10  # 10 minutos (más frecuente)
WORKER_INTERVAL_MINUTES=30  # 30 minutos (menos frecuente)
```

### Límite de Vuelos por Búsqueda

El worker busca máximo 5 vuelos por alerta para optimizar el uso de la API.

## 💡 Consejos

1. **Ejecutar 24/7**: Usar un VPS o servidor para monitoreo continuo
2. **Múltiples alertas**: El worker procesa todas las alertas activas automáticamente
3. **Historial**: Los snapshots de precios se guardan para análisis posterior
4. **Debugging**: Los logs detallados ayudan a identificar problemas

---

## 🔗 Enlaces Útiles

- [RapidAPI Kiwi.com Cheap Flights](https://rapidapi.com/kiwi/api/kiwi-com-cheap-flights)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
