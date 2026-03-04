# PesquisaMercado

Pesquisa de mercado na internet com Agno.

Entrada:
- `produto`

Saida:
- `valor`
- `nome_especifico`
- `site`

## Configuracao

No `.env`, defina uma chave conforme o provider:

- `PESQUISA_MERCADO_PROVIDER=maritalk` (padrao) ou `gemini`
- `MARITALK_API_KEY=...` para Maritalk
- `GOOGLE_API_KEY=...` para Gemini

Opcional:
- `MARITALK_MODEL=sabia-3.1`
- `GEMINI_MODEL=gemini-2.5-flash`

## Execucao

Com argumento:

```bash
.venv/bin/python PesquisaMercado/pesquisa_mercado.py "whey protein concentrado 900g"
```

Escolhendo provider:

```bash
.venv/bin/python PesquisaMercado/pesquisa_mercado.py "creatina 300g" --provider gemini
```
