import sys
from datetime import datetime
from fetch_events import get_recent_events
from generate_caption import generate_caption
from telegram_bot import send_notification, get_my_chat_id


def check_and_notify():
    """Ciclo principal: busca eventos UTT y notifica al equipo ODS."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n[{now}] 🔍 Buscando eventos de jugadores UTT...")

    events = get_recent_events(days_back=1)

    if not events:
        print("  Sin eventos relevantes en las últimas 24hs.")
        return

    print(f"\n  ✅ {len(events)} evento(s) encontrado(s). Generando captions...\n")

    for event in events:
        player_name = event["player"]["name"]
        print(f"  → {player_name}...")
        caption = generate_caption(event)
        if caption:
            send_notification(event, caption)


def simulate_demo():
    """
    Modo demo con eventos reales del 16/04/2026:
    - Emiliano Martínez: arco en cero vs Bologna (Europa League)
    - Emiliano Buendía: gol vs Bologna (Europa League)
    """
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
            "fixture": {
                "home": "Aston Villa",
                "away": "Bologna",
                "league": "Europa League",
                "date": "2026-04-16",
            },
        },
        {
            "player": {
                "name": "Emiliano Buendía",
                "club": "Aston Villa",
                "position": "Mediocampista",
                "nationality": "Argentina",
                "instagram": "emilianobuendia21",
                "notable": "",
            },
            "event_type": "Goal",
            "detail": "Normal Goal",
            "minute": 58,
            "team": "Aston Villa",
            "fixture": {
                "home": "Aston Villa",
                "away": "Bologna",
                "league": "Europa League",
                "date": "2026-04-16",
            },
        },
    ]

    print("\n🎬 MODO DEMO — UTT Monitor")
    print("Eventos reales del 16/04/2026 — Aston Villa vs Bologna (Europa League)\n")

    for i, event in enumerate(demo_events, 1):
        player_name = event["player"]["name"]
        detail = event["detail"]
        print(f"[{i}/{len(demo_events)}] {player_name} — {detail}")
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
    """Helper para obtener el chat_id de Telegram."""
    print("\n🔧 Buscando tu Chat ID de Telegram...")
    print("(Asegurate de haberle enviado al menos un mensaje al bot primero)\n")
    get_my_chat_id()


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--demo" in args:
        simulate_demo()

    elif "--setup-telegram" in args:
        setup_telegram()

    elif "--check" in args:
        # Corre una sola vez y termina — útil para probar o correr manualmente
        check_and_notify()

    else:
        print("🤖 UTT Monitor — corriendo un check único.")
        check_and_notify()
