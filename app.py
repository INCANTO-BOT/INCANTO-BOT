import os

import requests
from dotenv import load_dotenv
from flask import Flask, request

load_dotenv()

app = Flask(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
API_URL = f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages"

# ---------------------------------------------------------------
# PERSONALIZA AQUÍ: palabra clave -> respuesta
# ---------------------------------------------------------------
RESPUESTAS = {
    "hola": "¡Hola! 👋 Soy el asistente virtual. Escribe:\n"
            "1 - Horarios\n2 - Precios\n3 - Ubicación\n4 - Hablar con una persona",
    "1": "🕘 Atendemos de lunes a viernes, de 9:00 a 18:00.",
    "horarios": "🕘 Atendemos de lunes a viernes, de 9:00 a 18:00.",
    "2": "💲 Puedes ver nuestros precios en: https://tusitio.com/precios",
    "precios": "💲 Puedes ver nuestros precios en: https://tusitio.com/precios",
    "3": "📍 Estamos en Calle Ejemplo 123, Ciudad.",
    "ubicacion": "📍 Estamos en Calle Ejemplo 123, Ciudad.",
    "ubicación": "📍 Estamos en Calle Ejemplo 123, Ciudad.",
    "4": "👤 Un asesor te escribirá pronto. ¡Gracias por tu paciencia!",
}

RESPUESTA_POR_DEFECTO = (
    "No entendí tu mensaje 🤔\n"
    "Escribe *hola* para ver el menú de opciones."
)


def enviar_mensaje(destino: str, texto: str) -> None:
    """Envía un mensaje de texto por WhatsApp Cloud API."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": destino,
        "type": "text",
        "text": {"body": texto},
    }
    r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
    if not r.ok:
        print("Error al enviar:", r.status_code, r.text)


def elegir_respuesta(texto: str) -> str:
    texto = texto.strip().lower()
    if texto in RESPUESTAS:
        return RESPUESTAS[texto]
    # Busca la palabra clave dentro de frases más largas
    for clave, respuesta in RESPUESTAS.items():
        if len(clave) > 1 and clave in texto:
            return respuesta
    return RESPUESTA_POR_DEFECTO


@app.get("/webhook")
def verificar_webhook():
    """Meta llama a esta ruta una vez para verificar tu webhook."""
    if (
        request.args.get("hub.mode") == "subscribe"
        and request.args.get("hub.verify_token") == VERIFY_TOKEN
    ):
        return request.args.get("hub.challenge", ""), 200
    return "Token inválido", 403


@app.post("/webhook")
def recibir_mensaje():
    """Meta envía aquí cada mensaje entrante."""
    data = request.get_json(silent=True) or {}
    try:
        for entry in data.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for msg in value.get("messages", []):
                    remitente = msg["from"]
                    if msg.get("type") == "text":
                        texto = msg["text"]["body"]
                        enviar_mensaje(remitente, elegir_respuesta(texto))
                    else:
                        enviar_mensaje(
                            remitente,
                            "Por ahora solo entiendo mensajes de texto 🙂",
                        )
    except Exception as e:  # nunca devuelvas error a Meta o reintentará
        print("Error procesando webhook:", e)
    return "OK", 200


@app.get("/")
def home():
    return "Bot de WhatsApp activo ✅"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
