# Bot Agente de Viajes ✈️

Sistema completo para detectar vuelos baratos con alertas personalizadas y notificaciones por Telegram.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram Bot  │◄──►│  FastAPI Backend │◄──►│  PostgreSQL DB  │
│                 │    │                  │    │                 │
│ • Interfaz user │    │ • API REST       │    │ • Alertas       │
│ • Crear alertas │    │ • Lógica negocio │    │ • Usuarios      │
│ • Ver alertas   │    │ • CRUD completo  │    │ • Historial     │
│ • Eliminar      │    │ • 8 endpoints    │    │ • Notificaciones│
└─────────────────┘    └──────────────────┘    └─────────────────┘
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

# Instalar dependencias
pip install fastapi uvicorn psycopg2-binary python-telegram-bot python-dotenv requests
```

### 2. Base de Datos (PostgreSQL con Docker)

```bash
# Iniciar PostgreSQL
docker-compose up -d

# La base de datos se crea automáticamente con el schema
# Usuario: postgres | Password: password | DB: flight_alerts
```

### 3. Backend API

```bash
# Desde el directorio raíz
cd backend
python main.py

# API disponible en: http://localhost:8000
# Documentación: http://localhost:8000/docs
```

### 4. Bot de Telegram

```bash
# Configurar token en bot/.env
cd bot
cp .env.example .env
# Editar .env con tu TELEGRAM_BOT_TOKEN

# Ejecutar bot
python bot.py
```

## 🛠️ Funcionalidades Implementadas

### ✅ Backend API (FastAPI)
- **8 Endpoints REST** completamente funcionales
- **Health check** (`/health`)
- **CRUD Usuarios** (`GET/POST /users`)
- **CRUD Alertas** (`GET/POST/DELETE /alerts`)
- **Historial de precios** (`/alerts/{id}/price-history`)
- **Búsquedas manuales** (`/search`)
- **Base de datos PostgreSQL** con 4 tablas relacionadas

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

- **[LEVANTAR_SERVIDORES.md](./LEVANTAR_SERVIDORES.md)** - Guía completa de instalación y configuración
- **[bot/README_BOT.md](./bot/README_BOT.md)** - Documentación específica del bot de Telegram
- **API Docs** - Disponible en `http://localhost:8000/docs` cuando el backend esté corriendo

## 🔄 Estado del Proyecto

### ✅ Completado
- ✅ Backend API completo (8 endpoints)
- ✅ Base de datos PostgreSQL funcional
- ✅ Bot Telegram con todas las funcionalidades básicas
- ✅ Integración backend-bot-database
- ✅ Documentación y setup completo

### 🚧 Próximamente
- ⏳ Integración APIs de vuelos reales (Tequila/Amadeus)
- ⏳ Worker/Poller automático para precio
- ⏳ Notificaciones push automáticas
- ⏳ Interface web alternativa
- ⏳ Sistema de ML para predicción de precios

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
