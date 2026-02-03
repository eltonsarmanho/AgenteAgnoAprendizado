from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from agno.agent import Agent
from agno.media import File
from dotenv import load_dotenv
import os
from agno.models.openai import OpenAILike
import json
from agno.models.google import Gemini

load_dotenv(override=True)


# Modelo de dados para composição corporal
class ComposicaoCorporal(BaseModel):
    """Modelo para armazenar dados de composição corporal extraídos"""
    peso: Optional[float] = Field(None, description="Peso em kg")
    altura: Optional[float] = Field(None, description="Altura em cm ou metros")
    percentual_gordura: Optional[float] = Field(None, description="Percentual de gordura corporal")
    imc: Optional[float] = Field(None, description="Índice de Massa Corporal (IMC)")
    massa_magra: Optional[float] = Field(None, description="Massa magra em kg")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")


# Verificar se chave de API está configurada corretamente
maritaca_api_key = os.getenv("MARITALK_API_KEY")
if not maritaca_api_key:
    raise ValueError("A chave de API do Maritaca não está configurada. Por favor, defina a variável de ambiente 'MARITALK_API_KEY'.")

# Criar modelo Maritaca
model = OpenAILike(
    id="sabia-4",
    name="Maritaca Sabia 4",
    api_key=maritaca_api_key,
    base_url="https://chat.maritaca.ai/api",
    temperature=0,
)
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("A chave de API do Google não está configurada. Por favor, defina a variável de ambiente 'GOOGLE_API_KEY'.")

# model = Gemini(
#     id="gemini-2.5-flash",
#     api_key=google_api_key,
#     temperature=0,
# )
print(model)

# Criar agente especializado em extração de dados nutricionais
agent = Agent(
    model=model,
    markdown=True,
    structured_outputs=True,
    instructions=[
        "Você é um especialista em análise de documentos nutricionais.",
        "Sua tarefa é extrair dados de composição corporal de forma precisa.",
        "Extraia: Peso, Altura, Percentual de Gordura, IMC, Massa Magra.",
        "Se algum dado não estiver disponível, retorne None para esse campo.",
        "Seja preciso com as unidades de medida: peso em kg, altura em cm."
    ],
)


def extrair_composicao_corporal(pdf_path: str) -> ComposicaoCorporal:
    """
    Extrai dados de composição corporal de um PDF de nutricionista
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        ComposicaoCorporal: Objeto com os dados extraídos
    """
    try:
        # Carregar o PDF
        pdf_file = File(filepath=pdf_path)
        
        # Mensagem específica para extração
        mensagem = """
        Analise este documento nutricional e extraia os seguintes dados de composição corporal:
        
        1. Peso (em kg)
        2. Altura (em cm ou metros - converta para cm se necessário)
        3. Percentual de Gordura (%)
        4. IMC (Índice de Massa Corporal)
        5. Massa Magra (em kg)
        
        Forneça os dados no seguinte formato JSON:
        {
            "peso": <valor ou null>,
            "altura": <valor ou null>,
            "percentual_gordura": <valor ou null>,
            "imc": <valor ou null>,
            "massa_magra": <valor ou null>,
            "observacoes": "<texto ou null>"
        }
        
        Retorne APENAS o JSON com os valores numéricos encontrados.
        """
        
        # Executar extração
        response = agent.run(mensagem, files=[pdf_file])
        
        print("\n=== Resposta do Agente ===")
        print(response.content)
        print("\n=== Dados de Composição Corporal Extraídos ===\n")
        
        # Tentar parsear a resposta como JSON
        try:
            # Extrair JSON da resposta (pode vir com markdown)
            content = str(response.content)
            
            # Remover markdown code blocks se existirem
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parsear JSON
            dados = json.loads(content)
            composicao = ComposicaoCorporal(**dados)
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"Aviso: Não foi possível parsear JSON automaticamente: {e}")
            print("Retornando objeto vazio. Verifique a resposta acima.")
            composicao = ComposicaoCorporal()
        
        # Exibir dados extraídos
        print(f"Peso: {composicao.peso} kg" if composicao.peso else "Peso: Não encontrado")
        print(f"Altura: {composicao.altura} cm" if composicao.altura else "Altura: Não encontrado")
        print(f"Percentual de Gordura: {composicao.percentual_gordura}%" if composicao.percentual_gordura else "Percentual de Gordura: Não encontrado")
        print(f"IMC: {composicao.imc}" if composicao.imc else "IMC: Não encontrado")
        print(f"Massa Magra: {composicao.massa_magra} kg" if composicao.massa_magra else "Massa Magra: Não encontrado")
        if composicao.observacoes:
            print(f"Observações: {composicao.observacoes}")
        
        return composicao
            
    except Exception as e:
        print(f"Erro ao processar PDF: {str(e)}")
        raise


def salvar_json(composicao: ComposicaoCorporal, output_path: str = "composicao_corporal.json"):
    """
    Salva os dados extraídos em formato JSON
    
    Args:
        composicao: Objeto ComposicaoCorporal com os dados
        output_path: Caminho do arquivo JSON de saída
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(composicao.model_dump(), f, ensure_ascii=False, indent=2)
        print(f"\n✓ Dados salvos em: {output_path}")
    except Exception as e:
        print(f"Erro ao salvar JSON: {str(e)}")


# Exemplo de uso
if __name__ == "__main__":
    # Caminho para o PDF
    pdf_path = "Extract/DadoNutricionista.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Erro: Arquivo não encontrado em {pdf_path}")
        exit(1)
    
    # Extrair dados
    print(f"Processando arquivo: {pdf_path}\n")
    composicao = extrair_composicao_corporal(pdf_path)
    
    # Salvar em JSON
    salvar_json(composicao, "Extract/composicao_corporal_extraida.json")
    
    print("\n✓ Extração concluída com sucesso!")
