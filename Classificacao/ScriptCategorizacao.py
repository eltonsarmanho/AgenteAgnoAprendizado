"""
Script para categorizar exercícios por grupo muscular usando IA.
Lê o CSV de exercícios e gera um novo CSV com categorias.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from dotenv import load_dotenv
import os
from agno.models.openai import OpenAILike
from agno.models.google import Gemini

load_dotenv(override=True)


class ExerciseCategory(BaseModel):
    """Modelo para classificação de exercício"""
    exercicio: str = Field(description="Nome do exercício")
    categoria: str = Field(description="Grupo muscular principal: Peito, Costas, Ombro, Bíceps, Tríceps, Abdômen, Perna, Antebraço, Mobilidade/Alongamento")


# Configurar modelo
maritaca_api_key = os.getenv("MARITALK_API_KEY")
if not maritaca_api_key:
    raise ValueError("A chave de API do Maritaca não está configurada. Por favor, defina a variável de ambiente 'MARITALK_API_KEY'.")

model = OpenAILike(
    id="sabia-4",
    name="Maritaca Sabia 4",
    api_key=maritaca_api_key,
    base_url="https://chat.maritaca.ai/api",
    temperature=0,
)

# Criar agente especializado em categorização de exercícios
agent = Agent(
    model=model,
    markdown=True,
    structured_outputs=True,
    instructions=[
        "Você é um especialista em educação física e categorização de exercícios.",
        "Categorize exercícios nos seguintes grupos musculares: Peitoral Maior, Peitoral Menor, Latíssimo do Dorso, Trapézio, Romboides, Deltoide Anterior, Deltoide Lateral, Deltoide Posterior, Manguito Rotador, Bíceps Braquial, Braquial, Tríceps Braquial, Flexores do Antebraço, Extensores do Antebraço, Reto Abdominal, Oblíquos, Transverso do Abdômen, Eretores da Espinha, Iliopsoas, Glúteo Maior, Glúteo Médio/Mínimo, Quadríceps, Isquiotibiais, Adutores, Abdutores, Gastrocnêmio, Sóleo, Tibial Anterior",
        "Para exercícios que envolvem múltiplos grupos, escolha o PRINCIPAL.",
        "Responda sempre em JSON com a estrutura: {\"exercicio\": \"nome\", \"categoria\": \"grupo_muscular\"}"
    ],
)


def categorizar_exercicios(arquivo_entrada='exercicios_videos.csv', arquivo_saida='exercicios_categorizado.csv'):
    """
    Lê CSV de exercícios e categoriza cada um por grupo muscular.
    
    Args:
        arquivo_entrada (str): Arquivo CSV com exercícios e vídeos
        arquivo_saida (str): Arquivo CSV de saída com categorias
    """
    try:
        # Ler arquivo CSV
        df = pd.read_csv(arquivo_entrada)
        
        print(f"Lendo arquivo: {arquivo_entrada}")
        print(f"Total de exercícios: {len(df)}")
        
        # Lista para armazenar categorias
        categorias = []
        
        # Categorizar cada exercício
        for idx, row in df.iterrows():
            exercicio = row['Exercício']
            print(f"[{idx + 1}/{len(df)}] Categorizando: {exercicio}")
            
            # Usar agente para categorizar
            prompt = f"Categorize o exercício: '{exercicio}'"
            
            response = agent.run(prompt)
            
            # Extrair categoria da resposta
            try:
                # Tentar extrair JSON da resposta
                resposta_texto = str(response)
                
                # Se a resposta já contém o modelo estruturado
                if hasattr(response, 'categoria'):
                    categoria = response.categoria
                else:
                    # Tentar encontrar categoria na resposta
                    import re
                    match = re.search(r'"categoria"\s*:\s*"([^"]+)"', resposta_texto)
                    if match:
                        categoria = match.group(1)
                    else:
                        categoria = "Sem categoria"
                
                categorias.append({
                    'Exercício': exercicio,
                    'Categoria': categoria,
                    'Vídeo': row['Vídeo']
                })
                
                print(f"  → {categoria}")
                
            except Exception as e:
                print(f"  → Erro ao processar: {str(e)}")
                categorias.append({
                    'Exercício': exercicio,
                    'Categoria': 'Sem categoria',
                    'Vídeo': row['Vídeo']
                })
        
        # Criar DataFrame com resultado
        df_categorizado = pd.DataFrame(categorias)
        
        # Adicionar coluna alongamento (1 se exercício contém "Alongamento" no nome, 0 caso contrário)
        df_categorizado['alongamento'] = df_categorizado['Exercício'].str.contains('Alongamento', case=False, na=False).astype(int)
        
        # Reordenar colunas
        df_categorizado = df_categorizado[['Exercício', 'Categoria', 'Vídeo', 'alongamento']]
        
        # Salvar como CSV
        df_categorizado.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
        
        print(f"\n✓ Arquivo criado com sucesso: {arquivo_saida}")
        print(f"✓ Total de exercícios categorizados: {len(df_categorizado)}")
        
        # Exibir resumo de categorias
        print("\nResumo por categoria:")
        resumo = df_categorizado['Categoria'].value_counts()
        for categoria, quantidade in resumo.items():
            print(f"  {categoria}: {quantidade}")
        
        return df_categorizado
        
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_entrada}' não encontrado.")
        return None
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        return None


if __name__ == "__main__":
    # Categorizar exercícios
    arquivo_entrada = "Classificacao/exercicios_videos.csv"
    arquivo_saida = "Classificacao/exercicios_categorizado.csv"
    
    if os.path.exists(arquivo_entrada):
        df_resultado = categorizar_exercicios(arquivo_entrada, arquivo_saida)
        
        if df_resultado is not None:
            print("\nPrimeiras linhas do resultado:")
            print(df_resultado.head(10))
    else:
        print(f"Arquivo não encontrado: {arquivo_entrada}")
