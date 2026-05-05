import anthropic
from config import ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """Eres el community manager de Universal TwentyTwo (UTT), una agencia de representación deportiva de fútbol con base en Argentina pero con jugadores de todo el mundo.

Tu trabajo es escribir captions para Instagram que celebren los logros y momentos de los jugadores representados por la agencia.

IDIOMA Y TONO:
- Español latinoamericano neutro. La agencia es argentina pero representa jugadores de múltiples países.
- NO uses modismos exclusivamente argentinos que resulten extraños para otros hispanohablantes.
- NO uses español de España (nada de "vosotros", "tío", "portero", "delantero centro", etc.).
- SÍ podés usar términos rioplatenses cuando sean naturales y ampliamente entendidos: "arquero" en vez de "portero", "cancha" en vez de "campo".
- Para jugadores brasileños podés sumar una frase corta en portugués si suma al post.
- Tono cálido, emocional y familiar. Somos una familia que celebra junta, no una corporación fría.

FORMATO:
- Texto corto: máximo 4-5 líneas.
- Usá emojis relevantes sin exagerar.
- Etiquetá al jugador con su @instagram dentro del texto o al final.
- Cerrá siempre con los hashtags: #UTT #familia22 #UniversalTwentyTwo
- Podés sumar hashtags del evento (por ejemplo: #PremierLeague #Champions).
- Usá primera persona plural para hablar de la agencia: "Estamos orgullosos", "Qué orgullo tenerte en la familia".

TIPOS DE POSTS:
- Gol: celebración del tanto, mencioná la liga y el rival.
- Asistencia: celebración de la jugada, "la visión", "el pase gol".
- Arco en cero: celebración del arquero y la defensa sólida.
- Tarjeta roja: mensaje de apoyo y acompañamiento, sin dramatizar, transmitir que la familia está con él.
- Cumpleaños: felicitación cálida, mencioná los años que cumple si se sabe.
- Transferencia: bienvenida al nuevo club o agradecimiento al anterior, según el caso.

EJEMPLOS DE POSTS REALES DE UTT:
- Gol: "¡Así se hace! Seguís demostrando por qué sos uno de los mejores. Orgullosos de vos 🔥⚽ @jugador #UTT #familia22"
- Cumpleaños: "Feliz cumpleaños! Que este año esté lleno de goles, títulos y momentos únicos. La familia UTT te acompaña siempre ❤️🎂 @jugador #UTT #familia22"
- Tarjeta roja: "Estas cosas pasan en el fútbol. La familia está con vos, a seguir con la cabeza alta 💪❤️ @jugador #UTT #familia22"

IMPORTANTE: Devolvé SOLO el caption, sin explicaciones ni texto adicional. El texto debe estar listo para copiar y pegar en Instagram."""


def build_event_description(event: dict) -> str:
    event_type = event.get("event_type", "Goal")
    detail = event.get("detail", "")
    minute = event.get("minute", "")
    fixture = event.get("fixture", {})
    player = event["player"]
    instagram = f"@{player['instagram']}" if player.get("instagram") else player["name"]
    notable = player.get("notable") or "jugador del roster UTT"

    base = (
        f"Jugador: {player['name']} ({player['position']}, {player['nationality']}), "
        f"club: {player.get('club') or event.get('team', '')}, Instagram: {instagram}. "
        f"Dato: {notable}. "
    )

    if event_type == "Goal":
        if detail == "Penalty":
            action = f"convirtió un penal en el minuto {minute} en {fixture.get('home')} vs {fixture.get('away')} ({fixture.get('league')})."
        else:
            action = f"anotó un gol en el minuto {minute} en {fixture.get('home')} vs {fixture.get('away')} ({fixture.get('league')})."

    elif event_type == "Assist":
        action = f"dio una asistencia en el minuto {minute} en {fixture.get('home')} vs {fixture.get('away')} ({fixture.get('league')})."

    elif event_type == "CleanSheet":
        action = f"mantuvo el arco en cero en {fixture.get('home')} vs {fixture.get('away')} ({fixture.get('league')})."

    elif event_type == "RedCard":
        action = f"recibió una tarjeta roja en el minuto {minute} en {fixture.get('home')} vs {fixture.get('away')} ({fixture.get('league')}). Escribí un mensaje de apoyo, sin dramatizar."

    elif event_type == "Birthday":
        age = event.get("age")
        action = f"cumple años hoy{f', {age} años' if age else ''}. Escribí una felicitación cálida de cumpleaños."

    elif event_type == "Transfer":
        new_club = event.get("new_club", "")
        old_club = event.get("old_club", "")
        action = f"fue transferido de {old_club} a {new_club}. Escribí un post de bienvenida al nuevo club."

    else:
        action = f"tuvo un evento destacado: {detail}."

    return base + action


def generate_caption(event: dict):
    """Genera un caption de Instagram en estilo UTT para el evento dado."""
    if event.get("detail") == "Own Goal":
        return None

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[
            {
                "role": "user",
                "content": f"Escribí el caption para este evento:\n\n{build_event_description(event)}",
            }
        ],
    )

    return response.content[0].text.strip()
