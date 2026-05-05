import requests
import time
from datetime import datetime, timedelta
from config import FOOTBALL_API_KEY, LEAGUES
from players import find_player, load_players

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}

# Delay entre requests para respetar el límite del plan gratuito (10 req/min)
REQUEST_DELAY = 7  # segundos


def api_get(endpoint: str, params: dict) -> list:
    """Request a la API con manejo de rate limit."""
    time.sleep(REQUEST_DELAY)
    resp = requests.get(
        f"{BASE_URL}/{endpoint}",
        headers=HEADERS,
        params=params,
        timeout=10,
    )
    if resp.status_code == 429:
        print(f"  ⏳ Rate limit alcanzado, esperando 30s...")
        time.sleep(30)
        resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
    if resp.status_code != 200:
        print(f"  ⚠️  Error en API ({endpoint}): {resp.status_code}")
        return []
    return resp.json().get("response", [])


def get_fixtures_for_date(league_id: int, date_str: str) -> list:
    """Obtiene partidos finalizados de una liga en una fecha."""
    return api_get("fixtures", {"league": league_id, "date": date_str, "status": "FT"})


def get_fixture_events(fixture_id: int) -> list:
    """Obtiene todos los eventos de un partido."""
    return api_get("fixtures/events", {"fixture": fixture_id})


def get_fixture_lineups(fixture_id: int) -> list:
    """Obtiene las alineaciones de un partido (para detectar arqueros titulares)."""
    return api_get("fixtures/lineups", {"fixture": fixture_id})


def check_clean_sheet(fixture: dict, player: dict) -> bool:
    """
    Detecta si un arquero UTT mantuvo el arco en cero.
    Verifica que el equipo del arquero no recibió goles.
    """
    home_team = fixture["teams"]["home"]["name"]
    away_team = fixture["teams"]["away"]["name"]
    home_goals = fixture["goals"]["home"] or 0
    away_goals = fixture["goals"]["away"] or 0
    player_club = player.get("club", "").lower()

    if player_club in home_team.lower() and away_goals == 0:
        return True
    if player_club in away_team.lower() and home_goals == 0:
        return True
    return False


def player_in_lineup(fixture_id: int, player: dict) -> bool:
    """Verifica si un jugador jugó el partido revisando la alineación."""
    lineups = get_fixture_lineups(fixture_id)
    player_names = [player["name"].lower()] + [a.lower() for a in player["aliases"]]
    for team_lineup in lineups:
        for p in team_lineup.get("startXI", []):
            name = (p.get("player", {}).get("name") or "").lower()
            if any(n in name or name in n for n in player_names):
                return True
    return False


def get_recent_events(days_back: int = 1) -> list:
    """
    Escanea partidos recientes en todas las ligas monitoreadas.
    Detecta: goles, penales convertidos y arcos en cero de arqueros UTT.
    """
    found_events = []
    seen_events = set()

    dates = [
        (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back + 1)
    ]

    # Cargar arqueros del roster para detección de clean sheets
    all_players = load_players()
    goalkeepers = [p for p in all_players if p["position"].lower() == "arquero"]

    for league_name, league_id in LEAGUES.items():
        for date_str in dates:
            print(f"  Revisando {league_name} — {date_str}...")
            fixtures = get_fixtures_for_date(league_id, date_str)

            for fixture in fixtures:
                fixture_id = fixture["fixture"]["id"]
                home_team = fixture["teams"]["home"]["name"]
                away_team = fixture["teams"]["away"]["name"]
                fixture_info = {
                    "home": home_team,
                    "away": away_team,
                    "league": league_name,
                    "date": date_str,
                }

                # --- GOLES de jugadores UTT ---
                events = get_fixture_events(fixture_id)
                for event in events:
                    if event["type"] != "Goal" or event["detail"] == "Own Goal":
                        continue
                    player_name = (event["player"].get("name") or "").strip()
                    if not player_name:
                        continue
                    player = find_player(player_name)
                    if not player:
                        continue

                    event_key = f"{fixture_id}_{player['name']}_{event['time']['elapsed']}"
                    if event_key in seen_events:
                        continue
                    seen_events.add(event_key)

                    found_events.append({
                        "player": player,
                        "event_type": "Goal",
                        "detail": event["detail"],
                        "minute": event["time"]["elapsed"],
                        "team": event["team"]["name"],
                        "fixture": fixture_info,
                    })
                    print(f"    ⚽ Gol UTT: {player['name']} min.{event['time']['elapsed']}")

                # --- ARCO EN CERO de arqueros UTT ---
                for gk in goalkeepers:
                    event_key = f"{fixture_id}_{gk['name']}_cleansheet"
                    if event_key in seen_events:
                        continue
                    if check_clean_sheet(fixture, gk):
                        # Verificar que el arquero efectivamente jugó
                        if player_in_lineup(fixture_id, gk):
                            seen_events.add(event_key)
                            found_events.append({
                                "player": gk,
                                "event_type": "CleanSheet",
                                "detail": "Clean Sheet",
                                "minute": 90,
                                "team": gk["club"],
                                "fixture": fixture_info,
                            })
                            print(f"    🧤 Arco en cero UTT: {gk['name']}")

    return found_events
