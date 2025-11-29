"""
Test Embedding - Testes do sistema de embeddings
================================================

Testes para validar o funcionamento do sistema de embeddings
e da base vetorial LanceDB.
"""

from agno.embedder.sentence_transformer import SentenceTransformerEmbedder
from agno.vectordb.lancedb import LanceDb
import os


def test_embedder_initialization():
    """Testa inicializacao do embedder."""
    print("Testando inicializacao do embedder...")
    
    try:
        embedder = SentenceTransformerEmbedder()
        print("  ✅ Embedder inicializado com sucesso")
        return embedder
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return None


def test_embedding_generation(embedder):
    """Testa geracao de embeddings."""
    print("\nTestando geracao de embeddings...")
    
    textos = [
        "Este e um texto de exemplo para teste.",
        "Outro texto diferente para comparacao.",
        "Machine learning e inteligencia artificial.",
    ]
    
    for texto in textos:
        try:
            embedding = embedder.get_embedding(texto)
            print(f"  ✅ Texto: '{texto[:30]}...' -> dim={len(embedding)}")
        except Exception as e:
            print(f"  ❌ Erro ao gerar embedding: {e}")


def test_vector_db():
    """Testa conexao com LanceDB."""
    print("\nTestando conexao com LanceDB...")
    
    try:
        embedder = SentenceTransformerEmbedder()
        vector_db = LanceDb(
            table_name="test_table",
            uri="lancedb",
            embedder=embedder,
        )
        print("  ✅ LanceDB conectado com sucesso")
        return vector_db
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return None


def test_similarity_search():
    """Testa busca por similaridade."""
    print("\nTestando busca por similaridade...")
    
    try:
        embedder = SentenceTransformerEmbedder()
        
        # Gerar embeddings para comparacao
        texto1 = "O gato dormiu no sofa"
        texto2 = "O felino descansou no movel"
        texto3 = "Programacao em Python"
        
        emb1 = embedder.get_embedding(texto1)
        emb2 = embedder.get_embedding(texto2)
        emb3 = embedder.get_embedding(texto3)
        
        # Calcular similaridade (dot product simplificado)
        def cosine_sim(a, b):
            import numpy as np
            a = np.array(a)
            b = np.array(b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        
        sim_12 = cosine_sim(emb1, emb2)
        sim_13 = cosine_sim(emb1, emb3)
        
        print(f"  Similaridade '{texto1}' <-> '{texto2}': {sim_12:.4f}")
        print(f"  Similaridade '{texto1}' <-> '{texto3}': {sim_13:.4f}")
        
        if sim_12 > sim_13:
            print("  ✅ Textos semanticamente similares tem maior score")
        else:
            print("  ⚠️ Resultado inesperado na similaridade")
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")


def main():
    """Executa todos os testes."""
    print("=" * 60)
    print("Testes do Sistema de Embeddings")
    print("=" * 60)
    
    embedder = test_embedder_initialization()
    
    if embedder:
        test_embedding_generation(embedder)
    
    test_vector_db()
    test_similarity_search()
    
    print("\n" + "=" * 60)
    print("Testes finalizados")
    print("=" * 60)


if __name__ == "__main__":
    main()
