import os
from dotenv import load_dotenv

load_dotenv()

FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Ligas monitoreadas (IDs de API-Football)
LEAGUES = {
    "Champions League": 2,
    "Europa League": 3,
    "Premier League": 39,
    "La Liga": 140,
    "Serie A": 135,
    "Ligue 1": 61,
    "Bundesliga": 78,
    "Argentine Primera": 128,
    "Brazilian Serie A": 71,
    "Eredivisie": 88,
}

CURRENT_SEASON = 2025  # Temporada 2025-2026
