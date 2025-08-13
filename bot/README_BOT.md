# ============================================================================
# BOT DE TELEGRAM - AGENTE DE VIAJES
# ============================================================================

Bot de Telegram completamente funcional para gestión de alertas de vuelos con interfaz conversacional intuitiva.

## 📋 Tabla de Contenidos

1. [Configuración Inicial](#configuración-inicial)
2. [Configuración del Token](#configuración-del-token)
3. [Ejecución del Bot](#ejecución-del-bot)
4. [Comandos Disponibles](#comandos-disponibles)
5. [Funcionalidades](#funcionalidades)
6. [Flujo de Usuario](#flujo-de-usuario)
7. [Testing](#testing)
8. [Próximos Pasos](#próximos-pasos)

## 🚀 Configuración Inicial

### 1. CREAR EL BOT EN TELEGRAM

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Elige un nombre para tu bot (ej: "Bot Agente Viajes")
4. Elige un username (debe terminar en "bot", ej: "AgentVuelosBot")
5. **BotFather te dará un TOKEN** como: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. CONFIGURACIÓN DEL TOKEN

El bot está configurado para leer automáticamente el archivo `.env`. Asi que crea un .env.

**Opción 1: Usar archivo .env (Recomendado)**
```bash
# El archivo .env ya existe, solo edita el token:
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

**Opción 2: Variable de entorno del sistema**
```bash
# En macOS/Linux:
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
```

### 3. VERIFICAR DEPENDENCIAS

```bash
# Asegúrate de tener instalado:
pip install python-telegram-bot python-dotenv requests

# O todas las dependencias:
pip install fastapi uvicorn psycopg2-binary python-telegram-bot python-dotenv requests
```

## ▶️ Ejecución del Bot

### Ejecución Simple
```bash
# Desde el directorio bot/
cd bot
python bot.py
```

### Ejecución Completa (Backend + Bot)
```bash
# Terminal 1: Backend
docker-compose up -d  # Base de datos
cd backend && python main.py

# Terminal 2: Bot
cd bot && python bot.py
```

## 🤖 Comandos Disponibles

| Comando | Descripción | Funcionalidad |
|---------|-------------|---------------|
| `/start` | Iniciar el bot | Registro de usuario + menú principal |
| `/help` | Ver ayuda completa | Lista de comandos y tips |
| `/crear_alerta` | Crear nueva alerta | Conversación interactiva completa |
| `/mis_alertas` | Ver alertas activas | Lista + opciones de gestión |
| `/cancel` | Cancelar operación | Sale de conversación actual |

## ✨ Funcionalidades Implementadas

### ✅ **Gestión de Usuarios**
- ✅ Registro automático al usar `/start`
- ✅ Integración con backend API
- ✅ Manejo de errores de conexión

### ✅ **Creación de Alertas Interactiva**
- ✅ **Conversación paso a paso**
  1. Aeropuerto de origen (código IATA)
  2. Aeropuerto de destino (código IATA)
  3. Fecha de salida (DD/MM/YYYY)
  4. Tipo de vuelo (ida/ida y vuelta)
  5. Fecha de regreso (si aplica)
  6. Precio objetivo opcional

- ✅ **Validaciones Robustas**
  - Códigos IATA de 3 letras
  - Fechas futuras válidas
  - Origen ≠ Destino
  - Fecha regreso > Fecha salida
  - Precio numérico positivo

### ✅ **Gestión de Alertas**
- ✅ **Ver alertas activas** con detalles completos
- ✅ **Eliminar alertas** con selección individual
- ✅ **Navegación intuitiva** con botones inline
- ✅ **Confirmaciones** de operaciones exitosas

### ✅ **Interfaz de Usuario**
- ✅ **Botones inline interactivos**
- ✅ **Menús contextuales**
- ✅ **Navegación fluida** entre opciones
- ✅ **Mensajes informativos** claros
- ✅ **Manejo de errores** user-friendly

### ✅ **Integración Backend**
- ✅ **8 endpoints de API** utilizados
- ✅ **Manejo de errores HTTP**
- ✅ **Conversión de datos** correcta
- ✅ **Sincronización** usuario-bot-database

## 🔄 Flujo de Usuario Completo

### 1. Primer Uso
```
Usuario: /start
Bot: Bienvenida + Registro automático + Menú principal
```

### 2. Crear Alerta
```
Usuario: Clic "🆕 Crear Alerta"
Bot: "Ingresa origen (ej: MAD)"
Usuario: MAD
Bot: "Ingresa destino (ej: BCN)"
Usuario: BCN
Bot: "Ingresa fecha salida (DD/MM/YYYY)"
Usuario: 15/09/2025
Bot: "¿Solo ida o ida y vuelta?" [Botones]
Usuario: Clic "🔄 Ida y vuelta"
Bot: "Ingresa fecha regreso"
Usuario: 20/09/2025
Bot: "Precio objetivo en euros (opcional)"
Usuario: 150
Bot: "✅ Alerta creada exitosamente!" + [Opciones]
```

### 3. Ver y Gestionar Alertas
```
Usuario: Clic "📋 Mis Alertas"
Bot: Lista de alertas + [Crear Nueva] [Eliminar]
Usuario: Clic "🗑️ Eliminar Alerta"  
Bot: Lista con botones individuales "❌ Eliminar #X"
Usuario: Clic "❌ Eliminar #1"
Bot: "✅ Alerta eliminada exitosamente!" + [Opciones]
```

## 🧪 Testing del Bot

### 1. **Test Básico**
```bash
# En Telegram:
1. Buscar tu bot por username
2. Enviar /start
3. Verificar menú principal
```

### 2. **Test Creación de Alerta**
```bash
# Flujo completo:
1. Clic "🆕 Crear Alerta"
2. Seguir conversación completa
3. Verificar confirmación
4. Comprobar en backend:
   curl "http://localhost:8000/alerts?user_id=1"
```

### 3. **Test Eliminación**
```bash
# Test eliminar:
1. Clic "📋 Mis Alertas"
2. Clic "🗑️ Eliminar Alerta"
3. Seleccionar alerta específica
4. Verificar confirmación
```

### 4. **Test de Errores**
```bash
# Probar validaciones:
- Códigos IATA inválidos (ej: "Madrid")
- Fechas pasadas
- Fechas mal formateadas
- Precios negativos
- Origen = Destino
```

## 🏗️ Arquitectura del Bot

### **Componentes Principales**
```python
# Conversación para crear alertas
ConversationHandler()
├── Estados: ORIGIN → DESTINATION → DATE_FROM → DATE_TO → PRICE_TARGET
├── Validaciones: IATA, fechas, precios
└── Fallbacks: /cancel

# Botones inline para navegación
InlineKeyboardMarkup()
├── Menú principal
├── Gestión de alertas
└── Confirmaciones

# Integración API
call_api()
├── GET /users, /alerts
├── POST /users, /alerts
└── DELETE /alerts/{id}
```

### **Estados de Conversación**
- `ORIGIN`: Esperando código aeropuerto origen
- `DESTINATION`: Esperando código aeropuerto destino  
- `DATE_FROM`: Esperando fecha de salida
- `DATE_TO`: Esperando fecha de regreso
- `PRICE_TARGET`: Esperando precio objetivo

## 📈 Próximos Pasos

### 🔄 **Próximas Funcionalidades**
- [ ] **Editar alertas existentes**
- [ ] **Ver historial de precios** por alerta
- [ ] **Notificaciones push automáticas**
- [ ] **Búsquedas manuales** de vuelos
- [ ] **Configuración avanzada** (escalas, horarios)
- [ ] **Sugerencias de destinos** populares
- [ ] **Alertas de grupo** para múltiples usuarios

### 🚀 **Mejoras de UX**
- [ ] **Calendario interactivo** para fechas
- [ ] **Autocompletado** de aeropuertos
- [ ] **Mapas de precios** por destino
- [ ] **Estadísticas** personales de usuario
- [ ] **Temas visuales** personalizables

### 🔧 **Mejoras Técnicas**
- [ ] **Rate limiting** de solicitudes
- [ ] **Logging** avanzado
- [ ] **Métricas** de uso
- [ ] **Tests unitarios** automatizados
- [ ] **Deploy** en producción

## ⚠️ Troubleshooting

### **Bot no responde**
```bash
# Verificar:
1. Token correcto en .env
2. Backend ejecutándose en :8000
3. Base de datos conectada
4. No hay errores en consola
```

### **Error de API**
```bash
# Comprobar backend:
curl http://localhost:8000/health
# Debe devolver: {"status":"ok"}
```

### **Error de base de datos**
```bash
# Verificar PostgreSQL:
docker ps  # Debe mostrar contenedor corriendo
docker logs <container_id>  # Ver logs de errores
```

---
**🤖 Bot desarrollado con python-telegram-bot + FastAPI + PostgreSQL**
