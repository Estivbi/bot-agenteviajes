from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import datetime
import db
import json

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


# Ejemplo real: endpoint que lista usuarios desde la base de datos
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


# GET /alerts?user_id=123
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


# GET /alerts/{id}/price-history
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


# DELETE /alerts/{id}
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


# POST /check-now - Trigger manual para búsqueda
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
        # En un caso real, aquí llamarías a la API de Tequila/Amadeus
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
