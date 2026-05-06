"""Genera docs/index.html — dashboard completo de UTT."""
import csv, json, os, re
from datetime import date, timedelta
from pathlib import Path

BASE      = Path(__file__).parent
CSV_PATH  = BASE / "jugadores.csv"
INTEL_DIR = BASE / "intel"
CAPS_LOG  = BASE / "captions_log.json"
OUT       = BASE / "docs" / "index.html"

# ── Datos ──────────────────────────────────────────────────────────────────
players = []
with open(CSV_PATH, newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        players.append({k: v for k, v in row.items()})

def slug(name):
    s = name.lower()
    for a,b in [("á","a"),("é","e"),("í","i"),("ó","o"),("ú","u"),("ñ","n"),
                ("ã","a"),("â","a"),("ê","e"),("ô","o"),("ç","c"),("ü","u")]:
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")

intel = {}
if INTEL_DIR.exists():
    for f in INTEL_DIR.glob("*.json"):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            intel[slug(data.get("name", f.stem))] = data
        except Exception:
            pass

captions = []
if CAPS_LOG.exists():
    try:
        captions = json.loads(CAPS_LOG.read_text(encoding="utf-8"))
    except Exception:
        pass

today     = date.today()
today_str = today.strftime("%d/%m/%Y")

# ── Cumpleaños próximos (14 días) ─────────────────────────────────────────
upcoming_bdays = []
for p in players:
    bday = p.get("fecha_nacimiento", "")
    if not bday:
        continue
    try:
        bd = date.fromisoformat(bday)
        this_year = bd.replace(year=today.year)
        if this_year < today:
            this_year = bd.replace(year=today.year + 1)
        delta = (this_year - today).days
        if 0 <= delta <= 14:
            upcoming_bdays.append({
                "name": p["nombre"], "instagram": p.get("instagram",""),
                "days": delta, "age": today.year - bd.year + (1 if delta > 0 else 0),
                "date_str": this_year.strftime("%d %b"),
                "slug": slug(p["nombre"]),
            })
    except ValueError:
        pass
upcoming_bdays.sort(key=lambda x: x["days"])

# ── Stats globales ────────────────────────────────────────────────────────
countries   = len({p.get("nacionalidad","") for p in players if p.get("nacionalidad")})
caps_week   = sum(1 for c in captions
                  if (today - date.fromisoformat(c["date"])).days <= 7
                  if c.get("date"))
event_counts = {}
for c in captions:
    et = c.get("event_type","")
    event_counts[et] = event_counts.get(et, 0) + 1

# ── JS data ───────────────────────────────────────────────────────────────
PLAYERS_JS  = json.dumps(players,   ensure_ascii=False)
INTEL_JS    = json.dumps(intel,     ensure_ascii=False)
CAPTIONS_JS = json.dumps(captions,  ensure_ascii=False)
BDAYS_JS    = json.dumps(upcoming_bdays, ensure_ascii=False)
STATS_JS    = json.dumps({
    "total": len(players), "countries": countries,
    "caps_week": caps_week, "event_counts": event_counts,
    "updated": today_str,
}, ensure_ascii=False)

# ── HTML ──────────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>UTT Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0a0a0a;--surface:#111;--border:#1e1e1e;--text:#ddd;--muted:#555;
  --accent:#3b82f6;--accent2:#10b981;--warn:#f59e0b;--danger:#ef4444;
}}
body{{font-family:system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
a{{color:inherit;text-decoration:none}}

/* NAV */
nav{{background:#0d0d0d;border-bottom:1px solid var(--border);padding:.7rem 1.2rem;
     display:flex;align-items:center;gap:1.5rem;position:sticky;top:0;z-index:100}}
.logo{{font-weight:700;font-size:.95rem;letter-spacing:.1em;color:#fff;margin-right:auto}}
.nav-link{{color:var(--muted);font-size:.85rem;cursor:pointer;padding:.3rem .5rem;
           border-radius:6px;transition:.15s}}
.nav-link:hover,.nav-link.active{{color:#fff;background:var(--surface)}}

/* PAGES */
.page{{display:none;padding:1.4rem 1.2rem;max-width:1200px;margin:0 auto}}
.page.active{{display:block}}

/* HOME STATS */
.stats-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:.8rem;margin-bottom:1.5rem}}
.stat-card{{background:var(--surface);border:1px solid var(--border);border-radius:10px;
            padding:1rem;text-align:center}}
.stat-card .num{{font-size:2rem;font-weight:700;color:#fff}}
.stat-card .lbl{{font-size:.75rem;color:var(--muted);margin-top:.2rem}}

/* SECTIONS */
h2{{font-size:1rem;color:var(--muted);letter-spacing:.08em;margin-bottom:.9rem;
    text-transform:uppercase;font-weight:600}}
.section{{margin-bottom:2rem}}

/* ACTIVITY FEED */
.feed-item{{background:var(--surface);border:1px solid var(--border);border-radius:8px;
            padding:.85rem 1rem;margin-bottom:.5rem;display:flex;gap:.8rem;align-items:flex-start}}
.feed-emoji{{font-size:1.2rem;flex-shrink:0;margin-top:.05rem}}
.feed-body{{flex:1;min-width:0}}
.feed-title{{font-size:.88rem;font-weight:600;color:#fff}}
.feed-sub{{font-size:.77rem;color:var(--muted);margin-top:.2rem}}
.feed-caption{{font-size:.82rem;color:#aaa;margin-top:.4rem;
               border-left:2px solid var(--border);padding-left:.6rem;
               white-space:pre-line;line-height:1.4}}
.feed-date{{font-size:.72rem;color:var(--muted);flex-shrink:0;margin-top:.1rem}}

/* BIRTHDAYS */
.bday-list{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:.6rem}}
.bday-card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;
            padding:.75rem;display:flex;align-items:center;gap:.7rem;cursor:pointer}}
.bday-card:hover{{border-color:#444}}
.bday-icon{{font-size:1.4rem}}
.bday-name{{font-size:.85rem;font-weight:600}}
.bday-info{{font-size:.75rem;color:var(--muted);margin-top:.1rem}}
.badge{{display:inline-block;background:#1e3a5f;color:#7eb8f7;border-radius:4px;
        padding:1px 6px;font-size:.72rem;margin-left:.4rem}}
.badge.today{{background:#3a1f00;color:var(--warn)}}

/* ROSTER TABLE */
.search-bar{{margin-bottom:.9rem}}
input[type=search]{{background:var(--surface);border:1px solid var(--border);color:var(--text);
                    padding:.5rem 1rem;border-radius:8px;width:100%;max-width:380px;
                    font-size:.88rem;outline:none}}
input[type=search]:focus{{border-color:#444}}
table{{width:100%;border-collapse:collapse;font-size:.83rem}}
th{{background:#0d0d0d;color:var(--muted);padding:.55rem .75rem;text-align:left;
    position:sticky;top:46px;border-bottom:1px solid var(--border);
    cursor:pointer;user-select:none;white-space:nowrap}}
th:hover{{color:#ccc}}
td{{padding:.5rem .75rem;border-bottom:1px solid #141414;vertical-align:middle}}
tr:hover td{{background:#0f0f0f}}
.bday-row td{{background:#1a1500!important}}
.ig{{color:var(--accent);font-size:.78rem}}
.notable{{color:var(--muted);font-size:.73rem;display:block}}

/* PLAYER PROFILE */
.profile-back{{color:var(--accent);font-size:.85rem;cursor:pointer;margin-bottom:1rem;display:inline-flex;gap:.3rem;align-items:center}}
.profile-header{{display:flex;gap:1.2rem;align-items:flex-start;margin-bottom:1.5rem;flex-wrap:wrap}}
.profile-name{{font-size:1.6rem;font-weight:700;color:#fff}}
.profile-meta{{font-size:.85rem;color:var(--muted);margin-top:.3rem}}
.profile-status{{display:inline-block;padding:.2rem .6rem;border-radius:4px;font-size:.75rem;
                 font-weight:600;margin-top:.4rem}}
.status-activo{{background:#052e16;color:#4ade80}}
.status-lesionado{{background:#450a0a;color:#f87171}}
.status-suspendido{{background:#3a1f00;color:#fbbf24}}
.status-transferencia{{background:#1e3a5f;color:#7eb8f7}}
.intel-box{{background:var(--surface);border:1px solid var(--border);border-radius:8px;
            padding:1rem;margin-bottom:1rem;font-size:.87rem;line-height:1.6;color:#ccc}}
.timeline{{list-style:none}}
.tl-item{{padding:.6rem 0;border-bottom:1px solid var(--border);display:flex;gap:.75rem}}
.tl-dot{{width:8px;height:8px;border-radius:50%;flex-shrink:0;margin-top:.35rem}}
.dot-news{{background:var(--accent)}}
.dot-instagram{{background:var(--accent2)}}
.dot-match_event{{background:var(--warn)}}
.dot-other{{background:var(--muted)}}
.tl-content{{font-size:.82rem;color:#bbb;line-height:1.4}}
.tl-date{{font-size:.72rem;color:var(--muted);margin-left:auto;flex-shrink:0}}

/* CAPTIONS PAGE */
.cap-card{{background:var(--surface);border:1px solid var(--border);border-radius:8px;
           padding:1rem;margin-bottom:.7rem}}
.cap-header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem}}
.cap-player{{font-weight:600;font-size:.9rem}}
.cap-event{{font-size:.75rem;color:var(--muted)}}
.cap-text{{font-size:.85rem;color:#bbb;line-height:1.5;white-space:pre-line;
           border-left:2px solid var(--border);padding-left:.7rem}}
.copy-btn{{background:none;border:1px solid var(--border);color:var(--muted);
           padding:.2rem .5rem;border-radius:4px;font-size:.72rem;cursor:pointer}}
.copy-btn:hover{{color:#fff;border-color:#444}}

/* EMPTY */
.empty{{text-align:center;padding:3rem;color:var(--muted)}}
</style>
</head>
<body>

<nav>
  <span class="logo">UTT</span>
  <span class="nav-link active" onclick="goto('home')">Home</span>
  <span class="nav-link" onclick="goto('roster')">Roster</span>
  <span class="nav-link" onclick="goto('captions')">Captions</span>
</nav>

<!-- HOME -->
<div class="page active" id="page-home">
  <div class="stats-grid" id="stats-grid"></div>

  <div class="section">
    <h2>🎂 Cumpleaños próximos</h2>
    <div class="bday-list" id="bday-list"></div>
  </div>

  <div class="section">
    <h2>📋 Actividad reciente</h2>
    <div id="activity-feed"></div>
  </div>
</div>

<!-- ROSTER -->
<div class="page" id="page-roster">
  <div class="search-bar">
    <input id="q-roster" type="search" placeholder="Buscar jugador, club, posición...">
  </div>
  <table>
    <thead><tr>
      <th onclick="sortRoster('nombre')">Jugador ↕</th>
      <th onclick="sortRoster('posicion')">Posición ↕</th>
      <th onclick="sortRoster('club')">Club ↕</th>
      <th onclick="sortRoster('nacionalidad')">Nac. ↕</th>
      <th onclick="sortRoster('fecha_nacimiento')">Cumpleaños ↕</th>
      <th>Instagram</th>
    </tr></thead>
    <tbody id="roster-body"></tbody>
  </table>
</div>

<!-- PLAYER PROFILE -->
<div class="page" id="page-player">
  <span class="profile-back" onclick="goto('roster')">← Volver al roster</span>
  <div id="profile-content"></div>
</div>

<!-- CAPTIONS -->
<div class="page" id="page-captions">
  <div class="search-bar">
    <input id="q-caps" type="search" placeholder="Buscar jugador, evento...">
  </div>
  <div id="caps-list"></div>
</div>

<script>
// ── Data ──────────────────────────────────────────────────────────────────
const PLAYERS  = {PLAYERS_JS};
const INTEL    = {INTEL_JS};
const CAPTIONS = {CAPTIONS_JS};
const BDAYS    = {BDAYS_JS};
const STATS    = {STATS_JS};

const MONTHS = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"];
const EMOJIS = {{Goal:"⚽",Assist:"🎯",CleanSheet:"🧤",RedCard:"🟥",
                  Birthday:"🎂",News:"📰",InstagramPost:"📸",Transfer:"✈️"}};

function fmtBday(iso){{
  if(!iso) return "";
  const [,m,d]=iso.split("-");
  return `${{parseInt(d)}} ${{MONTHS[parseInt(m)]}}`;
}}
function isToday(iso){{
  if(!iso) return false;
  const [,m,d]=iso.split("-"),n=new Date();
  return parseInt(m)===n.getMonth()+1&&parseInt(d)===n.getDate();
}}
function pslug(name){{
  return name.toLowerCase()
    .replace(/[áàäâã]/g,"a").replace(/[éèëê]/g,"e").replace(/[íìïî]/g,"i")
    .replace(/[óòöôõ]/g,"o").replace(/[úùüû]/g,"u").replace(/ñ/g,"n")
    .replace(/ç/g,"c").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");
}}
function copyText(text, btn){{
  navigator.clipboard.writeText(text).then(()=>{{
    btn.textContent="✓ Copiado"; setTimeout(()=>btn.textContent="Copiar",2000);
  }});
}}

// ── Navigation ────────────────────────────────────────────────────────────
function goto(page, extra){{
  document.querySelectorAll(".page").forEach(p=>p.classList.remove("active"));
  document.querySelectorAll(".nav-link").forEach(l=>l.classList.remove("active"));
  const pageEl = document.getElementById("page-"+page);
  if(pageEl) pageEl.classList.add("active");
  const navEl = document.querySelector(`.nav-link[onclick="goto('${{page}}')"]`);
  if(navEl) navEl.classList.add("active");
  if(page==="player"&&extra) renderPlayer(extra);
  window.scrollTo(0,0);
}}

// ── HOME ──────────────────────────────────────────────────────────────────
function renderHome(){{
  // Stats
  const ec = STATS.event_counts||{{}};
  const statsData = [
    {{num: STATS.total,     lbl: "Jugadores"}},
    {{num: STATS.countries, lbl: "Países"}},
    {{num: STATS.caps_week, lbl: "Captions esta semana"}},
    {{num: ec.Goal||0,     lbl: "⚽ Goles detectados"}},
    {{num: ec.Assist||0,   lbl: "🎯 Asistencias"}},
    {{num: ec.CleanSheet||0,lbl:"🧤 Arcos en cero"}},
    {{num: ec.News||0,     lbl: "📰 Noticias"}},
  ];
  document.getElementById("stats-grid").innerHTML =
    statsData.map(s=>`<div class="stat-card"><div class="num">${{s.num}}</div><div class="lbl">${{s.lbl}}</div></div>`).join("");

  // Cumpleaños
  const bl = document.getElementById("bday-list");
  if(!BDAYS.length){{
    bl.innerHTML=`<p class="empty">Sin cumpleaños en los próximos 14 días.</p>`;
  }} else {{
    bl.innerHTML = BDAYS.map(b=>{{
      const label = b.days===0 ? `<span class="badge today">🎂 HOY</span>`
                  : b.days===1 ? `<span class="badge">Mañana</span>`
                  : `<span class="badge">En ${{b.days}} días</span>`;
      return `<div class="bday-card" onclick="goto('player','${{b.slug}}')">
        <span class="bday-icon">🎂</span>
        <div>
          <div class="bday-name">${{b.name}}${{label}}</div>
          <div class="bday-info">${{b.date_str}} · ${{b.age}} años</div>
        </div>
      </div>`;
    }}).join("");
  }}

  // Activity feed
  const feed = document.getElementById("activity-feed");
  if(!CAPTIONS.length){{
    feed.innerHTML=`<p class="empty">Sin actividad todavía. El bot la irá llenando.</p>`;
  }} else {{
    feed.innerHTML = CAPTIONS.slice(0,20).map(c=>{{
      const emoji = EMOJIS[c.event_type]||"📌";
      const fixture = c.fixture&&c.fixture!=="vs"?`· ${{c.fixture}}`:"";
      const league  = c.league?`· ${{c.league}}`:"";
      return `<div class="feed-item">
        <span class="feed-emoji">${{emoji}}</span>
        <div class="feed-body">
          <div class="feed-title">${{c.player}} <span style="color:var(--muted);font-weight:400">${{c.event_type}}</span></div>
          <div class="feed-sub">${{c.club}} ${{fixture}} ${{league}}</div>
          <div class="feed-caption">${{c.caption}}</div>
        </div>
        <div class="feed-date">${{c.date}}</div>
      </div>`;
    }}).join("");
  }}
}}

// ── ROSTER ────────────────────────────────────────────────────────────────
let rosterSorted=[...PLAYERS], rosterCol="", rosterAsc=true;

function renderRoster(){{
  const q = (document.getElementById("q-roster")||{{}}).value?.toLowerCase()||"";
  const data = rosterSorted.filter(p=>!q||Object.values(p).some(v=>v.toLowerCase().includes(q)));
  document.getElementById("roster-body").innerHTML = data.length===0
    ? `<tr><td colspan="6" class="empty">Sin resultados</td></tr>`
    : data.map(p=>{{
        const sl = pslug(p.nombre);
        return `<tr class="${{isToday(p.fecha_nacimiento)?"bday-row":""}}"
                    onclick="goto('player','${{sl}}')" style="cursor:pointer">
          <td><strong>${{p.nombre}}</strong>
            ${{p.notable?`<span class="notable">${{p.notable}}</span>`:""}}
          </td>
          <td>${{p.posicion}}</td>
          <td>${{p.club}}</td>
          <td>${{p.nacionalidad}}</td>
          <td>${{isToday(p.fecha_nacimiento)?"🎂 ":""}}${{fmtBday(p.fecha_nacimiento)}}</td>
          <td class="ig">${{p.instagram?"@"+p.instagram:""}}</td>
        </tr>`;
      }}).join("");
}}

function sortRoster(col){{
  if(rosterCol===col)rosterAsc=!rosterAsc;else{{rosterCol=col;rosterAsc=true;}}
  rosterSorted.sort((a,b)=>{{
    const av=a[col]||"",bv=b[col]||"";
    return rosterAsc?av.localeCompare(bv,"es"):bv.localeCompare(av,"es");
  }});
  renderRoster();
}}

document.getElementById("q-roster")?.addEventListener("input",renderRoster);

// ── PLAYER PROFILE ────────────────────────────────────────────────────────
function renderPlayer(sl){{
  const player = PLAYERS.find(p=>pslug(p.nombre)===sl);
  if(!player){{ document.getElementById("profile-content").innerHTML="<p>Jugador no encontrado.</p>"; return; }}

  const iv = INTEL[sl]||{{}};
  const context = iv.context||"";
  const status  = iv.status||"activo";
  const timeline= iv.timeline||[];

  const dotClass = t=>({{"news":"dot-news","instagram":"dot-instagram","match_event":"dot-match_event"}}[t]||"dot-other");
  const typeLabel= t=>({{"news":"Noticia","instagram":"Instagram","match_event":"Partido"}}[t]||t);

  // Captions de este jugador
  const playerCaps = CAPTIONS.filter(c=>pslug(c.player)===sl).slice(0,5);

  document.getElementById("profile-content").innerHTML = `
    <div class="profile-header">
      <div>
        <div class="profile-name">${{player.nombre}}</div>
        <div class="profile-meta">
          ${{player.posicion}} · ${{player.club}} · ${{player.nacionalidad}}
          ${{player.fecha_nacimiento?`· 🎂 ${{fmtBday(player.fecha_nacimiento)}}`:""}}
        </div>
        ${{player.instagram?`<div style="color:var(--accent);font-size:.85rem;margin-top:.3rem">@${{player.instagram}}</div>`:""}}
        <span class="profile-status status-${{status}}">${{status}}</span>
      </div>
    </div>

    ${{context?`
    <div class="section">
      <h2>🧠 Contexto actual</h2>
      <div class="intel-box">${{context}}</div>
    </div>`:"" }}

    ${{playerCaps.length?`
    <div class="section">
      <h2>📝 Últimos captions generados</h2>
      ${{playerCaps.map(c=>`
        <div class="cap-card">
          <div class="cap-header">
            <span class="cap-event">${{EMOJIS[c.event_type]||""}} ${{c.event_type}} · ${{c.date}}</span>
            <button class="copy-btn" onclick="copyText(\`${{c.caption}}\`,this)">Copiar</button>
          </div>
          <div class="cap-text">${{c.caption}}</div>
        </div>`).join("")}}
    </div>`:"" }}

    ${{timeline.length?`
    <div class="section">
      <h2>📅 Historial</h2>
      <ul class="timeline">
        ${{timeline.map(t=>`
          <li class="tl-item">
            <div class="tl-dot ${{dotClass(t.type)}}"></div>
            <div class="tl-content">
              <strong>${{typeLabel(t.type)}}</strong>
              ${{t.source?`<span style="color:var(--muted)"> · ${{t.source}}</span>`:""}}
              <br>${{t.content}}
            </div>
            <div class="tl-date">${{t.date}}</div>
          </li>`).join("")}}
      </ul>
    </div>`:"" }}

    ${{!context&&!timeline.length?`<p class="empty">Sin datos de inteligencia todavía.<br>Se irán acumulando automáticamente.</p>`:""}}
  `;
}}

// ── CAPTIONS ──────────────────────────────────────────────────────────────
function renderCaptions(){{
  const q=(document.getElementById("q-caps")||{{}}).value?.toLowerCase()||"";
  const data=CAPTIONS.filter(c=>!q||(c.player+c.event_type+c.caption+c.league).toLowerCase().includes(q));
  document.getElementById("caps-list").innerHTML = data.length===0
    ? `<p class="empty">Sin captions todavía.</p>`
    : data.map(c=>{{
        const emoji=EMOJIS[c.event_type]||"📌";
        const fix=c.fixture&&c.fixture!=="vs"?` · ${{c.fixture}}`:"";
        return `<div class="cap-card">
          <div class="cap-header">
            <div>
              <span class="cap-player">${{emoji}} ${{c.player}}</span>
              <span class="cap-event"> — ${{c.event_type}}${{fix}}${{c.league?" · "+c.league:""}}</span>
            </div>
            <div style="display:flex;gap:.5rem;align-items:center">
              <span style="font-size:.72rem;color:var(--muted)">${{c.date}}</span>
              <button class="copy-btn" onclick="copyText(\`${{c.caption}}\`,this)">Copiar</button>
            </div>
          </div>
          <div class="cap-text">${{c.caption}}</div>
        </div>`;
      }}).join("");
}}

document.getElementById("q-caps")?.addEventListener("input",renderCaptions);

// ── Init ──────────────────────────────────────────────────────────────────
renderHome();
renderRoster();
renderCaptions();
</script>
</body>
</html>"""

OUT.parent.mkdir(exist_ok=True)
OUT.write_text(HTML, encoding="utf-8")
print(f"Dashboard generado: {OUT} ({len(players)} jugadores, {len(captions)} captions)")
