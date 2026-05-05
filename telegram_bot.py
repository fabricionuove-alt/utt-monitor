import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def send_notification(event: dict, caption: str) -> bool:
    """
    Envía la notificación del evento al equipo ODS vía Telegram.
    Retorna True si se envió correctamente.
    """
    if not caption:
        return False

    player = event["player"]
    fixture = event["fixture"]
    detail = event.get("detail", "Gol")
    minute = event.get("minute", "?")

    event_type = event.get("event_type", "Goal")
    if event_type == "CleanSheet":
        event_emoji = "🧤"
        event_label = "Arco en cero"
    elif detail == "Penalty":
        event_emoji = "🎯"
        event_label = "Penal convertido"
    else:
        event_emoji = "⚽"
        event_label = "Gol"

    message = (
        f"🚨 <b>EVENTO UTT DETECTADO</b>\n\n"
        f"👤 <b>{player['name']}</b>\n"
        f"🏟 {player.get('club') or event['team']}\n"
        f"{event_emoji} {event_label} — min. {minute}\n"
        f"📅 {fixture['home']} vs {fixture['away']}\n"
        f"🏆 {fixture['league']} | {fixture['date']}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Caption sugerido:</b>\n\n"
        f"{caption}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 <i>Falta: adjuntar imagen o video del jugador</i>"
    )

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        },
        timeout=10,
    )

    if resp.status_code == 200:
        print(f"  📲 Notificación enviada: {player['name']}")
        return True
    else:
        print(f"  ❌ Error Telegram: {resp.status_code} — {resp.text}")
        return False


def get_my_chat_id() -> None:
    """
    Helper para obtener tu chat_id de Telegram.
    Usá esto después de enviarle cualquier mensaje al bot.
    """
    resp = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        timeout=10,
    )
    data = resp.json()
    updates = data.get("result", [])
    if not updates:
        print("No se encontraron mensajes. Enviále cualquier mensaje al bot primero.")
        return
    for update in updates:
        chat = update.get("message", {}).get("chat", {})
        print(f"Chat ID: {chat.get('id')} | Nombre: {chat.get('first_name')} {chat.get('last_name', '')}")
