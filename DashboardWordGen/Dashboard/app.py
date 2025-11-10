import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from data_loader import get_datasets
import unicodedata, re, math
import numpy as np
from datetime import datetime, date
import altair as alt

st.set_page_config(
    page_title="Dashboard Longitudinal WordGen", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ========== ESTILOS CSS CUSTOMIZADOS ==========
st.markdown("""
<style>
    /* Ajustar alinhamento vertical do checkbox */
    div[data-testid="stCheckbox"] {
        padding-top: 1.5rem;
        margin-bottom: 0;
    }
    
    /* Melhorar espaçamento do label do checkbox */
    div[data-testid="stCheckbox"] label {
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* Reduzir espaçamento entre elementos no expander */
    div[data-testid="stExpander"] div[data-testid="stVerticalBlock"] > div {
        gap: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ========== FUNÇÕES AUXILIARES ==========
def normalizar_turma(turma_original: str) -> str:
    """Normaliza valores de turma para formato padrão (5° Ano, 6° Ano, etc.)"""
    if pd.isna(turma_original):
        return turma_original
    
    turma_str = str(turma_original).upper().strip()
    
    if any(x in turma_str for x in ['5', 'QUINTO']):
        return '5° Ano'
    elif any(x in turma_str for x in ['6', 'SEXTO']):
        return '6° Ano'
    elif any(x in turma_str for x in ['7', 'SETIMO', 'SÉTIMO']):
        return '7° Ano'
    elif any(x in turma_str for x in ['8', 'OITAVO']):
        return '8° Ano'
    elif any(x in turma_str for x in ['9', 'NONO']):
        return '9° Ano'
    else:
        return turma_original

@st.cache_data(show_spinner=False)
def load_data():
    """Carrega e normaliza os datasets principais."""
    tde, vocab = get_datasets()
    
    if 'Turma' in tde.columns:
        tde['Turma_Original'] = tde['Turma'].copy()
        tde['Turma'] = tde['Turma'].apply(normalizar_turma)
    
    if 'Turma' in vocab.columns:
        vocab['Turma_Original'] = vocab['Turma'].copy()
        vocab['Turma'] = vocab['Turma'].apply(normalizar_turma)
    
    return tde, vocab

def calcular_idade(data_nascimento_str, data_referencia=None):
    """
    Calcula idade a partir da data de nascimento.
    
    Args:
        data_nascimento_str: String com data de nascimento (formato: DD/MM/YYYY ou YYYY-MM-DD)
        data_referencia: Data de referência para cálculo (default: hoje)
    
    Returns:
        Idade em anos (int) ou None se não puder calcular
    """
    if pd.isna(data_nascimento_str) or data_nascimento_str == '':
        return None
    
    if data_referencia is None:
        data_referencia = date.today()
    
    try:
        # Tentar formato DD/MM/YYYY
        if '/' in str(data_nascimento_str):
            data_nasc = datetime.strptime(str(data_nascimento_str), '%d/%m/%Y').date()
        # Tentar formato YYYY-MM-DD
        elif '-' in str(data_nascimento_str):
            data_nasc = datetime.strptime(str(data_nascimento_str), '%Y-%m-%d').date()
        else:
            return None
        
        # Calcular idade
        idade = data_referencia.year - data_nasc.year
        
        # Ajustar se ainda não fez aniversário este ano
        if (data_referencia.month, data_referencia.day) < (data_nasc.month, data_nasc.day):
            idade -= 1
        
        return idade if idade >= 0 else None
        
    except (ValueError, AttributeError):
        return None

def criar_faixas_etarias(idade):
    """
    Cria faixas etárias para agrupamento.
    
    Args:
        idade: Idade em anos
        
    Returns:
        String com faixa etária ou None
    """
    if pd.isna(idade) or idade is None:
        return None
    
    if idade < 10:
        return "< 10 anos"
    elif idade < 12:
        return "10-11 anos"
    elif idade < 14:
        return "12-13 anos"
    elif idade < 16:
        return "14-15 anos"
    else:
        return "≥ 16 anos"

@st.cache_data(show_spinner=False)
def carregar_palavras_ensinadas():
    """Carrega as palavras ensinadas de todas as fases."""
    import json
    import os
    
    palavras_por_fase = {}
    base_path = os.path.join(os.path.dirname(__file__), '..', 'Data')
    
    for fase in [2, 3, 4]:
        arquivo_path = os.path.join(base_path, f'Fase {fase}', 'PalavrasEnsinadasVocabulario.json')
        try:
            if os.path.exists(arquivo_path):
                with open(arquivo_path, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    # Tenta ambas as chaves possíveis
                    palavras = dados.get('palavras_ensinadas', dados.get('Palavras Ensinadas', []))
                    palavras_por_fase[fase] = set(palavras)
        except Exception as e:
            st.warning(f"Erro ao carregar palavras ensinadas da Fase {fase}: {e}")
            palavras_por_fase[fase] = set()
    
    return palavras_por_fase

def normalizar_palavra(palavra: str) -> str:
    """Normaliza palavra para comparação (remove acentos, lowercase, etc)."""
    if not palavra:
        return ""
    # Remove acentos
    palavra_norm = unicodedata.normalize('NFD', str(palavra))
    palavra_norm = ''.join(char for char in palavra_norm if unicodedata.category(char) != 'Mn')
    # Lowercase e strip
    palavra_norm = palavra_norm.lower().strip()
    # Remove pontuação no final
    palavra_norm = palavra_norm.rstrip('.,;:!?')
    return palavra_norm

def palavra_ensinada_match(palavra_teste: str, palavras_ensinadas: set) -> bool:
    """Verifica se palavra do teste corresponde a alguma palavra ensinada.
    
    Usa correspondência exata normalizada e correspondência de raiz com no mínimo 6 caracteres.
    """
    if not palavra_teste or not palavras_ensinadas:
        return False
    
    palavra_teste_norm = normalizar_palavra(palavra_teste)
    
    # Verificar correspondência exata normalizada
    for palavra_ensinada in palavras_ensinadas:
        palavra_ensinada_norm = normalizar_palavra(palavra_ensinada)
        
        # Correspondência exata
        if palavra_teste_norm == palavra_ensinada_norm:
            return True
        
        # Correspondência de raiz (primeiras 6 letras) - mais rigoroso
        if len(palavra_teste_norm) >= 6 and len(palavra_ensinada_norm) >= 6:
            if palavra_teste_norm[:6] == palavra_ensinada_norm[:6]:
                return True
    
    return False

def calcular_d_cohen(df_in: pd.DataFrame, col_pre: str = 'Score_Pre', col_pos: str = 'Score_Pos') -> float:
    """Calcula d de Cohen."""
    if df_in is None or df_in.empty:
        return float('nan')
    pre = df_in[col_pre].dropna()
    pos = df_in[col_pos].dropna()
    n_pre, n_pos = len(pre), len(pos)
    if n_pre < 2 or n_pos < 2:
        return float('nan')
    m_pre, m_pos = pre.mean(), pos.mean()
    sd_pre, sd_pos = pre.std(ddof=1), pos.std(ddof=1)
    if (sd_pre == 0 and sd_pos == 0):
        return float('nan')
    pooled = math.sqrt(((n_pre - 1) * sd_pre**2 + (n_pos - 1) * sd_pos**2) / (n_pre + n_pos - 2)) if (n_pre + n_pos - 2) > 0 else float('nan')
    if pooled == 0 or np.isnan(pooled):
        return float('nan')
    return (m_pos - m_pre) / pooled

def classificar_geral(d: float) -> str:
    if np.isnan(d):
        return 'Sem dados'
    ad = abs(d)
    if ad < 0.2:
        return 'Trivial'
    if ad < 0.5:
        return 'Pequeno'
    if ad < 0.8:
        return 'Médio'
    return 'Grande'

def benchmark_especifico(d: float, prova: str) -> tuple[str, bool]:
    if np.isnan(d):
        return ('Sem dados', False)
    if prova == 'TDE':
        return ('Bom resultado' if d >= 0.40 else 'Ponto de atenção', d >= 0.40)
    return ('Impacto significativo' if d >= 0.35 else 'Ponto de atenção', d >= 0.35)

def criar_metric_card(valor, titulo, icone, cor_box=(0, 123, 255), cor_fonte=(255, 255, 255)):
    """Cria um card métrico personalizado."""
    lnk = '<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.12.1/css/all.css" crossorigin="anonymous">'
    htmlstr = f"""<p style='background-color: rgb({cor_box[0]}, {cor_box[1]}, {cor_box[2]}, 0.85); 
                            color: rgb({cor_fonte[0]}, {cor_fonte[1]}, {cor_fonte[2]}, 0.95); 
                            font-size: 18px; 
                            font-weight: 600;
                            border-radius: 10px; 
                            padding: 20px 15px; 
                            text-align: center;
                            line-height: 1.4;
                            margin: 0;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);'>
                            <i class='{icone} fa-lg' style='margin-right: 10px;'></i> {valor}
                            <br><span style='font-size: 11px; 
                            font-weight: 300;
                            opacity: 0.9;
                            margin-top: 8px;
                            display: block;'>{titulo}</span></p>"""
    return lnk + htmlstr

# ========== LOAD DATA ==========
tde_df, vocab_df = load_data()

# Calcular idade para ambos os datasets
if 'DataAniversario' in tde_df.columns:
    tde_df['Idade'] = tde_df['DataAniversario'].apply(calcular_idade)
    tde_df['FaixaEtaria'] = tde_df['Idade'].apply(criar_faixas_etarias)

if 'DataAniversario' in vocab_df.columns:
    vocab_df['Idade'] = vocab_df['DataAniversario'].apply(calcular_idade)
    vocab_df['FaixaEtaria'] = vocab_df['Idade'].apply(criar_faixas_etarias)

PROVAS = {"TDE": tde_df, "VOCABULÁRIO": vocab_df}

# ========== HEADER ==========
st.title("📊 Dashboard Longitudinal - WordGen")
st.markdown("**Análise Comparativa de Desempenho: Pré-Teste vs Pós-Teste**")
st.markdown("---")

# ========== FILTROS NO TOPO (TOP BAR) ==========
with st.expander("🔍 **FILTROS DE ANÁLISE**", expanded=True):
    # LINHA ÚNICA - Filtros principais (Prova reduzida em 50%, Turma reduzida em 20%)
    col_f1, col_f2, col_f3, col_f4 = st.columns([0.5, 1, 1.5, 1.6])
    
    with col_f1:
        prova_sel = st.selectbox("📝 Prova", list(PROVAS.keys()))
        df = PROVAS[prova_sel]
    
    with col_f2:
        fases = sorted(df['Fase'].dropna().unique())
        fases_sel = st.multiselect("📅 Fase(s)", fases, default=fases)
        if fases_sel:
            df = df[df['Fase'].isin(fases_sel)]
    
    with col_f3:
        escolas = sorted(df['Escola'].dropna().unique())
        escola_sel = st.multiselect("🏫 Escola(s)", escolas, default=[])
        if escola_sel:
            df = df[df['Escola'].isin(escola_sel)]
    
    with col_f4:
        # Inicializar session_state ANTES de tudo
        if 'agregar_turmas' not in st.session_state:
            st.session_state.agregar_turmas = False
        
        # Sub-colunas: checkbox ao lado do multiselect
        sub_col1, sub_col2 = st.columns([3, 1.9])
        
        # IMPORTANTE: Processar checkbox PRIMEIRO em sub_col2
        with sub_col2:
            # Checkbox ao lado (com padding para alinhar)
            st.write("")  # Espaço para alinhar verticalmente
            # Captura o novo valor do checkbox
            novo_agregar = st.checkbox(
                "🔄 Agregar Turmas", 
                value=st.session_state.agregar_turmas, 
                key="agregar_checkbox"
            )
            # Atualiza session_state IMEDIATAMENTE
            if novo_agregar != st.session_state.agregar_turmas:
                st.session_state.agregar_turmas = novo_agregar
                st.rerun()  # Força rerun para atualizar o multiselect
        
        # Agora usa o valor atualizado do session_state
        agregar_turmas = st.session_state.agregar_turmas
        
        with sub_col1:
            # Multiselect de turmas (muda conforme checkbox)
            if agregar_turmas:
                coluna_turma = 'Turma'
                turmas_disponiveis = sorted(df['Turma'].dropna().unique())
                label_turmas = "🎓 Turma(s) - Agregadas"
            else:
                coluna_turma = 'Turma_Original'
                turmas_disponiveis = sorted(df['Turma_Original'].dropna().unique())
                label_turmas = "🎓 Turma(s) - Separadas"
            
            turmas_sel = st.multiselect(label_turmas, turmas_disponiveis, key="turmas_multiselect")
            if turmas_sel:
                df = df[df[coluna_turma].isin(turmas_sel)]
    
    # SEGUNDA LINHA - Filtros demográficos (Sexo e Idade)
    st.markdown("---")
    col_d1, col_d2, col_d3 = st.columns([1, 1.5, 2])
    
    with col_d1:
        # Filtro de Sexo
        if 'Sexo' in df.columns:
            sexos_disponiveis = sorted([s for s in df['Sexo'].dropna().unique() if s != ''])
            sexo_sel = st.multiselect("👤 Sexo", sexos_disponiveis, default=[])
            if sexo_sel:
                df = df[df['Sexo'].isin(sexo_sel)]
    
    with col_d2:
        # Filtro de Faixa Etária
        if 'FaixaEtaria' in df.columns:
            faixas_disponiveis = [f for f in ["< 10 anos", "10-11 anos", "12-13 anos", "14-15 anos", "≥ 16 anos"] 
                                  if f in df['FaixaEtaria'].unique()]
            faixa_sel = st.multiselect("🎂 Faixa Etária", faixas_disponiveis, default=[])
            if faixa_sel:
                df = df[df['FaixaEtaria'].isin(faixa_sel)]
    
    with col_d3:
        # Filtro de Idade Específica (range slider)
        if 'Idade' in df.columns:
            idades_validas = df['Idade'].dropna()
            if len(idades_validas) > 0:
                idade_min = int(idades_validas.min())
                idade_max = int(idades_validas.max())
                idade_range = st.slider(
                    "📊 Idade Específica (anos)",
                    min_value=idade_min,
                    max_value=idade_max,
                    value=(idade_min, idade_max),
                    step=1
                )
                df = df[(df['Idade'] >= idade_range[0]) & (df['Idade'] <= idade_range[1])]

st.markdown("---")

# ========== MÉTRICAS PRINCIPAIS ==========
st.subheader("📈 Resumo Estatístico")
col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(criar_metric_card(
        len(df), "Registros", "fas fa-database",
        (52, 152, 219), (255, 255, 255)
    ), unsafe_allow_html=True)

with col2:
    st.markdown(criar_metric_card(
        df['ID_Unico'].nunique(), "Alunos Únicos", "fas fa-users",
        (46, 204, 113), (255, 255, 255)
    ), unsafe_allow_html=True)

with col3:
    st.markdown(criar_metric_card(
        df['Escola'].nunique(), "Escolas", "fas fa-school",
        (155, 89, 182), (255, 255, 255)
    ), unsafe_allow_html=True)

with col4:
    turmas_count = df[coluna_turma].nunique()
    turma_label = "Turmas Agregadas" if agregar_turmas else "Turmas"
    st.markdown(criar_metric_card(
        turmas_count, turma_label, "fas fa-chalkboard-teacher",
        (230, 126, 34), (255, 255, 255)
    ), unsafe_allow_html=True)

with col5:
    d_val = calcular_d_cohen(df)
    prova_norm = 'TDE' if prova_sel.upper().startswith('TDE') else 'VOCAB'
    cls_espec, ok_flag = benchmark_especifico(d_val, prova_norm)
    
    if ok_flag:
        cor_box, cor_fonte, icone = (40, 167, 69), (255, 255, 255), "fas fa-check-circle"
    elif not np.isnan(d_val):
        cor_box, cor_fonte, icone = (255, 193, 7), (0, 0, 0), "fas fa-exclamation-triangle"
    else:
        cor_box, cor_fonte, icone = (108, 117, 125), (255, 255, 255), "fas fa-info-circle"
    
    val_str = '—' if np.isnan(d_val) else f"{d_val:.3f}"
    st.markdown(criar_metric_card(
        val_str, "Tamanho do Efeito", icone,
        cor_box, cor_fonte
    ), unsafe_allow_html=True)

st.markdown("---")

# ========== ANÁLISE DEMOGRÁFICA ==========
st.subheader("👥 Análise Demográfica")

# Criar abas para organizar visualizações demográficas
tab_dist, tab_perf = st.tabs(["📊 Distribuição", "📈 Performance por Perfil"])

with tab_dist:
    col_dist1, col_dist2 = st.columns(2, gap="large")
    
    # Gráfico 1: Distribuição por Sexo
    with col_dist1:
        with st.container(border=True):
            st.markdown("#### Distribuição por Sexo")
            
            if 'Sexo' in df.columns and not df['Sexo'].isna().all():
                # Contar alunos únicos por sexo
                dist_sexo = df.groupby('Sexo')['ID_Unico'].nunique().reset_index()
                dist_sexo.columns = ['Sexo', 'Quantidade']
                dist_sexo['Percentual'] = (dist_sexo['Quantidade'] / dist_sexo['Quantidade'].sum() * 100).round(1)
                dist_sexo['Label'] = dist_sexo.apply(
                    lambda row: f"{row['Quantidade']} ({row['Percentual']}%)", axis=1
                )
                
                # Cores customizadas para cada sexo
                color_scale = alt.Scale(
                    domain=['Masculino', 'Feminino'],
                    range=['#636EFA', '#EF553B']
                )
                
                chart_sexo = alt.Chart(dist_sexo).mark_bar().encode(
                    x=alt.X('Sexo:N', 
                           title='Sexo',
                           axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Quantidade:Q', 
                           title='Número de Alunos'),
                    color=alt.Color('Sexo:N', 
                                   scale=color_scale,
                                   legend=None),
                    tooltip=[
                        alt.Tooltip('Sexo:N', title='Sexo'),
                        alt.Tooltip('Quantidade:Q', title='Alunos'),
                        alt.Tooltip('Percentual:Q', title='Percentual (%)', format='.1f')
                    ]
                ).properties(
                    height=350
                )
                
                # Adicionar labels no topo das barras
                text_sexo = chart_sexo.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    text='Label:N'
                )
                
                st.altair_chart(chart_sexo + text_sexo, use_container_width=True)
            else:
                st.info("📊 Dados de sexo não disponíveis para os filtros selecionados")
    
    # Gráfico 2: Distribuição por Faixa Etária
    with col_dist2:
        with st.container(border=True):
            st.markdown("#### Distribuição por Faixa Etária")
            
            if 'FaixaEtaria' in df.columns and not df['FaixaEtaria'].isna().all():
                # Contar alunos únicos por faixa etária
                dist_idade = df.groupby('FaixaEtaria')['ID_Unico'].nunique().reset_index()
                dist_idade.columns = ['FaixaEtaria', 'Quantidade']
                dist_idade['Percentual'] = (dist_idade['Quantidade'] / dist_idade['Quantidade'].sum() * 100).round(1)
                dist_idade['Label'] = dist_idade.apply(
                    lambda row: f"{row['Quantidade']} ({row['Percentual']}%)", axis=1
                )
                
                # Ordenar as faixas corretamente
                ordem_faixas = ['< 10 anos', '10-11 anos', '12-13 anos', '14-15 anos', '≥ 16 anos']
                dist_idade['FaixaEtaria'] = pd.Categorical(
                    dist_idade['FaixaEtaria'], 
                    categories=ordem_faixas, 
                    ordered=True
                )
                dist_idade = dist_idade.sort_values('FaixaEtaria')
                
                chart_idade = alt.Chart(dist_idade).mark_bar().encode(
                    x=alt.X('FaixaEtaria:N',
                           title='Faixa Etária',
                           sort=ordem_faixas,
                           axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y('Quantidade:Q',
                           title='Número de Alunos'),
                    color=alt.Color('FaixaEtaria:N',
                                   scale=alt.Scale(scheme='viridis'),
                                   legend=None),
                    tooltip=[
                        alt.Tooltip('FaixaEtaria:N', title='Faixa Etária'),
                        alt.Tooltip('Quantidade:Q', title='Alunos'),
                        alt.Tooltip('Percentual:Q', title='Percentual (%)', format='.1f')
                    ]
                ).properties(
                    height=350
                )
                
                # Adicionar labels
                text_idade = chart_idade.mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontSize=11,
                    fontWeight='bold'
                ).encode(
                    text='Label:N'
                )
                
                st.altair_chart(chart_idade + text_idade, use_container_width=True)
            else:
                st.info("📊 Dados de idade não disponíveis para os filtros selecionados")

with tab_perf:
    # Performance por Sexo
    st.markdown("#### Performance por Sexo (Pré vs Pós-Teste)")
    
    if 'Sexo' in df.columns and not df['Sexo'].isna().all():
        # Preparar dados em formato longo
        df_perf_sexo = df.melt(
            id_vars=['Sexo', 'ID_Unico'],
            value_vars=['Score_Pre', 'Score_Pos'],
            var_name='Momento',
            value_name='Score'
        )
        df_perf_sexo['Momento'] = df_perf_sexo['Momento'].replace({
            'Score_Pre': 'Pré-Teste',
            'Score_Pos': 'Pós-Teste'
        })
        
        # Remover NaN para evitar problemas nos tooltips
        df_perf_sexo = df_perf_sexo.dropna(subset=['Score'])
        
        # Calcular médias para cada grupo
        medias_sexo = df_perf_sexo.groupby(['Sexo', 'Momento'], as_index=False)['Score'].mean()
        medias_sexo.columns = ['Sexo', 'Momento', 'Media']
        
        # Criar escala de cores
        color_scale = alt.Scale(
            domain=['Pré-Teste', 'Pós-Teste'],
            range=['#636EFA', '#EF553B']
        )
        
        # Escala de offset para separar os boxplots
        offset_scale = alt.Scale(
            domain=['Pré-Teste', 'Pós-Teste'],
            range=[-50, 50]
        )
        
        # Criar boxplot base
        boxplot_sexo = alt.Chart(df_perf_sexo).mark_boxplot(
            size=40,
            opacity=0.7
        ).encode(
            x=alt.X('Sexo:N', title='Sexo', axis=alt.Axis(labelAngle=0)),
            y=alt.Y('Score:Q', title='Score', scale=alt.Scale(zero=False)),
            color=alt.Color('Momento:N', scale=color_scale, legend=alt.Legend(title='Momento')),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale)
        ).properties(
            height=400
        )
        
        # Adicionar círculos com as médias
        pontos_media_sexo = alt.Chart(medias_sexo).mark_point(
            size=100,
            filled=True,
            opacity=0.9,
            stroke='white',
            strokeWidth=2
        ).encode(
            x=alt.X('Sexo:N'),
            y=alt.Y('Media:Q'),
            color=alt.Color('Momento:N', scale=color_scale, legend=None),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale),
            tooltip=[
                alt.Tooltip('Sexo:N', title='Sexo'),
                alt.Tooltip('Momento:N', title='Momento'),
                alt.Tooltip('Media:Q', title='Média', format='.2f')
            ]
        )
        
        # Adicionar labels de média acima dos círculos
        text_media_sexo = alt.Chart(medias_sexo).mark_text(
            align='center',
            baseline='bottom',
            dy=-12,
            fontSize=11,
            fontWeight='bold'
        ).encode(
            x=alt.X('Sexo:N'),
            y=alt.Y('Media:Q'),
            text=alt.Text('Media:Q', format='.1f'),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale),
            color=alt.value('black')
        )
        
        chart_final_sexo = (boxplot_sexo + pontos_media_sexo + text_media_sexo).configure_axis(
            labelFontSize=11,
            titleFontSize=13
        ).configure_legend(
            titleFontSize=12,
            labelFontSize=11
        )
        
        st.altair_chart(chart_final_sexo, use_container_width=True)
        
        # Estatísticas por sexo
        col_stat1, col_stat2 = st.columns(2)
        for idx, sexo in enumerate(sorted(df['Sexo'].dropna().unique())):
            df_sexo = df[df['Sexo'] == sexo]
            with col_stat1 if idx == 0 else col_stat2:
                st.markdown(f"**{sexo}**")
                pre_mean = df_sexo['Score_Pre'].mean()
                pos_mean = df_sexo['Score_Pos'].mean()
                ganho = pos_mean - pre_mean
                st.write(f"- Pré: {pre_mean:.2f} | Pós: {pos_mean:.2f}")
                st.write(f"- Ganho: {ganho:.2f} ({(ganho/pre_mean*100):.1f}%)")
    else:
        st.info("📊 Dados de sexo não disponíveis")
    
    st.markdown("---")
    
    # Performance por Faixa Etária
    st.markdown("#### Performance por Faixa Etária (Pré vs Pós-Teste)")
    
    if 'FaixaEtaria' in df.columns and not df['FaixaEtaria'].isna().all():
        # Preparar dados
        df_perf_idade = df.melt(
            id_vars=['FaixaEtaria', 'ID_Unico'],
            value_vars=['Score_Pre', 'Score_Pos'],
            var_name='Momento',
            value_name='Score'
        )
        df_perf_idade['Momento'] = df_perf_idade['Momento'].replace({
            'Score_Pre': 'Pré-Teste',
            'Score_Pos': 'Pós-Teste'
        })
        
        # Remover NaN para evitar problemas nos tooltips
        df_perf_idade = df_perf_idade.dropna(subset=['Score', 'FaixaEtaria'])
        
        # Ordenar faixas
        ordem_faixas = ['< 10 anos', '10-11 anos', '12-13 anos', '14-15 anos', '≥ 16 anos']
        df_perf_idade['FaixaEtaria'] = pd.Categorical(
            df_perf_idade['FaixaEtaria'],
            categories=ordem_faixas,
            ordered=True
        )
        df_perf_idade = df_perf_idade.sort_values('FaixaEtaria')
        
        # Calcular médias
        medias_idade = df_perf_idade.groupby(['FaixaEtaria', 'Momento'], as_index=False)['Score'].mean()
        medias_idade.columns = ['FaixaEtaria', 'Momento', 'Media']
        
        # Criar escala de cores
        color_scale = alt.Scale(
            domain=['Pré-Teste', 'Pós-Teste'],
            range=['#636EFA', '#EF553B']
        )
        
        # Escala de offset
        offset_scale = alt.Scale(
            domain=['Pré-Teste', 'Pós-Teste'],
            range=[-35, 35]
        )
        
        # Criar boxplot
        boxplot_idade = alt.Chart(df_perf_idade).mark_boxplot(
            size=30,
            opacity=0.7
        ).encode(
            x=alt.X('FaixaEtaria:N', 
                   title='Faixa Etária',
                   sort=ordem_faixas,
                   axis=alt.Axis(labelAngle=-45)),
            y=alt.Y('Score:Q', 
                   title='Score',
                   scale=alt.Scale(zero=False)),
            color=alt.Color('Momento:N', 
                           scale=color_scale,
                           legend=alt.Legend(title='Momento')),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale)
        ).properties(
            height=400
        )
        
        # Adicionar círculos com as médias
        pontos_media_idade = alt.Chart(medias_idade).mark_point(
            size=80,
            filled=True,
            opacity=0.9,
            stroke='white',
            strokeWidth=2
        ).encode(
            x=alt.X('FaixaEtaria:N', sort=ordem_faixas),
            y=alt.Y('Media:Q'),
            color=alt.Color('Momento:N', scale=color_scale, legend=None),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale),
            tooltip=[
                alt.Tooltip('FaixaEtaria:N', title='Faixa Etária'),
                alt.Tooltip('Momento:N', title='Momento'),
                alt.Tooltip('Media:Q', title='Média', format='.2f')
            ]
        )
        
        # Adicionar labels de média acima dos círculos
        text_media_idade = alt.Chart(medias_idade).mark_text(
            align='center',
            baseline='bottom',
            dy=-12,
            fontSize=10,
            fontWeight='bold'
        ).encode(
            x=alt.X('FaixaEtaria:N', sort=ordem_faixas),
            y=alt.Y('Media:Q'),
            text=alt.Text('Media:Q', format='.1f'),
            xOffset=alt.XOffset('Momento:N', scale=offset_scale),
            color=alt.value('black')
        )
        
        chart_final_idade = (boxplot_idade + pontos_media_idade + text_media_idade).configure_axis(
            labelFontSize=11,
            titleFontSize=13
        ).configure_legend(
            titleFontSize=12,
            labelFontSize=11
        )
        
        st.altair_chart(chart_final_idade, use_container_width=True)
        
        # Tabela de estatísticas por faixa etária
        st.markdown("**Estatísticas por Faixa Etária**")
        
        stats_list = []
        for faixa in ordem_faixas:
            df_faixa = df[df['FaixaEtaria'] == faixa]
            if len(df_faixa) > 0:
                pre_mean = df_faixa['Score_Pre'].mean()
                pos_mean = df_faixa['Score_Pos'].mean()
                ganho = pos_mean - pre_mean
                n_alunos = df_faixa['ID_Unico'].nunique()
                
                stats_list.append({
                    'Faixa Etária': faixa,
                    'N Alunos': n_alunos,
                    'Pré (μ)': f"{pre_mean:.2f}",
                    'Pós (μ)': f"{pos_mean:.2f}",
                    'Ganho': f"{ganho:.2f}",
                    'Ganho %': f"{(ganho/pre_mean*100):.1f}%"
                })
        
        if stats_list:
            df_stats = pd.DataFrame(stats_list)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)
    else:
        st.info("📊 Dados de idade não disponíveis")

st.markdown("---")

# ========== ANÁLISES PRINCIPAIS (LADO A LADO) ==========
if not df.empty:
    col_box, col_gran = st.columns([1.3, 1], gap="large")
    
    # ========== COLUNA 1: BOXPLOT ==========
    with col_box:
        with st.container(border=True, height=750):
            st.markdown("### 📊 Distribuição de Scores por Fase")
            
            # Controle de visualização por turmas
            visualizar_por_turmas = False
            if turmas_sel and len(turmas_sel) > 0:
                visualizar_por_turmas = st.checkbox(
                    "📋 Separar por Turma", 
                    value=False,
                    help="Ative para visualizar cada turma separadamente no gráfico"
                )
            
            try:
                import altair as alt
                
                # Transformar dados para formato longo
                if visualizar_por_turmas:
                    df_boxplot = df.melt(
                        id_vars=['Fase', coluna_turma], 
                        value_vars=['Score_Pre', 'Score_Pos'],
                        var_name='Momento', 
                        value_name='Score'
                    )
                else:
                    df_boxplot = df.melt(
                        id_vars=['Fase'], 
                        value_vars=['Score_Pre', 'Score_Pos'],
                        var_name='Momento', 
                        value_name='Score'
                    )
                
                df_boxplot['Momento'] = df_boxplot['Momento'].replace({
                    'Score_Pre': 'Pré-Teste',
                    'Score_Pos': 'Pós-Teste'
                })
                
                df_boxplot['Fase_str'] = df_boxplot['Fase'].astype(int).astype(str)
                
                # Calcular médias
                if visualizar_por_turmas:
                    medias = df_boxplot.groupby(['Fase', 'Fase_str', coluna_turma, 'Momento'])['Score'].mean().reset_index()
                else:
                    medias = df_boxplot.groupby(['Fase', 'Fase_str', 'Momento'])['Score'].mean().reset_index()
                medias = medias.rename(columns={'Score': 'Media'})
                
                # Criar boxplot
                color_scale = alt.Scale(domain=['Pré-Teste', 'Pós-Teste'], range=['#636EFA', '#EF553B'])
                offset_scale = alt.Scale(domain=['Pré-Teste', 'Pós-Teste'], range=[-40, 40])
                
                if visualizar_por_turmas:
                    base_chart = alt.Chart(df_boxplot)
                    
                    turmas_no_grafico = df_boxplot[coluna_turma].dropna().unique()
                    num_facetas = len(turmas_no_grafico) if len(turmas_no_grafico) > 0 else 1
                    
                    if num_facetas <= 2:
                        facet_width = 320
                        facet_spacing = 80
                        facet_columns = num_facetas
                    elif num_facetas == 3:
                        facet_width = 260
                        facet_spacing = 60
                        facet_columns = 3
                    else:
                        facet_width = 230
                        facet_spacing = 50
                        facet_columns = min(num_facetas, 4)
                    
                    boxplot_layer = base_chart.mark_boxplot(
                        size=30,
                        opacity=0.7
                    ).encode(
                        x=alt.X('Fase_str:N', title='Fase', axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('Score:Q', title='Score'),
                        color=alt.Color('Momento:N', scale=color_scale, legend=alt.Legend(title='Teste')),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale)
                    )
                    
                    pontos_media_layer = base_chart.transform_aggregate(
                        Media='mean(Score)',
                        groupby=['Fase', 'Fase_str', coluna_turma, 'Momento']
                    ).mark_point(
                        size=80,
                        filled=True,
                        opacity=0.9,
                        stroke='white',
                        strokeWidth=2
                    ).encode(
                        x=alt.X('Fase_str:N'),
                        y=alt.Y('Media:Q'),
                        color=alt.Color('Momento:N', scale=color_scale, legend=None),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale),
                        tooltip=[
                            alt.Tooltip('Fase:Q', title='Fase', format='d'),
                            alt.Tooltip(f'{coluna_turma}:N', title='Turma'),
                            alt.Tooltip('Momento:N', title='Teste'),
                            alt.Tooltip('Media:Q', title='Média', format='.2f')
                        ]
                    )
                    
                    # Adicionar labels de média acima dos círculos
                    text_media_layer = base_chart.transform_aggregate(
                        Media='mean(Score)',
                        groupby=['Fase', 'Fase_str', coluna_turma, 'Momento']
                    ).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-12,
                        fontSize=10,
                        fontWeight='bold'
                    ).encode(
                        x=alt.X('Fase_str:N'),
                        y=alt.Y('Media:Q'),
                        text=alt.Text('Media:Q', format='.1f'),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale),
                        color=alt.value('black')
                    )
                    
                    combined = alt.layer(boxplot_layer, pontos_media_layer, text_media_layer).properties(
                        width=facet_width,
                        height=380
                    )
                    
                    boxplot = combined.facet(
                        facet=alt.Facet(f'{coluna_turma}:N', title='Turma', 
                                       header=alt.Header(labelAngle=0, labelFontSize=12)),
                        columns=facet_columns
                    )
                    
                    chart_final = boxplot.properties(
                        title=f'Comparativo por Turma ({len(turmas_sel)} turma(s))'
                    ).configure_axis(
                        labelFontSize=11,
                        titleFontSize=13
                    ).configure_title(
                        fontSize=14,
                        anchor='start'
                    ).configure_legend(
                        titleFontSize=12,
                        labelFontSize=11
                    ).configure_view(
                        strokeWidth=0
                    ).configure_facet(
                        spacing=facet_spacing
                    )
                    
                else:
                    boxplot = alt.Chart(df_boxplot).mark_boxplot(
                        size=36,
                        opacity=0.7
                    ).encode(
                        x=alt.X('Fase_str:N', 
                               title='Fase',
                               axis=alt.Axis(labelAngle=0)),
                        y=alt.Y('Score:Q', 
                               title='Score'),
                        color=alt.Color('Momento:N', scale=color_scale, legend=alt.Legend(title='Teste')),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale)
                    ).properties(
                        width=600,
                        height=380
                    )
                    
                    pontos_media = alt.Chart(medias).mark_point(
                        size=100,
                        filled=True,
                        opacity=0.9,
                        stroke='white',
                        strokeWidth=2
                    ).encode(
                        x=alt.X('Fase_str:N'),
                        y=alt.Y('Media:Q'),
                        color=alt.Color('Momento:N', scale=color_scale, legend=None),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale),
                        tooltip=[
                            alt.Tooltip('Fase:Q', title='Fase', format='d'),
                            alt.Tooltip('Momento:N', title='Teste'),
                            alt.Tooltip('Media:Q', title='Média', format='.2f')
                        ]
                    )
                    
                    # Adicionar labels de média acima dos círculos
                    text_media = alt.Chart(medias).mark_text(
                        align='center',
                        baseline='bottom',
                        dy=-12,
                        fontSize=10,
                        fontWeight='bold'
                    ).encode(
                        x=alt.X('Fase_str:N'),
                        y=alt.Y('Media:Q'),
                        text=alt.Text('Media:Q', format='.1f'),
                        xOffset=alt.XOffset('Momento:N', scale=offset_scale),
                        color=alt.value('black')
                    )
                    
                    titulo = 'Distribuição Pré-Teste vs Pós-Teste por Fase'
                    
                    chart_final = (boxplot + pontos_media + text_media).properties(
                        title=titulo
                    ).configure_axis(
                        labelFontSize=12,
                        titleFontSize=14
                    ).configure_title(
                        fontSize=15,
                        anchor='start'
                    ).configure_legend(
                        titleFontSize=13,
                        labelFontSize=12
                    )
                
                st.altair_chart(chart_final, use_container_width=True)
                
                if visualizar_por_turmas and turmas_sel:
                    st.caption(f"📊 Comparação entre {len(turmas_sel)} turma(s)")
                
                # ========== GRÁFICO DE DELTA MÉDIO POR FASE ==========
                st.markdown("---")
                st.markdown("#### 📊 Ganho Médio por Fase")
                st.caption("Diferença entre Pós-Teste e Pré-Teste (Delta = Pós - Pré)")
                
                # Calcular delta médio por fase
                df_delta_fase = df.groupby('Fase', as_index=False).apply(
                    lambda x: pd.Series({
                        'Delta_Medio': x['Score_Pos'].mean() - x['Score_Pre'].mean(),
                        'N_Alunos': len(x)
                    }), include_groups=False
                ).reset_index(drop=True)
                
                df_delta_fase['Fase_str'] = df_delta_fase['Fase'].astype(int).astype(str)
                df_delta_fase['Cor'] = df_delta_fase['Delta_Medio'].apply(
                    lambda x: '#28a745' if x > 0 else '#dc3545' if x < 0 else '#6c757d'
                )
                
                # Criar gráfico de barras com Altair
                bar_delta = alt.Chart(df_delta_fase).mark_bar(
                    cornerRadiusTopLeft=4,
                    cornerRadiusTopRight=4,
                    opacity=0.85
                ).encode(
                    x=alt.X('Fase_str:N', 
                           title='Fase',
                           axis=alt.Axis(labelAngle=0)),
                    y=alt.Y('Delta_Medio:Q', 
                           title='Ganho Médio (Pós - Pré)',
                           scale=alt.Scale(domain=[
                               min(0, df_delta_fase['Delta_Medio'].min() - 1),
                               df_delta_fase['Delta_Medio'].max() + 1
                           ])),
                    color=alt.Color('Cor:N', scale=None, legend=None),
                    tooltip=[
                        alt.Tooltip('Fase:Q', title='Fase', format='d'),
                        alt.Tooltip('Delta_Medio:Q', title='Ganho Médio', format='.2f'),
                        alt.Tooltip('N_Alunos:Q', title='Nº Alunos', format='d')
                    ]
                ).properties(
                    width=600,
                    height=180
                )
                
                # Adicionar linha de referência no zero
                rule_zero = alt.Chart(pd.DataFrame({'y': [0]})).mark_rule(
                    strokeDash=[5, 5],
                    color='gray',
                    strokeWidth=1.5
                ).encode(
                    y='y:Q'
                )
                
                # Adicionar rótulos de valores nas barras
                text_delta = alt.Chart(df_delta_fase).mark_text(
                    align='center',
                    baseline='bottom',
                    dy=-5,
                    fontSize=12,
                    fontWeight='bold'
                ).encode(
                    x=alt.X('Fase_str:N'),
                    y=alt.Y('Delta_Medio:Q'),
                    text=alt.Text('Delta_Medio:Q', format='.2f'),
                    color=alt.value('black')
                )
                
                chart_delta_final = (bar_delta + rule_zero + text_delta).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_view(
                    strokeWidth=0
                )
                
                st.altair_chart(chart_delta_final, use_container_width=True)
                
                # Informação adicional
                melhor_fase = df_delta_fase.loc[df_delta_fase['Delta_Medio'].idxmax()]
                st.caption(f"🏆 **Maior ganho:** Fase {int(melhor_fase['Fase'])} com +{melhor_fase['Delta_Medio']:.2f} pontos ({int(melhor_fase['N_Alunos'])} alunos)")
                
            except ImportError:
                st.warning("⚠️ Altair não disponível. Usando Plotly...")
                
                df_boxplot = df.melt(
                    id_vars=['Fase'], 
                    value_vars=['Score_Pre', 'Score_Pos'],
                    var_name='Momento', 
                    value_name='Score'
                )
                df_boxplot['Momento'] = df_boxplot['Momento'].replace({
                    'Score_Pre': 'Pré-Teste',
                    'Score_Pos': 'Pós-Teste'
                })
                
                fig_fase = px.box(
                    df_boxplot,
                    x='Fase',
                    y='Score',
                    color='Momento',
                    title='Distribuição Pré-Teste vs Pós-Teste por Fase',
                    labels={'Score': 'Score', 'Momento': 'Teste'},
                    points='outliers'
                )
                
                fases_disponiveis = sorted(df_boxplot['Fase'].unique())
                fig_fase.update_xaxes(
                    tickmode='array',
                    tickvals=fases_disponiveis,
                    ticktext=[str(int(fase)) for fase in fases_disponiveis],
                    title='Fase'
                )
                
                st.plotly_chart(fig_fase, use_container_width=True)
    
    # ========== COLUNA 2: ANÁLISE GRANULAR ==========
    with col_gran:
        with st.container(border=True, height=750):
            st.markdown("### 🔍 Análise por Questão")
            
            questao_cols = [col for col in df.columns if col.startswith('Q') and ('_Pre' in col or '_Pos' in col)]
            
            if questao_cols:
                # Carregar mapeamento de questões para palavras POR FASE
                import json
                import os
                
                mapeamento_palavras = {}
                # Tentar carregar RespostaVocabulario.json de cada fase selecionada
                for fase in fases_sel:
                    try:
                        # Primeiro tenta o arquivo específico da fase
                        path_fase = os.path.join(os.path.dirname(__file__), '..', 'Data', f'Fase {int(fase)}', 'RespostaVocabulario.json')
                        if os.path.exists(path_fase):
                            with open(path_fase, 'r', encoding='utf-8') as f:
                                respostas = json.load(f)
                                for item in respostas:
                                    for q_key, q_data in item.items():
                                        if 'Palavra Trabalhada' in q_data:
                                            mapeamento_palavras[q_key] = q_data['Palavra Trabalhada']
                    except Exception as e:
                        pass
                
                # Se não encontrou nada, tenta o arquivo geral
                if not mapeamento_palavras:
                    try:
                        path_respostas = os.path.join(os.path.dirname(__file__), '..', 'Data', 'RespostaVocabulario.json')
                        if os.path.exists(path_respostas):
                            with open(path_respostas, 'r', encoding='utf-8') as f:
                                respostas = json.load(f)
                                for item in respostas:
                                    for q_key, q_data in item.items():
                                        if 'Palavra Trabalhada' in q_data:
                                            mapeamento_palavras[q_key] = q_data['Palavra Trabalhada']
                    except Exception as e:
                        pass
                
                questoes_nums = set()
                for col in questao_cols:
                    if '_Pre' in col:
                        q_num = col.split('_Pre')[0]
                        questoes_nums.add(q_num)
                
                questoes_nums = sorted(list(questoes_nums), key=lambda x: int(x[1:]))
                
                analise_questoes = []
                for q_num in questoes_nums:
                    col_pre = f"{q_num}_Pre"
                    col_pos = f"{q_num}_Pos"
                    
                    if col_pre in df.columns and col_pos in df.columns:
                        pct_pre = (df[col_pre].sum() / df[col_pre].count()) * 100 if df[col_pre].count() > 0 else 0
                        pct_pos = (df[col_pos].sum() / df[col_pos].count()) * 100 if df[col_pos].count() > 0 else 0
                        variacao = pct_pos - pct_pre
                        
                        # Usar palavra se disponível, senão usar Q1, Q2, etc.
                        palavra = mapeamento_palavras.get(q_num, q_num)
                        
                        analise_questoes.append({
                            'Palavra': palavra,
                            '% Pré': pct_pre,
                            '% Pós': pct_pos,
                            'Δ': variacao
                        })
                
                if analise_questoes:
                    df_analise = pd.DataFrame(analise_questoes)
                    df_analise_sorted = df_analise.sort_values('Δ', ascending=False)
                    
                    # Carregar palavras ensinadas se for Vocabulário
                    palavras_ensinadas_todas = set()
                    if prova_sel.upper().startswith('VOCABUL'):
                        palavras_por_fase = carregar_palavras_ensinadas()
                        # Juntar palavras de todas as fases selecionadas
                        for fase in fases_sel:
                            if fase in palavras_por_fase:
                                palavras_ensinadas_todas.update(palavras_por_fase[fase])
                    
                    # Tabela compacta com destaque para palavras ensinadas
                    def style_variacao(val):
                        if pd.isna(val):
                            return ''
                        elif val > 0:
                            return 'background-color: #e8f5e8; color: #2d5016; font-weight: bold'
                        elif val < 0:
                            return 'background-color: #fdf2f2; color: #721c24; font-weight: bold'
                        else:
                            return 'background-color: #f1f3f4; color: #495057; font-weight: bold'
                    
                    def style_palavra_ensinada(row):
                        """Destaca palavras ensinadas com fundo amarelo usando matching inteligente."""
                        if prova_sel.upper().startswith('VOCABUL') and palavra_ensinada_match(row['Palavra'], palavras_ensinadas_todas):
                            return ['background-color: #fff3cd; font-weight: bold'] * len(row)
                        return [''] * len(row)
                    
                    styled_analise = (df_analise_sorted.style
                                     .apply(style_palavra_ensinada, axis=1)
                                     .map(style_variacao, subset=['Δ'])
                                     .format({
                                         '% Pré': '{:.1f}%',
                                         '% Pós': '{:.1f}%',
                                         'Δ': '{:+.1f}%'
                                     }))
                    
                    st.caption("**Tabela de Evolução por Palavra**")
                    if prova_sel.upper().startswith('VOCABUL') and palavras_ensinadas_todas:
                        # Contar quantas palavras do teste correspondem às ensinadas
                        palavras_teste = df_analise_sorted['Palavra'].tolist()
                        palavras_matched = [p for p in palavras_teste if palavra_ensinada_match(p, palavras_ensinadas_todas)]
                        
                        st.caption(f"🟡 *Palavras destacadas em amarelo foram ensinadas no WordGen ({len(palavras_matched)} de {len(palavras_teste)} palavras do teste)*")
                        
                        # Debug: mostrar algumas correspondências (apenas em desenvolvimento)
                        if st.session_state.get('show_debug', False):
                            with st.expander("🔍 Debug - Correspondências encontradas"):
                                st.write(f"**Palavras ensinadas carregadas:** {len(palavras_ensinadas_todas)}")
                                st.write(f"**Fases selecionadas:** {fases_sel}")
                                st.write(f"**Palavras matched:** {palavras_matched}")
                    
                    st.dataframe(styled_analise, use_container_width=True, height=420)
                    
                    # ========== TOP 5 PALAVRAS ==========
                    st.markdown("---")
                    st.caption("**🏆 Destaques de Aprendizagem**")
                    
                    # TOP 5 Maior Ganho
                    top_5_ganho = df_analise_sorted.head(5)
                    # TOP 5 Menor Ganho (ou maior declínio)
                    top_5_declinio = df_analise_sorted.tail(5).sort_values('Δ', ascending=True)
                    
                    col_top, col_bottom = st.columns(2)
                    
                    with col_top:
                        st.markdown("**🟢 Maior Progresso**")
                        for idx, row in top_5_ganho.iterrows():
                            delta_val = row['Δ']
                            # Usar diferentes tons de verde baseado no valor
                            if delta_val > 20:
                                cor_fundo = "#d4edda"
                                cor_texto = "#155724"
                            elif delta_val > 10:
                                cor_fundo = "#e8f5e8"
                                cor_texto = "#2d5016"
                            else:
                                cor_fundo = "#f1f8f1"
                                cor_texto = "#3d6b21"
                            
                            st.markdown(f"""
                            <div style='background-color: {cor_fundo}; 
                                        padding: 8px 12px; 
                                        border-radius: 6px; 
                                        margin-bottom: 6px;
                                        border-left: 4px solid #28a745;'>
                                <span style='color: {cor_texto}; font-weight: 600; font-size: 13px;'>{row['Palavra']}</span>
                                <span style='float: right; color: {cor_texto}; font-weight: bold; font-size: 13px;'>+{delta_val:.1f}%</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    with col_bottom:
                        st.markdown("**🔴 Atenção Necessária**")
                        for idx, row in top_5_declinio.iterrows():
                            delta_val = row['Δ']
                            # Usar diferentes tons de vermelho/amarelo baseado no valor
                            if delta_val < 0:
                                cor_fundo = "#f8d7da"
                                cor_texto = "#721c24"
                                borda_cor = "#dc3545"
                            elif delta_val < 5:
                                cor_fundo = "#fff3cd"
                                cor_texto = "#856404"
                                borda_cor = "#ffc107"
                            else:
                                cor_fundo = "#fff9e6"
                                cor_texto = "#997404"
                                borda_cor = "#ffeb3b"
                            
                            simbolo = "" if delta_val < 0 else "+"
                            st.markdown(f"""
                            <div style='background-color: {cor_fundo}; 
                                        padding: 8px 12px; 
                                        border-radius: 6px; 
                                        margin-bottom: 6px;
                                        border-left: 4px solid {borda_cor};'>
                                <span style='color: {cor_texto}; font-weight: 600; font-size: 13px;'>{row['Palavra']}</span>
                                <span style='float: right; color: {cor_texto}; font-weight: bold; font-size: 13px;'>{simbolo}{delta_val:.1f}%</span>
                            </div>
                            """, unsafe_allow_html=True)
                
                else:
                    st.info("Sem questões válidas")
            else:
                st.info("Dataset não contém questões individuais")

st.markdown("---")

# ========== DISTRIBUIÇÃO DE GANHOS INDIVIDUAIS (EXPANDER) ==========
with st.expander("📊 **DISTRIBUIÇÃO DE GANHOS INDIVIDUAIS**", expanded=False):
    st.caption("Análise da variabilidade dos ganhos (Pós - Pré) entre todos os alunos")
    
    if not df.empty and 'Score_Pre' in df.columns and 'Score_Pos' in df.columns:
        # Calcular delta para cada aluno
        df_with_delta = df.copy()
        df_with_delta['Delta'] = df_with_delta['Score_Pos'] - df_with_delta['Score_Pre']
        
        # Remover valores nulos
        df_with_delta = df_with_delta.dropna(subset=['Delta'])
        
        if len(df_with_delta) > 0:
            try:
                import altair as alt
                
                # Estatísticas descritivas
                media_delta = df_with_delta['Delta'].mean()
                mediana_delta = df_with_delta['Delta'].median()
                std_delta = df_with_delta['Delta'].std()
                min_delta = df_with_delta['Delta'].min()
                max_delta = df_with_delta['Delta'].max()
                
                # Contar alunos por categoria
                melhoraram = len(df_with_delta[df_with_delta['Delta'] > 0])
                mantiveram = len(df_with_delta[df_with_delta['Delta'] == 0])
                pioraram = len(df_with_delta[df_with_delta['Delta'] < 0])
                total_alunos = len(df_with_delta)
                
                # Cards de estatísticas
                col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                
                with col_stat1:
                    st.metric(
                        label="📈 Melhoraram",
                        value=f"{melhoraram}",
                        delta=f"{(melhoraram/total_alunos*100):.1f}%",
                        delta_color="normal"
                    )
                
                with col_stat2:
                    st.metric(
                        label="➡️ Mantiveram",
                        value=f"{mantiveram}",
                        delta=f"{(mantiveram/total_alunos*100):.1f}%",
                        delta_color="off"
                    )
                
                with col_stat3:
                    st.metric(
                        label="📉 Pioraram",
                        value=f"{pioraram}",
                        delta=f"{(pioraram/total_alunos*100):.1f}%",
                        delta_color="inverse"
                    )
                
                with col_stat4:
                    st.metric(
                        label="📊 Ganho Médio",
                        value=f"{media_delta:.2f}",
                        delta=f"±{std_delta:.2f}",
                        delta_color="off"
                    )
                
                st.markdown("---")
                
                # Criar histograma com Altair
                st.markdown("#### 📊 Distribuição dos Ganhos")
                
                # Adicionar coluna de cor baseada no Delta
                df_with_delta['Cor'] = df_with_delta['Delta'].apply(
                    lambda x: 'Positivo' if x > 0 else ('Negativo' if x < 0 else 'Zero')
                )
                
                # Histograma de barras
                hist = alt.Chart(df_with_delta).mark_bar(
                    opacity=0.75,
                    binSpacing=1,
                    cornerRadiusTopLeft=3,
                    cornerRadiusTopRight=3
                ).encode(
                    x=alt.X('Delta:Q', 
                           bin=alt.Bin(maxbins=30), 
                           title='Ganho (Pós - Pré)',
                           axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
                    y=alt.Y('count()', 
                           title='Número de Alunos',
                           axis=alt.Axis(labelFontSize=11, titleFontSize=12)),
                    color=alt.Color('Cor:N',
                        scale=alt.Scale(
                            domain=['Positivo', 'Zero', 'Negativo'],
                            range=['#28a745', '#6c757d', '#dc3545']
                        ),
                        legend=None
                    ),
                    tooltip=[
                        alt.Tooltip('count()', title='Nº Alunos'),
                        alt.Tooltip('Delta:Q', title='Ganho', format='.1f', bin=True)
                    ]
                ).properties(
                    width=700,
                    height=350
                )
                
                # Linha vertical da média
                rule_media = alt.Chart(pd.DataFrame({'x': [media_delta]})).mark_rule(
                    color='red',
                    strokeWidth=3,
                    strokeDash=[5, 5]
                ).encode(
                    x='x:Q',
                    size=alt.value(2)
                )
                
                # Texto da média
                text_media = alt.Chart(pd.DataFrame({
                    'x': [media_delta],
                    'y': [0],
                    'label': [f'Média: {media_delta:.2f}']
                })).mark_text(
                    align='left',
                    dx=5,
                    dy=-10,
                    fontSize=12,
                    fontWeight='bold',
                    color='red'
                ).encode(
                    x='x:Q',
                    y=alt.Y('y:Q', scale=alt.Scale(domain=[0, 1])),
                    text='label:N'
                )
                
                # Linha vertical da mediana
                rule_mediana = alt.Chart(pd.DataFrame({'x': [mediana_delta]})).mark_rule(
                    color='blue',
                    strokeWidth=2,
                    strokeDash=[3, 3]
                ).encode(
                    x='x:Q'
                )
                
                # Combinar todas as camadas
                chart_final = (hist + rule_media + rule_mediana).configure_axis(
                    labelFontSize=11,
                    titleFontSize=12
                ).configure_view(
                    strokeWidth=0
                )
                
                st.altair_chart(chart_final, use_container_width=True)
                
                # Insights adicionais
                st.markdown("#### 💡 Sobre a Distribuição")
                
                col_insight1, col_insight2 = st.columns(2)
                
                with col_insight1:
                    st.info(f"""
                    **📊 Estatísticas Descritivas:**
                    - **Média:** {media_delta:.2f} pontos
                    - **Mediana:** {mediana_delta:.2f} pontos
                    - **Desvio Padrão:** ±{std_delta:.2f} pontos
                    - **Amplitude:** {min_delta:.2f} a {max_delta:.2f} pontos
                    """)
                
                with col_insight2:
                    # Calcular percentis
                    p25 = df_with_delta['Delta'].quantile(0.25)
                    p75 = df_with_delta['Delta'].quantile(0.75)
                    
                    # Identificar outliers (usando regra IQR)
                    iqr = p75 - p25
                    outliers_baixo = len(df_with_delta[df_with_delta['Delta'] < (p25 - 1.5 * iqr)])
                    outliers_alto = len(df_with_delta[df_with_delta['Delta'] > (p75 + 1.5 * iqr)])
                    
                    st.success(f"""
                    **🎯 Análise de Performance:**
                    - **Taxa de Sucesso:** {(melhoraram/total_alunos*100):.1f}% melhoraram
                    - **25º Percentil (Q1):** {p25:.2f} pontos
                    - **75º Percentil (Q3):** {p75:.2f} pontos
                    - **Outliers:** {outliers_baixo} baixo | {outliers_alto} alto
                    """)
                
                st.caption(f"📊 Análise baseada em {total_alunos} aluno(s) com dados completos de Pré e Pós-Teste")
                
            except ImportError:
                st.error("❌ Biblioteca Altair não disponível")
        else:
            st.warning("⚠️ Não há dados suficientes para análise de distribuição")
    else:
        st.info("💡 Dados de Score_Pre e Score_Pos necessários para esta visualização")

st.markdown("---")

# ========== EVOLUÇÃO HIERÁRQUICA (EXPANDER) ==========
with st.expander("🌐 **EVOLUÇÃO COMPARATIVA HIERÁRQUICA**", expanded=False):
    st.caption("Trajetórias longitudinais por Escola, Turma ou Aluno")
    
    # Inicializar estados
    if 'nivel_visualizacao' not in st.session_state:
        st.session_state.nivel_visualizacao = 'Escolas'
    if 'escolas_filtradas' not in st.session_state:
        st.session_state.escolas_filtradas = []
    if 'turmas_filtradas' not in st.session_state:
        st.session_state.turmas_filtradas = []
    
    # Informativo sobre Coortes (como info box ao invés de expander)
    st.info("""
    **ℹ️ O que são Coortes?**
    
    Coortes representam grupos de alunos baseados na fase em que iniciaram o programa:
    
    • **Coorte 1**: Alunos que começaram na Fase 2  
    • **Coorte 2**: Alunos que começaram na Fase 3  
    • **Coorte 3**: Alunos que começaram na Fase 4
    """)
    
    # Seletores
    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        coorte_drill = st.selectbox(
            "🎓 Filtrar por Coorte:",
            options=['Todas', 'Coorte 1', 'Coorte 2', 'Coorte 3'],
            key='drill_coorte_selector'
        )
    with col_sel2:
        nivel_viz = st.selectbox(
            "🔍 Nível de Visualização:",
            options=['Escolas', 'Turmas', 'Alunos'],
            key='nivel_visualizacao_selector'
        )
        st.session_state.nivel_visualizacao = nivel_viz
    
    # Preparar dados
    df_drill_base = df.copy()
    
    # Filtrar por coorte
    if coorte_drill != 'Todas':
        if 'coorte_anonimizado' in df_drill_base.columns:
            col_coorte = 'coorte_anonimizado'
        elif 'Coorte_Origem' in df_drill_base.columns:
            col_coorte = 'Coorte_Origem'
        elif 'Coorte' in df_drill_base.columns:
            col_coorte = 'Coorte'
        else:
            col_coorte = None
        
        if col_coorte:
            df_drill_base = df_drill_base[df_drill_base[col_coorte] == coorte_drill].copy()
    
    # Determinar colunas
    colunas_validas = True
    
    if 'escola_anonimizado' in df_drill_base.columns:
        col_escola = 'escola_anonimizado'
    elif 'Escola' in df_drill_base.columns:
        col_escola = 'Escola'
    else:
        st.error("❌ Coluna de escola não encontrada")
        colunas_validas = False
    
    if colunas_validas:
        if 'turma_anonimizado' in df_drill_base.columns:
            col_turma_h = 'turma_anonimizado'
        elif 'Turma' in df_drill_base.columns:
            col_turma_h = 'Turma'
        else:
            st.error("❌ Coluna de turma não encontrada")
            colunas_validas = False
    
    if colunas_validas:
        if 'aluno_anonimizado' in df_drill_base.columns:
            col_aluno = 'aluno_anonimizado'
        elif 'ID_Anonimizado' in df_drill_base.columns:
            col_aluno = 'ID_Anonimizado'
        elif 'Nome' in df_drill_base.columns:
            col_aluno = 'Nome'
        else:
            st.error("❌ Coluna de aluno não encontrada")
            colunas_validas = False
    
    if colunas_validas:
        if 'fase' in df_drill_base.columns:
            col_fase = 'fase'
        elif 'Fase' in df_drill_base.columns:
            col_fase = 'Fase'
        else:
            st.error("❌ Coluna de fase não encontrada")
            colunas_validas = False
    
    if colunas_validas:
        if 'Score_Pos' in df_drill_base.columns and 'Score_Pre' in df_drill_base.columns:
            df_drill_base['Delta'] = df_drill_base['Score_Pos'] - df_drill_base['Score_Pre']
            metric_options = {
                'Delta (Pós - Pré)': 'Delta',
                'Score Pré': 'Score_Pre',
                'Score Pós': 'Score_Pos'
            }
            metric_default_label = 'Delta (Pós - Pré)'
        elif 'pontuacao_total' in df_drill_base.columns:
            metric_options = {'Pontuação Total': 'pontuacao_total'}
            metric_default_label = 'Pontuação Total'
        else:
            st.error("❌ Colunas de pontuação não encontradas")
            colunas_validas = False
    
    if colunas_validas and metric_options:
        metric_labels = list(metric_options.keys())
        if metric_default_label is None or metric_default_label not in metric_labels:
            metric_default_label = metric_labels[0]
        if 'metric_parallel_selector' not in st.session_state:
            st.session_state.metric_parallel_selector = metric_default_label
        elif st.session_state.metric_parallel_selector not in metric_labels:
            st.session_state.metric_parallel_selector = metric_default_label
        default_index = metric_labels.index(st.session_state.metric_parallel_selector)
        
        metrica_label = st.selectbox(
            "📐 Métrica Longitudinal:",
            options=metric_labels,
            index=default_index,
            key='metric_parallel_selector'
        )
        metrica_col = metric_options[metrica_label]
        metrica_axis_title = metrica_label
    
    if not colunas_validas:
        st.info("⚠️ Visualização não disponível para esta configuração")
    elif df_drill_base.empty:
        st.warning(f"⚠️ Nenhum dado disponível para {prova_sel}")
    else:
        try:
            import altair as alt
            
            # Preparar dados
            if nivel_viz == 'Escolas':
                col_agrupamento = col_escola
                label_entidade = 'Escola'
            elif nivel_viz == 'Turmas':
                col_agrupamento = col_turma_h
                label_entidade = 'Turma'
            else:
                col_agrupamento = col_aluno
                label_entidade = 'Aluno'
            
            df_viz = df_drill_base.groupby([col_agrupamento, col_fase])[metrica_col].mean().reset_index()
            df_viz = df_viz.rename(columns={col_agrupamento: 'Entidade', col_fase: 'Fase', metrica_col: 'Valor'})
            
            # Filtros hierárquicos
            st.markdown("#### 🔽 Filtros Hierárquicos")
            col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
            
            with col_filtro1:
                todas_escolas = sorted(df_drill_base[col_escola].dropna().unique())
                # Filtrar defaults que ainda existem nas opções
                defaults_validos_escolas = [e for e in st.session_state.escolas_filtradas if e in todas_escolas]
                escolas_selecionadas = st.multiselect(
                    "🏫 Filtrar Escolas:",
                    options=todas_escolas,
                    default=defaults_validos_escolas,
                    key='filtro_escolas_parallel'
                )
                st.session_state.escolas_filtradas = escolas_selecionadas
            
            df_drill_filtrado = df_drill_base.copy()
            if escolas_selecionadas:
                df_drill_filtrado = df_drill_filtrado[df_drill_filtrado[col_escola].isin(escolas_selecionadas)]
            
            with col_filtro2:
                turmas_selecionadas = []
                if nivel_viz in ['Turmas', 'Alunos']:
                    todas_turmas = sorted(df_drill_filtrado[col_turma_h].dropna().unique())
                    # Filtrar defaults que ainda existem nas opções
                    defaults_validos = [t for t in st.session_state.turmas_filtradas if t in todas_turmas]
                    turmas_selecionadas = st.multiselect(
                        "🎓 Filtrar Turmas:",
                        options=todas_turmas,
                        default=defaults_validos,
                        key='filtro_turmas_parallel',
                        disabled=not escolas_selecionadas
                    )
                    st.session_state.turmas_filtradas = turmas_selecionadas
                    
                    if turmas_selecionadas:
                        df_drill_filtrado = df_drill_filtrado[df_drill_filtrado[col_turma_h].isin(turmas_selecionadas)]
                else:
                    st.info("👈 Disponível ao visualizar Turmas ou Alunos")
            
            with col_filtro3:
                alunos_selecionados = []
                if nivel_viz == 'Alunos':
                    todos_alunos = sorted(df_drill_filtrado[col_aluno].dropna().unique())
                    alunos_selecionados = st.multiselect(
                        "👨‍🎓 Filtrar Alunos:",
                        options=todos_alunos[:50],
                        key='filtro_alunos_parallel',
                        disabled=not turmas_selecionadas
                    )
                    
                    if alunos_selecionados:
                        df_drill_filtrado = df_drill_filtrado[df_drill_filtrado[col_aluno].isin(alunos_selecionados)]
                else:
                    st.info("👈 Disponível ao visualizar Alunos")
            
            # Reagregar
            df_viz = df_drill_filtrado.groupby([col_agrupamento, col_fase])[metrica_col].mean().reset_index()
            df_viz = df_viz.rename(columns={col_agrupamento: 'Entidade', col_fase: 'Fase', metrica_col: 'Valor'})
            
            if df_viz.empty:
                st.warning("⚠️ Nenhum dado com os filtros selecionados")
            else:
                st.markdown(f"#### 📊 Trajetórias de {label_entidade}s")
                
                df_wide = df_viz.pivot(index='Entidade', columns='Fase', values='Valor').reset_index()
                fases_disponiveis = [col for col in df_wide.columns if col != 'Entidade']
                
                if len(fases_disponiveis) < 2:
                    st.warning("⚠️ Necessário pelo menos 2 fases")
                else:
                    df_plot = df_viz.copy()
                    df_plot['Fase'] = df_plot['Fase'].astype(str)
                    
                    brush = alt.selection_interval(encodings=['y'])
                    
                    base = alt.Chart(df_plot).mark_line(
                        point=True,
                        strokeWidth=2,
                        opacity=0.6
                    ).encode(
                        x=alt.X('Fase:O', axis=alt.Axis(title='Fase', labelAngle=0)),
                        y=alt.Y('Valor:Q', axis=alt.Axis(title=metrica_axis_title)),
                        color=alt.Color('Entidade:N', legend=None if len(df_plot['Entidade'].unique()) > 15 else alt.Legend(title=label_entidade)),
                        detail='Entidade:N',
                        tooltip=[
                            alt.Tooltip('Entidade:N', title=label_entidade),
                            alt.Tooltip('Fase:O', title='Fase'),
                            alt.Tooltip('Valor:Q', title=metrica_axis_title, format='.2f')
                        ],
                        opacity=alt.condition(brush, alt.value(0.8), alt.value(0.2))
                    ).properties(
                        width=700,
                        height=400,
                        title=f'Evolução de {label_entidade}s: {prova_sel} - {coorte_drill}'
                    ).add_params(brush)
                    
                    media_por_fase = df_plot.groupby('Fase')['Valor'].mean().reset_index()
                    
                    linha_media = alt.Chart(media_por_fase).mark_line(
                        strokeWidth=4,
                        color='red',
                        strokeDash=[5, 5]
                    ).encode(
                        x='Fase:O',
                        y='Valor:Q'
                    )
                    
                    pontos_media = alt.Chart(media_por_fase).mark_point(
                        size=150,
                        color='red',
                        shape='diamond'
                    ).encode(
                        x='Fase:O',
                        y='Valor:Q',
                        tooltip=[
                            alt.Tooltip('Fase:O', title='Fase'),
                            alt.Tooltip('Valor:Q', title='Média', format='.2f')
                        ]
                    )
                    
                    chart_final = (base + linha_media + pontos_media).configure_axis(
                        labelFontSize=12,
                        titleFontSize=14
                    ).configure_title(
                        fontSize=16,
                        anchor='start'
                    )
                    
                    st.altair_chart(chart_final, use_container_width=True)
                    
                    # Estatísticas
                    st.markdown("#### 📈 Estatísticas da Seleção")
                    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
                    
                    n_entidades = df_viz['Entidade'].nunique()
                    n_alunos_unicos = df_drill_filtrado[col_aluno].nunique() if col_aluno in df_drill_filtrado.columns else 0
                    media_geral = df_viz['Valor'].mean()
                    
                    fases_ord = sorted(df_viz['Fase'].unique())
                    if len(fases_ord) >= 2:
                        primeira_fase = df_viz[df_viz['Fase'] == fases_ord[0]]['Valor'].mean()
                        ultima_fase = df_viz[df_viz['Fase'] == fases_ord[-1]]['Valor'].mean()
                        tendencia = ultima_fase - primeira_fase
                        tendencia_icon = "📈" if tendencia > 0 else "📉" if tendencia < 0 else "➡️"
                    else:
                        tendencia = 0
                        tendencia_icon = "➡️"
                    
                    variancia = df_viz['Valor'].std()
                    
                    with col_stat1:
                        valor_card1 = f"{n_entidades} / {n_alunos_unicos}"
                        titulo_card1 = f"{label_entidade}s / Alunos"
                        st.markdown(criar_metric_card(
                            valor=valor_card1,
                            titulo=titulo_card1,
                            icone="fas fa-layer-group",
                            cor_box=(52, 152, 219),
                            cor_fonte=(255, 255, 255)
                        ), unsafe_allow_html=True)
                    
                    with col_stat2:
                        st.markdown(criar_metric_card(
                            valor=f"{media_geral:.2f}",
                            titulo=f"{metrica_axis_title} Médio",
                            icone="fas fa-chart-line",
                            cor_box=(46, 204, 113),
                            cor_fonte=(255, 255, 255)
                        ), unsafe_allow_html=True)
                    
                    with col_stat3:
                        st.markdown(criar_metric_card(
                            valor=f"{tendencia_icon} {tendencia:+.2f}",
                            titulo="Tendência",
                            icone="fas fa-arrow-trend-up" if tendencia > 0 else "fas fa-arrow-trend-down",
                            cor_box=(155, 89, 182),
                            cor_fonte=(255, 255, 255)
                        ), unsafe_allow_html=True)
                    
                    with col_stat4:
                        st.markdown(criar_metric_card(
                            valor=f"±{variancia:.2f}",
                            titulo="Variabilidade",
                            icone="fas fa-chart-area",
                            cor_box=(230, 126, 34),
                            cor_fonte=(255, 255, 255)
                        ), unsafe_allow_html=True)
        
        except ImportError:
            st.error("❌ Altair não encontrada")
            st.info("💡 Usando Plotly...")
            
            if nivel_viz == 'Escolas':
                col_agrupamento = col_escola
                label_entidade = 'Escola'
            elif nivel_viz == 'Turmas':
                col_agrupamento = col_turma_h
                label_entidade = 'Turma'
            else:
                col_agrupamento = col_aluno
                label_entidade = 'Aluno'
            
            df_viz = df_drill_base.groupby([col_agrupamento, col_fase])[metrica_col].mean().reset_index()
            
            fig = px.line(
                df_viz,
                x=col_fase,
                y=metrica_col,
                color=col_agrupamento,
                markers=True,
                title=f'Evolução - {nivel_viz}',
                labels={
                    col_fase: 'Fase',
                    metrica_col: metrica_axis_title,
                    col_agrupamento: label_entidade
                }
            )
            
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ========== EVOLUÇÃO INDIVIDUAL (EXPANDER) ==========
with st.expander("👨‍🎓 **EVOLUÇÃO INDIVIDUAL**", expanded=False):
    # Filtro de aluno baseado nos filtros principais (Prova, Fases, Escolas)
    st.markdown("**Selecione um aluno para análise individual:**")
    
    # Criar dicionário com IDs e suas fases participadas
    if not df.empty:
        aluno_fases = df.groupby('ID_Anonimizado')['Fase'].apply(
            lambda x: ', '.join(sorted([str(int(f)) for f in x.dropna().unique()]))
        ).to_dict()
        
        # Criar lista de opções formatadas: "ID - Fases: X, Y, Z"
        opcoes_alunos = ["<selecione>"] + [
            f"{id_aluno} - Fases: {fases}" 
            for id_aluno, fases in sorted(aluno_fases.items())
        ]
        
        aluno_selecionado = st.selectbox(
            "🔒 Aluno para Análise Individual",
            opcoes_alunos,
            key="aluno_individual_evolucao"
        )
        
        # Extrair apenas o ID do aluno da seleção
        if aluno_selecionado != "<selecione>":
            id_anonimizado_sel = aluno_selecionado.split(" - Fases:")[0]
        else:
            id_anonimizado_sel = "<selecione>"
    else:
        st.warning("⚠️ Nenhum aluno encontrado com os filtros selecionados")
        id_anonimizado_sel = "<selecione>"
    
    st.markdown("---")
    
    if id_anonimizado_sel and id_anonimizado_sel != "<selecione>":
        df_ind = df[df['ID_Anonimizado'] == id_anonimizado_sel].sort_values('Fase')
        
        if df_ind.empty:
            st.info("Aluno não encontrado com filtros atuais")
        else:
            # Tabela detalhada
            df_show = df_ind[['Fase','Escola','Turma','Score_Pre','Score_Pos']].copy()
            df_show['Delta'] = df_show['Score_Pos'] - df_show['Score_Pre']
            df_show = df_show.rename(columns={
                'Score_Pre': 'Pré-Teste',
                'Score_Pos': 'Pós-Teste'
            })
            
            def style_delta(val):
                if pd.isna(val):
                    return ''
                elif val > 0:
                    return 'background-color: #e8f5e8; color: #2d5016; font-weight: bold; border-left: 4px solid #28a745'
                elif val == 0:
                    return 'background-color: #f1f3f4; color: #495057; font-weight: bold; border-left: 4px solid #6c757d'
                else:
                    return 'background-color: #fdf2f2; color: #721c24; font-weight: bold; border-left: 4px solid #dc3545'
            
            styled_df = (df_show.style
                         .map(style_delta, subset=['Delta'])
                         .format({
                             'Pré-Teste': '{:.1f}',
                             'Pós-Teste': '{:.1f}',
                             'Delta': '{:+.1f}'
                         }))
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Gráficos lado a lado
            col_ev1, col_ev2 = st.columns(2)
            
            with col_ev1:
                long_scores = (df_ind.melt(id_vars=['Fase'], value_vars=['Score_Pre','Score_Pos'],
                                          var_name='Momento', value_name='Score')
                                     .replace({'Score_Pre':'Pré-Teste','Score_Pos':'Pós-Teste'}))
                
                fig_scores = px.line(long_scores, x='Fase', y='Score', color='Momento', markers=True,
                                   title=f'Pré vs Pós - {id_anonimizado_sel}',
                                   labels={'Momento': 'Teste'})
                
                fig_scores.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=[2, 3, 4],
                        ticktext=['2', '3', '4'],
                        title='Fase'
                    )
                )
                st.plotly_chart(fig_scores, use_container_width=True)
            
            with col_ev2:
                df_delta = df_ind.copy()
                df_delta['Delta'] = df_delta['Score_Pos'] - df_delta['Score_Pre']
                
                fig_delta = px.line(df_delta, x='Fase', y='Delta', markers=True,
                                  title=f'Delta - {id_anonimizado_sel}',
                                  labels={'Delta': 'Delta (Pós - Pré)'})
                
                fig_delta.update_layout(
                    xaxis=dict(
                        tickmode='array',
                        tickvals=[2, 3, 4],
                        ticktext=['2', '3', '4'],
                        title='Fase'
                    )
                )
                fig_delta.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                
                st.plotly_chart(fig_delta, use_container_width=True)
    else:
        st.info("� Selecione um aluno na lista acima para visualizar sua evolução individual detalhada")

# ========== FOOTER ==========
st.markdown("---")
st.caption("Dashboard desenvolvido por Elton Sarmanho • Utilize filtros no topo para refinar a análise")
