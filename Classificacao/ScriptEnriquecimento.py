"""
Script para enriquecer o CSV de exercícios categorizados com metadados estruturados.
Adiciona as colunas: contraindicacoes, rehab_tags, movement_pattern.
"""

import pandas as pd
import json
import time
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field
from agno.agent import Agent
from dotenv import load_dotenv
import os
from agno.models.openai import OpenAILike

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Modelo estruturado de saída
# ---------------------------------------------------------------------------

MOVEMENT_PATTERNS = Literal[
    "squat", "hinge", "push", "pull",
    "rotation", "isometric", "unilateral",
    "machine", "mobility"
]


class ExerciseMetadata(BaseModel):
    """Metadados biomecânicos e de reabilitação de um exercício."""

    contraindicacoes: str = Field(
        description=(
            "Contraindicações clínicas relevantes em snake_case separadas por ponto-e-vírgula. "
            "Use 'nenhuma' se não houver contraindicação relevante. "
            "Exemplos: lesao_lca;condromalacia_patela | dor_lombar_aguda | nenhuma"
        )
    )
    rehab_tags: str = Field(
        description=(
            "Tags de uso em reabilitação/fisioterapia separadas por ponto-e-vírgula. "
            "Indique para quais condições o exercício é útil em contexto de reab. "
            "Exemplos: pos_operatorio_joelho;fortalecimento_glúteo | estabilizacao_lombar"
        )
    )
    movement_pattern: MOVEMENT_PATTERNS = Field(
        description=(
            "Padrão de movimento principal do exercício. "
            "Deve ser exatamente um dos valores: "
            "squat, hinge, push, pull, rotation, isometric, unilateral, machine, mobility"
        )
    )


# ---------------------------------------------------------------------------
# Configuração do modelo e agente
# ---------------------------------------------------------------------------

maritaca_api_key = os.getenv("MARITALK_API_KEY")
if not maritaca_api_key:
    raise ValueError(
        "A chave de API do Maritaca não está configurada. "
        "Por favor, defina a variável de ambiente 'MARITALK_API_KEY'."
    )

model = OpenAILike(
    id="sabiazinho-4",
    name="Maritaca Sabia 4",
    api_key=maritaca_api_key,
    base_url="https://chat.maritaca.ai/api",
    temperature=0,
)

agent = Agent(
    model=model,
    markdown=False,
    structured_outputs=True,
    instructions=[
        "Você é um especialista em educação física, biomecânica e fisioterapia.",
        "Sua tarefa é enriquecer exercícios com metadados clínicos e biomecânicos.",
        "",
        "Regras obrigatórias:",
        "1. Nunca altere o nome ou categoria do exercício.",
        "2. Sempre retorne dados estruturados e coerentes do ponto de vista biomecânico.",
        "3. contraindicacoes: termos curtos em snake_case, separados por ';'. Use 'nenhuma' se não houver.",
        "4. rehab_tags: tags de uso em contexto de reabilitação, separadas por ';'.",
        "5. movement_pattern deve ser EXATAMENTE um dos valores: squat, hinge, push, pull, rotation, isometric, unilateral, machine, mobility.",
        "6. Nunca invente informações médicas complexas ou absurdas.",
        "7. Mantenha coerência com o grupo muscular informado.",
    ],
)


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def enriquecer_exercicios(
    arquivo_entrada: str = "Classificacao/exercicios_categorizado.csv",
    arquivo_saida: str = "Classificacao/exercicios_enriquecidos.csv",
    arquivo_progresso: str = "Classificacao/exercicios_enriquecidos_parcial.csv",
    delay_entre_chamadas: float = 0.5,
) -> pd.DataFrame | None:
    """
    Lê o CSV categorizado e enriquece cada exercício com metadados via IA.

    Args:
        arquivo_entrada:        CSV de entrada com colunas Exercício/Categoria/Vídeo/alongamento.
        arquivo_saida:          CSV de saída final enriquecido.
        arquivo_progresso:      CSV parcial salvo incrementalmente para tolerância a falhas.
        delay_entre_chamadas:   Pausa (s) entre chamadas à API para evitar rate-limit.

    Returns:
        DataFrame enriquecido ou None em caso de erro fatal.
    """
    # --- Leitura do CSV de entrada ---
    try:
        df = pd.read_csv(arquivo_entrada)
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {arquivo_entrada}")
        return None
    except Exception as exc:
        print(f"[ERRO] Falha ao ler o CSV: {exc}")
        return None

    # Normalizar nomes de colunas para lidar com variações de acentuação
    col_map = {}
    for col in df.columns:
        col_norm = col.strip()
        col_map[col] = col_norm
    df.rename(columns=col_map, inplace=True)

    # Detectar coluna de nome do exercício (pode ser 'Exercício' ou 'Exercicio')
    col_exercicio = next(
        (c for c in df.columns if c.lower().replace("í", "i") == "exercicio"),
        None,
    )
    col_categoria = next(
        (c for c in df.columns if c.lower() == "categoria"),
        None,
    )
    if col_exercicio is None or col_categoria is None:
        print(f"[ERRO] Colunas esperadas não encontradas. Colunas presentes: {list(df.columns)}")
        return None

    print(f"✓ Arquivo lido: {arquivo_entrada}")
    print(f"✓ Total de exercícios: {len(df)}")
    print(f"✓ Colunas detectadas: {list(df.columns)}\n")

    # --- Retomar progresso anterior, se existir ---
    registros_prontos: dict[str, dict] = {}
    if Path(arquivo_progresso).exists():
        try:
            df_parcial = pd.read_csv(arquivo_progresso)
            for _, row in df_parcial.iterrows():
                registros_prontos[str(row[col_exercicio])] = row.to_dict()
            print(f"↺  Progresso anterior encontrado: {len(registros_prontos)} exercícios já processados.\n")
        except Exception:
            print("⚠  Arquivo de progresso corrompido — começando do zero.\n")

    # --- Processar cada exercício ---
    resultados: list[dict] = []

    for idx, row in df.iterrows():
        exercicio = str(row[col_exercicio])
        categoria = str(row[col_categoria])

        # Reutilizar resultado já obtido
        if exercicio in registros_prontos:
            print(f"[{idx + 1}/{len(df)}] ↩  Reutilizando: {exercicio}")
            resultados.append(registros_prontos[exercicio])
            continue

        print(f"[{idx + 1}/{len(df)}] ⚙  Enriquecendo: {exercicio} ({categoria})")

        prompt = (
            f"Exercício: {exercicio}\n"
            f"Grupo muscular / Categoria: {categoria}\n\n"
            "Forneça as contraindicações clínicas, tags de reabilitação e o padrão de movimento principal."
        )

        metadata: ExerciseMetadata | None = None
        tentativas = 3
        for tentativa in range(1, tentativas + 1):
            try:
                response = agent.run(prompt)
                # Extrair conteúdo da resposta (RunResponse ou objeto direto)
                content = response.content if hasattr(response, "content") else response

                if isinstance(content, ExerciseMetadata):
                    metadata = content
                elif isinstance(content, dict):
                    metadata = ExerciseMetadata(**content)
                else:
                    # Fallback: parsear texto como JSON
                    import re
                    texto = str(content)
                    # Tentar achar bloco JSON na resposta
                    match = re.search(r'\{[^{}]+\}', texto, re.DOTALL)
                    raw = match.group(0) if match else texto
                    data = json.loads(raw)
                    metadata = ExerciseMetadata(**data)
                break
            except Exception as exc:
                print(f"  ⚠ Tentativa {tentativa}/{tentativas} falhou: {exc}")
                if tentativa < tentativas:
                    time.sleep(2 ** tentativa)

        if metadata is None:
            print(f"  ✗ Falha ao obter metadados — usando valores padrão.")
            metadata = ExerciseMetadata(
                contraindicacoes="nenhuma",
                rehab_tags="avaliar_individualmente",
                movement_pattern="machine",
            )

        print(
            f"  contraindicacoes : {metadata.contraindicacoes}\n"
            f"  rehab_tags       : {metadata.rehab_tags}\n"
            f"  movement_pattern : {metadata.movement_pattern}"
        )

        registro = {
            **row.to_dict(),
            "contraindicacoes": metadata.contraindicacoes,
            "rehab_tags": metadata.rehab_tags,
            "movement_pattern": metadata.movement_pattern,
        }
        resultados.append(registro)

        # Salvar progresso incremental
        pd.DataFrame(resultados).to_csv(arquivo_progresso, index=False, encoding="utf-8-sig")

        time.sleep(delay_entre_chamadas)

    # --- Montar DataFrame final ---
    df_enriquecido = pd.DataFrame(resultados)

    # Garantir ordem de colunas: originais primeiro, depois as novas
    colunas_originais = list(df.columns)
    colunas_novas = ["contraindicacoes", "rehab_tags", "movement_pattern"]
    colunas_finais = colunas_originais + [c for c in colunas_novas if c not in colunas_originais]
    df_enriquecido = df_enriquecido[colunas_finais]

    # Salvar CSV final
    df_enriquecido.to_csv(arquivo_saida, index=False, encoding="utf-8-sig")

    # Remover arquivo de progresso parcial após conclusão bem-sucedida
    if Path(arquivo_progresso).exists():
        Path(arquivo_progresso).unlink()

    print(f"\n{'='*60}")
    print(f"✓ Arquivo final criado: {arquivo_saida}")
    print(f"✓ Total de exercícios enriquecidos: {len(df_enriquecido)}")

    print("\nDistribuição de movement_pattern:")
    for pattern, qtd in df_enriquecido["movement_pattern"].value_counts().items():
        print(f"  {pattern}: {qtd}")

    return df_enriquecido


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    BASE = Path(__file__).parent

    df_resultado = enriquecer_exercicios(
        arquivo_entrada=str(BASE / "exercicios_categorizado.csv"),
        arquivo_saida=str(BASE / "exercicios_enriquecidos.csv"),
        arquivo_progresso=str(BASE / "exercicios_enriquecidos_parcial.csv"),
        delay_entre_chamadas=0.5,
    )

    if df_resultado is not None:
        print("\nPrimeiras linhas do resultado:")
        print(
            df_resultado[
                ["Exercício", "Categoria", "contraindicacoes", "rehab_tags", "movement_pattern"]
            ].head(10).to_string(index=False)
        )
