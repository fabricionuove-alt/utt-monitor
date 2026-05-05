import os
import sys
import csv
import traceback
from datetime import date
from flask import Flask, request, jsonify, Response

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__)

CSV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "jugadores.csv")


@app.route("/jugadores")
def jugadores():
    players = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            players.append(row)

    today = date.today()
    rows = ""
    for p in players:
        bday = p.get("fecha_nacimiento", "")
        bday_str = ""
        highlight = ""
        if bday:
            try:
                bd = date.fromisoformat(bday)
                bday_str = bd.strftime("%d %b")
                if bd.month == today.month and bd.day == today.day:
                    highlight = "background:#fff3cd;"
            except ValueError:
                bday_str = bday
        rows += f"""<tr style="{highlight}">
            <td>{p['nombre']}</td>
            <td>{p['posicion']}</td>
            <td>{p['club']}</td>
            <td>{p['nacionalidad']}</td>
            <td>{bday_str}</td>
            <td>{"@" + p["instagram"] if p.get("instagram") else ""}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UTT — Roster</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 0; background: #0d0d0d; color: #eee; }}
  h1 {{ text-align:center; padding: 1.5rem 0 0.5rem; font-size: 1.4rem; letter-spacing:.05em; }}
  .sub {{ text-align:center; color:#888; font-size:.85rem; margin-bottom:1.2rem; }}
  table {{ width:100%; border-collapse:collapse; font-size:.88rem; }}
  th {{ background:#1a1a1a; color:#aaa; padding:.6rem .8rem; text-align:left; position:sticky; top:0; }}
  td {{ padding:.55rem .8rem; border-bottom:1px solid #1e1e1e; }}
  tr:hover td {{ background:#161616; }}
  .badge {{ display:inline-block; background:#1e3a5f; color:#7eb8f7; border-radius:4px; padding:1px 6px; font-size:.78rem; }}
</style>
</head>
<body>
<h1>Universal Twenty Two — Roster</h1>
<p class="sub">{len(players)} jugadores · Actualizado {today.strftime("%d/%m/%Y")}</p>
<table>
  <thead>
    <tr>
      <th>Jugador</th><th>Posición</th><th>Club</th><th>Nac.</th><th>Cumpleaños</th><th>Instagram</th>
    </tr>
  </thead>
  <tbody>{rows}</tbody>
</table>
</body>
</html>"""
    return Response(html, mimetype="text/html")


@app.route("/run")
def run():
    from bot_core import check_and_notify
    expected = os.getenv("CRON_SECRET")
    if expected:
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {expected}":
            return jsonify({"error": "unauthorized"}), 401
    try:
        check_and_notify()
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e), "trace": traceback.format_exc()}), 500


@app.route("/")
def index():
    return jsonify({"status": "UTT Monitor online", "endpoints": ["/jugadores", "/run"]})
