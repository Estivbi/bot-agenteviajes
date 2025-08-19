# ============================================================================
# BOT AGENTE VIAJES - TELEGRAM BOT
# ============================================================================
# Bot de Telegram que permite a los usuarios:
# - Crear alertas de vuelos
# - Ver sus alertas activas
# - Recibir notificaciones de precios
# - Gestionar su perfil
# ============================================================================

import os
import logging
import requests
import asyncio
from datetime import datetime, date
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, filters
)

# ============================================================================
# CONFIGURACIÓN Y LOGGING
# ============================================================================
# Cargar variables de entorno desde archivo .env
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL del backend API. ahora esta el de prod pero se puede cambiar al local cambiando la url, mira el .env
API_BASE_URL = os.getenv('BACKEND_URL', "https://backend-production-2b7f.up.railway.app")

# Estados para conversaciones
ORIGIN, DESTINATION, DATE_FROM, DATE_TO, PRICE_TARGET, MAX_STOPS = range(6)


# FUNCIONES AUXILIARES PARA API

def call_api(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Función auxiliar para llamar a nuestro backend API.
    """
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, params=data)
        elif method == "POST":
            response = requests.post(url, json=data)
        elif method == "DELETE":
            response = requests.delete(url)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling API {url}: {e}")
        return {"error": str(e)}

def get_or_create_user(telegram_user_id: int) -> Optional[int]:
    """
    Obtiene o crea un usuario en el backend y devuelve su ID interno.
    """
    # Primero intentamos obtener el usuario
    users_response = call_api("/users")
    if "error" not in users_response:
        for user in users_response.get("users", []):
            if user["telegram_id"] == telegram_user_id:
                return user["id"]
    
    # Si no existe, lo creamos
    create_response = call_api("/users", "POST", {"telegram_user_id": telegram_user_id})
    if "error" not in create_response and "user_id" in create_response:
        return create_response["user_id"]
    
    return None

# ============================================================================
# FUNCIÓN AUXILIAR: Menú Principal
# ============================================================================
def create_main_menu():
    """
    Crea el teclado inline con las opciones principales del bot.
    """
    keyboard = [
        [InlineKeyboardButton("🆕 Crear Alerta", callback_data="create_alert")],
        [InlineKeyboardButton("📋 Mis Alertas", callback_data="my_alerts")],
        [InlineKeyboardButton("❓ Ayuda", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============================================================================
# COMANDO: /start
# ============================================================================
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Comando de inicio del bot. Registra al usuario y muestra el menú principal.
    """
    user = update.effective_user
    user_id = get_or_create_user(user.id)
    
    if user_id:
        welcome_message = f"""
🛫 ¡Bienvenido a Bot Agente Viajes, {user.first_name}! 

Soy tu asistente personal para encontrar vuelos baratos. Puedo ayudarte a:

✈️ Crear alertas de vuelos
📊 Ver tus alertas activas
🔔 Notificarte cuando encuentre precios bajos
📈 Mostrarte el historial de precios

¿Qué te gustaría hacer?
        """
        
        reply_markup = create_main_menu()
        await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    else:
        await update.message.reply_text(
            "❌ Error al registrar usuario. Intenta de nuevo en unos minutos."
        )

# ============================================================================
# COMANDO: /help
# ============================================================================
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra la ayuda con todos los comandos disponibles.
    """
    help_text = """
🤖 Comandos disponibles:

/start - Iniciar el bot y registro
/crear_alerta - Crear una nueva alerta de vuelo
/mis_alertas - Ver todas tus alertas activas
/help - Mostrar esta ayuda

📝 Cómo crear una alerta:
1. Usa /crear_alerta
2. Ingresa origen (ej: MAD)
3. Ingresa destino (ej: BCN)
4. Selecciona fecha de salida
5. Opcionalmente: fecha de regreso, precio máximo

🔔 Notificaciones:
Te avisaré automáticamente cuando encuentre:
• Precios por debajo de tu objetivo
• Tendencias de precios interesantes
• Ofertas especiales

💡 Consejos:
• Usa códigos IATA (MAD, BCN, LHR, etc.)
• Puedes consultar la lista completa de códigos IATA aquí: https://es.wikipedia.org/wiki/Anexo:Aeropuertos_con_c%C3%B3digo_IATA
• Las alertas se revisan automáticamente
• Puedes tener múltiples alertas activas

¿Qué te gustaría hacer?
    """
    help_text = """
🤖 Comandos disponibles:

/start - Iniciar el bot y registro
/crear_alerta - Crear una nueva alerta de vuelo
/mis_alertas - Ver todas tus alertas activas
/help - Mostrar esta ayuda

📝 Cómo crear una alerta:
1. Usa /crear_alerta
2. Ingresa origen (ej: MAD)
3. Ingresa destino (ej: BCN)
4. Selecciona fecha de salida
5. Opcionalmente: fecha de regreso, precio máximo

🔔 Notificaciones:
Te avisaré automáticamente cuando encuentre:
• Precios por debajo de tu objetivo
• Tendencias de precios interesantes
• Ofertas especiales

💡 Consejos:
• Usa códigos IATA (MAD, BCN, LHR, etc.)
• Puedes consultar la lista completa de códigos IATA aquí: https://es.wikipedia.org/wiki/Anexo:Aeropuertos_con_c%C3%B3digo_IATA
• Las alertas se revisan automáticamente
• Puedes tener múltiples alertas activas

¿Qué te gustaría hacer?
    """
    
    reply_markup = create_main_menu()
    
    # Determinar si viene de callback o comando directo
    if update.callback_query:
        await update.callback_query.edit_message_text(help_text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(help_text, reply_markup=reply_markup)

# ============================================================================
# COMANDO: /mis_alertas
# ============================================================================
async def my_alerts_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra todas las alertas activas del usuario.
    """
    user_id = get_or_create_user(update.effective_user.id)
    if not user_id:
        # Determinar si viene de callback o comando directo
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Error al acceder a tus alertas.")
        else:
            await update.message.reply_text("❌ Error al acceder a tus alertas.")
        return

    alerts_response = call_api(f"/alerts?user_id={user_id}")
    
    if "error" in alerts_response:
        if update.callback_query:
            await update.callback_query.edit_message_text("❌ Error al obtener tus alertas.")
        else:
            await update.message.reply_text("❌ Error al obtener tus alertas.")
        return

    alerts = alerts_response.get("alerts", [])
    
    if not alerts:
        keyboard = [
            [InlineKeyboardButton("🆕 Crear Primera Alerta", callback_data="create_alert")],
            [InlineKeyboardButton("❓ Ayuda", callback_data="help")],
            [InlineKeyboardButton("🏠 Menú Principal", callback_data="start")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        message_text = "📭 No tienes alertas activas.\n¿Quieres crear tu primera alerta?"
        
        if update.callback_query:
            await update.callback_query.edit_message_text(message_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(message_text, reply_markup=reply_markup)
        return

    message = "📋 <b>Tus alertas activas:</b>\n\n"
    
    for i, alert in enumerate(alerts, 1):
        origin = alert["origin"]
        destination = alert["destination"]
        date_from = alert["date_from"]
        date_to = alert["date_to"]
        price_target = alert["price_target_cents"]
        message += f"{i}. {origin} → {destination}\n"
        message += f"📅 Salida: {date_from}\n"
        if date_to:
            message += f"🔄 Regreso: {date_to}\n"
        if price_target:
            message += f"💰 Precio objetivo: {price_target/100:.2f}€\n"
        message += f"🆔 ID: {alert['id']}\n\n"

    # Agregar botones para gestionar alertas
    keyboard = [
        [InlineKeyboardButton("🆕 Nueva Alerta", callback_data="create_alert")],
        [InlineKeyboardButton("🗑️ Eliminar Alerta", callback_data="delete_alert")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Determinar si viene de callback o comando directo
    if update.callback_query:
        await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(message, reply_markup=reply_markup, parse_mode='HTML')

# ============================================================================
# CONVERSACIÓN: CREAR ALERTA
# ============================================================================
async def start_create_alert(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Inicia la conversación para crear una nueva alerta.
    """
    query = update.callback_query
    iata_link = '<a href="https://www.iata.org/en/publications/directories/code-search/">Consulta la lista completa de códigos IATA aquí</a>'
    mensaje = (
        "🛫 <b>Crear Nueva Alerta</b>\n\n"
        "Por favor, ingresa el aeropuerto de <b>origen</b> (código IATA):\n"
        "Ejemplo: MAD (Madrid), BCN (Barcelona), LHR (Londres)\n\n"
        f"{iata_link}\n\n"
        "Usa /cancel para cancelar."
    )
    if query:
        await query.answer()
        await query.edit_message_text(mensaje, parse_mode='HTML')
    else:
        await update.message.reply_text(mensaje, parse_mode='HTML')
    return ORIGIN

async def get_origin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe el aeropuerto de origen y pide el destino.
    """
    origin = update.message.text.upper().strip()
    # Validar código IATA (3 letras)
    if len(origin) != 3 or not origin.isalpha():
        await update.message.reply_text(
            "❌ Por favor ingresa un código IATA válido de 3 letras (ej: MAD, BCN, LHR)."
        )
        return ORIGIN
    context.user_data['origin'] = origin
    iata_link = '<a href="https://es.wikipedia.org/wiki/Anexo:Aeropuertos_con_c%C3%B3digo_IATA">Consulta la lista completa de códigos IATA aquí</a>'
    mensaje = (
        f"✅ Origen: <b>{origin}</b>\n\n"
        "Ahora ingresa el aeropuerto de <b>destino</b> (código IATA):\n"
        "Ejemplo: BCN (Barcelona), LHR (Londres), CDG (París)\n\n"
        f"{iata_link}"
    )
    await update.message.reply_text(mensaje, parse_mode='HTML')
    return DESTINATION

async def get_destination(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe el aeropuerto de destino y pide la fecha de salida.
    """
    destination = update.message.text.upper().strip()
    # Validar código IATA
    if len(destination) != 3 or not destination.isalpha():
        await update.message.reply_text(
            "❌ Por favor ingresa un código IATA válido de 3 letras (ej: MAD, BCN, LHR)."
        )
        return DESTINATION
    if destination == context.user_data['origin']:
        await update.message.reply_text(
            "❌ El destino no puede ser igual al origen. Ingresa un destino diferente."
        )
        return DESTINATION
    context.user_data['destination'] = destination
    await update.message.reply_text(
        f"✅ Destino: <b>{destination}</b>\n\n"
        f"Ingresa la <b>fecha de salida</b> (formato: DD/MM/YYYY):\n"
        f"Ejemplo: 15/09/2025",
        parse_mode='HTML'
    )
    return DATE_FROM

async def get_date_from(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe la fecha de salida y pide si quiere fecha de regreso.
    """
    date_text = update.message.text.strip()
    try:
        # Intentar parsear la fecha
        date_from = datetime.strptime(date_text, "%d/%m/%Y").date()
        # Verificar que sea una fecha futura
        if date_from <= date.today():
            await update.message.reply_text(
                "❌ La fecha debe ser posterior a hoy. Ingresa una fecha futura."
            )
            return DATE_FROM
        context.user_data['date_from'] = date_from
        # Preguntar por fecha de regreso
        keyboard = [
            [InlineKeyboardButton("✈️ Solo ida", callback_data="no_return")],
            [InlineKeyboardButton("🔄 Ida y vuelta", callback_data="with_return")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Fecha de salida: <b>{date_from.strftime('%d/%m/%Y')}</b>\n\n"
            f"¿Necesitas vuelo de regreso?",
            reply_markup=reply_markup,
            parse_mode='HTML'
        )
        return DATE_TO
    except ValueError:
        await update.message.reply_text(
            "❌ Formato de fecha incorrecto. Usa el formato DD/MM/YYYY (ej: 15/09/2025)."
        )
        return DATE_FROM

async def handle_return_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Maneja la selección de fecha de regreso.
    """
    query = update.callback_query
    await query.answer()
    
    if query.data == "no_return":
        context.user_data['date_to'] = None
        await query.edit_message_text(
            "✅ Vuelo de **solo ida**\n\n"
            "Ingresa tu **precio objetivo máximo** en euros (opcional):\n"
            "Ejemplo: 150\n\n"
            "O escribe 'skip' para omitir.",
            parse_mode='Markdown'
        )
        return PRICE_TARGET
    
    elif query.data == "with_return":
        await query.edit_message_text(
            "Ingresa la **fecha de regreso** (formato: DD/MM/YYYY):\n"
            "Debe ser posterior a la fecha de salida."
        )
        return DATE_TO

async def get_date_to(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe la fecha de regreso.
    """
    date_text = update.message.text.strip()
    
    try:
        date_to = datetime.strptime(date_text, "%d/%m/%Y").date()
        date_from = context.user_data['date_from']
        
        if date_to <= date_from:
            await update.message.reply_text(
                "❌ La fecha de regreso debe ser posterior a la fecha de salida."
            )
            return DATE_TO
        
        context.user_data['date_to'] = date_to
        
        await update.message.reply_text(
            f"✅ Fecha de regreso: **{date_to.strftime('%d/%m/%Y')}**\n\n"
            f"Ingresa tu **precio objetivo máximo** en euros (opcional):\n"
            f"Ejemplo: 150\n\n"
            f"O escribe 'skip' para omitir.",
            parse_mode='Markdown'
        )
        
        return PRICE_TARGET
        
    except ValueError:
        await update.message.reply_text(
            "❌ Formato de fecha incorrecto. Usa el formato DD/MM/YYYY (ej: 20/09/2025)."
        )
        return DATE_TO

async def get_price_target(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Recibe el precio objetivo y crea la alerta.
    """
    price_text = update.message.text.strip().lower()
    
    if price_text == "skip":
        context.user_data['price_target_cents'] = None
    else:
        try:
            price_euros = float(price_text)
            if price_euros <= 0:
                await update.message.reply_text(
                    "❌ El precio debe ser mayor a 0. Intenta de nuevo o escribe 'skip'."
                )
                return PRICE_TARGET
            context.user_data['price_target_cents'] = int(price_euros * 100)
        except ValueError:
            await update.message.reply_text(
                "❌ Precio inválido. Ingresa un número (ej: 150) o escribe 'skip'."
            )
            return PRICE_TARGET
    
    # Crear la alerta llamando al API
    await create_alert_api_call(update, context)
    return ConversationHandler.END

async def create_alert_api_call(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Llama al API para crear la alerta con todos los datos recopilados.
    """
    user_id = get_or_create_user(update.effective_user.id)
    if not user_id:
        await update.message.reply_text("❌ Error al crear la alerta.")
        return

    # Comprobar que todos los datos requeridos existen en context.user_data
    required_fields = ['origin', 'destination', 'date_from']
    missing_fields = [f for f in required_fields if f not in context.user_data]
    if missing_fields:
        await update.message.reply_text(
            f"❌ Faltan datos para crear la alerta: {', '.join(missing_fields)}. Por favor, reinicia el proceso."
        )
        context.user_data.clear()
        return

    # Preparar datos para el API
    alert_data = {
        "user_id": user_id,
        "origin": context.user_data['origin'],
        "destination": context.user_data['destination'],
        "date_from": context.user_data['date_from'].isoformat(),
        "date_to": context.user_data['date_to'].isoformat() if context.user_data.get('date_to') else None,
        "price_target_cents": context.user_data.get('price_target_cents'),
        "max_stops": 2  # Por defecto máximo 2 escalas
    }

    # Llamar al API
    response = call_api("/alerts", "POST", alert_data)

    if "error" in response:
        await update.message.reply_text(
            f"❌ Error al crear la alerta: {response['error']}"
        )
        return

    # Mostrar resumen de la alerta creada (formato HTML seguro para Telegram)
    origin = context.user_data['origin']
    destination = context.user_data['destination']
    date_from = context.user_data['date_from']
    date_to = context.user_data.get('date_to')
    price_target = context.user_data.get('price_target_cents')
    iata_link = '<a href="https://es.wikipedia.org/wiki/Anexo:Aeropuertos_con_c%C3%B3digo_IATA">Consulta la lista completa de códigos IATA aquí</a>'
    summary = (
        "✅ <b>¡Alerta creada exitosamente!</b>\n\n"
        f"🛫 <b>Ruta:</b> {origin} → {destination}\n"
        f"📅 <b>Salida:</b> {date_from.strftime('%d/%m/%Y')}\n"
    )
    if date_to:
        summary += f"🔄 <b>Regreso:</b> {date_to.strftime('%d/%m/%Y')}\n"
    if price_target:
        summary += f"💰 <b>Precio objetivo:</b> {price_target/100:.2f}€\n"
    summary += f"\n🔔 Te notificaré cuando encuentre precios interesantes.\n\n{iata_link}"
    # Limpiar datos temporales
    context.user_data.clear()
    keyboard = [
        [InlineKeyboardButton("📋 Ver Mis Alertas", callback_data="my_alerts")],
        [InlineKeyboardButton("🆕 Crear Otra Alerta", callback_data="create_alert")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    # Detectar si viene de callback o mensaje
    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(summary, reply_markup=reply_markup, parse_mode='HTML')
    else:
        await update.message.reply_text(summary, reply_markup=reply_markup, parse_mode='HTML')

# ============================================================================
# COMANDO: /cancel
# ============================================================================
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancela cualquier conversación activa y muestra el menú principal.
    """
    context.user_data.clear()
    
    cancel_message = """
❌ Operación cancelada.

¿Qué te gustaría hacer ahora?
    """
    
    reply_markup = create_main_menu()
    await update.message.reply_text(cancel_message, reply_markup=reply_markup)
    return ConversationHandler.END

# ============================================================================
# FUNCIONES PARA ELIMINAR ALERTAS
# ============================================================================
async def show_delete_alerts_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Muestra un menú para seleccionar qué alerta eliminar.
    """
    user_id = get_or_create_user(update.effective_user.id)
    if not user_id:
        await update.callback_query.edit_message_text("❌ Error al acceder a tus alertas.")
        return

    alerts_response = call_api(f"/alerts?user_id={user_id}")
    
    if "error" in alerts_response:
        await update.callback_query.edit_message_text("❌ Error al obtener tus alertas.")
        return

    alerts = alerts_response.get("alerts", [])
    
    if not alerts:
        await update.callback_query.edit_message_text(
            "📭 No tienes alertas para eliminar.\n\n¿Quieres crear una nueva alerta?",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🆕 Crear Alerta", callback_data="create_alert")]])
        )
        return

    message = "🗑️ Selecciona la alerta que quieres eliminar:\n\n"
    keyboard = []
    for i, alert in enumerate(alerts, 1):
        origin = alert["origin"]
        destination = alert["destination"]
        date_from = alert["date_from"]
        alert_info = f"{i}. {origin} → {destination} ({date_from})"
        message += f"{alert_info}\n"
        
        # Botón para eliminar esta alerta específica
        keyboard.append([InlineKeyboardButton(f"❌ Eliminar #{i}", callback_data=f"delete_{alert['id']}")])

    # Agregar botón para cancelar
    keyboard.append([InlineKeyboardButton("↩️ Volver a Mis Alertas", callback_data="my_alerts")])
    keyboard.append([InlineKeyboardButton("🏠 Menú Principal", callback_data="start")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(message, reply_markup=reply_markup, parse_mode='HTML')

async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE, alert_id: str) -> None:
    """
    Elimina una alerta específica.
    """
    try:
        alert_id_int = int(alert_id)
    except ValueError:
        await update.callback_query.edit_message_text("❌ ID de alerta inválido.")
        return
    
    # Llamar a la API para eliminar la alerta
    delete_response = call_api(f"/alerts/{alert_id_int}", "DELETE")
    
    if "error" in delete_response:
        await update.callback_query.edit_message_text(
            f"❌ Error al eliminar la alerta: {delete_response['error']}",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("↩️ Volver", callback_data="my_alerts")]])
        )
        return
    
    # Confirmar eliminación exitosa
    success_message = "✅ Alerta eliminada exitosamente.\n\n¿Qué te gustaría hacer ahora?"
    keyboard = [
        [InlineKeyboardButton("📋 Ver Mis Alertas", callback_data="my_alerts")],
        [InlineKeyboardButton("🆕 Crear Nueva Alerta", callback_data="create_alert")],
        [InlineKeyboardButton("🏠 Menú Principal", callback_data="start")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.edit_message_text(success_message, reply_markup=reply_markup, parse_mode='HTML')

# ============================================================================
# MANEJADOR DE BOTONES INLINE
# ============================================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Maneja los clicks en botones inline.
    """
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_command(update, context)
    elif query.data == "my_alerts":
        await my_alerts_command(update, context)
    elif query.data == "create_alert":
        await start_create_alert(update, context)
    elif query.data == "delete_alert":
        await show_delete_alerts_menu(update, context)
    elif query.data.startswith("delete_"):
        # Eliminar alerta específica
        alert_id = query.data.replace("delete_", "")
        await delete_alert(update, context, alert_id)
    elif query.data == "start":
        # Mostrar menú principal
        user = update.effective_user
        welcome_message = f"""
🛫 ¡Hola de nuevo, {user.first_name}! 

¿Qué te gustaría hacer?
        """
        reply_markup = create_main_menu()
        await query.edit_message_text(welcome_message, reply_markup=reply_markup)

# ============================================================================
# CONFIGURACIÓN Y EJECUCIÓN DEL BOT
# ============================================================================
def main() -> None:
    """
    Función principal que configura y ejecuta el bot.
    """
    # Token del bot (debe configurarse como variable de entorno)
    TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    if not TOKEN:
        print("❌ Error: Define la variable TELEGRAM_BOT_TOKEN")
        print("Ejemplo: export TELEGRAM_BOT_TOKEN='tu_token_aqui'")
        return

    # Crear aplicación
    application = Application.builder().token(TOKEN).build()

    # Configurar conversación para crear alertas
    create_alert_handler = ConversationHandler(
        entry_points=[
            CommandHandler("crear_alerta", start_create_alert),
            CallbackQueryHandler(start_create_alert, pattern="^create_alert$")
        ],
        states={
            ORIGIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_origin)],
            DESTINATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_destination)],
            DATE_FROM: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_date_from)],
            DATE_TO: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_date_to),
                CallbackQueryHandler(handle_return_date, pattern="^(no_return|with_return)$")
            ],
            PRICE_TARGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_target)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)]
    )

    # Agregar handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("mis_alertas", my_alerts_command))
    application.add_handler(create_alert_handler)
    application.add_handler(CallbackQueryHandler(button_handler))

    # Ejecutar bot
    print("🤖 Bot iniciado. Presiona Ctrl+C para detener.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
