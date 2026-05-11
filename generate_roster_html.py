"""Genera docs/index.html — UTT Monitor Dashboard."""
import csv, json
from datetime import date, timedelta
from pathlib import Path

BASE  = Path(__file__).parent
OUT   = BASE / "docs" / "index.html"
TODAY = date.today()

# ── Cargar datos reales ───────────────────────────────────────────────────
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
    if not bd: continue
    try:
        bd_date   = date.fromisoformat(bd)
        this_year = bd_date.replace(year=TODAY.year)
        if this_year < TODAY:
            this_year = bd_date.replace(year=TODAY.year+1)
        days = (this_year - TODAY).days
        age  = TODAY.year - bd_date.year + (1 if days > 0 else 0)
        entry = {"name": p["nombre"], "instagram": p.get("instagram",""),
                 "age": age, "days": days, "date_str": this_year.strftime("%d/%m")}
        if days == 0:   bdays_today.append(entry)
        elif days <= 7: bdays_soon.append(entry)
    except ValueError:
        pass
bdays_soon.sort(key=lambda x: x["days"])

# ── Captions recientes (últimos 7 días) ───────────────────────────────────
recent_caps = []
for c in captions:
    try:
        if (TODAY - date.fromisoformat(c["date"])).days <= 7:
            recent_caps.append(c)
    except Exception:
        pass

# ── Partidos ──────────────────────────────────────────────────────────────
today_str    = TODAY.strftime("%Y-%m-%d")
tomorrow_str = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
today_fix    = [f for f in fixtures if f["date"] == today_str]
tomorrow_fix = [f for f in fixtures if f["date"] == tomorrow_str]

# ── Datos de ejemplo (secciones ilustrativas) ─────────────────────────────
MOCK_LIVE = [
    {
        "home": "Liverpool", "away": "Wolverhampton",
        "league": "Premier League", "minute": "67'", "score": "2-0",
        "players": [{"name": "Alexander Isak", "event": "⚽ 34' · ⚽ 61'", "ig": "alex_isak"}]
    },
    {
        "home": "Aston Villa", "away": "Brentford",
        "league": "Premier League", "minute": "45+2'", "score": "1-0",
        "players": [
            {"name": "Emiliano Martínez", "event": "🧤 sin goles en contra", "ig": "emi_martinez26"},
            {"name": "Emiliano Buendía",  "event": "🎯 43'",                "ig": "em10buendia"},
        ]
    },
]

MOCK_FORGOTTEN = [
    {"name": "Rodrigo Garro",           "club": "Corinthians", "days": 18, "ig": "rodrigarroo"},
    {"name": "Sandi Lovric",            "club": "Udinese",     "days": 14, "ig": "sandilovric"},
    {"name": "Lucas Boyé",              "club": "Alavés",      "days": 11, "ig": "lucasboye31"},
    {"name": "Lucas Martínez Quarta",   "club": "River Plate", "days":  9, "ig": "chinomartinezquarta96"},
]

MOCK_SEASON = [
    {"name": "Alexander Isak",    "ig": "alex_isak",             "club": "Liverpool",    "s1": ("⚽","18"), "s2": ("🎯","7"),  "s3": ("🏟️","31")},
    {"name": "Emiliano Martínez", "ig": "emi_martinez26",         "club": "Aston Villa",  "s1": ("🧤","14"), "s2": ("⛔","89"), "s3": ("🏟️","36")},
    {"name": "Emiliano Buendía",  "ig": "em10buendia",            "club": "Aston Villa",  "s1": ("⚽","9"),  "s2": ("🎯","11"), "s3": ("🏟️","30")},
    {"name": "Rodrigo Garro",     "ig": "rodrigarroo",            "club": "Corinthians",  "s1": ("⚽","6"),  "s2": ("🎯","8"),  "s3": ("🏟️","28")},
]

MOCK_IG = [
    {"name": "Luka Modric",        "ig": "lukamodric10",         "followers": "28.5M", "growth": "+180k", "up": True},
    {"name": "Emiliano Martínez",  "ig": "emi_martinez26",        "followers": "8.2M",  "growth": "+45k",  "up": True},
    {"name": "Alexander Isak",     "ig": "alex_isak",             "followers": "2.1M",  "growth": "+23k",  "up": True},
    {"name": "Emiliano Buendía",   "ig": "em10buendia",           "followers": "1.4M",  "growth": "+8k",   "up": True},
]

MOCK_ALERTS = [
    {"emoji": "📋", "player": "Sandi Lovric",        "note": "Contrato vence Junio 2026 — 1 mes",             "color": "#ef4444", "urgent": True},
    {"emoji": "✈️", "player": "Lucas Boyé",           "note": "Interés de Getafe CF — ventana de transferencia","color": "#14b8a6", "urgent": False},
    {"emoji": "🌍", "player": "Emiliano Martínez",   "note": "Convocado Argentina vs Paraguay — 10 Jun",       "color": "#3b82f6", "urgent": False},
    {"emoji": "🌍", "player": "Alexander Isak",       "note": "Convocado Suecia UEFA Nations League — 7 Jun",   "color": "#3b82f6", "urgent": False},
]

# ── Helpers ───────────────────────────────────────────────────────────────
EVENT_META = {
    "Goal":          ("⚽", "GOL",           "#22c55e"),
    "Assist":        ("🎯", "ASISTENCIA",    "#3b82f6"),
    "CleanSheet":    ("🧤", "ARCO EN CERO",  "#8b5cf6"),
    "RedCard":       ("🟥", "TARJETA ROJA",  "#ef4444"),
    "Birthday":      ("🎂", "CUMPLEAÑOS",    "#f59e0b"),
    "News":          ("📰", "PRENSA",        "#6b7280"),
    "InstagramPost": ("📸", "INSTAGRAM",     "#ec4899"),
    "Transfer":      ("✈️", "TRANSFERENCIA", "#14b8a6"),
}

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

def fmt_kickoff(iso):
    try:    return iso.split("T")[1][:5] + " UTC"
    except: return ""

def ig_avatar(handle):
    if not handle: return ""
    return f"https://unavatar.io/instagram/{handle.lstrip('@')}"

def caption_card(c):
    emoji, label, color = EVENT_META.get(c.get("event_type",""), ("📌","EVENTO","#6b7280"))
    league  = esc(c.get("league",""))
    fixture = esc(c.get("fixture",""))
    if fixture == "vs": fixture = ""
    ig      = c.get("instagram","").lstrip("@")
    cap_raw = c.get("caption","").replace("`","\\`").replace("\\","\\\\").replace("\r","")
    cap_html= esc(c.get("caption","")).replace("\n","<br>")
    avatar  = ig_avatar(ig) if ig else ""
    meta_str = " · ".join(p for p in [league, fixture] if p)
    try:
        days_ago   = (TODAY - date.fromisoformat(c["date"])).days
        date_badge = "hoy" if days_ago == 0 else ("ayer" if days_ago == 1 else f"hace {days_ago}d")
    except Exception:
        date_badge = ""
    av_html   = (f"<img class='avatar' src='{avatar}' onerror=\"this.style.display='none'\" loading='lazy'>"
                 if avatar else f"<div class='avatar-placeholder'>{emoji}</div>")
    date_html = f"<span class='card-date'>{date_badge}</span>" if date_badge else ""
    meta_html = meta_str if meta_str else "&nbsp;"
    return f"""
<div class="card">
  <div class="card-top" style="border-left:3px solid {color}">
    <div class="card-left">
      {av_html}
      <div class="card-info">
        <div class="card-name">{esc(c['player'])}</div>
        <div class="card-meta">{meta_html}</div>
      </div>
    </div>
    <div class="card-right">
      {date_html}
      <span class="tag" style="background:{color}22;color:{color};border:1px solid {color}44">{label}</span>
    </div>
  </div>
  <div class="card-caption">{cap_html}</div>
  <button class="copy-btn" onclick="copy(`{cap_raw}`,this)">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
    Copiar caption
  </button>
</div>"""

def fixture_row(f):
    player_names = "".join(
        f"<span class='fp'><b>{esc(p['name'])}</b>"
        + (f" <span class='fp-ig'>@{esc(p['instagram'])}</span>" if p.get("instagram") else "")
        + "</span>"
        for p in f["players"]
    )
    kt = fmt_kickoff(f["kickoff"])
    status = f["status"]
    if status in ("1H","2H","HT","ET","P"):
        badge = '<span class="badge-live">● EN VIVO</span>'
    elif status == "FT":
        badge = '<span class="badge-done">FT</span>'
    else:
        badge = f'<span class="badge-time">{kt}</span>' if kt else ''
    return f"""
<div class="fixture-card">
  <div class="fixture-top">
    <div class="fixture-teams">{esc(f['home'])} <span class="vs">vs</span> {esc(f['away'])}</div>
    {badge}
  </div>
  <div class="fixture-league">{esc(f['league'])}</div>
  <div class="fixture-players">{player_names}</div>
</div>"""

# ── Sección helper ─────────────────────────────────────────────────────────
def section_hdr(title, count=None, preview=False):
    badge = f'<span class="section-count">{count}</span>' if count is not None else ''
    prev  = '<span class="preview-tag">EJEMPLO</span>' if preview else ''
    return f'<div class="section-header">{prev}<span class="section-title">{title}</span>{badge}</div>'

# ── Construir secciones ───────────────────────────────────────────────────
sections = []

# ═══ STATS BAR ═══════════════════════════════════════════════════════════
live_count = len(MOCK_LIVE)
stats_html = f"""
<div class="stats-bar">
  <div class="stat-item">
    <div class="stat-val">{len(players)}</div>
    <div class="stat-lbl">Jugadores</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">{len(recent_caps)}</div>
    <div class="stat-lbl">Eventos / semana</div>
  </div>
  <div class="stat-item stat-live">
    <div class="stat-val">{live_count} <span class="live-dot">●</span></div>
    <div class="stat-lbl">En vivo</div>
  </div>
  <div class="stat-item">
    <div class="stat-val">{len(today_fix) + len(tomorrow_fix)}</div>
    <div class="stat-lbl">Próximos partidos</div>
  </div>
</div>"""
sections.append(stats_html)

# ═══ CUMPLEAÑOS HOY ══════════════════════════════════════════════════════
for b in bdays_today:
    ig     = b.get("instagram","").lstrip("@")
    avatar = ig_avatar(ig) if ig else ""
    av_html = (f"<img class='bday-avatar' src='{avatar}' onerror=\"this.style.display='none'\" loading='lazy'>"
               if avatar else "<span class='bday-emoji'>🎂</span>")
    ig_html = f'<div class="bday-alert-ig">@{esc(b["instagram"])}</div>' if b.get("instagram") else ''
    sections.append(f"""
<div class="bday-alert">
  {av_html}
  <div class="bday-alert-text">
    <div class="bday-alert-name">¡{esc(b['name'])} cumple {b['age']} hoy! 🎉</div>
    {ig_html}
  </div>
</div>""")

# ═══ PARA POSTEAR ════════════════════════════════════════════════════════
if recent_caps:
    caps_html = "".join(caption_card(c) for c in recent_caps)
    sections.append(f"""
<section>
  {section_hdr("Para postear", len(recent_caps))}
  {caps_html}
</section>""")
else:
    sections.append(f"""
<section>
  {section_hdr("Para postear")}
  <div class="empty-state">
    <div class="empty-icon">📭</div>
    <div>Sin eventos recientes</div>
    <div class="empty-sub">El bot te avisa cuando haya algo</div>
  </div>
</section>""")

# ═══ EN VIVO (ilustrativo) ════════════════════════════════════════════════
live_rows = ""
for m in MOCK_LIVE:
    pnames = "".join(
        f"<div class='live-player'>"
        f"<img class='live-avatar' src='{ig_avatar(p['ig'])}' onerror=\"this.style.display='none'\" loading='lazy'>"
        f"<div><div class='live-pname'>{esc(p['name'])}</div>"
        f"<div class='live-event'>{esc(p['event'])}</div></div>"
        f"</div>"
        for p in m["players"]
    )
    live_rows += f"""
<div class="live-card">
  <div class="live-header">
    <div class="live-teams">{esc(m['home'])} <span class="vs">vs</span> {esc(m['away'])}</div>
    <div class="live-score">{esc(m['score'])}</div>
  </div>
  <div class="live-sub">
    <span class="badge-live">● EN VIVO {esc(m['minute'])}</span>
    <span class="live-league">{esc(m['league'])}</span>
  </div>
  <div class="live-players">{pnames}</div>
</div>"""

sections.append(f"""
<section>
  {section_hdr("En vivo ahora", len(MOCK_LIVE), preview=True)}
  {live_rows}
</section>""")

# ═══ PRÓXIMOS PARTIDOS (real) ═════════════════════════════════════════════
if today_fix:
    sections.append(f"""
<section>
  {section_hdr("Hoy juegan", len(today_fix))}
  {"".join(fixture_row(f) for f in today_fix)}
</section>""")

if tomorrow_fix:
    sections.append(f"""
<section>
  {section_hdr("Mañana juegan", len(tomorrow_fix))}
  {"".join(fixture_row(f) for f in tomorrow_fix)}
</section>""")

if not today_fix and not tomorrow_fix:
    sections.append(f"""
<section>
  {section_hdr("Próximos partidos")}
  <div class="empty-state">
    <div class="empty-icon">🏟️</div>
    <div>Sin partidos en las próximas 48hs</div>
  </div>
</section>""")

# ═══ SIN POSTEAR (ilustrativo) ════════════════════════════════════════════
forg_rows = ""
for p in MOCK_FORGOTTEN:
    avatar = ig_avatar(p["ig"])
    forg_rows += f"""
<div class="forg-row">
  <img class="forg-avatar" src="{avatar}" onerror="this.style.display='none'" loading="lazy">
  <div class="forg-info">
    <div class="forg-name">{esc(p['name'])}</div>
    <div class="forg-club">{esc(p['club'])}</div>
  </div>
  <span class="forg-days">{p['days']}d</span>
</div>"""

sections.append(f"""
<section>
  {section_hdr("Sin postear", len(MOCK_FORGOTTEN), preview=True)}
  <div class="forg-list">
    {forg_rows}
  </div>
</section>""")

# ═══ CUMPLEAÑOS PRÓXIMOS (real) ═══════════════════════════════════════════
if bdays_soon:
    items = "".join(f"""
<div class="bday-row">
  <div class="bday-row-left">
    <span class="bday-cake">🎂</span>
    <div>
      <div class="bday-row-name">{esc(b['name'])}</div>
      <div class="bday-row-meta">Cumple {b['age']} · {b['date_str']}</div>
    </div>
  </div>
  <span class="bday-days">{b['days']}d</span>
</div>""" for b in bdays_soon)
    sections.append(f"""
<section>
  {section_hdr("Cumpleaños esta semana")}
  <div class="bday-list">{items}</div>
</section>""")

# ═══ TEMPORADA (ilustrativo) ══════════════════════════════════════════════
season_rows = ""
for p in MOCK_SEASON:
    avatar = ig_avatar(p["ig"])
    s1_e, s1_v = p["s1"]
    s2_e, s2_v = p["s2"]
    s3_e, s3_v = p["s3"]
    season_rows += f"""
<div class="season-row">
  <img class="season-avatar" src="{avatar}" onerror="this.style.display='none'" loading="lazy">
  <div class="season-name">{esc(p['name'])}<span class="season-club">{esc(p['club'])}</span></div>
  <div class="season-stats">
    <div class="season-stat"><span class="ss-emoji">{s1_e}</span><span class="ss-val">{s1_v}</span></div>
    <div class="season-stat"><span class="ss-emoji">{s2_e}</span><span class="ss-val">{s2_v}</span></div>
    <div class="season-stat"><span class="ss-emoji">{s3_e}</span><span class="ss-val">{s3_v}</span></div>
  </div>
</div>"""

sections.append(f"""
<section>
  {section_hdr("Temporada 25/26", preview=True)}
  <div class="season-list">{season_rows}</div>
</section>""")

# ═══ INSTAGRAM (ilustrativo) ══════════════════════════════════════════════
ig_rows = ""
for p in MOCK_IG:
    avatar  = ig_avatar(p["ig"])
    arrow   = "↑" if p["up"] else "↓"
    clr     = "#22c55e" if p["up"] else "#ef4444"
    ig_rows += f"""
<div class="ig-row">
  <img class="ig-avatar" src="{avatar}" onerror="this.style.display='none'" loading="lazy">
  <div class="ig-info">
    <div class="ig-name">{esc(p['name'])}</div>
    <div class="ig-handle">@{esc(p['ig'])}</div>
  </div>
  <div class="ig-stats">
    <div class="ig-followers">{esc(p['followers'])}</div>
    <div class="ig-growth" style="color:{clr}">{arrow} {esc(p['growth'])}</div>
  </div>
</div>"""

sections.append(f"""
<section>
  {section_hdr("Redes sociales", preview=True)}
  <div class="ig-list">{ig_rows}</div>
</section>""")

# ═══ ALERTAS (ilustrativo) ════════════════════════════════════════════════
alert_rows = ""
for a in MOCK_ALERTS:
    urgent_class = " alert-urgent" if a["urgent"] else ""
    alert_rows += f"""
<div class="alert-row{urgent_class}" style="border-left:3px solid {a['color']}">
  <span class="alert-emoji">{a['emoji']}</span>
  <div class="alert-body">
    <div class="alert-player">{esc(a['player'])}</div>
    <div class="alert-note">{esc(a['note'])}</div>
  </div>
</div>"""

sections.append(f"""
<section>
  {section_hdr("Alertas", len(MOCK_ALERTS), preview=True)}
  <div class="alert-list">{alert_rows}</div>
</section>""")

# ── Render final ──────────────────────────────────────────────────────────
body     = "\n".join(sections)
updated  = TODAY.strftime("%d/%m/%Y")
day_es   = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][TODAY.weekday()]
month_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][TODAY.month-1]
date_str = f"{day_es} {TODAY.day} {month_es}"

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>UTT Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#080808;--surface:#111;--surface2:#1a1a1a;
  --border:#232323;--border2:#2e2e2e;
  --text:#f0f0f0;--muted:#555;--muted2:#888;
  --gold:#e8b84b;--gold-dim:#e8b84b18;
  --green:#22c55e;--red:#ef4444;--blue:#3b82f6;
}}
body{{font-family:'Inter',system-ui,sans-serif;background:var(--bg);color:var(--text);
      max-width:480px;margin:0 auto;padding-bottom:4rem;-webkit-font-smoothing:antialiased}}

/* ── HEADER ──────────────────────────────────────────────── */
header{{padding:1.1rem 1rem .9rem;display:flex;justify-content:space-between;
        align-items:center;border-bottom:1px solid var(--border);
        position:sticky;top:0;background:var(--bg);z-index:10}}
.logo-wrap{{display:flex;align-items:center;gap:.6rem}}
.logo-img{{height:26px;width:auto;filter:brightness(0) invert(1)}}
.logo-divider{{width:1px;height:16px;background:var(--border2)}}
.logo-label{{font-family:'Barlow Condensed',sans-serif;font-size:.68rem;
             letter-spacing:.18em;color:var(--muted2);font-weight:600;text-transform:uppercase}}
.header-right{{text-align:right}}
.header-date{{font-size:.78rem;font-weight:600}}
.header-updated{{font-size:.63rem;color:var(--muted);margin-top:.1rem}}
.header-countdown{{display:inline-flex;align-items:center;gap:.3rem;font-size:.6rem;
                   color:var(--gold);margin-top:.2rem;
                   font-family:'Barlow Condensed',sans-serif;font-weight:600;letter-spacing:.05em}}
.countdown-dot{{width:5px;height:5px;border-radius:50%;background:var(--gold);
                animation:pulse 1.4s ease-in-out infinite}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.15}}}}

/* ── STATS BAR ───────────────────────────────────────────── */
.stats-bar{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;
            background:var(--border);border-top:1px solid var(--border);
            border-bottom:1px solid var(--border);margin-bottom:.25rem}}
.stat-item{{background:var(--bg);padding:.7rem .5rem;text-align:center}}
.stat-val{{font-family:'Barlow Condensed',sans-serif;font-size:1.3rem;
           font-weight:800;color:var(--text);line-height:1}}
.stat-lbl{{font-size:.55rem;color:var(--muted);margin-top:.25rem;
           text-transform:uppercase;letter-spacing:.06em;line-height:1.2}}
.stat-live .stat-val{{color:var(--red)}}
.live-dot{{font-size:.6rem;animation:pulse 1s infinite}}

/* ── SECTION HEADERS ─────────────────────────────────────── */
section{{padding:1.1rem 1rem 0}}
.section-header{{display:flex;align-items:center;gap:.5rem;margin-bottom:.85rem}}
.section-title{{font-family:'Barlow Condensed',sans-serif;font-size:.7rem;font-weight:700;
                letter-spacing:.15em;text-transform:uppercase;color:var(--muted2)}}
.section-count{{background:var(--gold);color:#000;font-size:.6rem;font-weight:700;
                border-radius:99px;padding:.1rem .45rem;
                font-family:'Barlow Condensed',sans-serif}}
.preview-tag{{font-family:'Barlow Condensed',sans-serif;font-size:.58rem;font-weight:700;
              letter-spacing:.08em;text-transform:uppercase;
              color:#7c6f3a;border:1px dashed #7c6f3a55;
              padding:.1rem .35rem;border-radius:4px}}

/* ── BIRTHDAY ALERT ──────────────────────────────────────── */
.bday-alert{{margin:1rem 1rem 0;background:linear-gradient(135deg,#1a1200,#0f0c00);
             border:1px solid #3d2e00;border-radius:12px;
             display:flex;align-items:center;gap:.9rem;padding:1rem 1.1rem}}
.bday-avatar{{width:46px;height:46px;border-radius:50%;object-fit:cover;border:2px solid var(--gold)}}
.bday-emoji{{font-size:2rem;flex-shrink:0}}
.bday-alert-name{{font-weight:700;font-size:.93rem}}
.bday-alert-ig{{font-size:.75rem;color:var(--gold);margin-top:.15rem}}

/* ── CAPTION CARDS ───────────────────────────────────────── */
.card{{background:var(--surface);border:1px solid var(--border);
       border-radius:14px;overflow:hidden;margin-bottom:.7rem}}
.card-top{{display:flex;align-items:center;justify-content:space-between;
           gap:.75rem;padding:.85rem 1rem .75rem;background:var(--surface2)}}
.card-left{{display:flex;align-items:center;gap:.7rem;flex:1;min-width:0}}
.avatar{{width:40px;height:40px;border-radius:50%;object-fit:cover;
         flex-shrink:0;border:1px solid var(--border2)}}
.avatar-placeholder{{width:40px;height:40px;border-radius:50%;background:var(--border2);
                     display:flex;align-items:center;justify-content:center;
                     font-size:1.1rem;flex-shrink:0}}
.card-info{{min-width:0}}
.card-name{{font-weight:600;font-size:.88rem;white-space:nowrap;
            overflow:hidden;text-overflow:ellipsis}}
.card-meta{{font-size:.7rem;color:var(--muted2);margin-top:.1rem;
            white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.card-right{{display:flex;flex-direction:column;align-items:flex-end;gap:.3rem;flex-shrink:0}}
.card-date{{font-size:.58rem;color:var(--muted);font-family:'Barlow Condensed',sans-serif;
            font-weight:600;letter-spacing:.05em;text-transform:uppercase}}
.tag{{font-family:'Barlow Condensed',sans-serif;font-size:.58rem;font-weight:700;
      letter-spacing:.1em;padding:.22rem .48rem;border-radius:6px;white-space:nowrap}}
.card-caption{{font-size:.84rem;line-height:1.65;color:#c0c0c0;padding:.85rem 1rem;
               border-top:1px solid var(--border);border-bottom:1px solid var(--border);
               white-space:pre-line}}
.copy-btn{{width:100%;padding:.65rem 1rem;background:var(--gold);color:#000;border:none;
           font-family:'Barlow Condensed',sans-serif;font-size:.83rem;font-weight:700;
           letter-spacing:.08em;text-transform:uppercase;cursor:pointer;
           display:flex;align-items:center;justify-content:center;gap:.5rem;transition:.15s}}
.copy-btn:active{{opacity:.85;transform:scale(.99)}}
.copy-btn.done{{background:var(--green);color:#fff}}

/* ── FIXTURES ────────────────────────────────────────────── */
.fixture-card{{background:var(--surface);border:1px solid var(--border);
               border-radius:12px;padding:.85rem 1rem;margin-bottom:.6rem}}
.fixture-top{{display:flex;align-items:center;justify-content:space-between;margin-bottom:.3rem}}
.fixture-teams{{font-weight:700;font-size:.9rem}}
.vs{{color:var(--muted);font-weight:400;margin:0 .3rem;font-size:.82rem}}
.fixture-league{{font-size:.68rem;color:var(--muted);margin-bottom:.5rem}}
.badge-live{{font-size:.63rem;font-weight:700;color:var(--red);
             font-family:'Barlow Condensed',sans-serif;letter-spacing:.08em;
             animation:pulse 1.2s infinite}}
.badge-done{{font-size:.65rem;color:var(--muted);font-family:'Barlow Condensed',sans-serif}}
.badge-time{{font-size:.7rem;font-weight:600;color:var(--gold);
             font-family:'Barlow Condensed',sans-serif}}
.fixture-players{{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.4rem}}
.fp{{font-size:.76rem;color:#aaa;display:flex;align-items:center;gap:.25rem}}
.fp-ig{{color:var(--gold);font-size:.7rem}}

/* ── EN VIVO ─────────────────────────────────────────────── */
.live-card{{background:var(--surface);border:1px solid #2a1a1a;
            border-left:3px solid var(--red);border-radius:12px;
            padding:.85rem 1rem;margin-bottom:.6rem}}
.live-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:.3rem}}
.live-teams{{font-weight:700;font-size:.9rem}}
.live-score{{font-family:'Barlow Condensed',sans-serif;font-size:1.1rem;
             font-weight:800;color:var(--gold)}}
.live-sub{{display:flex;align-items:center;gap:.6rem;margin-bottom:.6rem}}
.live-league{{font-size:.68rem;color:var(--muted)}}
.live-players{{display:flex;flex-direction:column;gap:.5rem}}
.live-player{{display:flex;align-items:center;gap:.6rem}}
.live-avatar{{width:30px;height:30px;border-radius:50%;object-fit:cover;
              border:1px solid var(--border2);flex-shrink:0}}
.live-pname{{font-size:.8rem;font-weight:600}}
.live-event{{font-size:.7rem;color:var(--muted2);margin-top:.05rem}}

/* ── SIN POSTEAR ─────────────────────────────────────────── */
.forg-list{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden}}
.forg-row{{display:flex;align-items:center;gap:.7rem;padding:.7rem 1rem;
           border-bottom:1px solid var(--border)}}
.forg-row:last-child{{border:none}}
.forg-avatar{{width:34px;height:34px;border-radius:50%;object-fit:cover;
              border:1px solid var(--border2);flex-shrink:0}}
.forg-info{{flex:1;min-width:0}}
.forg-name{{font-size:.83rem;font-weight:600}}
.forg-club{{font-size:.68rem;color:var(--muted);margin-top:.05rem}}
.forg-days{{font-family:'Barlow Condensed',sans-serif;font-size:.75rem;font-weight:700;
            color:#c0392b;background:#c0392b18;border:1px solid #c0392b33;
            padding:.2rem .5rem;border-radius:99px;white-space:nowrap}}

/* ── BIRTHDAYS LIST ──────────────────────────────────────── */
.bday-list{{background:var(--surface);border:1px solid var(--border);
            border-radius:12px;overflow:hidden}}
.bday-row{{display:flex;align-items:center;justify-content:space-between;
           padding:.7rem 1rem;border-bottom:1px solid var(--border)}}
.bday-row:last-child{{border:none}}
.bday-row-left{{display:flex;align-items:center;gap:.65rem}}
.bday-cake{{font-size:1rem}}
.bday-row-name{{font-size:.83rem;font-weight:600}}
.bday-row-meta{{font-size:.68rem;color:var(--muted);margin-top:.05rem}}
.bday-days{{font-family:'Barlow Condensed',sans-serif;font-size:.75rem;font-weight:700;
            color:var(--gold);background:var(--gold-dim);border:1px solid #e8b84b2a;
            padding:.2rem .5rem;border-radius:99px}}

/* ── TEMPORADA ───────────────────────────────────────────── */
.season-list{{background:var(--surface);border:1px solid var(--border);
              border-radius:12px;overflow:hidden}}
.season-row{{display:flex;align-items:center;gap:.7rem;padding:.75rem 1rem;
             border-bottom:1px solid var(--border)}}
.season-row:last-child{{border:none}}
.season-avatar{{width:36px;height:36px;border-radius:50%;object-fit:cover;
                border:1px solid var(--border2);flex-shrink:0}}
.season-name{{flex:1;font-size:.83rem;font-weight:600;min-width:0;
              white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
              display:flex;flex-direction:column}}
.season-club{{font-size:.65rem;color:var(--muted);font-weight:400;margin-top:.05rem}}
.season-stats{{display:flex;gap:.6rem;flex-shrink:0}}
.season-stat{{display:flex;align-items:center;gap:.2rem;
              background:var(--surface2);border:1px solid var(--border);
              padding:.25rem .5rem;border-radius:8px}}
.ss-emoji{{font-size:.75rem}}
.ss-val{{font-family:'Barlow Condensed',sans-serif;font-size:.85rem;
         font-weight:700;color:var(--text)}}

/* ── INSTAGRAM ───────────────────────────────────────────── */
.ig-list{{background:var(--surface);border:1px solid var(--border);
          border-radius:12px;overflow:hidden}}
.ig-row{{display:flex;align-items:center;gap:.7rem;padding:.7rem 1rem;
         border-bottom:1px solid var(--border)}}
.ig-row:last-child{{border:none}}
.ig-avatar{{width:36px;height:36px;border-radius:50%;object-fit:cover;
            border:1px solid var(--border2);flex-shrink:0}}
.ig-info{{flex:1;min-width:0}}
.ig-name{{font-size:.83rem;font-weight:600;white-space:nowrap;
          overflow:hidden;text-overflow:ellipsis}}
.ig-handle{{font-size:.68rem;color:var(--muted);margin-top:.05rem}}
.ig-stats{{text-align:right;flex-shrink:0}}
.ig-followers{{font-family:'Barlow Condensed',sans-serif;font-size:.9rem;
               font-weight:700;color:var(--text)}}
.ig-growth{{font-size:.68rem;font-weight:600;margin-top:.05rem}}

/* ── ALERTAS ─────────────────────────────────────────────── */
.alert-list{{display:flex;flex-direction:column;gap:.5rem}}
.alert-row{{background:var(--surface);border:1px solid var(--border);
            border-radius:10px;padding:.75rem 1rem;
            display:flex;align-items:flex-start;gap:.7rem}}
.alert-urgent{{background:#1a0a0a}}
.alert-emoji{{font-size:1.1rem;flex-shrink:0;margin-top:.05rem}}
.alert-player{{font-size:.83rem;font-weight:600}}
.alert-note{{font-size:.72rem;color:var(--muted2);margin-top:.15rem;line-height:1.4}}

/* ── EMPTY STATE ─────────────────────────────────────────── */
.empty-state{{text-align:center;padding:2rem 1rem;color:var(--muted);
              font-size:.83rem;background:var(--surface);
              border:1px solid var(--border);border-radius:12px}}
.empty-icon{{font-size:1.8rem;margin-bottom:.5rem}}
.empty-sub{{font-size:.72rem;margin-top:.3rem}}
</style>
</head>
<body>

<header>
  <div class="logo-wrap">
    <img class="logo-img"
         src="https://universaltt.com/wp-content/uploads/2023/04/cropped-Recurso-3-1.png"
         onerror="this.style.display='none'" alt="UTT">
    <div class="logo-divider"></div>
    <span class="logo-label">Monitor</span>
  </div>
  <div class="header-right">
    <div class="header-date">{date_str}</div>
    <div class="header-updated">Act. {updated}</div>
    <div class="header-countdown">
      <span class="countdown-dot"></span>
      próx. en <span id="countdown">--:--:--</span>
    </div>
  </div>
</header>

{body}

<script>
function copy(text, btn){{
  navigator.clipboard.writeText(text).then(()=>{{
    const orig = btn.innerHTML;
    btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg> Copiado`;
    btn.classList.add("done");
    setTimeout(()=>{{ btn.innerHTML=orig; btn.classList.remove("done"); }},2500);
  }});
}}
(function(){{
  function nextRun(){{
    const now=new Date(),ms=now.getTime();
    const d=Date.UTC(now.getUTCFullYear(),now.getUTCMonth(),now.getUTCDate());
    const iv=4*3600*1000;
    return d+Math.ceil((ms-d)/iv)*iv-ms;
  }}
  function pad(n){{return String(n).padStart(2,'0')}}
  function tick(){{
    let s=Math.max(0,Math.round(nextRun()/1000));
    const h=Math.floor(s/3600);s-=h*3600;
    const m=Math.floor(s/60);s-=m*60;
    const el=document.getElementById('countdown');
    if(el)el.textContent=pad(h)+':'+pad(m)+':'+pad(s);
  }}
  tick();setInterval(tick,1000);
}})();
</script>
</body>
</html>"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"Dashboard generado: {len(recent_caps)} para postear, {len(today_fix)} partidos hoy, {len(bdays_today)} cumpleaños hoy")
