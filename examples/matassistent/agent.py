"""
🍳 Matlagningsassistent – AI-Agent

En matlagningsassistent som hjälper med enhetsomvandling, portionsräkning och recept.
Använder verktyg för beräkningar och svarar på svenska.

Kör:
    python -m examples.matassistent.agent
"""

from langchain_core.tools import tool
from langchain.agents import create_agent
from datetime import datetime

from util.models import get_model
from util.streaming_utils import STREAM_MODES, handle_stream
from util.pretty_print import get_user_input, print_welcome, print_goodbye


# ──────────────────────────── VERKTYG ────────────────────────────


@tool
def omvandla_enhet(mangd: float, fran_enhet: str, till_enhet: str) -> str:
    """Omvandla mellan matlagningsenheter.

    Stödda enheter: ml, dl, l, tsk, msk, kopp, gram, kg
    """
    till_ml = {
        "ml": 1, "dl": 100, "l": 1000,
        "tsk": 5, "msk": 15,
        "kopp": 240, "koppar": 240,
        "gram": 1, "g": 1, "kg": 1000,
    }

    fran = fran_enhet.lower().strip()
    till = till_enhet.lower().strip()

    if fran not in till_ml:
        return f"Okänd enhet: {fran}. Stödda: {', '.join(till_ml.keys())}"
    if till not in till_ml:
        return f"Okänd enhet: {till}. Stödda: {', '.join(till_ml.keys())}"

    ml_varde = mangd * till_ml[fran]
    resultat = ml_varde / till_ml[till]

    return f"{mangd} {fran} = {round(resultat, 2)} {till}"


@tool
def berakna_portioner(original_portioner: int, onskat_portioner: int, ingrediens: str, mangd: float, enhet: str) -> str:
    """Skala ett recept till önskat antal portioner.

    Parametrar:
        original_portioner: Receptets originalportioner
        onskat_portioner: Önskat antal portioner
        ingrediens: Namn på ingrediensen
        mangd: Originalmängd
        enhet: Enhet (t.ex. dl, g, st)
    """
    faktor = onskat_portioner / original_portioner
    ny_mangd = round(mangd * faktor, 1)

    return (
        f"Skalning: {original_portioner} → {onskat_portioner} portioner (x{round(faktor, 2)})\n"
        f"{ingrediens}: {mangd} {enhet} → {ny_mangd} {enhet}"
    )


@tool
def hamta_tid() -> str:
    """Hämta aktuellt datum och tid – användbart för tidsplanering av matlagning."""
    return datetime.now().strftime("Datum: %Y-%m-%d, Tid: %H:%M:%S")


# ──────────────────────────── MAIN ────────────────────────────


def run():
    print_welcome(
        title="Matlagningsassistent – AI-Agent",
        description="Jag hjälper med enhetsomvandling, portioner och receptförslag. Skriv 'avsluta' för att stänga.",
    )

    model = get_model()

    agent = create_agent(
        model=model,
        tools=[omvandla_enhet, berakna_portioner, hamta_tid],
        system_prompt=(
            "Du är en matlagningsassistent som hjälper med recept, "
            "enhetsomvandling och portionsberäkning. "
            "Svara alltid på svenska. "
            "Om användaren frågar om enheter, använd verktyget omvandla_enhet. "
            "Om användaren vill skala ett recept, använd berakna_portioner. "
            "Ge även kreativa receptförslag och matlagningstips."
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
        handle_stream(process_stream, agent_name="Matassistenten")

    print_goodbye("Smaklig måltid! 🍽️")


if __name__ == "__main__":
    run()
