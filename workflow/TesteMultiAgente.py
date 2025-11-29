"""Teste Multi-Agente com Traducao de Texto"""
from agno.agent import Agent
from agno.workflow import Workflow
from agno.models.openai import OpenAILike
from agno.team import Team
import os
from dotenv import load_dotenv

load_dotenv(override=True)

maritaca_api_key = os.getenv("MARITALK_API_KEY")
if not maritaca_api_key:
    print("MARITALK_API_KEY nao encontrada no arquivo .env")
    raise ValueError("MARITALK_API_KEY e obrigatoria")

try:
    print(f"MARITALK_API_KEY carregada: {maritaca_api_key[:20]}...")
    model = OpenAILike(
        id="sabia-3",
        name="Maritaca Sabia 3",
        api_key=maritaca_api_key,
        base_url="https://chat.maritaca.ai/api",
        temperature=0,
    )
    print("Modelo Maritaca (Sabia 3) carregado com sucesso!")
except Exception as e:
    print(f"Erro ao carregar Maritaca: {e}")
    raise


def detectar_idioma_solicitado(texto):
    """Detecta o idioma solicitado no texto."""
    texto_lower = texto.lower()
    palavras_espanhol = ['espanol', 'espanhol', 'castelhano', 'in spanish']
    palavras_frances = ['frances', 'francais', 'in french']
    
    for palavra in palavras_espanhol:
        if palavra in texto_lower:
            return 'espanhol'
    for palavra in palavras_frances:
        if palavra in texto_lower:
            return 'frances'
    return 'frances'


def criar_agente_tradutor(idioma, model):
    """Cria um agente tradutor especifico para o idioma."""
    if idioma == 'espanhol':
        return Agent(
            model=model,
            name="Tradutor Espanhol",
            instructions="Traduza para ESPANHOL. Responda EXCLUSIVAMENTE em espanhol.",
        )
    else:
        return Agent(
            model=model,
            name="Tradutor Frances",
            instructions="Traduza para FRANCES. Responda EXCLUSIVAMENTE em frances.",
        )


tradutor_frances = Agent(
    model=model,
    name="Tradutor Frances",
    instructions="Traduza o texto do portugues para o frances de forma simples e clara.",
)

tradutor_espanhol = Agent(
    model=model,
    name="Tradutor Espanhol",
    instructions="Traduza o texto do portugues para o espanhol de forma simples e clara."
)

profissional_escrita = Agent(
    model=model,
    name="Profissional de escrita",
    instructions="Escreva um texto claro e envolvente mantendo o idioma indicado.",
)


def processar_com_idioma(prompt):
    """Processa a solicitacao detectando o idioma."""
    idioma_detectado = detectar_idioma_solicitado(prompt)
    
    print(f"\nIdioma detectado: {idioma_detectado.upper()}")
    print(f"Prompt original: {prompt}\n")
    print("=" * 60)
    
    tradutor = criar_agente_tradutor(idioma_detectado, model)
    
    team = Team(
        name=f"Traducao para {idioma_detectado.upper()}",
        members=[tradutor],
        model=model,
        instructions=f"Responda EXCLUSIVAMENTE em {idioma_detectado.upper()}."
    )
    
    content_workflow = Workflow(
        name=f"Criacao de Conteudo em {idioma_detectado.upper()}",
        steps=[team, profissional_escrita],
    )
    
    content_workflow.print_response(prompt, stream=True)


def processar_com_idioma_simples(prompt):
    """Versao simplificada que usa um unico agente."""
    idioma_detectado = detectar_idioma_solicitado(prompt)
    
    print(f"\nIdioma detectado: {idioma_detectado.upper()}")
    print(f"Prompt original: {prompt}\n")
    print("=" * 60)
    
    agente = criar_agente_tradutor(idioma_detectado, model)
    agente.print_response(prompt, stream=True)


if __name__ == "__main__":
    print("\nTESTE: Multi-Agente com Traducao\n")
    
    print("TESTE 1: Sem idioma especificado -> FRANCES padrao")
    processar_com_idioma_simples("Povos originarios do Brasil")
    
    print("\n\nTESTE 2: FRANCES especificado")
    processar_com_idioma_simples("Povos originarios do Brasil. Responda em frances")
    
    print("\n\nTESTE 3: ESPANHOL especificado")
    processar_com_idioma_simples("Povos originarios do Brasil. Responda em espanhol")
