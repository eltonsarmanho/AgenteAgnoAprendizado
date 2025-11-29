# 📚 README - Consultador de Pares Pergunta/Resposta RAG

## 🎯 Objetivo

Consultar, visualizar e exportar **pares pergunta/resposta** salvos no banco SQLite do RagSQLITEGemini.

**Antes:** ❌ Apenas respostas visíveis  
**Depois:** ✅ Perguntas + Respostas em pares estruturados

---

## 🚀 Início Rápido

### 1. Menu Interativo (Recomendado)

```bash
cd RAG
python consultar_rag_novo.py
```

**Opções:**
```
1️⃣  Listar todas as sessões
2️⃣  Visualizar pares pergunta/resposta de uma sessão  ← NOVO
3️⃣  Buscar por palavra-chave
4️⃣  Ver estatísticas gerais
5️⃣  Exportar TODOS os pares para arquivo  ← NOVO
```

### 2. Exemplos Programáticos

```bash
cd RAG
python exemplos_pares.py
```

Demonstra 5 casos de uso:
- ✅ Extrair pares de uma sessão
- ✅ Buscar por palavra-chave
- ✅ Salvar em JSON customizado
- ✅ Filtrar por modelo de IA
- ✅ Análise de frequência de palavras

---

## 💻 Uso Programático

### Exemplo Básico

```python
from RAG.consultar_rag_novo import ConsultadorRAG

# Conectar
consultador = ConsultadorRAG(db_file="data.db")
consultador.conectar()

# Extrair pares
sessoes = consultador.listar_sessoes()
session_id = sessoes[0]['session_id']
pares = consultador.extrair_pares_pergunta_resposta(session_id)

# Usar dados
for par in pares:
    print(f"❓ {par['pergunta']}")
    print(f"🤖 {par['resposta']}\n")

consultador.desconectar()
```

### Buscar por Palavra-chave

```python
# Busca em pergunta E resposta
pares = consultador.buscar_pares_por_palavra("Banco de Dados")

for par in pares:
    print(f"Session: {par['session_id']}")
    print(f"P: {par['pergunta'][:80]}...")
    print(f"R: {par['resposta'][:80]}...\n")
```

---

## 📊 Estrutura de Dados

Cada par retornado tem esta estrutura:

```python
{
    'run_id': 'uuid-da-run',
    'session_id': 'rag_session',
    'numero': 1,                    # Número sequencial nesta sessão
    'pergunta': 'Quem são os professores?',
    'resposta': 'Os professores são...',
    'timestamp': '2025-11-21 10:30:00',
    'user_id': 'user',
    'model': 'mistral-7b'
}
```

---

## 📁 Arquivos do Projeto

| Arquivo | Descrição |
|---------|-----------|
| `RAG/consultar_rag_novo.py` | Script principal com menu interativo |
| `RAG/exemplos_pares.py` | 5 exemplos de uso programático |

---

## ✅ Status

- ✅ Script principal funcionando
- ✅ Exemplos testados
- ✅ Exportação funcionando
- ✅ Pronto para produção

---

**Versão:** 1.0  
**Data:** Novembro 2025  
**Status:** 🟢 Ativo e Funcional
