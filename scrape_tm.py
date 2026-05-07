"""
Scraper de Transfermarkt para completar jugadores.csv de UTT.
- Extrae todos los jugadores de las 7 páginas de la agencia
- Para cada jugador nuevo o sin fecha_nacimiento, visita su perfil y saca el DOB
- Actualiza jugadores.csv sin borrar datos existentes (instagram, aliases, notable)
"""
import csv
import re
import time
import unicodedata
from pathlib import Path
import requests
from bs4 import BeautifulSoup

AGENCY_URL = "https://www.transfermarkt.com/universal-twenty-two/beraterfirma/berater/2722"
BASE_URL   = "https://www.transfermarkt.com"
OUT_CSV    = Path(__file__).parent / "jugadores.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

FIELDNAMES = ["nombre","aliases","club","posicion","nacionalidad","instagram","notable","fecha_nacimiento"]


def slug(name: str) -> str:
    """Normaliza nombre para comparar (sin tildes, lower, sin espacios extra)."""
    n = unicodedata.normalize("NFD", name)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", n).strip().lower()


def get_soup(url: str, delay=2) -> BeautifulSoup | None:
    time.sleep(delay)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}: {url}")
            return None
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  Error: {e}")
        return None


def scrape_agency_page(page: int) -> list[dict]:
    """Devuelve lista de {nombre, posicion, club, tm_url} de una página."""
    url = AGENCY_URL if page == 1 else f"{AGENCY_URL}/ajax/yw1/page/{page}"
    soup = get_soup(url)
    if not soup:
        return []

    players = []
    # Solo la primera tabla.items = jugadores (la segunda = managers/coaches)
    first_table = soup.select_one("table.items")
    if not first_table:
        return []
    for row in first_table.select("tbody tr.odd, tbody tr.even"):
        # Nombre y link del jugador
        name_tag = row.select_one("td.hauptlink a")
        if not name_tag:
            continue
        name = name_tag.get_text(strip=True)
        href = name_tag.get("href", "")
        tm_url = BASE_URL + href if href.startswith("/") else href

        # Posición (segunda línea dentro de la celda de nombre)
        pos_tag = row.select_one("td:nth-child(2) tr:nth-child(2) td")
        pos = pos_tag.get_text(strip=True) if pos_tag else ""

        # Club actual (logo con alt text)
        club_tag = row.select_one("td.zentriert img.tiny_wappen")
        club = club_tag.get("title", "").strip() if club_tag else ""
        if not club:
            club_tag2 = row.select_one("td.no-border-links a")
            club = club_tag2.get_text(strip=True) if club_tag2 else ""

        players.append({"nombre": name, "posicion": pos, "club": club, "tm_url": tm_url})

    return players


def scrape_player_dob(tm_url: str) -> dict:
    """Devuelve {fecha_nacimiento, nacionalidad, posicion} del perfil del jugador."""
    soup = get_soup(tm_url, delay=2)
    if not soup:
        return {}

    result = {}

    # La info-table usa spans alternados: regular (label) → bold (value)
    spans = soup.select("div.info-table span.info-table__content")
    for i, span in enumerate(spans):
        if "info-table__content--regular" in span.get("class", []):
            label = span.get_text(strip=True).lower()
            # El siguiente span bold es el valor
            if i + 1 < len(spans):
                val_span = spans[i + 1]
                val = val_span.get_text(strip=True)

                if "date of birth" in label or "fecha" in label:
                    # Formato: "22/05/1988 (37)" → YYYY-MM-DD
                    m = re.search(r"(\d{2})/(\d{2})/(\d{4})", val)
                    if m:
                        result["fecha_nacimiento"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

                elif "citizenship" in label or "ciudadanía" in label:
                    # Puede tener varias banderas, tomamos la primera
                    img = val_span.select_one("img[title]")
                    if img:
                        result["nacionalidad"] = img.get("title", "").strip()
                    elif val:
                        result["nacionalidad"] = val.split("\n")[0].strip()

                elif "position" in label or "posición" in label:
                    if not result.get("posicion"):
                        result["posicion"] = val

    return result


def main():
    # Cargar CSV existente
    existing = {}
    if OUT_CSV.exists():
        for p in csv.DictReader(OUT_CSV.open(encoding="utf-8")):
            existing[slug(p["nombre"])] = p

    print(f"Jugadores existentes en CSV: {len(existing)}")

    # Scrapear todas las páginas de la agencia
    all_tm = []
    for page in range(1, 8):
        print(f"Scrapeando página {page}/7...")
        players = scrape_agency_page(page)
        print(f"  {len(players)} jugadores encontrados")
        all_tm.extend(players)
        time.sleep(1)

    print(f"\nTotal en TM: {len(all_tm)}")

    # Procesar cada jugador de TM
    added, updated, skipped = 0, 0, 0
    for p in all_tm:
        key = slug(p["nombre"])
        existing_entry = existing.get(key)

        needs_dob = not existing_entry or not existing_entry.get("fecha_nacimiento", "").strip()

        if existing_entry and not needs_dob:
            skipped += 1
            continue

        # Buscar DOB en perfil TM
        print(f"  Buscando DOB: {p['nombre']}...")
        extra = scrape_player_dob(p["tm_url"])

        if existing_entry:
            # Actualizar solo campos faltantes
            if extra.get("fecha_nacimiento"):
                existing_entry["fecha_nacimiento"] = extra["fecha_nacimiento"]
            if extra.get("nacionalidad") and not existing_entry.get("nacionalidad", "").strip():
                existing_entry["nacionalidad"] = extra["nacionalidad"]
            if p.get("club") and not existing_entry.get("club", "").strip():
                existing_entry["club"] = p["club"]
            existing[key] = existing_entry
            updated += 1
        else:
            # Nuevo jugador
            new_entry = {
                "nombre":           p["nombre"],
                "aliases":          "",
                "club":             p.get("club", ""),
                "posicion":         p.get("posicion", ""),
                "nacionalidad":     extra.get("nacionalidad", ""),
                "instagram":        "",
                "notable":          "no",
                "fecha_nacimiento": extra.get("fecha_nacimiento", ""),
            }
            existing[key] = new_entry
            added += 1

    print(f"\nResultados: {added} nuevos, {updated} actualizados, {skipped} sin cambios")

    # Guardar CSV actualizado
    rows = list(existing.values())
    rows.sort(key=lambda x: x["nombre"].lower())
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV guardado: {len(rows)} jugadores → {OUT_CSV}")

    # Stats finales
    con_dob = sum(1 for r in rows if r.get("fecha_nacimiento", "").strip())
    con_ig  = sum(1 for r in rows if r.get("instagram", "").strip())
    print(f"Con fecha nacimiento: {con_dob}/{len(rows)}")
    print(f"Con Instagram: {con_ig}/{len(rows)}")


if __name__ == "__main__":
    main()
