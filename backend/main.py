from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from . import db

app = FastAPI()

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

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
import datetime
from . import db

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
