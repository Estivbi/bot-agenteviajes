-- Esquema inicial de la base de datos
-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de alertas
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    origin VARCHAR(3) NOT NULL,
    destination VARCHAR(3) NOT NULL,
    date_from DATE NOT NULL,
    date_to DATE,
    price_target_cents INTEGER,
    airlines_include TEXT[],
    airlines_exclude TEXT[],
    max_stops INTEGER,
    airports_alternatives TEXT[],
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de snapshots de precios
CREATE TABLE IF NOT EXISTS search_snapshots (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    found_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    price_cents INTEGER,
    details JSONB
);

-- Tabla de notificaciones enviadas
CREATE TABLE IF NOT EXISTS notifications_sent (
    id SERIAL PRIMARY KEY,
    alert_id INTEGER REFERENCES alerts(id),
    price_cents INTEGER,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
