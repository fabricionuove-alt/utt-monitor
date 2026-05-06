"""
Monitorea noticias de prensa sobre jugadores UTT via Google News RSS.
Guarda URLs ya vistas en seen_news.json para evitar duplicados.
"""
import json
import hashlib
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from pathlib import Path
from players import load_players
from player_intel import update_intel

SEEN_FILE = Path(__file__).parent / "seen_news.json"

# Jugadores con suficiente presencia mediática para monitorear
# (nombres exactos como aparecen en prensa)
PRIORITY_SEARCHES = [
    "Alexander Isak",
    "Mile Svilar",
    "Emiliano Buendía",
    "Emiliano Martínez",
    "Rodrigo Garro",
    "Luka Modrić",
    "Lucas Martínez Quarta",
    "Emiliano Buendia",
    "Nemanja Matić",
    "Gelson Martins",
    "Luciano Gondou",
    "Lucas Boyé",
    "Nahuel Tenaglia",
    "Pedro de la Vega",
    "Kiril Despodov",
    "Universal Twenty Two",
    "UTT fútbol agencia",
]

# Dominios de medios relevantes (filtramos ruido)
TRUSTED_DOMAINS = {
    "espn", "marca", "ole", "infobae", "clarin", "tycsports", "goal",
    "bbc", "guardian", "skysports", "theathletic", "transfermarkt",
    "sofascore", "fotmob", "90min", "mundodeportivo", "sport",
    "tuttosport", "gazzetta", "lequipe", "kicker", "record",
    "globoesporte", "uol", "diarioas", "relevo",
}


def _rss_url(query: str) -> str:
    import urllib.parse
    q = urllib.parse.quote(f'"{query}"')
    return f"https://news.google.com/rss/search?q={q}&hl=es&gl=AR&ceid=AR:es&num=5"


def _parse_rss(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    items = []
    for item in root.findall(".//item"):
        title   = (item.findtext("title") or "").strip()
        link    = (item.findtext("link") or "").strip()
        pub     = (item.findtext("pubDate") or "").strip()
        source  = (item.findtext("source") or "").strip()
        items.append({"title": title, "url": link, "pub": pub, "source": source})
    return items


def _is_recent(pub_str: str, hours: int = 24) -> bool:
    """Verifica que la noticia no tenga más de `hours` horas."""
    if not pub_str:
        return True  # si no hay fecha, la incluimos
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT"):
        try:
            dt = datetime.strptime(pub_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return datetime.now(timezone.utc) - dt < timedelta(hours=hours)
        except ValueError:
            continue
    return True


def _is_trusted(url: str) -> bool:
    url_lower = url.lower()
    return any(domain in url_lower for domain in TRUSTED_DOMAINS)


def _url_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()


def _load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    return set()


def _save_seen(seen: set) -> None:
    # Mantener solo los últimos 2000 para que el archivo no crezca infinito
    data = list(seen)[-2000:]
    SEEN_FILE.write_text(json.dumps(data), encoding="utf-8")


def get_news_events() -> list[dict]:
    """
    Busca noticias recientes sobre jugadores UTT.
    Retorna lista de eventos con tipo 'News'.
    """
    seen = _load_seen()
    players_by_name = {p["name"]: p for p in load_players()}
    found = []
    new_seen = set()

    for query in PRIORITY_SEARCHES:
        try:
            resp = requests.get(_rss_url(query), timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                continue
            articles = _parse_rss(resp.text)
        except Exception as e:
            print(f"  ⚠️  Error buscando '{query}': {e}")
            continue

        for art in articles:
            uid = _url_id(art["url"])
            if uid in seen or uid in new_seen:
                continue
            if not _is_recent(art["pub"]):
                continue

            new_seen.add(uid)

            # Buscar qué jugador UTT se menciona
            player = None
            for name, p in players_by_name.items():
                if name.lower() in art["title"].lower():
                    player = p
                    break

            # Si es mención de la agencia sin jugador específico, usar placeholder
            if not player and "universal twenty two" in query.lower():
                player = {"name": "Universal Twenty Two", "position": "Agencia",
                          "nationality": "", "club": "", "instagram": "", "notable": "",
                          "aliases": []}

            if not player:
                continue

            print(f"    📰 Noticia: {art['title'][:60]}...")

            # Actualizar intel del jugador con la noticia
            if player.get("position") != "Agencia":
                update_intel(
                    player=player,
                    info_type="news",
                    content=art["title"],
                    source=art["source"],
                )

            found.append({
                "player": player,
                "event_type": "News",
                "detail": "News",
                "minute": None,
                "team": player.get("club", ""),
                "fixture": {},
                "news_title": art["title"],
                "news_url": art["url"],
                "news_source": art["source"],
            })

    seen.update(new_seen)
    _save_seen(seen)
    return found
