"""
RagSQLITE - Sistema RAG com SQLite
==================================

Implementacao do sistema RAG usando SQLite para persistencia
de sessoes e historico de conversas.
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


class RagSQLITE:
    """Sistema RAG com armazenamento SQLite."""
    
    def __init__(
        self, 
        db_file: str = "data.db",
        pdf_folder: str = "file",
        table_name: str = "agno_sessions",
        session_id: str = "default_session"
    ):
        """
        Inicializa o sistema RAG.
        
        Args:
            db_file: Arquivo do banco SQLite
            pdf_folder: Pasta com arquivos PDF
            table_name: Nome da tabela de sessoes
            session_id: ID da sessao atual
        """
        self.db_file = db_file
        self.pdf_folder = pdf_folder
        self.table_name = table_name
        self.session_id = session_id
        
        # Configurar componentes
        self._setup_model()
        self._setup_embedder()
        self._setup_vector_db()
        self._setup_knowledge_base()
        self._setup_storage()
        self._setup_agent()
    
    def _setup_model(self):
        """Configura o modelo de linguagem."""
        api_key = os.getenv("MARITALK_API_KEY")
        if not api_key:
            raise ValueError("MARITALK_API_KEY e obrigatoria")
        
        self.model = OpenAILike(
            id="sabia-3",
            name="Maritaca Sabia 3",
            api_key=api_key,
            base_url="https://chat.maritaca.ai/api",
            temperature=0,
        )
    
    def _setup_embedder(self):
        """Configura o embedder."""
        self.embedder = SentenceTransformerEmbedder()
    
    def _setup_vector_db(self):
        """Configura o banco vetorial."""
        self.vector_db = LanceDb(
            table_name="recipes",
            uri="lancedb",
            embedder=self.embedder,
        )
    
    def _setup_knowledge_base(self):
        """Configura a base de conhecimento."""
        self.knowledge_base = PDFKnowledgeBase(
            path=self.pdf_folder,
            vector_db=self.vector_db,
        )
    
    def _setup_storage(self):
        """Configura o armazenamento SQLite."""
        self.storage = SqliteStorage(
            table_name=self.table_name,
            db_file=self.db_file,
        )
    
    def _setup_agent(self):
        """Configura o agente."""
        self.agent = Agent(
            model=self.model,
            name="RAG Agent",
            knowledge=self.knowledge_base,
            storage=self.storage,
            session_id=self.session_id,
            search_knowledge=True,
            instructions="""Voce e um assistente inteligente.
Responda perguntas usando o conhecimento disponivel.
Seja preciso e forneca informacoes uteis.""",
        )
    
    def load_documents(self):
        """Carrega os documentos na base de conhecimento."""
        self.knowledge_base.load()
    
    def ask(self, question: str, stream: bool = True):
        """
        Faz uma pergunta ao agente.
        
        Args:
            question: A pergunta
            stream: Se deve usar streaming na resposta
        """
        if stream:
            self.agent.print_response(question, stream=True)
        else:
            response = self.agent.run(question)
            return response.content
    
    def run_interactive(self):
        """Executa modo interativo."""
        print("Sistema RAG SQLite - Modo Interativo")
        print("Digite 'sair' para encerrar\n")
        
        while True:
            question = input("\nPergunta: ").strip()
            
            if question.lower() in ['sair', 'exit', 'quit']:
                break
            
            if question:
                print("\nResposta:")
                self.ask(question)


# Exemplo de uso
if __name__ == "__main__":
    rag = RagSQLITE()
    rag.load_documents()
    rag.run_interactive()
