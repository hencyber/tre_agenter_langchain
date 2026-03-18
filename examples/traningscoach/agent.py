"""
🏋️ Träningscoach – AI-Agent

En personlig träningscoach som hjälper med BMI, kaloribehov och träningsråd.
Använder verktyg för beräkningar och svarar på svenska.

Kör:
    python -m examples.traningscoach.agent
"""

from langchain_core.tools import tool
from langchain.agents import create_agent
from datetime import datetime

from util.models import get_model
from util.streaming_utils import STREAM_MODES, handle_stream
from util.pretty_print import get_user_input, print_welcome, print_goodbye


# ──────────────────────────── VERKTYG ────────────────────────────


@tool
def berakna_bmi(vikt_kg: float, langd_cm: float) -> str:
    """Beräkna BMI (Body Mass Index) utifrån vikt i kg och längd i cm."""
    langd_m = langd_cm / 100
    bmi = round(vikt_kg / (langd_m ** 2), 1)

    if bmi < 18.5:
        kategori = "Undervikt"
    elif bmi < 25:
        kategori = "Normalvikt"
    elif bmi < 30:
        kategori = "Övervikt"
    else:
        kategori = "Fetma"

    return f"BMI: {bmi} ({kategori})"


@tool
def berakna_kaloribehov(vikt_kg: float, langd_cm: float, alder: int, kon: str, aktivitetsniva: str) -> str:
    """Beräkna dagligt kaloribehov med Harris-Benedict-formeln.

    Parametrar:
        vikt_kg: Vikt i kilogram
        langd_cm: Längd i centimeter
        alder: Ålder i år
        kon: 'man' eller 'kvinna'
        aktivitetsniva: 'stillasittande', 'lätt', 'måttlig', 'aktiv' eller 'mycket aktiv'
    """
    if kon.lower() in ("man", "male", "m"):
        bmr = 88.362 + (13.397 * vikt_kg) + (4.799 * langd_cm) - (5.677 * alder)
    else:
        bmr = 447.593 + (9.247 * vikt_kg) + (3.098 * langd_cm) - (4.330 * alder)

    faktorer = {
        "stillasittande": 1.2, "lätt": 1.375, "måttlig": 1.55,
        "aktiv": 1.725, "mycket aktiv": 1.9,
    }
    faktor = faktorer.get(aktivitetsniva.lower(), 1.55)
    dagligt_behov = round(bmr * faktor)

    return (
        f"BMR (basmetabolism): {round(bmr)} kcal\n"
        f"Aktivitetsnivå: {aktivitetsniva} (faktor {faktor})\n"
        f"Dagligt kaloribehov: {dagligt_behov} kcal"
    )


@tool
def hamta_tid() -> str:
    """Hämta aktuellt datum och tid."""
    return datetime.now().strftime("Datum: %Y-%m-%d, Tid: %H:%M:%S")


# ──────────────────────────── MAIN ────────────────────────────


def run():
    print_welcome(
        title="Träningscoach – AI-Agent",
        description="Jag hjälper dig med BMI, kaloribehov och träningsråd. Skriv 'avsluta' för att stänga.",
    )

    model = get_model()

    agent = create_agent(
        model=model,
        tools=[berakna_bmi, berakna_kaloribehov, hamta_tid],
        system_prompt=(
            "# Roll\n"
            "Du är en personlig träningscoach och hälsorådgivare.\n\n"
            "# Språk\n"
            "Svara alltid på svenska.\n\n"
            "# Uppgifter\n"
            "- Hjälp användaren med träningsråd och kostråd\n"
            "- Beräkna BMI med verktyget berakna_bmi\n"
            "- Beräkna dagligt kaloribehov med verktyget berakna_kaloribehov\n"
            "- Ge konkreta träningsprogram och kostförslag\n\n"
            "# Regler\n"
            "- Använd ALLTID verktygen för beräkningar, gissa aldrig\n"
            "- Fråga efter vikt, längd, ålder och kön om det behövs\n"
            "- Var motiverande och stödjande, men ärlig med resultaten\n\n"
            "# Svarsformat\n"
            "- Ge korta, tydliga svar\n"
            "- Använd punktlistor för tränings- och kostråd\n"
            "- Avsluta med ett uppmuntrande meddelande"
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
        handle_stream(process_stream, agent_name="Träningscoach")

    print_goodbye("Bra jobbat! Fortsätt träna! 💪")


if __name__ == "__main__":
    run()
