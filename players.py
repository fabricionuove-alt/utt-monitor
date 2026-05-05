import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "jugadores.csv")


def load_players() -> list:
    """Carga el roster de jugadores UTT desde jugadores.csv."""
    players = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            players.append({
                "name": row["nombre"].strip(),
                "aliases": [a.strip() for a in row["aliases"].split("|") if a.strip()],
                "club": row["club"].strip(),
                "position": row["posicion"].strip(),
                "nationality": row["nacionalidad"].strip(),
                "instagram": row["instagram"].strip(),
                "notable": row["notable"].strip(),
            })
    return players


def find_player(name_in_api: str):
    """Busca si un jugador del evento pertenece al roster de UTT."""
    players = load_players()
    name_lower = name_in_api.lower().strip()
    for player in players:
        all_names = [player["name"]] + player["aliases"]
        for n in all_names:
            if n.lower() in name_lower or name_lower in n.lower():
                return player
    return None
