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

# ── Captions recientes (últimos 7 días) ───────────────────────────────────
recent_caps = []
for c in captions:
    try:
        cap_date = date.fromisoformat(c["date"])
        if (TODAY - cap_date).days <= 7:
            recent_caps.append(c)
    except Exception:
        pass

# ── Partidos hoy / mañana ────────────────────────────────────────────────
today_str    = TODAY.strftime("%Y-%m-%d")
tomorrow_str = (TODAY + timedelta(days=1)).strftime("%Y-%m-%d")
today_fix    = [f for f in fixtures if f["date"] == today_str]
tomorrow_fix = [f for f in fixtures if f["date"] == tomorrow_str]

# ── Helpers ───────────────────────────────────────────────────────────────
EVENT_META = {
    "Goal":          ("⚽", "GOL",          "#22c55e"),
    "Assist":        ("🎯", "ASISTENCIA",   "#3b82f6"),
    "CleanSheet":    ("🧤", "ARCO EN CERO", "#8b5cf6"),
    "RedCard":       ("🟥", "TARJETA ROJA", "#ef4444"),
    "Birthday":      ("🎂", "CUMPLEAÑOS",   "#f59e0b"),
    "News":          ("📰", "PRENSA",       "#6b7280"),
    "InstagramPost": ("📸", "INSTAGRAM",    "#ec4899"),
    "Transfer":      ("✈️", "TRANSFERENCIA","#14b8a6"),
}

def esc(s):
    return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;").replace("'","&#39;")

def fmt_kickoff(iso):
    try:
        t = iso.split("T")[1][:5]
        return t + " UTC"
    except Exception:
        return ""

def ig_avatar(handle):
    """URL de avatar de Instagram vía unavatar.io (proxy gratuito)."""
    if not handle:
        return ""
    clean = handle.lstrip("@")
    return f"https://unavatar.io/instagram/{clean}"

def caption_card(c):
    emoji, label, color = EVENT_META.get(c.get("event_type",""), ("📌","EVENTO","#6b7280"))
    league = esc(c.get("league",""))
    fixture = esc(c.get("fixture",""))
    if fixture == "vs": fixture = ""
    ig = c.get("instagram","").lstrip("@")
    cap_raw = c.get("caption","").replace("`","\\`").replace("\\","\\\\").replace("\r","")
    cap_html = esc(c.get("caption","")).replace("\n","<br>")
    avatar = ig_avatar(ig) if ig else ""

    meta_parts = [p for p in [league, fixture] if p]
    meta_str = " · ".join(meta_parts)

    # Date badge (days ago)
    try:
        cap_date = date.fromisoformat(c["date"])
        days_ago = (TODAY - cap_date).days
        date_badge = "hoy" if days_ago == 0 else (f"ayer" if days_ago == 1 else f"hace {days_ago}d")
    except Exception:
        date_badge = ""

    avatar_html = (f"<img class='avatar' src='{avatar}' onerror=\"this.style.display='none'\" loading='lazy'>"
                   if avatar else f"<div class='avatar-placeholder'>{emoji}</div>")
    meta_content = meta_str if meta_str else "&nbsp;"
    date_html = f"<span class='card-date'>{date_badge}</span>" if date_badge else ""
    return f"""
<div class="card">
  <div class="card-top" style="border-left:3px solid {color}">
    <div class="card-left">
      {avatar_html}
      <div class="card-info">
        <div class="card-name">{esc(c['player'])}</div>
        <div class="card-meta">{meta_content}</div>
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
        status_html = '<span class="badge-live">● EN VIVO</span>'
    elif status == "FT":
        status_html = '<span class="badge-done">FT</span>'
    else:
        status_html = f'<span class="badge-time">{kt}</span>' if kt else ''

    return f"""
<div class="fixture-card">
  <div class="fixture-teams">{esc(f['home'])} <span class="vs">vs</span> {esc(f['away'])}</div>
  <div class="fixture-bottom">
    <span class="fixture-league">{esc(f['league'])}</span>
    {status_html}
  </div>
  <div class="fixture-players">{player_names}</div>
</div>"""

# ── HTML ──────────────────────────────────────────────────────────────────
sections = []

# — Cumpleaños HOY —
for b in bdays_today:
    ig = b.get("instagram","").lstrip("@")
    avatar = ig_avatar(ig) if ig else ""
    ig_str = f"@{esc(b['instagram'])}" if b.get("instagram") else ""
    avatar_html = (f"<img class='bday-avatar' src='{avatar}' onerror=\"this.style.display='none'\" loading='lazy'>"
                   if avatar else "<span class='bday-emoji'>🎂</span>")
    ig_html = f'<div class="bday-alert-ig">{ig_str}</div>' if ig_str else ''
    sections.append(f"""
<div class="bday-alert">
  {avatar_html}
  <div class="bday-alert-text">
    <div class="bday-alert-name">¡{esc(b['name'])} cumple {b['age']} hoy! 🎉</div>
    {ig_html}
  </div>
</div>""")

# — Para postear hoy —
if recent_caps:
    caps_html = "".join(caption_card(c) for c in recent_caps)
    sections.append(f"""
<section>
  <div class="section-header">
    <span class="section-title">Para postear</span>
    <span class="section-count">{len(recent_caps)}</span>
  </div>
  {caps_html}
</section>""")
else:
    sections.append("""
<section>
  <div class="section-header">
    <span class="section-title">Para postear</span>
  </div>
  <div class="empty-state">
    <div class="empty-icon">📭</div>
    <div>Sin eventos recientes</div>
    <div class="empty-sub">El bot te avisa cuando haya algo</div>
  </div>
</section>""")

# — Partidos hoy —
if today_fix:
    rows = "".join(fixture_row(f) for f in today_fix)
    sections.append(f"""
<section>
  <div class="section-header">
    <span class="section-title">Hoy juegan</span>
    <span class="section-count">{len(today_fix)}</span>
  </div>
  {rows}
</section>""")

# — Partidos mañana —
if tomorrow_fix:
    rows = "".join(fixture_row(f) for f in tomorrow_fix)
    sections.append(f"""
<section>
  <div class="section-header">
    <span class="section-title">Mañana juegan</span>
    <span class="section-count">{len(tomorrow_fix)}</span>
  </div>
  {rows}
</section>""")

if not today_fix and not tomorrow_fix:
    sections.append("""
<section>
  <div class="section-header">
    <span class="section-title">Próximos partidos</span>
  </div>
  <div class="empty-state">
    <div class="empty-icon">🏟️</div>
    <div>Sin partidos en las próximas 48hs</div>
  </div>
</section>""")

# — Cumpleaños próximos —
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
  <div class="section-header">
    <span class="section-title">Cumpleaños esta semana</span>
  </div>
  <div class="bday-list">{items}</div>
</section>""")

body = "\n".join(sections)
updated = TODAY.strftime("%d/%m/%Y")
day_es  = ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][TODAY.weekday()]
month_es = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"][TODAY.month-1]
date_str = f"{day_es} {TODAY.day} {month_es}"

HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<title>UTT — Daily Board</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#080808;
  --surface:#111111;
  --surface2:#1a1a1a;
  --border:#232323;
  --border2:#2e2e2e;
  --text:#f0f0f0;
  --muted:#666;
  --muted2:#888;
  --gold:#e8b84b;
  --gold-dim:#e8b84b22;
}}
body{{
  font-family:'Inter',system-ui,sans-serif;
  background:var(--bg);
  color:var(--text);
  max-width:480px;
  margin:0 auto;
  padding-bottom:3rem;
  -webkit-font-smoothing:antialiased;
}}

/* ── HEADER ── */
header{{
  padding:1.25rem 1rem 1rem;
  display:flex;
  justify-content:space-between;
  align-items:center;
  border-bottom:1px solid var(--border);
  position:sticky;top:0;
  background:var(--bg);
  z-index:10;
}}
.logo-wrap{{display:flex;align-items:center;gap:.6rem}}
.logo-img{{height:28px;width:auto;filter:brightness(0) invert(1)}}
.logo-divider{{width:1px;height:18px;background:var(--border2)}}
.logo-label{{
  font-family:'Barlow Condensed',sans-serif;
  font-size:.7rem;letter-spacing:.18em;
  color:var(--muted2);font-weight:600;text-transform:uppercase
}}
.header-right{{text-align:right}}
.header-date{{font-size:.78rem;font-weight:600;color:var(--text)}}
.header-updated{{font-size:.65rem;color:var(--muted);margin-top:.1rem}}
.header-countdown{{
  display:inline-flex;align-items:center;gap:.35rem;
  font-size:.6rem;color:var(--gold);margin-top:.25rem;
  font-family:'Barlow Condensed',sans-serif;font-weight:600;letter-spacing:.06em;
}}
.countdown-dot{{width:5px;height:5px;border-radius:50%;background:var(--gold);
  animation:blink 1.4s ease-in-out infinite}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}

/* ── BIRTHDAY ALERT ── */
.bday-alert{{
  margin:1rem 1rem 0;
  background:linear-gradient(135deg,#1a1200 0%,#141000 100%);
  border:1px solid #3d2e00;
  border-radius:12px;
  display:flex;align-items:center;gap:.9rem;
  padding:1rem 1.1rem;
}}
.bday-avatar{{width:48px;height:48px;border-radius:50%;object-fit:cover;border:2px solid var(--gold)}}
.bday-emoji{{font-size:2.2rem;flex-shrink:0}}
.bday-alert-name{{font-weight:700;font-size:.95rem;color:#fff}}
.bday-alert-ig{{font-size:.78rem;color:var(--gold);margin-top:.2rem}}

/* ── SECTIONS ── */
section{{padding:1.25rem 1rem 0}}
.section-header{{
  display:flex;align-items:center;gap:.6rem;
  margin-bottom:.9rem;
}}
.section-title{{
  font-family:'Barlow Condensed',sans-serif;
  font-size:.7rem;font-weight:700;
  letter-spacing:.15em;text-transform:uppercase;
  color:var(--muted2);
}}
.section-count{{
  background:var(--gold);
  color:#000;
  font-size:.62rem;font-weight:700;
  border-radius:99px;
  padding:.1rem .45rem;
  font-family:'Barlow Condensed',sans-serif;
  letter-spacing:.05em;
}}

/* ── CAPTION CARDS ── */
.card{{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:14px;
  overflow:hidden;
  margin-bottom:.75rem;
}}
.card-top{{
  display:flex;align-items:center;
  justify-content:space-between;
  gap:.75rem;
  padding:.9rem 1rem .75rem;
  background:var(--surface2);
}}
.card-left{{display:flex;align-items:center;gap:.75rem;flex:1;min-width:0}}
.avatar{{
  width:42px;height:42px;border-radius:50%;
  object-fit:cover;flex-shrink:0;
  border:1px solid var(--border2);
}}
.avatar-placeholder{{
  width:42px;height:42px;border-radius:50%;
  background:var(--border2);
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;flex-shrink:0;
}}
.card-info{{min-width:0}}
.card-name{{
  font-weight:600;font-size:.9rem;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.card-meta{{font-size:.72rem;color:var(--muted2);margin-top:.1rem;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.card-right{{display:flex;flex-direction:column;align-items:flex-end;gap:.3rem;flex-shrink:0}}
.card-date{{font-size:.6rem;color:var(--muted);font-family:'Barlow Condensed',sans-serif;font-weight:600;letter-spacing:.05em;text-transform:uppercase}}
.tag{{
  font-family:'Barlow Condensed',sans-serif;
  font-size:.6rem;font-weight:700;letter-spacing:.1em;
  padding:.25rem .5rem;border-radius:6px;
  white-space:nowrap;flex-shrink:0;
}}
.card-caption{{
  font-size:.85rem;line-height:1.65;
  color:#c8c8c8;
  padding:.85rem 1rem;
  border-top:1px solid var(--border);
  border-bottom:1px solid var(--border);
  white-space:pre-line;
}}
.copy-btn{{
  width:100%;padding:.7rem 1rem;
  background:var(--gold);color:#000;
  border:none;
  font-family:'Barlow Condensed',sans-serif;
  font-size:.85rem;font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;
  cursor:pointer;
  display:flex;align-items:center;justify-content:center;gap:.5rem;
  transition:.15s;
}}
.copy-btn:active{{opacity:.85;transform:scale(.99)}}
.copy-btn.done{{background:#22c55e;color:#fff}}

/* ── FIXTURES ── */
.fixture-card{{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  padding:.9rem 1rem;
  margin-bottom:.6rem;
}}
.fixture-teams{{
  font-weight:700;font-size:.93rem;
  margin-bottom:.4rem;
}}
.vs{{color:var(--muted);font-weight:400;margin:0 .3rem;font-size:.85rem}}
.fixture-bottom{{
  display:flex;align-items:center;gap:.5rem;
  margin-bottom:.55rem;
}}
.fixture-league{{font-size:.72rem;color:var(--muted);}}
.badge-live{{
  font-size:.65rem;font-weight:700;color:#ef4444;
  font-family:'Barlow Condensed',sans-serif;letter-spacing:.08em;
  animation:blink 1.2s infinite;
}}
@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
.badge-done{{font-size:.68rem;color:var(--muted);font-family:'Barlow Condensed',sans-serif}}
.badge-time{{
  font-size:.72rem;font-weight:600;color:var(--gold);
  font-family:'Barlow Condensed',sans-serif;
}}
.fixture-players{{
  display:flex;flex-wrap:wrap;gap:.35rem;
}}
.fp{{
  font-size:.78rem;color:#bbb;
  display:flex;align-items:center;gap:.25rem;
}}
.fp-ig{{color:var(--gold);font-size:.72rem}}

/* ── BIRTHDAYS LIST ── */
.bday-list{{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  overflow:hidden;
}}
.bday-row{{
  display:flex;align-items:center;justify-content:space-between;
  padding:.75rem 1rem;
  border-bottom:1px solid var(--border);
}}
.bday-row:last-child{{border:none}}
.bday-row-left{{display:flex;align-items:center;gap:.65rem}}
.bday-cake{{font-size:1.1rem}}
.bday-row-name{{font-size:.85rem;font-weight:600}}
.bday-row-meta{{font-size:.7rem;color:var(--muted);margin-top:.1rem}}
.bday-days{{
  font-family:'Barlow Condensed',sans-serif;
  font-size:.78rem;font-weight:700;
  color:var(--gold);
  background:var(--gold-dim);
  border:1px solid #e8b84b33;
  padding:.2rem .55rem;border-radius:99px;
}}

/* ── EMPTY STATE ── */
.empty-state{{
  text-align:center;
  padding:2rem 1rem;
  color:var(--muted);
  font-size:.85rem;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
}}
.empty-icon{{font-size:2rem;margin-bottom:.5rem}}
.empty-sub{{font-size:.75rem;margin-top:.3rem;color:var(--muted)}}
</style>
</head>
<body>

<header>
  <div class="logo-wrap">
    <img class="logo-img"
         src="https://universaltt.com/wp-content/uploads/2023/04/cropped-Recurso-3-1.png"
         onerror="this.style.display='none'"
         alt="UTT">
    <div class="logo-divider"></div>
    <span class="logo-label">Daily Board</span>
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
    setTimeout(()=>{{ btn.innerHTML=orig; btn.classList.remove("done"); }}, 2500);
  }});
}}

// ── Countdown al próximo refresh (cron cada 4h UTC: 0,4,8,12,16,20) ──────
(function(){{
  function nextRun(){{
    const now = new Date();
    const ms = now.getTime();
    const dayStart = Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate());
    const elapsed = ms - dayStart;
    const interval = 4 * 3600 * 1000;
    const next = dayStart + Math.ceil(elapsed / interval) * interval;
    return next - ms;
  }}
  function pad(n){{ return String(n).padStart(2,'0'); }}
  function tick(){{
    let s = Math.max(0, Math.round(nextRun() / 1000));
    const h = Math.floor(s / 3600); s -= h * 3600;
    const m = Math.floor(s / 60);   s -= m * 60;
    const el = document.getElementById('countdown');
    if(el) el.textContent = pad(h)+':'+pad(m)+':'+pad(s);
  }}
  tick();
  setInterval(tick, 1000);
}})();
</script>
</body>
</html>"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"Dashboard generado: {len(recent_caps)} para postear, {len(today_fix)} partidos hoy, {len(bdays_today)} cumpleaños hoy")
