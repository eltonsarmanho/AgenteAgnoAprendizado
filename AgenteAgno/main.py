"""
Main - Ponto de entrada do sistema RAG
======================================

Sistema principal para execucao do RAG com SQLite e Agentes.
"""

from agno.agent import Agent
from agno.models.openai import OpenAILike
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.lancedb import LanceDb
from agno.storage.sqlite import SqliteStorage
from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
import os
from dotenv import load_dotenv

# Carregar variaveis de ambiente
load_dotenv(override=True)


def criar_agente():
    """Cria e configura o agente RAG."""
    api_key = os.getenv("MARITALK_API_KEY")
    
    if not api_key:
        raise ValueError("MARITALK_API_KEY nao encontrada nas variaveis de ambiente")
    
    # Configurar modelo Maritaca
    model = OpenAILike(
        id="sabia-3",
        name="Maritaca Sabia 3",
        api_key=api_key,
        base_url="https://chat.maritaca.ai/api",
        temperature=0,
    )
    
    # Configurar embedder para vetorizacao
    embedder = SentenceTransformerEmbedder()
    
    # Configurar banco vetorial LanceDB
    vector_db = LanceDb(
        table_name="recipes",
        uri="lancedb",
        embedder=embedder,
    )
    
    # Configurar base de conhecimento com PDFs
    knowledge_base = PDFKnowledgeBase(
        path="file",
        vector_db=vector_db,
    )
    
    # Configurar storage SQLite
    storage = SqliteStorage(
        table_name="agno_sessions",
        db_file="data.db",
    )
    
    # Criar agente
    agente = Agent(
        model=model,
        name="Agente RAG",
        knowledge=knowledge_base,
        storage=storage,
        session_id="sessao_principal",
        search_knowledge=True,
        instructions="""Voce e um assistente especializado em responder perguntas
baseado nos documentos carregados. Use o conhecimento disponivel para fornecer
respostas precisas e uteis. Sempre cite as fontes quando possivel.""",
    )
    
    return agente, knowledge_base


def main():
    """Funcao principal do sistema."""
    print("=" * 60)
    print("Sistema RAG com Agentes Agno")
    print("=" * 60)
    
    try:
        agente, knowledge_base = criar_agente()
        
        # Carregar documentos
        print("\nCarregando documentos da base de conhecimento...")
        knowledge_base.load()
        print("Documentos carregados com sucesso!")
        
        # Loop interativo
        while True:
            print("\n" + "-" * 40)
            pergunta = input("Digite sua pergunta (ou 'sair' para encerrar): ").strip()
            
            if pergunta.lower() in ['sair', 'exit', 'quit', 'q']:
                print("Encerrando sistema...")
                break
            
            if not pergunta:
                print("Por favor, digite uma pergunta valida.")
                continue
            
            print("\nBuscando resposta...\n")
            agente.print_response(pergunta, stream=True)
            
    except Exception as e:
        print(f"Erro: {e}")
        raise


if __name__ == "__main__":
    main()
