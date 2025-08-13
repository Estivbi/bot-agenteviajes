# ============================================================================
# INTEGRACIÓN API DE VUELOS - KIWI.COM VIA RAPIDAPI
# ============================================================================
# Módulo para buscar vuelos reales usando RapidAPI Kiwi.com Cheap Flights
# 300 búsquedas/mes gratis - Datos reales de vuelos
# ============================================================================

import os
import requests
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, date, timedelta
import json
import base64

logger = logging.getLogger(__name__)

class FlightSearchAPI:
    """
    Cliente principal para búsqueda de vuelos usando RapidAPI Kiwi.com Cheap Flights
    300 búsquedas/mes gratis - Datos reales de vuelos de Kiwi.com
    """
    
    def __init__(self):
        self.api_key = os.getenv('RAPIDAPI_KEY')
        self.base_url = "https://kiwi-com-cheap-flights.p.rapidapi.com"
        
    def search_flights(self, origin: str, destination: str, date_from: str, **kwargs) -> Dict[str, Any]:
        """Buscar vuelos usando RapidAPI Kiwi.com Cheap Flights"""
        
        if not self.api_key:
            logger.warning("No RapidAPI key configured")
            return self._no_api_response(origin, destination, date_from)
        
        try:
            # Usar endpoint round-trip de RapidAPI Kiwi.com Cheap Flights
            url = f"{self.base_url}/round-trip"
            
            headers = {
                'x-rapidapi-host': 'kiwi-com-cheap-flights.p.rapidapi.com',
                'x-rapidapi-key': self.api_key
            }
            
            # Transformar códigos de aeropuerto a formato requerido por Kiwi
            source = self._format_location_for_kiwi(origin)
            destination_formatted = self._format_location_for_kiwi(destination)
            
            # Parámetros mínimos esenciales para el bot
            params = {
                'source': source,
                'destination': destination_formatted,
                'currency': 'eur',
                'locale': 'es',  # Respuesta en español
                'sortBy': 'PRICE',
                'transportTypes': 'FLIGHT',
                'contentProviders': 'KIWI',
                'limit': kwargs.get('limit', 10)
            }
            
            logger.info(f"🥝 Kiwi Cheap Flights búsqueda: {source} → {destination_formatted}")
            logger.info(f"Parámetros: {params}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                flights = self._process_kiwi_results(data, origin, destination)
                
                return {
                    'success': True,
                    'flights': flights,
                    'total_results': len(flights),
                    'api_used': 'kiwi_rapidapi'
                }
            else:
                logger.error(f"Kiwi Cheap Flights error: {response.status_code} - {response.text}")
                return self._no_api_response(origin, destination, date_from)
                
        except Exception as e:
            logger.error(f"Kiwi Cheap Flights exception: {e}")
            return self._no_api_response(origin, destination, date_from)
    
    def _format_location_for_kiwi(self, airport_code: str) -> str:
        """Formatear ubicación para RapidAPI Kiwi.com (requiere formato específico)"""
        # Mapeo de códigos de aeropuerto a formato Kiwi
        location_mapping = {
            'MAD': 'City:madrid_es',
            'BCN': 'City:barcelona_es', 
            'LHR': 'City:london_gb',
            'CDG': 'City:paris_fr',
            'FCO': 'City:rome_it',
            'AMS': 'City:amsterdam_nl',
            'FRA': 'City:frankfurt_de',
            'MUC': 'City:munich_de',
            'VIE': 'City:vienna_at',
            'ZUR': 'City:zurich_ch',
            'JFK': 'City:new-york_us',
            'LAX': 'City:los-angeles_us',
            'ORD': 'City:chicago_us',
            'MIA': 'City:miami_us',
            'DXB': 'City:dubai_ae',
            'SIN': 'City:singapore_sg',
            'NRT': 'City:tokyo_jp',
            'ICN': 'City:seoul_kr',
            'PEK': 'City:beijing_cn',
            'SYD': 'City:sydney_au',
            'MEL': 'City:melbourne_au',
            'YYZ': 'City:toronto_ca',
            'YVR': 'City:vancouver_ca',
            'GRU': 'City:sao-paulo_br',
            'GIG': 'City:rio-de-janeiro_br',
            'BOG': 'City:bogota_co',
            'LIM': 'City:lima_pe',
            'SCL': 'City:santiago_cl',
            'EZE': 'City:buenos-aires_ar'
        }
        
        # Si tenemos el mapeo específico, usarlo
        if airport_code.upper() in location_mapping:
            return location_mapping[airport_code.upper()]
        
        # Alternativamente, intentar con formato Country
        country_mapping = {
            'ES': 'Country:ES',  # España
            'FR': 'Country:FR',  # Francia
            'IT': 'Country:IT',  # Italia
            'DE': 'Country:DE',  # Alemania
            'GB': 'Country:GB',  # Reino Unido
            'US': 'Country:US'   # Estados Unidos
        }
        
        # Como fallback, usar formato City genérico
        return f'City:{airport_code.lower()}'

    def _process_kiwi_results(self, data: Dict, origin: str, destination: str) -> List[Dict]:
        """Procesar resultados de RapidAPI Kiwi.com Round Trip API"""
        flights = []
        
        # La respuesta real tiene esta estructura
        itineraries = data.get('itineraries', [])
        
        for i, itinerary in enumerate(itineraries[:12]):  # Máximo 12 resultados
            try:
                # Información básica del precio
                price_info = itinerary.get('price', {})
                price_eur = float(price_info.get('amount', 200))
                
                # Información del vuelo de ida
                outbound = itinerary.get('outbound', {})
                outbound_segments = outbound.get('sectorSegments', [])
                
                if not outbound_segments:
                    continue
                
                first_segment = outbound_segments[0].get('segment', {})
                
                # Información de origen y destino
                source_info = first_segment.get('source', {})
                dest_info = first_segment.get('destination', {})
                
                # Extraer información de aerolínea
                carrier = first_segment.get('carrier', {})
                airline = carrier.get('name', 'Unknown')
                
                # Extraer ciudades desde la estructura real
                origin_city = source_info.get('city', {}).get('name', f'Ciudad {origin}')
                dest_city = dest_info.get('city', {}).get('name', f'Ciudad {destination}')
                
                processed_flight = {
                    'id': f'kiwi_round_{itinerary.get("id", i)}',
                    'price_euros': float(price_eur),
                    'origin': origin,
                    'destination': destination,
                    'origin_city': origin_city,
                    'destination_city': dest_city,
                    'departure_time': source_info.get('localTime', '2025-09-15T08:00:00'),
                    'arrival_time': dest_info.get('localTime', '2025-09-15T10:30:00'),
                    'airlines': [airline],
                    'stops': len(outbound_segments) - 1,
                    'booking_link': self._extract_booking_link_real(itinerary),
                    'found_at': datetime.now().isoformat(),
                    'api_used': 'kiwi_round_trip',
                    'flight_duration': self._format_duration(first_segment.get('duration', 7200)),
                    'availability': itinerary.get('lastAvailable', {}).get('seatsLeft', 9),
                    'validating_airline': airline,
                    'cabin_class': first_segment.get('cabinClass', 'ECONOMY'),
                    'flight_number': f"{carrier.get('code', 'XX')}{first_segment.get('code', '000')}"
                }
                
                flights.append(processed_flight)
                
            except Exception as e:
                logger.error(f"Error procesando itinerario Kiwi: {e}")
                continue
        
        # Ordenar por precio
        flights.sort(key=lambda x: x.get('price_euros', 9999))
        return flights
    
    def _extract_booking_link_real(self, itinerary: Dict) -> str:
        """Extraer enlace de reserva del itinerario real"""
        booking_options = itinerary.get('bookingOptions', {}).get('edges', [])
        if booking_options:
            first_option = booking_options[0].get('node', {})
            booking_url = first_option.get('bookingUrl', '')
            if booking_url:
                return f"https://kiwi.com{booking_url}"
        return 'https://kiwi.com'
    
    def _format_duration(self, duration_seconds: int) -> str:
        """Formatear duración en segundos a formato legible"""
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        return f"PT{hours}H{minutes}M"
    
    def _format_date_for_kiwi(self, date_str: str) -> str:
        """Kiwi usa formato DD/MM/YYYY"""
        try:
            if '/' in date_str and len(date_str) == 10:
                # Ya está en formato DD/MM/YYYY
                return date_str
            elif '-' in date_str:
                # Convertir de YYYY-MM-DD a DD/MM/YYYY
                parsed = datetime.strptime(date_str, "%Y-%m-%d")
                return parsed.strftime('%d/%m/%Y')
            return date_str
        except:
            return date_str
    
    def _calculate_duration(self, departure: str, arrival: str) -> str:
        """Calcular duración del vuelo"""
        try:
            if departure and arrival:
                dep_time = datetime.fromisoformat(departure.replace('Z', '+00:00'))
                arr_time = datetime.fromisoformat(arrival.replace('Z', '+00:00'))
                duration = arr_time - dep_time
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                return f"PT{int(hours)}H{int(minutes)}M"
            return "2h 30m"
        except:
            return "2h 30m"
    
    def _no_api_response(self, origin: str, destination: str, date_from: str) -> Dict[str, Any]:
        """Respuesta cuando no hay API key o falla"""
        return {
            'success': False,
            'error': 'RapidAPI no configurada o sin créditos',
            'flights': [],
            'total_results': 0,
            'api_used': 'rapidapi_error'
        }
    
    def get_locations(self, query: str) -> Dict[str, Any]:
        """
        Búsqueda básica de ubicaciones (códigos IATA comunes)
        """
        mock_locations = {
            'madrid': [{'code': 'MAD', 'name': 'Madrid-Barajas Airport', 'city': 'Madrid', 'country': 'Spain'}],
            'barcelona': [{'code': 'BCN', 'name': 'Barcelona-El Prat Airport', 'city': 'Barcelona', 'country': 'Spain'}],
            'london': [{'code': 'LHR', 'name': 'Heathrow Airport', 'city': 'London', 'country': 'United Kingdom'}],
            'paris': [{'code': 'CDG', 'name': 'Charles de Gaulle Airport', 'city': 'Paris', 'country': 'France'}],
            'rome': [{'code': 'FCO', 'name': 'Fiumicino Airport', 'city': 'Rome', 'country': 'Italy'}],
            'amsterdam': [{'code': 'AMS', 'name': 'Schiphol Airport', 'city': 'Amsterdam', 'country': 'Netherlands'}],
            'frankfurt': [{'code': 'FRA', 'name': 'Frankfurt Airport', 'city': 'Frankfurt', 'country': 'Germany'}],
            'new york': [{'code': 'JFK', 'name': 'Kennedy Airport', 'city': 'New York', 'country': 'United States'}],
            'los angeles': [{'code': 'LAX', 'name': 'Los Angeles Airport', 'city': 'Los Angeles', 'country': 'United States'}],
        }
        
        query_lower = query.lower()
        locations = []
        
        for city, location_list in mock_locations.items():
            if query_lower in city:
                locations.extend(location_list)
        
        return {
            'success': True,
            'locations': locations[:5]  # Máximo 5 resultados
        }

# Instancia global
flights_api = FlightSearchAPI()

def search_flights_for_alert(alert_data: Dict) -> Dict[str, Any]:
    """
    Función de conveniencia para buscar vuelos basados en una alerta.
    """
    return flights_api.search_flights(
        origin=alert_data['origin'],
        destination=alert_data['destination'],
        date_from=alert_data['departure_date'],
        return_from=alert_data.get('return_date'),
        limit=5
    )
