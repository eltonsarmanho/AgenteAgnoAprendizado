import pandas as pd
import unicodedata
import re
import sys
import os
import functools

# Configuração de paths para deploy EC2
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

# Caminhos dos arquivos de dados (relativos ao Dashboard)
ARQ_TDE = os.path.join(os.path.dirname(__file__), 'TDE_longitudinal.csv')
ARQ_VOC = os.path.join(os.path.dirname(__file__), 'vocabulario_longitudinal.csv')

@functools.lru_cache(maxsize=4)
def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def normalize_name(s: str) -> str:
    if pd.isna(s):
        return ''
    s = str(s).strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r'\s+', ' ', s)
    return s

def anonimizar_estudante(id_unico: str, nome_completo: str) -> str:
    """
    Cria identificador anonimizado para estudante seguindo LGPD.
    
    Formato: [PRIMEIRAS_6_LETRAS_ID] - [INICIAIS_NOME]
    Exemplo: "56E9C8 - AAS" para ABIGAIL ALVES DOS SANTOS (ID: 56E9C824252F)
    
    Args:
        id_unico: ID único do estudante (ex: 56E9C824252F)
        nome_completo: Nome completo do estudante
        
    Returns:
        String anonimizada no formato especificado
    """
    if pd.isna(id_unico) or pd.isna(nome_completo):
        return "DESCONHECIDO"
    
    # Pegar primeiros 6 caracteres do ID
    id_parcial = str(id_unico)[:6]
    
    # Criar iniciais do nome (primeira letra de cada palavra)
    nome_normalizado = normalize_name(nome_completo)
    palavras = nome_normalizado.split()
    
    # Pegar primeira letra de cada palavra (máximo 4 iniciais para não ficar muito longo)
    iniciais = ''.join([p[0] for p in palavras if p])[:4]
    
    return f"{id_parcial} - {iniciais}"

def extract_year(turma: str):
    if pd.isna(turma):
        return None
    t = str(turma).upper()
    m = re.search(r'(6|7|8|9)\s*(?:º|°)?\s*ANO', t)
    if m:
        return int(m.group(1))
    m2 = re.search(r'\b(6|7|8|9)\b', t)
    if m2:
        return int(m2.group(1))
    return None

def create_coorte_origem(df):
    """
    Cria coluna de Coorte_Origem baseada na primeira fase em que cada aluno participou.
    
    Coortes representam o ponto de entrada do aluno no programa:
    - Coorte 1: Alunos que começaram na Fase 2 (primeira fase de avaliação)
    - Coorte 2: Alunos que começaram na Fase 3 (entraram mais tarde)
    - Coorte 3: Alunos que começaram na Fase 4 (última fase de entrada)
    
    A coorte é determinada pela menor fase em que o ID_Unico aparece nos dados,
    garantindo rastreamento longitudinal correto mesmo se o aluno mudar de turma.
    """
    # Para cada ID_Unico, encontrar a menor fase (primeira participação)
    primeira_participacao = df.groupby('ID_Unico')['Fase'].min().reset_index()
    primeira_participacao = primeira_participacao.rename(columns={'Fase': 'Primeira_Fase'})
    
    # Mapear fase inicial para número de coorte
    # Fase 2 → Coorte 1, Fase 3 → Coorte 2, Fase 4 → Coorte 3
    def fase_para_coorte(fase):
        if pd.isna(fase):
            return None
        fase_num = int(fase)
        if fase_num == 2:
            return 'Coorte 1'
        elif fase_num == 3:
            return 'Coorte 2'
        elif fase_num == 4:
            return 'Coorte 3'
        else:
            return f'Coorte {fase_num - 1}'  # Fallback genérico
    
    primeira_participacao['Coorte_Origem'] = primeira_participacao['Primeira_Fase'].apply(fase_para_coorte)
    
    # Merge para trazer coorte para todos os registros do aluno
    df = df.merge(primeira_participacao[['ID_Unico', 'Coorte_Origem']], on='ID_Unico', how='left')
    
    # Também criar coluna auxiliar com a turma original da primeira fase (útil para debug)
    primeira_turma = df.merge(primeira_participacao[['ID_Unico', 'Primeira_Fase']], on='ID_Unico', how='left')
    turma_origem_map = {}
    for id_unico in primeira_turma['ID_Unico'].unique():
        aluno_dados = primeira_turma[primeira_turma['ID_Unico'] == id_unico]
        primeira_fase_aluno = aluno_dados['Primeira_Fase'].iloc[0]
        turma_na_primeira_fase = aluno_dados[aluno_dados['Fase'] == primeira_fase_aluno]['Turma_Origem'].iloc[0] if 'Turma_Origem' in aluno_dados.columns else None
        turma_origem_map[id_unico] = turma_na_primeira_fase
    
    df['Turma_Primeira_Fase'] = df['ID_Unico'].map(turma_origem_map)
    
    return df

def get_datasets():
    tde = load_csv(ARQ_TDE)
    vocab = load_csv(ARQ_VOC)
    
    # Processamento TDE
    if 'NomeNorm' not in tde.columns:
        tde['NomeNorm'] = tde['Nome'].apply(normalize_name)
    if 'Ano' not in tde.columns:
        tde['Ano'] = tde['Turma'].apply(extract_year)
    tde = create_coorte_origem(tde)
    
    # Criar identificador anonimizado (LGPD)
    if 'ID_Anonimizado' not in tde.columns:
        tde['ID_Anonimizado'] = tde.apply(
            lambda row: anonimizar_estudante(row['ID_Unico'], row['Nome']), 
            axis=1
        )
    
    # Processamento Vocabulário
    if 'NomeNorm' not in vocab.columns:
        vocab['NomeNorm'] = vocab['Nome'].apply(normalize_name)
    if 'Ano' not in vocab.columns:
        vocab['Ano'] = vocab['Turma'].apply(extract_year)
    vocab = create_coorte_origem(vocab)
    
    # Criar identificador anonimizado (LGPD)
    if 'ID_Anonimizado' not in vocab.columns:
        vocab['ID_Anonimizado'] = vocab.apply(
            lambda row: anonimizar_estudante(row['ID_Unico'], row['Nome']), 
            axis=1
        )
    
    return tde, vocab


