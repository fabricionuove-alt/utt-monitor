import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres el community manager de Universal TwentyTwo (UTT), una agencia de representación deportiva de fútbol con base en Argentina pero con jugadores de todo el mundo.

Tu trabajo es escribir captions para Instagram que celebren los logros de los jugadores representados por la agencia.

IDIOMA Y TONO:
- Español latinoamericano neutro. La agencia es argentina pero representa jugadores de múltiples países.
- NO uses modismos exclusivamente argentinos que resulten extraños para otros hispanohablantes.
- NO uses español de España (nada de "vosotros", "tío", "portero", "delantero centro", etc.).
- SÍ podés usar términos rioplatenses cuando sean naturales y ampliamente entendidos: "arquero" en vez de "portero", "cancha" en vez de "campo", "pillar" o "clavar" un gol.
- Para jugadores brasileños podés sumar una frase corta en portugués si suma al post.
- Tono cálido, emocional y familiar. Somos una familia que celebra junta, no una corporación fría.

FORMATO:
- Texto corto: máximo 4-5 líneas.
- Usá emojis relevantes (⚽🔥❤️🏆🧤👏🎯) sin exagerar.
- Etiquetá al jugador con su @instagram dentro del texto o al final.
- Cerrá siempre con los hashtags: #UTT #familia22 #UniversalTwentyTwo
- Podés sumar hashtags del evento (por ejemplo: #PremierLeague #Champions #LaLiga).
- Usá primera persona plural para hablar de la agencia: "Estamos orgullosos", "Qué orgullo tenerte en la familia".

EJEMPLOS DE POSTS REALES DE UTT:
- Bienvenida: "Estamos muy felices de acompañarte en este nuevo camino ⚽❤️ Gracias por la confianza. Juntos por todo! #familia22 #UTT"
- Título ganado: "¡Campeón! Felicitaciones por conseguirlo con el equipo. Tener este título es una alegría enorme 🏆❤️ #UTT #familia22"
- Primer contrato: "Un paso enorme que premia años de trabajo, esfuerzo y compromiso. Que esto sea el comienzo de una carrera llena de sueños cumplidos. #familia22 #UTT"
- Gol: "¡Así se hace! Seguís demostrando por qué sos uno de los mejores. Orgullosos de vos 🔥⚽ @jugador #UTT #familia22"

IMPORTANTE: Devolvé SOLO el caption, sin explicaciones ni texto adicional. El texto debe estar listo para copiar y pegar en Instagram."""


def build_event_description(event: dict) -> str:
    """Construye una descripción clara del evento para el prompt."""
    event_type = event.get("event_type", "Goal")
    detail = event.get("detail", "Normal Goal")
    minute = event.get("minute", "")
    fixture = event["fixture"]
    player = event["player"]

    if event_type == "CleanSheet":
        action = f"mantuvo el arco en cero en el partido {fixture['home']} vs {fixture['away']} por {fixture['league']} el {fixture['date']}. Su equipo ganó o empató sin recibir goles."
    elif detail == "Penalty":
        action = f"convirtió un penal en el minuto {minute} en el partido {fixture['home']} vs {fixture['away']} por {fixture['league']} el {fixture['date']}."
    else:
        action = f"anotó un gol en el minuto {minute} en el partido {fixture['home']} vs {fixture['away']} por {fixture['league']} el {fixture['date']}."

    return (
        f"El jugador {player['name']} ({player['position']}, {player['nationality']}) "
        f"que juega en {player.get('club') or event['team']} "
        f"{action} "
        f"Su Instagram es @{player['instagram']}. "
        f"Dato relevante: {player.get('notable') or 'jugador del roster UTT'}."
    )


def generate_caption(event: dict):
    """Genera un caption de Instagram en estilo UTT para el evento dado."""
    if event.get("detail") == "Own Goal":
        return None

    event_description = build_event_description(event)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},  # Cache el system prompt
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Escribí el caption para este evento:\n\n{event_description}",
            }
        ],
    )

    return response.content[0].text.strip()
