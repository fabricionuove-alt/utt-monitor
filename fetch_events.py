import requests
import time
from datetime import datetime, timedelta
from config import FOOTBALL_API_KEY, LEAGUES, CURRENT_SEASON
from players import find_player, load_players

BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}

REQUEST_DELAY = 7  # segundos entre requests (plan gratuito: 10 req/min)


def api_get(endpoint: str, params: dict) -> list:
    time.sleep(REQUEST_DELAY)
    resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
    if resp.status_code == 429:
        print(f"  ⏳ Rate limit, esperando 30s...")
        time.sleep(30)
        resp = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
    if resp.status_code != 200:
        print(f"  ⚠️  Error en API ({endpoint}): {resp.status_code}")
        return []
    return resp.json().get("response", [])


def get_fixtures_for_date(league_id: int, date_str: str) -> list:
    return api_get("fixtures", {"league": league_id, "date": date_str, "status": "FT"})


def get_fixture_events(fixture_id: int) -> list:
    return api_get("fixtures/events", {"fixture": fixture_id})


def get_fixture_lineups(fixture_id: int) -> list:
    return api_get("fixtures/lineups", {"fixture": fixture_id})


def get_transfers(player_api_id: int) -> list:
    return api_get("transfers", {"player": player_api_id})


def check_clean_sheet(fixture: dict, player: dict) -> bool:
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
    Detecta: goles, penales, asistencias, tarjetas rojas y arcos en cero.
    """
    found_events = []
    seen_events = set()

    dates = [
        (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(days_back + 1)
    ]

    all_players = load_players()
    goalkeepers = [p for p in all_players if "arquero" in p["position"].lower()]

    for league_name, league_id in LEAGUES.items():
        for date_str in dates:
            print(f"  Revisando {league_name} — {date_str}...")
            fixtures = get_fixtures_for_date(league_id, date_str)

            for fixture in fixtures:
                fixture_id = fixture["fixture"]["id"]
                fixture_info = {
                    "home": fixture["teams"]["home"]["name"],
                    "away": fixture["teams"]["away"]["name"],
                    "league": league_name,
                    "date": date_str,
                }

                events = get_fixture_events(fixture_id)

                for event in events:
                    etype = event.get("type", "")
                    detail = event.get("detail", "")
                    minute = event["time"]["elapsed"]
                    player_name = (event["player"].get("name") or "").strip()
                    assist_name = (event.get("assist", {}) or {}).get("name") or ""

                    # --- GOLES (incluye penales) ---
                    if etype == "Goal" and detail != "Own Goal":
                        player = find_player(player_name)
                        if player:
                            key = f"{fixture_id}_{player['name']}_{minute}_goal"
                            if key not in seen_events:
                                seen_events.add(key)
                                found_events.append({
                                    "player": player,
                                    "event_type": "Goal",
                                    "detail": detail,
                                    "minute": minute,
                                    "team": event["team"]["name"],
                                    "fixture": fixture_info,
                                })
                                print(f"    ⚽ Gol: {player['name']} min.{minute}")

                    # --- ASISTENCIAS ---
                    if etype == "Goal" and detail != "Own Goal" and assist_name:
                        player = find_player(assist_name)
                        if player:
                            key = f"{fixture_id}_{player['name']}_{minute}_assist"
                            if key not in seen_events:
                                seen_events.add(key)
                                found_events.append({
                                    "player": player,
                                    "event_type": "Assist",
                                    "detail": "Assist",
                                    "minute": minute,
                                    "team": event["team"]["name"],
                                    "fixture": fixture_info,
                                })
                                print(f"    🎯 Asistencia: {player['name']} min.{minute}")

                    # --- TARJETAS ROJAS ---
                    if etype == "Card" and detail in ("Red Card", "Yellow Red Card"):
                        player = find_player(player_name)
                        if player:
                            key = f"{fixture_id}_{player['name']}_{minute}_red"
                            if key not in seen_events:
                                seen_events.add(key)
                                found_events.append({
                                    "player": player,
                                    "event_type": "RedCard",
                                    "detail": detail,
                                    "minute": minute,
                                    "team": event["team"]["name"],
                                    "fixture": fixture_info,
                                })
                                print(f"    🟥 Tarjeta roja: {player['name']} min.{minute}")

                # --- ARCO EN CERO ---
                for gk in goalkeepers:
                    key = f"{fixture_id}_{gk['name']}_cleansheet"
                    if key not in seen_events and check_clean_sheet(fixture, gk):
                        if player_in_lineup(fixture_id, gk):
                            seen_events.add(key)
                            found_events.append({
                                "player": gk,
                                "event_type": "CleanSheet",
                                "detail": "Clean Sheet",
                                "minute": 90,
                                "team": gk["club"],
                                "fixture": fixture_info,
                            })
                            print(f"    🧤 Arco en cero: {gk['name']}")

    return found_events


def get_birthday_events() -> list:
    """Retorna jugadores UTT que cumplen años hoy."""
    from datetime import date
    today = date.today()
    birthday_events = []
    for player in load_players():
        bday = player.get("fecha_nacimiento", "")
        if not bday:
            continue
        try:
            bd = date.fromisoformat(bday)
            if bd.month == today.month and bd.day == today.day:
                age = today.year - bd.year
                birthday_events.append({
                    "player": player,
                    "event_type": "Birthday",
                    "detail": "Birthday",
                    "age": age,
                    "minute": None,
                    "team": player.get("club", ""),
                    "fixture": {},
                })
                print(f"    🎂 Cumpleaños: {player['name']} ({age} años)")
        except ValueError:
            continue
    return birthday_events
