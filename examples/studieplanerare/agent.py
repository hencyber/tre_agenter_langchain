"""
📚 Studieplanerare – AI-Agent

En studieplanerare som hjälper med Pomodoro-scheman, betygsberäkning och studietips.
Använder verktyg för beräkningar och svarar på svenska.

Kör:
    python -m examples.studieplanerare.agent
"""

from langchain_core.tools import tool
from langchain.agents import create_agent
from datetime import datetime, timedelta

from util.models import get_model
from util.streaming_utils import STREAM_MODES, handle_stream
from util.pretty_print import get_user_input, print_welcome, print_goodbye


# ──────────────────────────── VERKTYG ────────────────────────────


@tool
def berakna_pomodoro(studie_minuter: int, paus_minuter: int = 5, lang_paus: int = 15) -> str:
    """Beräkna ett Pomodoro-studieschema.

    Parametrar:
        studie_minuter: Total studietid i minuter
        paus_minuter: Kort paus mellan pass (standard 5 min)
        lang_paus: Lång paus var 4:e pass (standard 15 min)
    """
    pass_langd = 25
    antal_pass = studie_minuter // pass_langd
    resterande = studie_minuter % pass_langd

    total_paus = 0
    schema = []
    aktuell_tid = datetime.now()

    for i in range(1, antal_pass + 1):
        start = aktuell_tid.strftime("%H:%M")
        aktuell_tid += timedelta(minutes=pass_langd)
        slut = aktuell_tid.strftime("%H:%M")
        schema.append(f"  Pass {i}: {start}–{slut} (25 min studier)")

        if i < antal_pass:
            if i % 4 == 0:
                paus = lang_paus
                schema.append(f"  ☕ Lång paus: {paus} min")
            else:
                paus = paus_minuter
                schema.append(f"  ⏸  Kort paus: {paus} min")
            aktuell_tid += timedelta(minutes=paus)
            total_paus += paus

    if resterande > 0:
        start = aktuell_tid.strftime("%H:%M")
        aktuell_tid += timedelta(minutes=resterande)
        slut = aktuell_tid.strftime("%H:%M")
        schema.append(f"  Extra: {start}–{slut} ({resterande} min)")

    resultat = f"Pomodoro-schema för {studie_minuter} minuter studier:\n"
    resultat += f"Antal pass: {antal_pass}\n"
    resultat += f"Total paustid: {total_paus} min\n"
    resultat += f"Klart ca: {aktuell_tid.strftime('%H:%M')}\n\n"
    resultat += "\n".join(schema)

    return resultat


@tool
def berakna_snittbetyg(betyg: str) -> str:
    """Beräkna snittbetyg (GPA) från en lista med bokstavsbetyg.

    Parametrar:
        betyg: Kommaseparerade betyg, t.ex. 'A,B,C,A,B'
    """
    betyg_varden = {"A": 5, "B": 4, "C": 3, "D": 2, "E": 1, "F": 0}
    betyg_lista = [b.strip().upper() for b in betyg.split(",")]
    varden = []

    for b in betyg_lista:
        if b in betyg_varden:
            varden.append(betyg_varden[b])
        else:
            return f"Okänt betyg: {b}. Använd A, B, C, D, E eller F."

    snitt = sum(varden) / len(varden)

    if snitt >= 4.5:
        snitt_bokstav = "A"
    elif snitt >= 3.5:
        snitt_bokstav = "B"
    elif snitt >= 2.5:
        snitt_bokstav = "C"
    elif snitt >= 1.5:
        snitt_bokstav = "D"
    elif snitt >= 0.5:
        snitt_bokstav = "E"
    else:
        snitt_bokstav = "F"

    return (
        f"Betyg: {', '.join(betyg_lista)}\n"
        f"Antal kurser: {len(varden)}\n"
        f"Snittpoäng: {round(snitt, 2)} / 5.0\n"
        f"Snittbetyg: {snitt_bokstav}"
    )


@tool
def hamta_tid() -> str:
    """Hämta aktuellt datum, veckodag och tid."""
    nu = datetime.now()
    veckodag = ["Måndag", "Tisdag", "Onsdag", "Torsdag", "Fredag", "Lördag", "Söndag"]
    return f"{veckodag[nu.weekday()]}, {nu.strftime('%Y-%m-%d')} kl {nu.strftime('%H:%M:%S')}"


# ──────────────────────────── MAIN ────────────────────────────


def run():
    print_welcome(
        title="Studieplanerare – AI-Agent",
        description="Jag hjälper med studieplanering, Pomodoro-scheman och betyg. Skriv 'avsluta' för att stänga.",
    )

    model = get_model()

    agent = create_agent(
        model=model,
        tools=[berakna_pomodoro, berakna_snittbetyg, hamta_tid],
        system_prompt=(
            "# Roll\n"
            "Du är en studieplanerare och akademisk rådgivare.\n\n"
            "# Språk\n"
            "Svara alltid på svenska.\n\n"
            "# Uppgifter\n"
            "- Skapa Pomodoro-scheman med verktyget berakna_pomodoro\n"
            "- Beräkna snittbetyg med verktyget berakna_snittbetyg\n"
            "- Ge studietips och hjälp med studieplanering\n\n"
            "# Regler\n"
            "- Använd ALLTID verktygen för beräkningar\n"
            "- Fråga hur mycket tid studenten har och vilka ämnen\n"
            "- Anpassa råd efter studentens situation\n\n"
            "# Svarsformat\n"
            "- Studiescheman: visa tydliga tider och pauser\n"
            "- Betyg: visa både poäng och bokstavsbetyg\n"
            "- Avsluta med uppmuntran och nästa steg"
        ),
    )

    while True:
        user_input = get_user_input("Ställ din fråga")
        if not user_input or user_input.lower() in ("avsluta", "quit", "exit", "q"):
            break

        process_stream = agent.stream(
            {"messages": [{"role": "user", "content": user_input}]},
            stream_mode=STREAM_MODES,
        )
        handle_stream(process_stream, agent_name="Studieplaneraren")

    print_goodbye("Lycka till med studierna! 📖")


if __name__ == "__main__":
    run()
