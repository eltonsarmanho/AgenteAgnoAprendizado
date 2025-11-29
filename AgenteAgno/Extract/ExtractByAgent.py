"""
ExtractByAgent - Extracao de Dados por Agente
==============================================

Script para extrair dados estruturados de documentos
usando agentes de IA.
"""

from agno.agent import Agent
from agno.models.openai import OpenAILike
import os
import json
from dotenv import load_dotenv
from typing import Dict, List, Optional

load_dotenv(override=True)


class ExtractByAgent:
    """Extrator de dados usando agentes de IA."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Inicializa o extrator."""
        self.api_key = api_key or os.getenv("MARITALK_API_KEY")
        if not self.api_key:
            raise ValueError("API key e obrigatoria")
        
        self.model = OpenAILike(
            id="sabia-3",
            name="Maritaca Sabia 3",
            api_key=self.api_key,
            base_url="https://chat.maritaca.ai/api",
            temperature=0,
        )
        
        self.agente_extrator = Agent(
            model=self.model,
            name="Extrator de Dados",
            instructions="""Voce e um especialista em extracao de dados estruturados.
            
Analise o texto fornecido e extraia:
1. Entidades nomeadas (pessoas, organizacoes, locais)
2. Datas e periodos
3. Valores numericos e monetarios
4. Coordenadas geograficas
5. Informacoes relevantes

Retorne os dados em formato JSON estruturado."""
        )
    
    def extrair(self, texto: str) -> Dict:
        """Extrai dados do texto usando o agente."""
        prompt = f"""Analise o seguinte texto e extraia dados estruturados:

TEXTO:
{texto}

Retorne um JSON com os dados extraidos."""
        
        response = self.agente_extrator.run(prompt)
        return {
            'texto_original': texto[:200] + '...' if len(texto) > 200 else texto,
            'resposta': response.content if response else None
        }
    
    def extrair_entidades(self, texto: str) -> List[Dict]:
        """Extrai apenas entidades nomeadas."""
        prompt = f"""Liste todas as entidades nomeadas no texto:

TEXTO:
{texto}

Formato: JSON com listas de pessoas, organizacoes, locais."""
        
        response = self.agente_extrator.run(prompt)
        return response.content if response else []
    
    def extrair_datas(self, texto: str) -> List[str]:
        """Extrai datas do texto."""
        prompt = f"""Liste todas as datas mencionadas no texto:

TEXTO:
{texto}

Formato: Lista de datas no formato YYYY-MM-DD quando possivel."""
        
        response = self.agente_extrator.run(prompt)
        return response.content if response else []


def main():
    """Funcao principal de demonstracao."""
    try:
        extrator = ExtractByAgent()
        
        texto_teste = """
        A empresa XYZ Ltda foi fundada em 15 de marco de 2020 por Joao Silva.
        Localizada em Sao Paulo, a empresa possui um capital de R$ 500.000,00.
        O terreno esta nas coordenadas -23.55, -46.63.
        """
        
        print("Extraindo dados...")
        resultado = extrator.extrair(texto_teste)
        print(f"\nResultado: {resultado}")
        
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
