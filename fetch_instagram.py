"""
Monitorea los posts públicos de Instagram de jugadores UTT con instaloader.
Detecta posts nuevos y actualiza el intel de cada jugador.
"""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from players import load_players
from player_intel import update_intel

SEEN_FILE = Path(__file__).parent / "seen_instagram.json"


def _load_seen() -> set:
    if SEEN_FILE.exists():
        return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")))
    return set()


def _save_seen(seen: set) -> None:
    data = list(seen)[-2000:]
    SEEN_FILE.write_text(json.dumps(data), encoding="utf-8")


def get_instagram_events() -> list[dict]:
    """
    Descarga posts recientes de los perfiles públicos de Instagram de jugadores UTT.
    Retorna eventos con tipo 'InstagramPost' para los posts nuevos.
    """
    try:
        import instaloader
    except ImportError:
        print("  ⚠️  instaloader no instalado.")
        return []

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    seen = _load_seen()
    new_seen = set()
    found = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)

    players = [p for p in load_players() if p.get("instagram")]

    for player in players:
        ig_handle = player["instagram"]
        try:
            profile = instaloader.Profile.from_username(L.context, ig_handle)
        except Exception as e:
            print(f"  ⚠️  No se pudo acceder a @{ig_handle}: {e}")
            continue

        try:
            for post in profile.get_posts():
                # Solo revisar posts de los últimos 3 días
                post_date = post.date_utc.replace(tzinfo=timezone.utc)
                if post_date < cutoff:
                    break

                post_id = post.shortcode
                if post_id in seen or post_id in new_seen:
                    continue

                new_seen.add(post_id)

                caption_text = (post.caption or "").strip()
                if not caption_text:
                    continue

                print(f"    📸 Nuevo post de @{ig_handle}: {caption_text[:60]}...")

                # Actualizar intel del jugador con el post
                update_intel(
                    player=player,
                    info_type="instagram",
                    content=f"Post de Instagram: {caption_text[:400]}",
                    source=f"@{ig_handle}",
                )

                found.append({
                    "player": player,
                    "event_type": "InstagramPost",
                    "detail": "Instagram Post",
                    "minute": None,
                    "team": player.get("club", ""),
                    "fixture": {},
                    "post_caption": caption_text,
                    "post_url": f"https://instagram.com/p/{post_id}/",
                    "post_date": post_date.strftime("%Y-%m-%d"),
                })

        except Exception as e:
            print(f"  ⚠️  Error leyendo posts de @{ig_handle}: {e}")
            continue

    seen.update(new_seen)
    _save_seen(seen)
    return found
