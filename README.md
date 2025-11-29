# 🤖 AgenteAgno - Sistema de Agentes com RAG

Projeto multi-agente inteligente com Retrieval-Augmented Generation (RAG), busca vetorial e tradução automática.

## 📋 Características

- **🧠 RAG (Retrieval-Augmented Generation)**: Sistema RAG com SQLite e Gemini
- **💬 Consultador de Pares Q&A**: Menu interativo para consultar pares pergunta/resposta
- **🌍 Tradução Multi-Agente**: Tradução automática para Francês/Espanhol com detecção de idioma
- **📍 Extração Geográfica**: Extração de coordenadas e dados geográficos
- **🔍 Busca Vetorial**: Busca avançada com embeddings
- **📊 23 Pares Q&A**: Base de dados com perguntas e respostas de diferentes sessões

## 📁 Estrutura do Projeto

```
AgenteAgno/
├── RAG/
│   ├── RagSQLITE.py           # Sistema RAG com SQLite
│   ├── RagSQLITEGemini.py     # Sistema RAG com Gemini
│   ├── consultar_rag_novo.py  # Consultador com menu interativo
│   └── exemplos_pares.py      # 5 exemplos de uso
├── Extract/
│   ├── GeoExtractor.py        # Extração de coordenadas
│   └── ExtractByAgent.py      # Extração via agentes
├── workflow/
│   └── TesteMultiAgente.py    # Multi-agente tradução FR/ES
├── main.py                    # Script principal
├── test_embedding.py          # Testes de embeddings
├── data.db                    # Banco SQLite com 23 pares Q&A
└── README.md                  # Este arquivo
```

## 🚀 Início Rápido

### Pré-requisitos

```bash
python 3.8+
pip install agno
pip install python-dotenv
```

### Usar Menu Interativo

```bash
cd AgenteAgno/RAG
python consultar_rag_novo.py
```

**Opções:**
- 1️⃣ Listar todas as sessões
- 2️⃣ Visualizar pares pergunta/resposta
- 3️⃣ Buscar por palavra-chave
- 4️⃣ Ver estatísticas
- 5️⃣ Exportar todos os pares

### Executar Exemplos

```bash
python exemplos_pares.py
```

Demonstra 5 casos de uso:
1. Extrair pares de uma sessão
2. Buscar por palavra-chave
3. Exportar para JSON customizado
4. Filtrar por modelo de IA
5. Análise de frequência de palavras

### Usar em Código

```python
from RAG.consultar_rag_novo import ConsultadorRAG

consultador = ConsultadorRAG(db_file="data.db")
consultador.conectar()

# Listar sessões
sessoes = consultador.listar_sessoes()

# Extrair pares
pares = consultador.extrair_pares_pergunta_resposta(sessoes[0]['session_id'])

# Buscar por palavra
resultados = consultador.buscar_pares_por_palavra("professores")

# Exportar
consultador.exportar_json(pares)
consultador.exportar_txt(pares)

consultador.desconectar()
```

## 📊 Dados do Projeto

| Métrica | Valor |
|---------|-------|
| **Linhas de código** | ~1,500 |
| **Scripts Python** | 9 |
| **Pares Q&A** | 23 |
| **Sessões** | 3 |
| **Modelos de IA** | 4 (Qwen, Mistral, Llama, Sabia) |
| **Métodos/Funções** | 25+ |

### Modelos Utilizados

- 🔴 **Qwen2-7B-Instruct**: 9 respostas
- 🟣 **Mistral-7B**: 3 respostas
- 🟠 **Llama-3.1-8B**: 4 respostas
- 🟢 **Maritaca Sabia-3**: 7 respostas

## 🤖 Scripts Principais

### 1. `consultar_rag_novo.py` (350 linhas)

Consultador interativo com 7 métodos principais:

```python
class ConsultadorRAG:
    def conectar()                                    # Conectar ao banco
    def listar_sessoes()                             # Listar sessões
    def extrair_pares_pergunta_resposta(session_id)  # Extrair pares
    def buscar_pares_por_palavra(palavra)            # Buscar
    def exportar_json(pares, arquivo)                # Exportar JSON
    def exportar_txt(pares, arquivo)                 # Exportar TXT
    def menu_interativo()                            # Menu com 5 opções
```

### 2. `exemplos_pares.py` (150 linhas)

5 exemplos práticos demonstrando:
- Extração de dados
- Busca e filtros
- Exportação
- Análise estatística

### 3. `TesteMultiAgente.py` (90 linhas)

Sistema multi-agente com:
- Detecção automática de idioma
- Tradução para Francês/Espanhol
- 2 implementações (Workflow e Agente simples)

### 4. `RagSQLITE.py` (200 linhas)

Sistema RAG completo com SQLite:
- Processamento de documentos
- Embeddings
- Busca semântica

## 📦 Estrutura de Dados

### Pares Pergunta/Resposta

```python
{
    'run_id': 'uuid',
    'session_id': 'rag_session',
    'numero': 1,
    'pergunta': 'Quem são os professores?',
    'resposta': 'Os professores são...',
    'timestamp': '2025-11-21 10:30:00',
    'user_id': 'user',
    'model': 'mistral-7b'
}
```

## 🔧 Configuração

### .env (Exemplo)

```
MARITALK_API_KEY=sua_chave_aqui
GOOGLE_API_KEY=sua_chave_aqui
```

## 💻 Exemplos de Uso

### Exemplo 1: Menu Interativo

```bash
$ python RAG/consultar_rag_novo.py

📋 CONSULTADOR DE PARES PERGUNTA/RESPOSTA
1. Listar todas as sessões
2. Visualizar pares de uma sessão
3. Buscar por palavra-chave
4. Ver estatísticas
5. Exportar todos os pares
0. Sair

Escolha uma opção: 2
```

### Exemplo 2: Extrair Pares Programaticamente

```python
from RAG.consultar_rag_novo import ConsultadorRAG

c = ConsultadorRAG()
c.conectar()
pares = c.extrair_pares_pergunta_resposta('rag_hf_otimizado')
print(f"✅ Extraídos {len(pares)} pares")
c.desconectar()
```

### Exemplo 3: Buscar e Exportar

```python
consultador = ConsultadorRAG()
consultador.conectar()

# Buscar
resultados = consultador.buscar_pares_por_palavra("banco de dados")

# Exportar
consultador.exportar_json(resultados, "banco_dados.json")
consultador.exportar_txt(resultados, "banco_dados.txt")

consultador.desconectar()
```

## 📈 Estatísticas do Banco

```
Total de Sessões: 3

1. rag_hf_otimizado
   └─ 15 pares
   
2. rag_session_maritaca
   └─ 7 pares
   
3. rag_session
   └─ 1 par

Total: 23 pares pergunta/resposta
```

## 🌐 Tradutor Multi-Agente

```python
from workflow.TesteMultiAgente import processar_com_idioma_simples

# Francês (padrão)
processar_com_idioma_simples("Povos originários do Brasil")

# Espanhol
processar_com_idioma_simples("Povos originários. Responda em espanhol")
```

## 📚 Documentação Completa

Ver em cada arquivo:
- `RAG/consultar_rag_novo.py` - Docstrings detalhadas
- `RAG/exemplos_pares.py` - 5 exemplos comentados
- `workflow/TesteMultiAgente.py` - Explicação de idiomas

## 🔗 Repositório

https://github.com/eltonsarmanho/AgenteAgnoAprendizado

## 📝 Licença

MIT

## 👥 Autor

Elton Sarmanho

---

**Status**: ✅ Pronto para produção

**Última atualização**: Novembro 2025

**Versão**: 1.0
