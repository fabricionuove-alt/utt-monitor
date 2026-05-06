import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

EMOJIS = {
    "Goal":       ("⚽", "Gol"),
    "Assist":     ("🎯", "Asistencia"),
    "CleanSheet": ("🧤", "Arco en cero"),
    "RedCard":    ("🟥", "Tarjeta roja"),
    "Birthday":   ("🎂", "Cumpleaños"),
    "Transfer":   ("✈️", "Transferencia"),
    "Penalty":    ("🎯", "Penal convertido"),
    "News":          ("📰", "Prensa"),
    "InstagramPost": ("📸", "Post de Instagram"),
}


def send_notification(event: dict, caption: str) -> bool:
    if not caption:
        return False

    player   = event["player"]
    fixture  = event.get("fixture", {})
    etype    = event.get("event_type", "Goal")
    detail   = event.get("detail", "")
    minute   = event.get("minute")

    # Emoji y label
    if detail == "Penalty":
        emoji, label = EMOJIS["Penalty"]
    else:
        emoji, label = EMOJIS.get(etype, ("📌", etype))

    # Cabecera del mensaje
    header_lines = [
        f"🚨 <b>EVENTO UTT DETECTADO</b>\n",
        f"👤 <b>{player['name']}</b>",
        f"🏟 {player.get('club') or event.get('team', '')}",
        f"{emoji} {label}" + (f" — min. {minute}" if minute else ""),
    ]

    if fixture.get("home"):
        header_lines += [
            f"📅 {fixture['home']} vs {fixture['away']}",
            f"🏆 {fixture['league']} | {fixture.get('date', '')}",
        ]

    if etype == "Birthday":
        age = event.get("age")
        header_lines.append(f"🎉 ¡{age} años!" if age else "🎉 ¡Feliz cumpleaños!")

    if etype == "Transfer":
        header_lines.append(f"➡️ {event.get('old_club', '?')} → {event.get('new_club', '?')}")

    if etype == "News":
        header_lines.append(f"🔗 <a href=\"{event.get('news_url', '')}\">Ver noticia</a> — {event.get('news_source', '')}")

    if etype == "InstagramPost":
        post_preview = (event.get("post_caption") or "")[:120]
        header_lines.append(f"💬 \"{post_preview}...\"")
        header_lines.append(f"🔗 <a href=\"{event.get('post_url', '')}\">Ver post</a>")

    message = "\n".join(header_lines)
    message += (
        f"\n\n━━━━━━━━━━━━━━━━━━━━\n"
        f"📝 <b>Caption sugerido:</b>\n\n"
        f"{caption}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📸 <i>Falta: adjuntar imagen o video del jugador</i>"
    )

    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
        timeout=10,
    )

    if resp.status_code == 200:
        print(f"  📲 Enviado: {player['name']} ({label})")
        return True
    else:
        print(f"  ❌ Error Telegram: {resp.status_code} — {resp.text}")
        return False


def get_my_chat_id() -> None:
    resp = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates",
        timeout=10,
    )
    updates = resp.json().get("result", [])
    if not updates:
        print("No se encontraron mensajes. Enviále cualquier mensaje al bot primero.")
        return
    for u in updates:
        chat = u.get("message", {}).get("chat", {})
        print(f"Chat ID: {chat.get('id')} | {chat.get('first_name')} {chat.get('last_name', '')}")
