import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from bot.handlers import (
    process_message, 
    start_request_flow, 
    user_states, 
    cancel_request_flow, 
    revert_step, 
    get_summary,
    confirm_and_save
)
from bot.openai_client import ask_openai

load_dotenv()

# -------------------------------------------------------
# HELPER: TECLADO DE NAVEGACIÓN (ATRÁS / CANCELAR)
# -------------------------------------------------------
def nav_keyboard(include_back=True):
    buttons = []
    if include_back:
        buttons.append(InlineKeyboardButton("⬅️ Atrás", callback_data="flow_back"))
    buttons.append(InlineKeyboardButton("❌ Cancelar", callback_data="flow_cancel"))
    return InlineKeyboardMarkup([buttons])

# -------------------------------------------------------
# MENÚS PRINCIPALES
# -------------------------------------------------------
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 Ver Requisitos", callback_data="requisitos")],
        [InlineKeyboardButton("🕒 Horarios y Ubicación", callback_data="horario")],
        [InlineKeyboardButton("🚀 Iniciar Solicitud", callback_data="solicitud")],
    ])

def solicitud_menu():
    # Incluimos botón Cancelar aquí también
    keyboard = [
        [InlineKeyboardButton("📘 Constancia", callback_data="tipo_constancia")],
        [InlineKeyboardButton("🗂️ Trámite Admin.", callback_data="tipo_tramite")],
        [InlineKeyboardButton("❓ Consulta Técnica", callback_data="tipo_consulta")],
        [InlineKeyboardButton("📌 Otro", callback_data="tipo_otro")],
        [InlineKeyboardButton("⬅️ Atrás", callback_data="flow_back"), InlineKeyboardButton("❌ Cancelar", callback_data="flow_cancel")]
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Enviar Solicitud", callback_data="flow_confirm")],
        [InlineKeyboardButton("⬅️ Corregir / Atrás", callback_data="flow_back")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="flow_cancel")],
    ])

# -------------------------------------------------------
# START
# -------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["has_started"] = True
    # Si había un estado anterior colgado, lo limpiamos
    cancel_request_flow(update.effective_user.id)
    
    await update.message.reply_text(
        "👋 *¡Bienvenido al Asistente CSDC!*\n\n"
        "Soy tu asistente virtual. Puedo ayudarte a gestionar trámites o resolver dudas.\n\n"
        "**¿En qué puedo apoyarte hoy?**",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

# -------------------------------------------------------
# MANEJO DE BOTONES (CALLBACKS)
# -------------------------------------------------------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    # --- NAVEGACIÓN Y CONTROL ---
    
    # 1. Cancelar Solicitud
    if data == "flow_cancel":
        cancel_request_flow(user_id)
        await query.message.edit_text("❌ *Solicitud cancelada.*", parse_mode="Markdown")
        await query.message.reply_text("¿Te puedo ayudar en algo más?", reply_markup=main_menu())
        return

    # 2. Confirmar y Guardar (Paso final)
    if data == "flow_confirm":
        success = confirm_and_save(user_id)
        if success:
            await query.message.edit_text(
                "✅ *¡Solicitud Enviada con Éxito!*\n\n"
                "Hemos recibido tu información. Recibirás una notificación en tu correo institucional pronto.",
                parse_mode="Markdown"
            )
            await query.message.reply_text("¿Deseas realizar otra gestión?", reply_markup=main_menu())
        else:
            await query.message.reply_text("⚠️ Hubo un error guardando la solicitud. Intenta de nuevo.")
        return

    # 3. Retroceder (Atrás)
    if data == "flow_back":
        new_step = revert_step(user_id)
        
        # Redirigir según el paso al que volvimos
        if new_step == 1:
             await query.message.reply_text("📝 Ingresemos de nuevo tu *nombre completo*:", reply_markup=nav_keyboard(include_back=False), parse_mode="Markdown")
        elif new_step == 2:
             await query.message.reply_text("📧 Indícame tu *correo institucional*:", reply_markup=nav_keyboard(), parse_mode="Markdown")
        elif new_step == 3:
             await query.message.reply_text("📂 Selecciona el *tipo de solicitud*:", reply_markup=solicitud_menu(), parse_mode="Markdown")
        elif new_step == 4:
             await query.message.reply_text("✍️ Describe brevemente tu *solicitud o detalle*:", reply_markup=nav_keyboard(), parse_mode="Markdown")
        return

    # --- OPCIONES DEL MENÚ PRINCIPAL ---

    if data == "requisitos":
        from bot.intents import FAQ_INTENTS
        await query.message.reply_text(FAQ_INTENTS["requisitos"], parse_mode="Markdown")

    elif data == "horario":
        from bot.intents import FAQ_INTENTS
        await query.message.reply_text(FAQ_INTENTS["horario"], parse_mode="Markdown")

    elif data == "solicitud":
        start_request_flow(user_id)
        await query.message.reply_text(
            "🚀 *Iniciemos tu solicitud.*\n\n"
            "Por favor, escribe tu *nombre completo*:",
            reply_markup=nav_keyboard(include_back=False), # No hay 'atrás' en el primer paso
            parse_mode="Markdown"
        )

    # --- SELECCIÓN TIPO SOLICITUD (Paso 3) ---
    elif data.startswith("tipo_"):
        if user_id in user_states:
            tipo = data.replace("tipo_", "").capitalize()
            user_states[user_id]["data"]["tipo_solicitud"] = tipo
            user_states[user_id]["step"] = 4
            
            await query.message.edit_text(f"📌 *Tipo seleccionado:* {tipo}", parse_mode="Markdown")
            await query.message.reply_text(
                "✍️ Por último, describe **brevemente** tu solicitud:\n_(Ej: Necesito constancia de notas ciclo I-2024)_",
                reply_markup=nav_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("⚠️ Sesión expirada. Escribe /start")

# -------------------------------------------------------
# MANEJO DE MENSAJES DE TEXTO
# -------------------------------------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()

    # Primera vez
    if "has_started" not in context.user_data:
        await start(update, context)
        return

    # Reset con saludos comunes si no hay flujo activo
    saludos = ["hola", "buenas", "hi", "hello"]
    if text.lower() in saludos and user_id not in user_states:
        await update.message.reply_text("👋 ¡Hola! ¿En qué puedo ayudarte?", reply_markup=main_menu())
        return

    # Procesar lógica
    response = process_message(user_id, text)

    # --- MANEJO DE RESPUESTAS ESPECIALES DEL HANDLER ---

    # A) Iniciar flujo (cuando viene de NLP "quiero registrar solicitud")
    if response == "__START_FLOW__":
        await update.message.reply_text(
            "🚀 *Iniciemos tu solicitud.*\n\nEscribe tu *nombre completo*:",
            reply_markup=nav_keyboard(include_back=False),
            parse_mode="Markdown"
        )
        return

    # B) Mostrar Menú de Tipos
    if response == "__SHOW_TIPO_MENU__":
        await update.message.reply_text(
            "📂 Selecciona la *categoría*:",
            reply_markup=solicitud_menu(),
            parse_mode="Markdown"
        )
        return

    # C) Mostrar FICHA RESUMEN (Paso 5)
    if response == "__SHOW_SUMMARY__":
        data = get_summary(user_id)
        if data:
            summary_text = (
                "📄 *CONFIRMACIÓN DE SOLICITUD*\n"
                "--------------------------------\n"
                f"👤 *Nombre:* {data['nombre']}\n"
                f"📧 *Correo:* {data['correo']}\n"
                f"📌 *Tipo:* {data['tipo_solicitud']}\n"
                f"📝 *Detalle:* {data['detalle']}\n"
                "--------------------------------\n"
                "¿La información es correcta?"
            )
            await update.message.reply_text(summary_text, reply_markup=confirm_menu(), parse_mode="Markdown")
        return

    # D) Fallback IA
    if response == "__AI_FALLBACK__":
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        ai_response = ask_openai(text)
        await update.message.reply_text(ai_response, parse_mode="Markdown")
        return

    # E) Respuesta normal del flujo (preguntas de nombre/correo)
    # Agregamos botones de navegación si estamos dentro del flujo
    markup = nav_keyboard() if user_id in user_states else None
    await update.message.reply_text(response, reply_markup=markup, parse_mode="Markdown")

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def start_bot():
    token = os.getenv("TELEGRAM_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 CSDC Assistant actualizado y corriendo...")
    app.run_polling()