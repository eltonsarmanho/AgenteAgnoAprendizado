"""
Exemplos de Uso: Consultador de Pares Pergunta/Resposta
========================================================

Este arquivo demonstra 5 formas diferentes de usar o ConsultadorRAG
para extrair, buscar, filtrar e analisar pares pergunta/resposta.
"""

import json
from consultar_rag_novo import ConsultadorRAG

def exemplo_1_extrair_pares():
    """Exemplo 1: Extrair todos os pares de uma sessão"""
    print("\n" + "="*80)
    print("📚 EXEMPLO 1: Extrair Pares de Uma Sessão")
    print("="*80)
    
    consultador = ConsultadorRAG(db_file="../data.db")
    consultador.conectar()
    
    # Obter primeira sessão
    sessoes = consultador.listar_sessoes()
    if sessoes:
        session_id = sessoes[0]['session_id']
        pares = consultador.extrair_pares_pergunta_resposta(session_id)
        
        print(f"\n✅ Extraídos {len(pares)} pares da sessão '{session_id}':\n")
        for par in pares[:3]:  # Mostrar apenas os 3 primeiros
            print(f"P: {par['pergunta'][:60]}...")
            print(f"R: {par['resposta'][:60]}...\n")
    
    consultador.desconectar()


def exemplo_2_buscar_palavra_chave():
    """Exemplo 2: Buscar pares por palavra-chave"""
    print("\n" + "="*80)
    print("🔍 EXEMPLO 2: Buscar Pares por Palavra-Chave")
    print("="*80)
    
    consultador = ConsultadorRAG(db_file="../data.db")
    consultador.conectar()
    
    # Buscar palavra-chave
    palavra = "professores"
    pares = consultador.buscar_pares_por_palavra(palavra)
    
    print(f"\n✅ Encontrados {len(pares)} pares com '{palavra}':\n")
    for par in pares[:3]:
        print(f"Session: {par['session_id']}")
        print(f"P: {par['pergunta'][:60]}...")
        print(f"R: {par['resposta'][:60]}...\n")
    
    consultador.desconectar()


def exemplo_3_exportar_json():
    """Exemplo 3: Exportar pares para JSON customizado"""
    print("\n" + "="*80)
    print("💾 EXEMPLO 3: Exportar Pares para JSON")
    print("="*80)
    
    consultador = ConsultadorRAG(db_file="../data.db")
    consultador.conectar()
    
    # Extrair todos os pares
    sessoes = consultador.listar_sessoes()
    todos_pares = []
    for sessao in sessoes:
        pares = consultador.extrair_pares_pergunta_resposta(sessao['session_id'])
        todos_pares.extend(pares)
    
    # Exportar
    consultador.exportar_json(todos_pares, "pares_customizado.json")
    print(f"✅ Total de pares exportados: {len(todos_pares)}")
    
    consultador.desconectar()


def exemplo_4_filtrar_por_modelo():
    """Exemplo 4: Filtrar pares por modelo de IA"""
    print("\n" + "="*80)
    print("🤖 EXEMPLO 4: Filtrar Pares por Modelo de IA")
    print("="*80)
    
    consultador = ConsultadorRAG(db_file="../data.db")
    consultador.conectar()
    
    # Extrair todos os pares
    sessoes = consultador.listar_sessoes()
    todos_pares = []
    for sessao in sessoes:
        pares = consultador.extrair_pares_pergunta_resposta(sessao['session_id'])
        todos_pares.extend(pares)
    
    # Agrupar por modelo
    modelos = {}
    for par in todos_pares:
        modelo = par['model']
        if modelo not in modelos:
            modelos[modelo] = []
        modelos[modelo].append(par)
    
    # Mostrar estatísticas
    print(f"\n✅ Modelos encontrados:\n")
    for modelo, pares in sorted(modelos.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  🤖 {modelo}: {len(pares)} pares")
    
    consultador.desconectar()


def exemplo_5_analise_frequencia():
    """Exemplo 5: Análise de frequência de palavras"""
    print("\n" + "="*80)
    print("📊 EXEMPLO 5: Análise de Frequência de Palavras")
    print("="*80)
    
    consultador = ConsultadorRAG(db_file="../data.db")
    consultador.conectar()
    
    # Extrair todos os pares
    sessoes = consultador.listar_sessoes()
    todos_pares = []
    for sessao in sessoes:
        pares = consultador.extrair_pares_pergunta_resposta(sessao['session_id'])
        todos_pares.extend(pares)
    
    # Contar frequência de palavras
    palavras = {}
    for par in todos_pares:
        texto = (par['pergunta'] + " " + par['resposta']).lower()
        for palavra in texto.split():
            # Filtrar palavras pequenas
            if len(palavra) > 5:
                palavra = palavra.strip('.,!?;:')
                palavras[palavra] = palavras.get(palavra, 0) + 1
    
    # Mostrar top 10
    print(f"\n✅ Top 10 Palavras Mais Frequentes:\n")
    for i, (palavra, freq) in enumerate(sorted(palavras.items(), key=lambda x: x[1], reverse=True)[:10], 1):
        print(f"  {i}. {palavra}: {freq} ocorrências")
    
    consultador.desconectar()


if __name__ == "__main__":
    print("\n🚀 EXEMPLOS DE USO: CONSULTADOR RAG\n")
    
    try:
        exemplo_1_extrair_pares()
        exemplo_2_buscar_palavra_chave()
        exemplo_3_exportar_json()
        exemplo_4_filtrar_por_modelo()
        exemplo_5_analise_frequencia()
        
        print("\n" + "="*80)
        print("✅ TODOS OS EXEMPLOS EXECUTADOS COM SUCESSO!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}\n")
