"""
Script para extrair dados de exercícios e vídeos de um arquivo Excel com múltiplas abas.
Gera um CSV com as colunas: Exercício, Vídeo
"""

import pandas as pd
import os

def extrair_exercicios_videos(arquivo_excel, arquivo_saida='exercicios_videos.csv'):
    """
    Lê arquivo Excel com múltiplas abas e extrai colunas Exercício e Vídeo.
    
    Args:
        arquivo_excel (str): Caminho do arquivo Excel de origem
        arquivo_saida (str): Nome do arquivo CSV de saída
    """
    try:
        # Ler todas as abas do arquivo Excel
        excel_file = pd.ExcelFile(arquivo_excel)
        
        # Lista para armazenar os dados de todas as abas
        dados_completos = []
        
        # Iterar por todas as abas
        for aba in excel_file.sheet_names:
            print(f"Processando aba: {aba}")
            
            # Ler a aba atual
            df = pd.read_excel(excel_file, sheet_name=aba)
            
            # Verificar se as colunas existem
            if 'Exercício' in df.columns and 'Vídeo' in df.columns:
                # Extrair apenas as colunas de interesse
                df_filtrado = df[['Exercício', 'Vídeo']].copy()
                
                # Remover linhas com valores nulos em ambas as colunas
                df_filtrado = df_filtrado.dropna(subset=['Exercício', 'Vídeo'], how='all')
                
                # Marcar se veio da aba de alongamentos
                df_filtrado['alongamento'] = 1 if 'Alongamentos' in aba else 0
                
                # Adicionar à lista
                dados_completos.append(df_filtrado)
            else:
                print(f"Aviso: Aba '{aba}' não possui as colunas 'Exercício' e/ou 'Vídeo'")
        
        # Concatenar todos os dados
        if dados_completos:
            df_final = pd.concat(dados_completos, ignore_index=True)
            
            # Manter apenas nomes de exercícios únicos (primeira ocorrência)
            df_final = df_final.drop_duplicates(subset=['Exercício'], keep='first')
            
            # Remover linhas com valores nulos
            df_final = df_final.dropna()
            
            # Salvar como CSV
            df_final.to_csv(arquivo_saida, index=False, encoding='utf-8-sig')
            
            print(f"\nArquivo CSV criado com sucesso: {arquivo_saida}")
            print(f"Total de registros: {len(df_final)}")
            
            return df_final
        else:
            print("Nenhum dado foi encontrado nas abas do arquivo.")
            return None
            
    except FileNotFoundError:
        print(f"Erro: Arquivo '{arquivo_excel}' não encontrado.")
    except Exception as e:
        print(f"Erro ao processar arquivo: {str(e)}")
        return None

if __name__ == "__main__":
    # Configurar o caminho do arquivo Excel
    arquivo_entrada = "Classificacao/Treino.xlsx"  # Altere para o nome do seu arquivo
    
    # Verificar se o arquivo existe
    if os.path.exists(arquivo_entrada):
        df_resultado = extrair_exercicios_videos(arquivo_entrada)
        
        if df_resultado is not None:
            print("\nPrimeiras linhas do resultado:")
            print(df_resultado.head())
    else:
        print(f"Por favor, coloque o arquivo Excel '{arquivo_entrada}' no mesmo diretório do script.")
        print("Ou altere a variável 'arquivo_entrada' com o caminho correto.")
