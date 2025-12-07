from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import File
from dotenv import load_dotenv

load_dotenv(override=True)

agent = Agent(
    model=Gemini(
        id="gemini-2.5-flash"),
    markdown=True,
)

file_path = Path(__file__).parent.joinpath("Escritura1.pdf")
print(file_path)

# Opção 1: Usar filepath diretamente (recomendado - o agno detecta o mime_type automaticamente)
agent.print_response(
    "Esse documento possui selo de autenticidade do Tribunal de Justiça. Responda apenas com SIM ou NAO.",
    files=[File(filepath=file_path, mime_type="application/pdf")],
    stream=True,
)