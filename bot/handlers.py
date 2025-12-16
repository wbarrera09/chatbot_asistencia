from bot.intents import classify_intent, FAQ_INTENTS
from bot.db import register_request

# Estado temporal del usuario
user_states = {}

def start_request_flow(user_id):
    user_states[user_id] = {
        "step": 1,
        "data": {
            "nombre": "",
            "correo": "",
            "tipo_solicitud": "",
            "detalle": ""
        }
    }

def cancel_request_flow(user_id):
    if user_id in user_states:
        del user_states[user_id]
        return True
    return False

def revert_step(user_id):
    """Retrocede un paso en el flujo"""
    if user_id in user_states:
        current_step = user_states[user_id]["step"]
        if current_step > 1:
            user_states[user_id]["step"] -= 1
            return user_states[user_id]["step"]
    return 1

def get_summary(user_id):
    """Devuelve los datos actuales para la ficha resumen"""
    if user_id in user_states:
        return user_states[user_id]["data"]
    return None

def process_message(user_id, text):
    # Si el usuario está registrando una solicitud
    if user_id in user_states:
        return handle_request_flow(user_id, text)

    # Intentos FAQ
    intent = classify_intent(text)
    if intent in FAQ_INTENTS:
        return FAQ_INTENTS[intent]

    # Iniciar solicitud desde intención
    if intent == "registrar_solicitud":
        start_request_flow(user_id)
        return "__START_FLOW__"

    # Fallback → IA
    return "__AI_FALLBACK__"

def handle_request_flow(user_id, text):
    state = user_states[user_id]
    step = state["step"]

    # Paso 1: Guardar Nombre -> Ir a Paso 2
    if step == 1:
        state["data"]["nombre"] = text
        state["step"] = 2
        return f"Gracias, *{text}*. 👋\n\n📧 Indícame tu *correo electrónico institucional*:"

    # Paso 2: Guardar Correo -> Ir a Paso 3 (Menú Tipo)
    if step == 2:
        state["data"]["correo"] = text
        state["step"] = 3
        return "__SHOW_TIPO_MENU__"

    # Paso 3: Selección de Tipo (Se hace vía botones, no texto)
    if step == 3:
        return "__SHOW_TIPO_MENU__"

    # Paso 4: Guardar Detalle -> Ir a Paso 5 (Resumen/Confirmación)
    if step == 4:
        state["data"]["detalle"] = text
        state["step"] = 5  # Nuevo paso de confirmación
        return "__SHOW_SUMMARY__"

    # Paso 5: Esperando confirmación (Botón), si escriben texto lo ignoramos o pedimos botón
    if step == 5:
        return "__SHOW_SUMMARY__"

    return "Error de estado. Escribe /start para reiniciar."

def confirm_and_save(user_id):
    """Función final llamada por el botón de Confirmar"""
    if user_id not in user_states:
        return False
    
    data = user_states[user_id]["data"]
    try:
        register_request(
            user_id,
            data["nombre"],
            data["correo"],
            data["tipo_solicitud"],
            data["detalle"]
        )
        del user_states[user_id]
        return True
    except Exception as e:
        print(f"Error DB: {e}")
        return False