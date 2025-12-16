FAQ_INTENTS = {
    "horario": (
        "🕒 *Horario de Atención CSDC*\n\n"
        "Estamos disponibles de *Lunes a Viernes*.\n"
        "• 🏢 Atención presencial: 8:00 AM - 4:00 PM\n"
        "• 🌐 Recepción de solicitudes en línea: 24/7\n\n"
        "¡Te esperamos!"
    ),
    "requisitos": (
        "📋 *Requisitos Generales*\n\n"
        "Para la mayoría de trámites necesitarás tener a la mano:\n"
        "1. 🆔 DUI vigente (foto legible).\n"
        "2. 📝 Formulario de solicitud completo.\n"
        "3. 📎 Comprobantes específicos según el área.\n\n"
        "💡 *Tip: Si inicias una solicitud aquí, te guiaremos paso a paso.*"
    ),
    "informacion": (
        "🤖 *Información General*\n\n"
        "Soy el Asistente Virtual del CSDC. Puedo ayudarte a:\n"
        "✅ Conocer requisitos de trámites.\n"
        "✅ Consultar horarios y ubicación.\n"
        "✅ Registrar solicitudes oficiales directamente desde este chat."
    )
}

def classify_intent(message: str):
    msg = message.lower()

    if "horario" in msg or "hora" in msg or "abierto" in msg:
        return "horario"

    if "requisito" in msg or "documento" in msg or "necesito" in msg:
        return "requisitos"

    if "información" in msg or "informacion" in msg or "ayuda" in msg:
        return "informacion"

    if "solicitud" in msg or "tramite" in msg or "trámite" in msg or "constancia" in msg:
        return "registrar_solicitud"

    return "otro"