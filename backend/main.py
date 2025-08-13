from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import datetime
import db
import json
import os
from dotenv import load_dotenv
from flights_api import flights_api, search_flights_for_alert

# Cargar variables de entorno
load_dotenv()

# configuración de la app fastapi
app = FastAPI(
    title="Bot Agente Viajes API",
    description="API REST para gestión de alertas de vuelos",
    version="1.0.0"
)

# Endpoint simple para verificar que la API está funcionando
@app.get("/health")
def health():
    return {"status": "ok"}


# Devuelve todos los usuarios registrados en el sistema
@app.get("/users")
def list_users():
    """
    Devuelve una lista de usuarios desde la tabla users.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, telegram_id, created_at FROM users ORDER BY id ASC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    users = [
        {"id": row[0], "telegram_id": row[1], "created_at": row[2].isoformat()} for row in rows
    ]
    return {"users": users}

# Modelo de datos para crear un usuario nuevo
class UserCreate(BaseModel):
    telegram_user_id: int = Field(..., description="ID del usuario de Telegram")


@app.post("/users")
def create_user(user: UserCreate):
    """
    Crea un nuevo usuario en la tabla users.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO users (telegram_id) 
            VALUES (%s) 
            RETURNING id;
            """,
            (user.telegram_user_id,)
        )
        user_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    
    return {"message": "Usuario creado exitosamente", "user_id": user_id}


# Devuelve todas las alertas activas de un usuario específico
@app.get("/alerts")
def list_alerts(user_id: int = Query(..., description="ID del usuario")):
    """
    Devuelve todas las alertas de un usuario concreto.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT id, origin, destination, date_from, date_to, price_target_cents, airlines_include, airlines_exclude, max_stops, airports_alternatives, active, created_at
        FROM alerts
        WHERE user_id = %s
        ORDER BY created_at DESC;
        """,
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    alerts = []
    for row in rows:
        alerts.append({
            "id": row[0],
            "origin": row[1],
            "destination": row[2],
            "date_from": row[3].isoformat(),
            "date_to": row[4].isoformat() if row[4] else None,
            "price_target_cents": row[5],
            "airlines_include": row[6],
            "airlines_exclude": row[7],
            "max_stops": row[8],
            "airports_alternatives": row[9],
            "active": row[10],
            "created_at": row[11].isoformat()
        })
    return {"alerts": alerts}


# Devuelve el historial completo de búsquedas y precios de una alerta
@app.get("/alerts/{alert_id}/price-history")
def get_alert_price_history(alert_id: int):
    """
    Devuelve el histórico de precios de una alerta específica.
    Útil para mostrar gráficos de evolución del precio.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    
    # Verificar que la alerta existe
    cur.execute("SELECT id FROM alerts WHERE id = %s", (alert_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    # Obtener histórico de precios
    cur.execute(
        """
        SELECT id, searched_at, price_cents, raw_response
        FROM search_snapshots
        WHERE alert_id = %s
        ORDER BY searched_at ASC;
        """,
        (alert_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            "snapshot_id": row[0],
            "searched_at": row[1].isoformat(),
            "price_cents": row[2],
            "price_euros": round(row[2] / 100, 2) if row[2] else None,
            "raw_data": row[3]
        })
    
    return {"alert_id": alert_id, "price_history": history}


# Marca una alerta como inactiva (soft delete)
@app.delete("/alerts/{alert_id}")
def delete_alert(alert_id: int):
    """
    Elimina una alerta específica por su ID.
    También elimina todos los registros relacionados (histórico de precios y notificaciones).
    """
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        # Verificar que la alerta existe
        cur.execute("SELECT id FROM alerts WHERE id = %s", (alert_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        # Eliminar notificaciones relacionadas
        cur.execute("DELETE FROM notifications_sent WHERE alert_id = %s", (alert_id,))
        
        # Eliminar histórico de precios
        cur.execute("DELETE FROM search_snapshots WHERE alert_id = %s", (alert_id,))
        
        # Eliminar la alerta
        cur.execute("DELETE FROM alerts WHERE id = %s", (alert_id,))
        
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    
    return {"message": f"Alerta {alert_id} eliminada correctamente"}


# Modelo para actualizar una alerta
class AlertUpdate(BaseModel):
    active: Optional[bool] = Field(None, description="Activar/desactivar la alerta")
    price_target_cents: Optional[int] = Field(None, description="Nuevo precio objetivo en céntimos")
    airlines_include: Optional[List[str]] = Field(None, description="Nuevas aerolíneas a incluir")
    airlines_exclude: Optional[List[str]] = Field(None, description="Nuevas aerolíneas a excluir")
    max_stops: Optional[int] = Field(None, description="Nuevas escalas máximas")


# PATCH /alerts/{id}
@app.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, alert_update: AlertUpdate):
    """
    Actualiza una alerta específica (activar/desactivar, cambiar precio objetivo, etc.).
    Solo se actualizan los campos proporcionados.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        # Verificar que la alerta existe
        cur.execute("SELECT id FROM alerts WHERE id = %s", (alert_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        # Preparar los campos a actualizar
        update_fields = []
        update_values = []
        
        if alert_update.active is not None:
            update_fields.append("active = %s")
            update_values.append(alert_update.active)
        
        if alert_update.price_target_cents is not None:
            update_fields.append("price_target_cents = %s")
            update_values.append(alert_update.price_target_cents)
        
        if alert_update.airlines_include is not None:
            update_fields.append("airlines_include = %s")
            update_values.append(alert_update.airlines_include)
        
        if alert_update.airlines_exclude is not None:
            update_fields.append("airlines_exclude = %s")
            update_values.append(alert_update.airlines_exclude)
        
        if alert_update.max_stops is not None:
            update_fields.append("max_stops = %s")
            update_values.append(alert_update.max_stops)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        
        # Ejecutar la actualización
        update_values.append(alert_id)  # Para el WHERE
        query = f"UPDATE alerts SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, update_values)
        
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    
    return {"message": f"Alerta {alert_id} actualizada correctamente"}


# Modelo de datos para crear una alerta
class AlertCreate(BaseModel):
    user_id: int = Field(..., description="ID del usuario que crea la alerta")
    origin: str = Field(..., min_length=3, max_length=3, description="Código IATA de origen")
    destination: str = Field(..., min_length=3, max_length=3, description="Código IATA de destino")
    date_from: datetime.date = Field(..., description="Fecha de salida (YYYY-MM-DD)")
    date_to: Optional[datetime.date] = Field(None, description="Fecha de regreso (opcional)")
    price_target_cents: Optional[int] = Field(None, description="Precio objetivo en céntimos (opcional)")
    airlines_include: Optional[List[str]] = Field(None, description="Aerolíneas a incluir (opcional)")
    airlines_exclude: Optional[List[str]] = Field(None, description="Aerolíneas a excluir (opcional)")
    max_stops: Optional[int] = Field(None, description="Escalas máximas (opcional)")
    airports_alternatives: Optional[List[str]] = Field(None, description="Aeropuertos alternativos (opcional)")

# Crea una nueva alerta de vuelo para un usuario
@app.post("/alerts")
def create_alert(alert: AlertCreate):
    """
    Crea una nueva alerta de vuelo y la guarda en la base de datos.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO alerts (
                user_id, origin, destination, date_from, date_to, price_target_cents,
                airlines_include, airlines_exclude, max_stops, airports_alternatives, active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            RETURNING id;
            """,
            (
                alert.user_id,
                alert.origin.upper(),
                alert.destination.upper(),
                alert.date_from,
                alert.date_to,
                alert.price_target_cents,
                alert.airlines_include,
                alert.airlines_exclude,
                alert.max_stops,
                alert.airports_alternatives
            )
        )
        alert_id = cur.fetchone()[0]
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    return {"alert_id": alert_id, "message": "Alerta creada correctamente"}


# Lanza una búsqueda inmediata de precios para testing
@app.post("/check-now/{alert_id}")
def check_alert_now(alert_id: int):
    """
    Lanza una búsqueda manual inmediata para una alerta específica.
    Útil para testing o búsquedas bajo demanda.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        # Verificar que la alerta existe
        cur.execute("SELECT id, origin, destination, date_from FROM alerts WHERE id = %s", (alert_id,))
        alert_data = cur.fetchone()
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alerta no encontrada")
        
        # Por ahora, insertamos un precio de ejemplo (más tarde conectaremos con APIs reales)
        # En un caso real, aquí llamo a la API de Tequila/Amadeus por ejemplo o kiwi
        example_price = 15000  # 150€ en céntimos
        
        cur.execute(
            """
            INSERT INTO search_snapshots (alert_id, price_cents, raw_response)
            VALUES (%s, %s, %s)
            RETURNING id;
            """,
            (alert_id, example_price, json.dumps({"example": "manual_check", "price": example_price}))
        )
        
        snapshot_id = cur.fetchone()[0]
        conn.commit()
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()
    
    return {
        "message": f"Búsqueda manual ejecutada para alerta {alert_id}",
        "snapshot_id": snapshot_id,
        "price_found": f"{example_price/100}€"
    }

# ============================================================================
# ENDPOINTS PARA API DE VUELOS REALES
# ============================================================================

class FlightSearchRequest(BaseModel):
    origin: str = Field(..., description="Código IATA del aeropuerto de origen", min_length=3, max_length=3)
    destination: str = Field(..., description="Código IATA del aeropuerto de destino", min_length=3, max_length=3)
    date_from: str = Field(..., description="Fecha de salida (DD/MM/YYYY)")
    date_to: Optional[str] = Field(None, description="Fecha hasta para salida (DD/MM/YYYY)")
    return_from: Optional[str] = Field(None, description="Fecha de regreso desde (DD/MM/YYYY)")
    return_to: Optional[str] = Field(None, description="Fecha de regreso hasta (DD/MM/YYYY)")
    max_stopovers: int = Field(2, description="Máximo número de escalas")
    limit: int = Field(10, description="Límite de resultados")

@app.post("/flights/search")
def search_flights(request: FlightSearchRequest):
    """
    Busca vuelos reales usando la API de Tequila/Kiwi.com.
    
    Este endpoint permite buscar vuelos en tiempo real con precios actuales.
    Si no hay API key configurada, devuelve datos mock para testing.
    """
    try:
        # Validar códigos IATA
        if request.origin.upper() == request.destination.upper():
            raise HTTPException(status_code=400, detail="El origen y destino no pueden ser iguales")
        
        # Buscar vuelos usando la API
        result = flights_api.search_flights(
            origin=request.origin.upper(),
            destination=request.destination.upper(),
            date_from=request.date_from,
            date_to=request.date_to,
            return_from=request.return_from,
            return_to=request.return_to,
            max_stopovers=request.max_stopovers,
            limit=request.limit
        )
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Error buscando vuelos'))
        
        return {
            "success": True,
            "flights": result['flights'],
            "total_results": result['total_results'],
            "api_used": result.get('api_used', 'tequila'),
            "search_params": {
                "origin": request.origin.upper(),
                "destination": request.destination.upper(),
                "date_from": request.date_from,
                "return_from": request.return_from,
                "max_stopovers": request.max_stopovers
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.get("/flights/locations")
def search_locations(query: str = Query(..., description="Nombre de ciudad o aeropuerto para buscar")):
    """
    Busca códigos IATA de aeropuertos/ciudades.
    
    Útil para autocompletar y validar códigos IATA.
    """
    try:
        if len(query.strip()) < 2:
            raise HTTPException(status_code=400, detail="La búsqueda debe tener al menos 2 caracteres")
        
        result = flights_api.get_locations(query)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', 'Error buscando ubicaciones'))
        
        return {
            "success": True,
            "locations": result['locations'],
            "query": query
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/alerts/{alert_id}/search-real")
def search_flights_for_alert_endpoint(alert_id: int):
    """
    Busca vuelos reales para una alerta específica y guarda el resultado.
    
    Este endpoint toma los parámetros de una alerta existente y busca vuelos
    reales usando la API de Tequila, guardando los resultados en el historial.
    """
    conn = db.get_connection()
    cur = conn.cursor()
    
    try:
        # Obtener datos de la alerta
        cur.execute("""
            SELECT user_id, origin, destination, date_from, date_to, max_stops 
            FROM alerts WHERE id = %s AND is_active = true
        """, (alert_id,))
        
        alert_data = cur.fetchone()
        if not alert_data:
            raise HTTPException(status_code=404, detail="Alerta no encontrada o inactiva")
        
        user_id, origin, destination, date_from, date_to, max_stops = alert_data
        
        # Buscar vuelos reales
        search_result = flights_api.search_flights(
            origin=origin,
            destination=destination,
            date_from=date_from.strftime('%d/%m/%Y'),
            return_from=date_to.strftime('%d/%m/%Y') if date_to else None,
            max_stopovers=max_stops or 2,
            limit=5
        )
        
        if not search_result['success']:
            raise HTTPException(status_code=500, detail=f"Error buscando vuelos: {search_result.get('error')}")
        
        flights = search_result['flights']
        if not flights:
            # Guardar búsqueda sin resultados
            cur.execute("""
                INSERT INTO search_snapshots (alert_id, price_cents, found_at, details)
                VALUES (%s, %s, %s, %s)
                RETURNING id
            """, (alert_id, None, datetime.datetime.now(), json.dumps({"message": "No flights found"})))
            
            snapshot_id = cur.fetchone()[0]
            conn.commit()
            
            return {
                "success": True,
                "message": "Búsqueda completada pero no se encontraron vuelos",
                "flights_found": 0,
                "snapshot_id": snapshot_id,
                "api_used": search_result.get('api_used')
            }
        
        # Guardar el mejor precio encontrado
        best_flight = min(flights, key=lambda x: x.get('price_euros', 9999))
        best_price_cents = int(best_flight['price_euros'] * 100)
        
        # Guardar en historial
        cur.execute("""
            INSERT INTO search_snapshots (alert_id, price_cents, found_at, details)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (alert_id, best_price_cents, datetime.datetime.now(), json.dumps({
            "flights_found": len(flights),
            "best_price_euros": best_flight['price_euros'],
            "best_flight": best_flight,
            "api_used": search_result.get('api_used'),
            "total_results": len(flights)
        })))
        
        snapshot_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            "success": True,
            "message": f"Búsqueda completada para alerta {alert_id}",
            "flights_found": len(flights),
            "best_price_euros": best_flight['price_euros'],
            "best_flight": {
                "price": best_flight['price_euros'],
                "origin": best_flight['origin'],
                "destination": best_flight['destination'],
                "departure": best_flight['departure_time'],
                "airline": best_flight['airlines'][0] if best_flight['airlines'] else 'Unknown',
                "stops": best_flight['stops']
            },
            "snapshot_id": snapshot_id,
            "api_used": search_result.get('api_used')
        }
        
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# lanzo server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
