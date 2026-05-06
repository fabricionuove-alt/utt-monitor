"""
Sistema de inteligencia por jugador.
Mantiene un perfil actualizado de cada jugador basado en noticias e Instagram.
Ese contexto se usa después para generar captions más ricos.
"""
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import anthropic
from config import ANTHROPIC_API_KEY

INTEL_DIR = Path(__file__).parent / "intel"
INTEL_DIR.mkdir(exist_ok=True)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

UPDATE_PROMPT = """Sos el analista de datos de UTT (Universal Twenty Two), una agencia de representación deportiva.
Tu trabajo es mantener actualizado el perfil de inteligencia de cada jugador.

Dado el perfil actual y una nueva pieza de información, devolvé un JSON con el perfil actualizado.

Reglas:
- El campo "context" debe ser un párrafo corto (3-5 oraciones) que resuma lo más relevante del jugador HOY.
  Incluí: forma actual, estado físico, situación en el club, rumores relevantes, últimos logros.
- El campo "status" debe ser: "activo", "lesionado", "suspendido" o "transferencia".
- Agregá el nuevo item al inicio del "timeline" (máximo 20 items en el historial).
- Devolvé SOLO el JSON, sin explicaciones."""


def _slug(name: str) -> str:
    s = name.lower()
    s = re.sub(r"[áàäâ]", "a", s)
    s = re.sub(r"[éèëê]", "e", s)
    s = re.sub(r"[íìïî]", "i", s)
    s = re.sub(r"[óòöô]", "o", s)
    s = re.sub(r"[úùüû]", "u", s)
    s = re.sub(r"[ñ]", "n", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _intel_path(player_name: str) -> Path:
    return INTEL_DIR / f"{_slug(player_name)}.json"


def get_intel(player_name: str) -> dict:
    path = _intel_path(player_name)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {
        "name": player_name,
        "last_updated": None,
        "status": "activo",
        "context": "",
        "timeline": [],
    }


def save_intel(intel: dict) -> None:
    path = _intel_path(intel["name"])
    intel["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(intel, ensure_ascii=False, indent=2), encoding="utf-8")


def update_intel(player: dict, info_type: str, content: str, source: str = "") -> dict:
    """
    Actualiza el perfil de inteligencia de un jugador con nueva información.
    info_type: "news" | "instagram" | "match_event"
    """
    intel = get_intel(player["name"])

    new_item = {
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "type": info_type,
        "content": content[:500],
        "source": source,
    }

    current_context = intel.get("context") or "Sin información previa."
    current_status = intel.get("status", "activo")
    timeline_preview = intel.get("timeline", [])[:5]

    prompt = f"""Perfil actual de {player['name']}:
- Club: {player.get('club', 'desconocido')}
- Posición: {player.get('position', '')}
- Nacionalidad: {player.get('nationality', '')}
- Estado actual: {current_status}
- Contexto actual: {current_context}
- Historial reciente: {json.dumps(timeline_preview, ensure_ascii=False)}

Nueva información ({info_type}):
{content}
Fuente: {source}

Devolvé el perfil actualizado como JSON con los campos: name, status, context, timeline.
El timeline debe incluir el nuevo item más los anteriores (máximo 20)."""

    try:
        resp = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            system=UPDATE_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text.strip()
        # Extraer JSON aunque venga con markdown
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            updated = json.loads(match.group())
            intel.update({
                "name": player["name"],
                "status": updated.get("status", intel["status"]),
                "context": updated.get("context", intel["context"]),
                "timeline": ([new_item] + updated.get("timeline", intel["timeline"]))[:20],
            })
    except Exception as e:
        print(f"  ⚠️  Error actualizando intel de {player['name']}: {e}")
        intel["timeline"] = ([new_item] + intel.get("timeline", []))[:20]

    save_intel(intel)
    return intel


def get_intel_summary(player_name: str) -> str:
    """Retorna el contexto del jugador para usar en el prompt de caption."""
    intel = get_intel(player_name)
    ctx = intel.get("context", "")
    status = intel.get("status", "activo")
    if not ctx:
        return ""
    status_note = f" (Estado: {status})" if status != "activo" else ""
    return f"Contexto actualizado del jugador{status_note}: {ctx}"
