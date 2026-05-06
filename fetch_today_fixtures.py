"""
Busca los partidos de HOY y MAÑANA en las ligas monitoreadas
donde juegan equipos de jugadores UTT.
Guarda el resultado en today_fixtures.json.
"""
import json
import time
import requests
from datetime import date, timedelta
from pathlib import Path
from config import FOOTBALL_API_KEY, LEAGUES
from players import load_players

OUT = Path(__file__).parent / "today_fixtures.json"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": FOOTBALL_API_KEY}
DELAY = 7


def api_get(endpoint, params):
    time.sleep(DELAY)
    r = requests.get(f"{BASE_URL}/{endpoint}", headers=HEADERS, params=params, timeout=10)
    if r.status_code != 200:
        return []
    return r.json().get("response", [])


def get_fixtures():
    players = load_players()
    # Mapeo club → jugador(es) UTT
    club_players = {}
    for p in players:
        club = p.get("club", "").strip().lower()
        if not club or club in ("retirado", "sin club", ""):
            continue
        club_players.setdefault(club, []).append(p)

    today = date.today()
    dates = [today.strftime("%Y-%m-%d"), (today + timedelta(days=1)).strftime("%Y-%m-%d")]
    matches = []
    seen = set()

    for league_name, league_id in LEAGUES.items():
        for d in dates:
            fixtures = api_get("fixtures", {"league": league_id, "date": d})
            for fix in fixtures:
                fid = fix["fixture"]["id"]
                if fid in seen:
                    continue

                home = fix["teams"]["home"]["name"]
                away = fix["teams"]["away"]["name"]
                status = fix["fixture"]["status"]["short"]
                kickoff = fix["fixture"]["date"]  # ISO string

                # Buscar jugadores UTT en cualquiera de los dos equipos
                utt_players = []
                for club_key, plist in club_players.items():
                    if club_key in home.lower() or club_key in away.lower():
                        utt_players.extend(plist)

                if not utt_players:
                    continue

                seen.add(fid)
                matches.append({
                    "date": d,
                    "kickoff": kickoff,
                    "home": home,
                    "away": away,
                    "league": league_name,
                    "status": status,
                    "players": [
                        {"name": p["name"], "instagram": p.get("instagram",""),
                         "position": p.get("position",""), "club": p.get("club","")}
                        for p in utt_players
                    ],
                })

    matches.sort(key=lambda x: x["kickoff"])
    OUT.write_text(json.dumps(matches, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  {len(matches)} partido(s) encontrado(s) con jugadores UTT.")
    return matches


if __name__ == "__main__":
    get_fixtures()
