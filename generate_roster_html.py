"""Genera docs/index.html con los jugadores del CSV embebidos como JSON."""
import csv, json, os
from datetime import date

BASE = os.path.dirname(os.path.abspath(__file__))
CSV  = os.path.join(BASE, "jugadores.csv")
OUT  = os.path.join(BASE, "docs", "index.html")

players = []
with open(CSV, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        players.append({k: v for k, v in row.items()})

data_js = json.dumps(players, ensure_ascii=False)
today   = date.today().strftime("%d/%m/%Y")

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UTT — Roster</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,sans-serif;background:#0d0d0d;color:#eee}}
  header{{padding:1.6rem 1rem .4rem;text-align:center}}
  h1{{font-size:1.3rem;letter-spacing:.06em;color:#fff}}
  .sub{{color:#666;font-size:.82rem;margin-top:.3rem}}
  .search{{display:flex;justify-content:center;padding:1rem}}
  input{{background:#161616;border:1px solid #2a2a2a;color:#eee;padding:.5rem 1rem;
         border-radius:8px;width:100%;max-width:420px;font-size:.9rem;outline:none}}
  input:focus{{border-color:#444}}
  table{{width:100%;border-collapse:collapse;font-size:.84rem}}
  th{{background:#111;color:#777;padding:.6rem .8rem;text-align:left;
      position:sticky;top:0;border-bottom:1px solid #1e1e1e;cursor:pointer;user-select:none}}
  th:hover{{color:#ccc}}
  td{{padding:.5rem .8rem;border-bottom:1px solid #161616;vertical-align:middle}}
  tr:hover td{{background:#131313}}
  .ig{{color:#7eb8f7;font-size:.78rem}}
  .bday-today td{{background:#1a1500!important}}
  .notable{{color:#666;font-size:.74rem;display:block}}
  .empty{{text-align:center;padding:3rem;color:#555}}
</style>
</head>
<body>
<header>
  <h1>UNIVERSAL TWENTY TWO — ROSTER</h1>
  <p class="sub" id="sub"></p>
</header>
<div class="search">
  <input id="q" type="search" placeholder="Buscar jugador, club, posición...">
</div>
<table>
  <thead><tr>
    <th onclick="sort('nombre')">Jugador ↕</th>
    <th onclick="sort('posicion')">Posición ↕</th>
    <th onclick="sort('club')">Club ↕</th>
    <th onclick="sort('nacionalidad')">Nac. ↕</th>
    <th onclick="sort('fecha_nacimiento')">Cumpleaños ↕</th>
    <th>Instagram</th>
  </tr></thead>
  <tbody id="body"></tbody>
</table>
<script>
const PLAYERS = {data_js};
const MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
let sorted = [...PLAYERS], sortCol = "", sortAsc = true;

function fmtBday(iso){{
  if(!iso) return "";
  const [,m,d] = iso.split("-");
  return `${{parseInt(d)}} ${{MONTHS[parseInt(m)]}}`;
}}
function isToday(iso){{
  if(!iso) return false;
  const [,m,d] = iso.split("-"), n = new Date();
  return parseInt(m)===n.getMonth()+1 && parseInt(d)===n.getDate();
}}
function render(){{
  const q = document.getElementById("q").value.toLowerCase();
  const data = sorted.filter(p => !q ||
    Object.values(p).some(v => v.toLowerCase().includes(q)));
  document.getElementById("sub").textContent =
    `${{data.length}} jugador${{data.length!==1?"es":""}} · Actualizado {today}`;
  document.getElementById("body").innerHTML = data.length===0
    ? `<tr><td colspan="6" class="empty">Sin resultados</td></tr>`
    : data.map(p=>`<tr class="${{isToday(p.fecha_nacimiento)?"bday-today":""}}">
        <td><strong>${{p.nombre}}</strong>${{p.notable?`<span class="notable">${{p.notable}}</span>`:""}}
        </td>
        <td>${{p.posicion}}</td>
        <td>${{p.club}}</td>
        <td>${{p.nacionalidad}}</td>
        <td>${{isToday(p.fecha_nacimiento)?"🎂 ":""}}${{fmtBday(p.fecha_nacimiento)}}</td>
        <td class="ig">${{p.instagram?"@"+p.instagram:""}}</td>
      </tr>`).join("");
}}
function sort(col){{
  if(sortCol===col) sortAsc=!sortAsc; else {{sortCol=col;sortAsc=true;}}
  sorted.sort((a,b)=>{{
    const av=a[col]||"", bv=b[col]||"";
    return sortAsc?av.localeCompare(bv,"es"):bv.localeCompare(av,"es");
  }});
  render();
}}
document.getElementById("q").addEventListener("input", render);
render();
</script>
</body>
</html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"Generado: {OUT} ({len(players)} jugadores)")
