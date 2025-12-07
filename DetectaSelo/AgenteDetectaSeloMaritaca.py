from pathlib import Path

from agno.agent import Agent
from agno.models.google import Gemini
from agno.media import File
from dotenv import load_dotenv
import os
from agno.models.openai import OpenAILike

load_dotenv(override=True)

# Verificar se chave de API está configurada corretamente
maritaca_api_key = os.getenv("MARITALK_API_KEY")
if not maritaca_api_key:
    raise ValueError("A chave de API do Maritaca não está configurada. Por favor, defina a variável de ambiente 'MARITALK_API_KEY'.")

# Criar modelo Gemini
model = OpenAILike(
            id="sabia-3.1",
            name="Maritaca Sabia 3",
            api_key=maritaca_api_key,
            base_url="https://chat.maritaca.ai/api",
            temperature=0,
        )
        


# Criar agente
agent = Agent(
    model=model,
    markdown=True,
)

