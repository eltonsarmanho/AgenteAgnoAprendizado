"""
RagSQLITEGemini - RAG com SQLite e Agentes
==========================================

Sistema de Retrieval Augmented Generation usando
SQLite para armazenamento e agentes para respostas.
"""

from agno.agent import Agent
from agno.models.openai import OpenAILike
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.vectordb.lancedb import LanceDb
from agno.storage.sqlite import SqliteStorage
from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
import os
from dotenv import load_dotenv

load_dotenv(override=True)


class RagSQLITEGemini:
    """Sistema RAG com SQLite e agentes."""
    
    def __init__(self, db_file: str = "data.db", pdf_folder: str = "file"):
        """Inicializa o sistema RAG."""
        self.db_file = db_file
        self.pdf_folder = pdf_folder
        self.api_key = os.getenv("MARITALK_API_KEY")
        
        if not self.api_key:
            raise ValueError("MARITALK_API_KEY e obrigatoria")
        
        # Configurar modelo
        self.model = OpenAILike(
            id="sabia-3",
            name="Maritaca Sabia 3",
            api_key=self.api_key,
            base_url="https://chat.maritaca.ai/api",
            temperature=0,
        )
        
        # Configurar embedder
        self.embedder = SentenceTransformerEmbedder()
        
        # Configurar vector database
        self.vector_db = LanceDb(
            table_name="recipes",
            uri="lancedb",
            embedder=self.embedder,
        )
        
        # Configurar knowledge base
        self.knowledge_base = PDFKnowledgeBase(
            path=self.pdf_folder,
            vector_db=self.vector_db,
        )
        
        # Configurar storage
        self.storage = SqliteStorage(
            table_name="agno_sessions",
            db_file=self.db_file,
        )
        
        # Criar agente
        self.agente = Agent(
            model=self.model,
            name="RAG Agent",
            knowledge=self.knowledge_base,
            storage=self.storage,
            session_id="rag_session",
            search_knowledge=True,
            instructions="""Voce e um assistente especializado.
Use o conhecimento disponivel para responder as perguntas.
Seja preciso e cite as fontes quando possivel.""",
        )
    
    def carregar_documentos(self):
        """Carrega documentos do PDF."""
        print("Carregando documentos...")
        self.knowledge_base.load()
        print("Documentos carregados com sucesso!")
    
    def perguntar(self, pergunta: str, stream: bool = True):
        """Faz uma pergunta ao sistema RAG."""
        print(f"\nPergunta: {pergunta}\n")
        print("=" * 60)
        
        if stream:
            self.agente.print_response(pergunta, stream=True)
        else:
            response = self.agente.run(pergunta)
            print(f"Resposta: {response.content}")
            return response
    
    def menu_interativo(self):
        """Menu interativo para consultas."""
        print("\n" + "=" * 60)
        print("RAG SQLite Gemini - Sistema de Perguntas e Respostas")
        print("=" * 60)
        
        while True:
            print("\nOpcoes:")
            print("1. Fazer pergunta")
            print("2. Recarregar documentos")
            print("3. Ver historico")
            print("0. Sair")
            
            opcao = input("\nEscolha: ").strip()
            
            if opcao == "0":
                print("Saindo...")
                break
            elif opcao == "1":
                pergunta = input("Digite sua pergunta: ").strip()
                if pergunta:
                    self.perguntar(pergunta)
            elif opcao == "2":
                self.carregar_documentos()
            elif opcao == "3":
                print("Funcionalidade em desenvolvimento...")
            else:
                print("Opcao invalida!")


def main():
    """Funcao principal."""
    try:
        rag = RagSQLITEGemini()
        rag.menu_interativo()
    except Exception as e:
        print(f"Erro: {e}")


if __name__ == "__main__":
    main()
