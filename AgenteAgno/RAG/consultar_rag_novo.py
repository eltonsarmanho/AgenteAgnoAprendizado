"""
Consultador de Pares Pergunta/Resposta do RAG
==============================================

Script para consultar, visualizar e exportar pares pergunta/resposta
armazenados no banco SQLite do RagSQLITEGemini.

Características:
- Menu interativo com 5 opções
- Busca por palavra-chave
- Exportação para JSON e TXT
- Análise estatística
"""

import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime

class ConsultadorRAG:
    """Classe para consultar pares pergunta/resposta do RAG."""
    
    def __init__(self, db_file: str = "data.db"):
        """
        Inicializa o consultador.
        
        Args:
            db_file: Caminho do arquivo SQLite
        """
        self.db_file = db_file
        self.conexao = None
    
    def conectar(self):
        """Conecta ao banco de dados SQLite."""
        try:
            self.conexao = sqlite3.connect(self.db_file)
            self.conexao.row_factory = sqlite3.Row
            print(f"✅ Conectado ao banco: {self.db_file}")
        except Exception as e:
            print(f"❌ Erro ao conectar: {e}")
            raise
    
    def desconectar(self):
        """Desconecta do banco de dados."""
        if self.conexao:
            self.conexao.close()
            print("✅ Desconectado do banco")
    
    def listar_sessoes(self) -> List[Dict]:
        """
        Lista todas as sessões disponíveis.
        
        Returns:
            Lista de dicionários com informações das sessões
        """
        try:
            cursor = self.conexao.cursor()
            cursor.execute("SELECT session_id, user_id, created_at FROM agno_sessions ORDER BY created_at DESC")
            sessoes = []
            for row in cursor.fetchall():
                sessoes.append({
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'created_at': row['created_at']
                })
            return sessoes
        except Exception as e:
            print(f"❌ Erro ao listar sessões: {e}")
            return []
    
    def obter_dados_sessao(self, session_id: str) -> Dict:
        """
        Obtém dados completos de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Dicionário com dados da sessão
        """
        try:
            cursor = self.conexao.cursor()
            cursor.execute("SELECT * FROM agno_sessions WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            
            if row:
                return {
                    'session_id': row['session_id'],
                    'user_id': row['user_id'],
                    'created_at': row['created_at'],
                    'runs': row['runs']
                }
            return {}
        except Exception as e:
            print(f"❌ Erro ao obter dados: {e}")
            return {}
    
    def extrair_pares_pergunta_resposta(self, session_id: str) -> List[Dict]:
        """
        Extrai pares pergunta/resposta de uma sessão.
        
        Args:
            session_id: ID da sessão
            
        Returns:
            Lista de pares {pergunta, resposta, ...}
        """
        try:
            dados = self.obter_dados_sessao(session_id)
            if not dados:
                return []
            
            # Parsear o JSON dos runs (pode ser string ou já ser dict)
            runs_data = dados.get('runs')
            
            # Se for string, fazer parse
            if isinstance(runs_data, str):
                try:
                    runs = json.loads(runs_data)
                except:
                    return []
            else:
                runs = runs_data if runs_data else []
            
            # Extrair pares
            pares = []
            for i, run in enumerate(runs, 1):
                try:
                    # A pergunta pode estar em input.input_content
                    pergunta = ""
                    if isinstance(run.get('input'), dict):
                        pergunta = run['input'].get('input_content', '')
                    elif isinstance(run.get('input'), str):
                        input_data = json.loads(run['input'])
                        pergunta = input_data.get('input_content', '')
                    
                    # A resposta está em content
                    resposta = run.get('content', '')
                    
                    par = {
                        'run_id': run.get('run_id', ''),
                        'session_id': session_id,
                        'numero': i,
                        'pergunta': pergunta,
                        'resposta': resposta,
                        'timestamp': run.get('created_at', ''),
                        'user_id': dados.get('user_id', ''),
                        'model': run.get('model', '')
                    }
                    
                    pares.append(par)
                except Exception as e:
                    print(f"⚠️  Erro ao processar run {i}: {e}")
                    continue
            
            return pares
        except Exception as e:
            print(f"❌ Erro ao extrair pares: {e}")
            return []
    
    def buscar_pares_por_palavra(self, palavra: str) -> List[Dict]:
        """
        Busca pares por palavra-chave (em pergunta e resposta).
        
        Args:
            palavra: Palavra-chave para buscar
            
        Returns:
            Lista de pares encontrados
        """
        try:
            sessoes = self.listar_sessoes()
            resultados = []
            palavra_lower = palavra.lower()
            
            for sessao in sessoes:
                pares = self.extrair_pares_pergunta_resposta(sessao['session_id'])
                for par in pares:
                    if (palavra_lower in par['pergunta'].lower() or 
                        palavra_lower in par['resposta'].lower()):
                        resultados.append(par)
            
            return resultados
        except Exception as e:
            print(f"❌ Erro ao buscar: {e}")
            return []
    
    def exportar_json(self, pares: List[Dict], nome_arquivo: str = "pares_pergunta_resposta.json"):
        """
        Exporta pares para JSON.
        
        Args:
            pares: Lista de pares
            nome_arquivo: Nome do arquivo de saída
        """
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                json.dump(pares, f, indent=2, ensure_ascii=False)
            print(f"✅ Exportados {len(pares)} pares para '{nome_arquivo}'")
        except Exception as e:
            print(f"❌ Erro ao exportar JSON: {e}")
    
    def exportar_txt(self, pares: List[Dict], nome_arquivo: str = "pares_pergunta_resposta.txt"):
        """
        Exporta pares para TXT formatado.
        
        Args:
            pares: Lista de pares
            nome_arquivo: Nome do arquivo de saída
        """
        try:
            with open(nome_arquivo, 'w', encoding='utf-8') as f:
                f.write("📋 PARES PERGUNTA/RESPOSTA - RAG\n")
                f.write("=" * 100 + "\n\n")
                
                for par in pares:
                    f.write(f"{par['numero']}. ❓ PERGUNTA:\n")
                    f.write("-" * 100 + "\n")
                    f.write(f"{par['pergunta']}\n\n")
                    
                    f.write(f"   🤖 RESPOSTA:\n")
                    f.write("-" * 100 + "\n")
                    f.write(f"{par['resposta']}\n\n")
                    
                    f.write(f"   📊 Meta: run_id={par['run_id']}, timestamp={par['timestamp']}, model={par['model']}\n")
                    f.write("=" * 100 + "\n\n")
            
            print(f"✅ Exportados {len(pares)} pares para '{nome_arquivo}'")
        except Exception as e:
            print(f"❌ Erro ao exportar TXT: {e}")
    
    def listar_modelos(self) -> Dict[str, int]:
        """
        Lista modelos utilizados e contagem de pares.
        
        Returns:
            Dicionário {modelo: contagem}
        """
        try:
            sessoes = self.listar_sessoes()
            modelos = {}
            
            for sessao in sessoes:
                pares = self.extrair_pares_pergunta_resposta(sessao['session_id'])
                for par in pares:
                    modelo = par['model']
                    modelos[modelo] = modelos.get(modelo, 0) + 1
            
            return modelos
        except Exception as e:
            print(f"❌ Erro ao listar modelos: {e}")
            return {}
    
    def menu_interativo(self):
        """Menu interativo com 5 opções."""
        while True:
            print("\n" + "=" * 60)
            print("📋 CONSULTADOR DE PARES PERGUNTA/RESPOSTA")
            print("=" * 60)
            print("1. Listar todas as sessões")
            print("2. Visualizar pares de uma sessão")
            print("3. Buscar por palavra-chave")
            print("4. Ver estatísticas")
            print("5. Exportar todos os pares")
            print("0. Sair")
            print("=" * 60)
            
            opcao = input("Escolha uma opção: ").strip()
            
            if opcao == "0":
                print("✅ Saindo...")
                break
            
            elif opcao == "1":
                sessoes = self.listar_sessoes()
                if sessoes:
                    print("\n📋 Todas as Sessões:\n")
                    for i, sessao in enumerate(sessoes, 1):
                        pares = self.extrair_pares_pergunta_resposta(sessao['session_id'])
                        print(f"{i}. {sessao['session_id']}")
                        print(f"   Usuário: {sessao['user_id']}")
                        print(f"   Data: {sessao['created_at']}")
                        print(f"   ✓ {len(pares)} pares pergunta/resposta\n")
                else:
                    print("❌ Nenhuma sessão encontrada")
            
            elif opcao == "2":
                try:
                    num = int(input("Digite o número da sessão: "))
                    sessoes = self.listar_sessoes()
                    if 1 <= num <= len(sessoes):
                        session_id = sessoes[num - 1]['session_id']
                        pares = self.extrair_pares_pergunta_resposta(session_id)
                        
                        print(f"\n💬 Pares da Sessão '{session_id}':")
                        print("=" * 100)
                        
                        for par in pares:
                            print(f"\n{par['numero']}. ❓ PERGUNTA:")
                            print("-" * 100)
                            print(par['pergunta'])
                            print(f"\n   🤖 RESPOSTA:")
                            print("-" * 100)
                            print(par['resposta'])
                            print(f"\n   📊 Meta: {par['model']} | {par['timestamp']}")
                            print("=" * 100)
                    else:
                        print("❌ Número inválido")
                except ValueError:
                    print("❌ Digite um número válido")
            
            elif opcao == "3":
                palavra = input("Digite a palavra-chave: ").strip()
                pares = self.buscar_pares_por_palavra(palavra)
                if pares:
                    print(f"\n🔍 Encontrados {len(pares)} pares com '{palavra}':\n")
                    for par in pares:
                        print(f"Session: {par['session_id']}")
                        print(f"P: {par['pergunta'][:80]}...")
                        print(f"R: {par['resposta'][:80]}...\n")
                else:
                    print(f"❌ Nenhum par encontrado com '{palavra}'")
            
            elif opcao == "4":
                sessoes = self.listar_sessoes()
                modelos = self.listar_modelos()
                total_pares = sum(len(self.extrair_pares_pergunta_resposta(s['session_id'])) for s in sessoes)
                
                print(f"\n📊 ESTATÍSTICAS:")
                print(f"  📋 Sessões: {len(sessoes)}")
                print(f"  💬 Total de Pares: {total_pares}")
                print(f"  🤖 Modelos utilizados: {len(modelos)}")
                print(f"\n  Detalhes por modelo:")
                for modelo, count in sorted(modelos.items(), key=lambda x: x[1], reverse=True):
                    print(f"    - {modelo}: {count} pares")
            
            elif opcao == "5":
                sessoes = self.listar_sessoes()
                todos_pares = []
                for sessao in sessoes:
                    pares = self.extrair_pares_pergunta_resposta(sessao['session_id'])
                    todos_pares.extend(pares)
                
                self.exportar_json(todos_pares)
                self.exportar_txt(todos_pares)
            
            else:
                print("❌ Opção inválida")


def main():
    """Função principal."""
    consultador = ConsultadorRAG(db_file="data.db")
    consultador.conectar()
    
    try:
        consultador.menu_interativo()
    finally:
        consultador.desconectar()


if __name__ == "__main__":
    main()
