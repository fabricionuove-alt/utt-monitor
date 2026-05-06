"""Genera docs/index.html — dashboard CM de UTT, pensado para celular."""
import csv, json, re
from datetime import date, timedelta
from pathlib import Path

BASE     = Path(__file__).parent
OUT      = BASE / "docs" / "index.html"
TODAY    = date.today()

# ── Cargar datos ──────────────────────────────────────────────────────────
def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")) if Path(path).exists() else default
    except Exception:
        return default

players  = list(csv.DictReader(open(BASE/"jugadores.csv", encoding="utf-8")))
captions = load_json(BASE/"captions_log.json", [])
fixtures = load_json(BASE/"today_fixtures.json", [])

# ── Cumpleaños ────────────────────────────────────────────────────────────
bdays_today, bdays_soon = [], []
for p in players:
    bd = p.get("fecha_nacimiento","")
    if not bd:
        continue
    try:
        bd_date = date.fromisoformat(bd)
        this_year = bd_date.replace(year=TODAY.year)
        if this_year < TODAY:
            this_year = bd_date.replace(year=TODAY.year+1)
        days = (this_year - TODAY).days
        age  = TODAY.year - bd_date.year + (1 if days > 0 else 0)
        entry = {"name": p["nombre"], "instagram": p.get("instagram",""),
                 "age": age, "days": days, "date_str": this_year.strftime("%d/%m")}
        if days == 0:
            bdays_today.append(entry)
        elif days <= 7:
            bdays_soon.append(entry)
    except ValueError:
        pass
bdays_soon.sort(key=lambda x: x["days"])

# ── Captions recientes (últimas 48hs) ─────────────────────────────────────
recent_caps = []
for c in captions:
    try:
        cap_date = date.fromisoformat(c["date"])
        if (TODAY - cap_date).days <= 1:
            recent_caps.append(c)
    except Exception:
        pass

# ── Partidos hoy / mañana ────────────────────────────────────────────────
today_str    = TODAY.strftime("%Y-%m-%d")
tomorrow_str = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
today_fix    = [f for f in fixtures if f["date"] == today_str]
tomorrow_fix = [f for f in fixtures if f["date"] == tomorrow_str]

# ── Helpers ───────────────────────────────────────────────────────────────
EMOJIS = {"Goal":"⚽","Assist":"🎯","CleanSheet":"🧤","RedCard":"🟥",
          "Birthday":"🎂","News":"📰","InstagramPost":"📸","Transfer":"✈️"}

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

def fmt_kickoff(iso):
    # "2026-05-06T20:00:00+00:00" → "20:00"
    try:
        t = iso.split("T")[1][:5]
        return t + " UTC"
    except Exception:
        return ""

def caption_card(c):
    emoji  = EMOJIS.get(c.get("event_type",""), "📌")
    league = f" · {esc(c['league'])}" if c.get("league") else ""
    fix    = f" · {esc(c['fixture'])}" if c.get("fixture") and c["fixture"] != "vs" else ""
    ig     = f"@{esc(c['instagram'])}" if c.get("instagram") else ""
    cap    = esc(c.get("caption","")).replace("\n","<br>")
    cap_raw = c.get("caption","").replace("`","\\`").replace("\\","\\\\")
    return f"""
<div class="card">
  <div class="card-header">
    <span class="card-emoji">{emoji}</span>
    <div>
      <div class="card-name">{esc(c['player'])}</div>
      <div class="card-meta">{esc(c.get('event_type',''))}{league}{fix}</div>
    </div>
    {f'<div class="card-ig">{ig}</div>' if ig else ''}
  </div>
  <div class="card-caption" id="cap-{id(c)}">{cap}</div>
  <button class="copy-btn" onclick="copy(`{cap_raw}`,this)">Copiar caption</button>
</div>"""

def fixture_row(f):
    player_names = " · ".join(
        f"<b>{esc(p['name'])}</b>" + (f" <span class='ig-s'>@{esc(p['instagram'])}</span>" if p.get("instagram") else "")
        for p in f["players"]
    )
    kt = fmt_kickoff(f["kickoff"])
    status = f["status"]
    if status in ("1H","2H","HT","ET","P"):
        status_html = '<span class="live">● EN VIVO</span>'
    elif status == "FT":
        status_html = '<span class="done">Finalizado</span>'
    else:
        status_html = f'<span class="time">{kt}</span>' if kt else ''

    return f"""
<div class="fixture">
  <div class="fixture-match">{esc(f['home'])} <span class="vs">vs</span> {esc(f['away'])}</div>
  <div class="fixture-sub">{esc(f['league'])} {status_html}</div>
  <div class="fixture-players">{player_names}</div>
</div>"""

# ── HTML ──────────────────────────────────────────────────────────────────
sections = []

# — Cumpleaños HOY —
for b in bdays_today:
    ig = f"@{esc(b['instagram'])}" if b.get("instagram") else ""
    sections.append(f"""
<div class="alert-bday">
  <span class="alert-icon">🎂</span>
  <div>
    <div class="alert-name">¡Hoy cumple {b['age']} años {esc(b['name'])}!</div>
    {f'<div class="alert-ig">{ig}</div>' if ig else ''}
  </div>
</div>""")

# — Para postear hoy —
if recent_caps:
    caps_html = "".join(caption_card(c) for c in recent_caps)
    sections.append(f"""
<section>
  <h2>📥 Para postear</h2>
  {caps_html}
</section>""")
else:
    sections.append("""
<section>
  <h2>📥 Para postear</h2>
  <div class="empty">Sin eventos recientes. El bot avisará cuando haya algo.</div>
</section>""")

# — Partidos hoy —
if today_fix:
    rows = "".join(fixture_row(f) for f in today_fix)
    sections.append(f"""
<section>
  <h2>🏟️ Hoy juegan</h2>
  {rows}
</section>""")

# — Partidos mañana —
if tomorrow_fix:
    rows = "".join(fixture_row(f) for f in tomorrow_fix)
    sections.append(f"""
<section>
  <h2>📅 Mañana juegan</h2>
  {rows}
</section>""")

if not today_fix and not tomorrow_fix:
    sections.append("""
<section>
  <h2>🏟️ Próximos partidos</h2>
  <div class="empty">Sin partidos en los próximas 48hs.</div>
</section>""")

# — Cumpleaños próximos —
if bdays_soon:
    bday_items = "".join(f"""
<div class="bday-item">
  <span class="bday-icon">🎂</span>
  <div>
    <div class="bday-name">{esc(b['name'])} · {b['age']} años</div>
    <div class="bday-when">En {b['days']} día{'s' if b['days']>1 else ''} · {b['date_str']}</div>
  </div>
</div>""" for b in bdays_soon)
    sections.append(f"""
<section>
  <h2>🗓️ Cumpleaños esta semana</h2>
  {bday_items}
</section>""")

body = "\n".join(sections)
updated = TODAY.strftime("%d/%m/%Y")

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>UTT — Daily</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0a0a0a;--surface:#141414;--border:#222;
  --text:#e5e5e5;--muted:#666;--accent:#3b82f6;
  --green:#10b981;--yellow:#f59e0b;--red:#ef4444;
}}
body{{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);
      color:var(--text);max-width:600px;margin:0 auto;padding-bottom:2rem}}

header{{padding:1.2rem 1rem .6rem;display:flex;justify-content:space-between;align-items:center;
        border-bottom:1px solid var(--border)}}
.logo{{font-weight:800;font-size:1.1rem;letter-spacing:.08em}}
.updated{{font-size:.72rem;color:var(--muted)}}

section{{padding:1rem 1rem 0}}
h2{{font-size:.75rem;font-weight:700;letter-spacing:.1em;color:var(--muted);
    text-transform:uppercase;margin-bottom:.75rem}}

/* Alert cumpleaños hoy */
.alert-bday{{background:#1a1000;border:1px solid #3a2500;border-radius:10px;
             display:flex;align-items:center;gap:.8rem;padding:1rem;margin:1rem 1rem 0}}
.alert-icon{{font-size:2rem}}
.alert-name{{font-weight:700;font-size:1rem}}
.alert-ig{{color:var(--accent);font-size:.82rem;margin-top:.2rem}}

/* Caption cards */
.card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;
       padding:1rem;margin-bottom:.75rem}}
.card-header{{display:flex;align-items:flex-start;gap:.7rem;margin-bottom:.75rem}}
.card-emoji{{font-size:1.5rem;flex-shrink:0}}
.card-name{{font-weight:700;font-size:.95rem}}
.card-meta{{font-size:.75rem;color:var(--muted);margin-top:.15rem}}
.card-ig{{margin-left:auto;font-size:.78rem;color:var(--accent);white-space:nowrap}}
.card-caption{{font-size:.88rem;line-height:1.6;color:#ccc;
               background:#0d0d0d;border-radius:8px;padding:.75rem;
               white-space:pre-line;margin-bottom:.75rem}}
.copy-btn{{width:100%;padding:.65rem;background:var(--accent);color:#fff;
           border:none;border-radius:8px;font-size:.88rem;font-weight:600;
           cursor:pointer;transition:.15s}}
.copy-btn:active{{opacity:.8}}
.copy-btn.done{{background:var(--green)}}

/* Fixtures */
.fixture{{background:var(--surface);border:1px solid var(--border);border-radius:10px;
          padding:.9rem 1rem;margin-bottom:.6rem}}
.fixture-match{{font-weight:700;font-size:.95rem}}
.vs{{color:var(--muted);font-weight:400;margin:0 .3rem}}
.fixture-sub{{font-size:.75rem;color:var(--muted);margin:.25rem 0 .4rem;
              display:flex;align-items:center;gap:.5rem}}
.live{{color:var(--red);font-weight:700;font-size:.72rem;
       animation:blink 1.2s infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.4}}}}
.done{{color:var(--muted)}}
.time{{color:var(--yellow)}}
.fixture-players{{font-size:.82rem;color:#aaa}}
.ig-s{{color:var(--accent);font-size:.75rem}}

/* Cumpleaños próximos */
.bday-item{{display:flex;align-items:center;gap:.75rem;padding:.6rem 0;
            border-bottom:1px solid var(--border)}}
.bday-item:last-child{{border:none}}
.bday-icon{{font-size:1.3rem}}
.bday-name{{font-size:.88rem;font-weight:600}}
.bday-when{{font-size:.75rem;color:var(--muted);margin-top:.1rem}}

.empty{{color:var(--muted);font-size:.85rem;padding:.5rem 0}}
</style>
</head>
<body>
<header>
  <span class="logo">UTT</span>
  <span class="updated">Actualizado {updated}</span>
</header>

{body}

<script>
function copy(text, btn){{
  navigator.clipboard.writeText(text).then(()=>{{
    btn.textContent = "✓ Copiado";
    btn.classList.add("done");
    setTimeout(()=>{{ btn.textContent="Copiar caption"; btn.classList.remove("done"); }}, 3000);
  }});
}}
</script>
</body>
</html>"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"Dashboard generado: {len(recent_caps)} para postear, {len(today_fix)} partidos hoy, {len(bdays_today)} cumpleaños hoy")
