from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import File
from dotenv import load_dotenv
import os
load_dotenv(override=True)

# Verificar se chave de API está configurada corretamente
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("A chave de API do Google não está configurada. Por favor, defina a variável de ambiente 'GOOGLE_API_KEY'.")

# Criar modelo Gemini
model = Gemini(
    id="gemini-2.5-flash",
    api_key=google_api_key,
    temperature=0,
)
print(model)


# Criar agente
agent = Agent(
    model=model,
    markdown=True,
)

file_path = Path(__file__).parent.joinpath("Escritura2.pdf")
print(file_path)

# Opção 1: Usar filepath diretamente (recomendado - o agno detecta o mime_type automaticamente)
agent.print_response(
    "Esse documento possui selo de autenticidade do Tribunal de Justiça. Responda apenas com SIM ou NAO.",
    files=[File(filepath=file_path, mime_type="application/pdf")],
    stream=True,
)