# Bot Agente de Viajes ✈️

Sistema completo para detectar vuelos baratos con alertas personalizadas y notificaciones por Telegram.

## � **API de Vuelos: Kiwi.com via RapidAPI**
- **300 búsquedas gratuitas/mes** sin tarjeta de crédito
- **Datos reales de vuelos** de Kiwi.com (precios desde 53€)
- **Respuesta en español** con moneda en euros
- **Enlaces de reserva válidos** directos a Kiwi.com

## �🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │◄──►│  FastAPI Backend │◄──►│  PostgreSQL DB  │
│                 │    │                  │    │                 │
│ • Interfaz user │    │ • API REST       │    │ • Alertas       │
│ • Crear alertas │    │ • RapidAPI Kiwi  │    │ • Usuarios      │
│ • Ver alertas   │    │ • CRUD completo  │    │ • Historial     │
│ • Eliminar      │    │ • 8 endpoints    │    │ • Notificaciones│
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         └────────────────────────┼─────────► RapidAPI Kiwi.com
                                  │           300 búsquedas/mes
                                  │           Datos reales de vuelos
                                  └─────────► Worker Background
                                             Monitoreo automático
```

## 📁 Estructura del Proyecto

```
bot-agenteviajes/
├── backend/               # API FastAPI
│   ├── main.py           # Endpoints REST (8 endpoints)
│   ├── db.py             # Conexión PostgreSQL
│   └── requirements.txt  # Dependencias backend
├── bot/                  # Bot de Telegram
│   ├── bot.py           # Bot completo con conversaciones
│   ├── .env             # Variables de entorno
│   ├── .env.example     # Plantilla de configuración
│   └── README_BOT.md    # Documentación específica del bot
├── db/                  # Base de datos
│   └── schema.sql       # Schema completo (4 tablas)
├── docker-compose.yml   # PostgreSQL containerizado
├── LEVANTAR_SERVIDORES.md  # Guía de inicio completa
└── README.md           # Este archivo
```

## 🚀 Inicio Rápido

### 1. Configuración Inicial

```bash
# Clonar y entrar al proyecto
git clone <repo>
cd bot-agenteviajes

# Crear y activar entorno virtual
python3 -m venv venv
source venv/bin/activate

```bash
# Instalar dependencias
pip install fastapi uvicorn psycopg2-binary python-telegram-bot python-dotenv requests

# Configurar RapidAPI Kiwi.com (300 búsquedas/mes gratis)
# 1. Regístrate en: https://rapidapi.com/kiwi.com1/api/cheap-flights
# 2. Crea cuenta gratuita (sin tarjeta de crédito)
# 3. Obtén tu API key para "Cheap Flights"
```

### 2. Variables de Entorno

```bash
# En el archivo .env del bot
RAPIDAPI_KEY=tu_clave_rapidapi_aquí

# En el archivo backend/.env  
RAPIDAPI_KEY=tu_clave_rapidapi_aquí
```

### 2. Base de Datos (PostgreSQL con Docker)

```bash
# Iniciar PostgreSQL
docker-compose up -d

# La base de datos se crea automáticamente con el schema
# Usuario: ++++ | Password: ++++++ | DB: vuelos
```

### 3. Backend API con Kiwi.com

```bash
# Desde el directorio raíz
cd backend
python main.py

# API disponible en: http://localhost:8000
# Documentación: http://localhost:8000/docs

# ✅ Ya integrado con RapidAPI Kiwi.com
# ✅ 300 búsquedas gratuitas/mes
# ✅ Datos reales de vuelos desde 53€
```

### 4. Worker Background (Monitoreo Automático)

```bash
# Worker para monitoreo automático de alertas
cd worker
./start_worker.sh

# O manualmente:
python3 worker.py

# ✅ Revisa alertas cada 15 minutos
# ✅ Envía notificaciones automáticas por Telegram
# ✅ Actualiza historial de precios automáticamente
# ✅ Proceso 24/7 en background
```

### 4. Bot de Telegram

```bash
# Configurar tokens en bot/.env
cd bot
cp .env.example .env
# Editar .env con:
# - TELEGRAM_BOT_TOKEN (de @BotFather)  
# - RAPIDAPI_KEY (de RapidAPI Kiwi.com)

# Ejecutar bot
python bot.py
```

## 🛠️ Funcionalidades Implementadas

### ✅ API de Vuelos (RapidAPI Kiwi.com)
- **300 búsquedas gratuitas/mes** sin necesidad de tarjeta
- **Datos reales de Kiwi.com** (precios desde 53€ MAD→BCN)
- **Respuesta en español** con moneda euros
- **Enlaces de reserva válidos** directos a Kiwi.com
- **Mapeo de 30+ aeropuertos** principales mundiales

### ✅ Backend API (FastAPI)
- **8 Endpoints REST** completamente funcionales
- **Health check** (`/health`)
- **CRUD Usuarios** (`GET/POST /users`)
- **CRUD Alertas** (`GET/POST/DELETE /alerts`)
- **Historial de precios** (`/alerts/{id}/price-history`)
- **Búsquedas manuales** (`/search`) con RapidAPI Kiwi.com
- **Base de datos PostgreSQL** con 4 tablas relacionadas

### ✅ Worker Background
- **Monitoreo automático cada 15 minutos** de alertas activas
- **Notificaciones por Telegram** cuando encuentra precios objetivo
- **Historial de precios** actualizado automáticamente
- **Anti-spam**: No envía múltiples notificaciones por la misma alerta en 24h
- **Procesamiento asíncrono** sin bloquear la API
- **Logging completo** para debugging y monitoreo
- **Script de inicio automatizado** con `start_worker.sh`

### ✅ Bot de Telegram
- **Interfaz conversacional** completa
- **Creación interactiva de alertas** (origen, destino, fechas, precio)
- **Gestión de alertas** (ver, eliminar)
- **Validaciones** (códigos IATA, fechas, precios)
- **Botones inline** y navegación fluida
- **Integración completa** con backend API

### ✅ Base de Datos
- **PostgreSQL 14** containerizado
- **4 tablas** con relaciones: users, alerts, search_snapshots, notifications_sent
- **Schema automático** en Docker startup
- **Datos persistentes** con volumen Docker

## 📊 Schema de Base de Datos

```sql
users                    alerts                  search_snapshots
├── id (PK)             ├── id (PK)            ├── id (PK)
├── telegram_id         ├── user_id (FK)       ├── alert_id (FK)
└── created_at          ├── origin             ├── price_cents
                        ├── destination        ├── found_at
                        ├── date_from          └── details
                        ├── date_to
                        ├── price_target_cents
                        ├── max_stops
                        └── is_active

notifications_sent
├── id (PK)
├── alert_id (FK)
├── price_cents
└── sent_at
```

## 🔧 API Endpoints

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/users` | Listar usuarios |
| POST | `/users` | Crear usuario |
| GET | `/alerts` | Listar alertas (por user_id) |
| POST | `/alerts` | Crear alerta |
| DELETE | `/alerts/{id}` | Eliminar alerta |
| GET | `/alerts/{id}/price-history` | Historial precios |
| POST | `/search` | Búsqueda manual |

## 🤖 Comandos del Bot

| Comando | Descripción |
|---------|-------------|
| `/start` | Iniciar bot y registro |
| `/crear_alerta` | Crear nueva alerta |
| `/mis_alertas` | Ver alertas activas |
| `/help` | Mostrar ayuda |
| `/cancel` | Cancelar operación |

## 📖 Documentación Adicional

- **[bot/README_BOT.md](./bot/README_BOT.md)** - Documentación específica del bot de Telegram
- **API Docs** - Disponible en `http://localhost:8000/docs` cuando el backend esté corriendo

## 🔄 Estado del Proyecto

### ✅ Completado
- ✅ **Backend API completo** (8 endpoints) con RapidAPI Kiwi.com
- ✅ **Base de datos PostgreSQL** funcional con 4 tablas
- ✅ **Bot Telegram** con todas las funcionalidades básicas
- ✅ **Worker de monitoreo automático** con notificaciones 24/7
- ✅ **Integración completa** backend-bot-database-worker
- ✅ **Documentación completa** y setup automatizado
- ✅ **300 búsquedas/mes gratuitas** con RapidAPI Kiwi.com

### 🚧 Próximamente
- ⏳ **Interface web** alternativa para gestión de alertas
- ⏳ **Sistema de ML** para predicción de precios
- ⏳ **Múltiples APIs** de vuelos (Amadeus, Skyscanner)
- ⏳ **Dashboard de analytics** para tendencias de precios
- ⏳ **Alertas por email** además de Telegram

## 🤝 Contribución

1. Fork del proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

---
*Desarrollado como sistema de alertas de vuelos inteligente* ✈️
