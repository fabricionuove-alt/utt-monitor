import sys
from datetime import datetime
from fetch_events import get_recent_events, get_birthday_events
from fetch_news import get_news_events
from fetch_instagram import get_instagram_events
from generate_caption import generate_caption
from telegram_bot import send_notification, get_my_chat_id


def check_and_notify():
    """Busca goles, asistencias, tarjetas rojas y arcos en cero de jugadores UTT."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[{now}] 🔍 Buscando eventos de jugadores UTT...")

    events = get_recent_events(days_back=1)

    if not events:
        print("  Sin eventos relevantes en las últimas 24hs.")
        return

    print(f"\n  ✅ {len(events)} evento(s) encontrado(s). Generando captions...\n")
    for event in events:
        caption = generate_caption(event)
        if caption:
            send_notification(event, caption)


def check_news():
    """Busca noticias de prensa sobre jugadores UTT y notifica."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[{now}] 📰 Buscando noticias de prensa...")

    events = get_news_events()

    if not events:
        print("  Sin noticias nuevas.")
        return

    print(f"\n  📰 {len(events)} noticia(s) encontrada(s). Generando captions...\n")
    for event in events:
        caption = generate_caption(event)
        if caption:
            send_notification(event, caption)


def check_instagram():
    """Revisa posts nuevos de los jugadores UTT en Instagram."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[{now}] 📸 Revisando Instagram de jugadores UTT...")

    events = get_instagram_events()

    if not events:
        print("  Sin posts nuevos.")
        return

    print(f"\n  📸 {len(events)} post(s) nuevo(s). Generando captions...\n")
    for event in events:
        caption = generate_caption(event)
        if caption:
            send_notification(event, caption)


def check_birthdays():
    """Chequea si algún jugador UTT cumple años hoy y notifica."""
    now = datetime.now().strftime("%Y-%m-%d")
    print(f"\n[{now}] 🎂 Revisando cumpleaños del día...")

    events = get_birthday_events()

    if not events:
        print("  Sin cumpleaños hoy.")
        return

    print(f"\n  🎉 {len(events)} cumpleaños hoy!\n")
    for event in events:
        caption = generate_caption(event)
        if caption:
            send_notification(event, caption)


def simulate_demo():
    demo_events = [
        {
            "player": {
                "name": "Emiliano Martínez",
                "club": "Aston Villa",
                "position": "Arquero",
                "nationality": "Argentina",
                "instagram": "emi_martinez26",
                "notable": "Campeón del Mundo con Argentina en Qatar 2022",
            },
            "event_type": "CleanSheet",
            "detail": "Clean Sheet",
            "minute": 90,
            "team": "Aston Villa",
            "fixture": {"home": "Aston Villa", "away": "Bologna", "league": "Europa League", "date": "2026-04-16"},
        },
        {
            "player": {
                "name": "Emiliano Buendía",
                "club": "Aston Villa",
                "position": "Mediocampista",
                "nationality": "Argentina",
                "instagram": "em10buendia",
                "notable": "",
            },
            "event_type": "Assist",
            "detail": "Assist",
            "minute": 58,
            "team": "Aston Villa",
            "fixture": {"home": "Aston Villa", "away": "Bologna", "league": "Europa League", "date": "2026-04-16"},
        },
        {
            "player": {
                "name": "Alexander Isak",
                "club": "Liverpool",
                "position": "Delantero",
                "nationality": "Suecia",
                "instagram": "alex_isak",
                "notable": "",
            },
            "event_type": "RedCard",
            "detail": "Red Card",
            "minute": 72,
            "team": "Liverpool",
            "fixture": {"home": "Liverpool", "away": "Arsenal", "league": "Premier League", "date": "2026-04-16"},
        },
    ]

    print("\n🎬 MODO DEMO — UTT Monitor\n")
    for i, event in enumerate(demo_events, 1):
        player_name = event["player"]["name"]
        etype = event["event_type"]
        print(f"[{i}/{len(demo_events)}] {player_name} — {etype}")
        print("📡 Generando caption con IA...\n")
        caption = generate_caption(event)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print("📝 CAPTION GENERADO:\n")
        print(caption)
        print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
        print("📲 Enviando a Telegram...")
        send_notification(event, caption)
        print()

    print("✅ Demo completado. Revisá Telegram.")


def setup_telegram():
    print("\n🔧 Buscando tu Chat ID de Telegram...\n")
    get_my_chat_id()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--demo" in args:
        simulate_demo()
    elif "--setup-telegram" in args:
        setup_telegram()
    elif "--birthdays" in args:
        check_birthdays()
    elif "--instagram" in args:
        check_instagram()
    elif "--news" in args:
        check_news()
    elif "--check" in args:
        check_and_notify()
    else:
        check_and_notify()
