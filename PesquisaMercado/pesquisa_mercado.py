"""
Pesquisa de mercado com Agno.

Busca as melhores ofertas de um produto em sites oficiais brasileiros,
validando URLs em paralelo e deduplicando por domínio.
"""

import argparse
import json
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from typing import List, Optional

from agno.agent import Agent
from agno.models.deepseek import DeepSeek
from agno.models.google import Gemini
from agno.models.openai import OpenAILike
from agno.tools.duckduckgo import DuckDuckGoTools
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv(override=True)

# ---------------------------------------------------------------------------
# Domínios bloqueados: buscadores, redes sociais, comparadores e marketplaces
# ---------------------------------------------------------------------------
DOMINIOS_BLOQUEADOS: frozenset[str] = frozenset(
    {
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "yahoo.com",
        "facebook.com",
        "instagram.com",
        "youtube.com",
        "tiktok.com",
        "x.com",
        "twitter.com",
        "pinterest.com",
        "reddit.com",
        "buscape.com.br",
        "buscape.com.br",
        "zoom.com.br",
        "bondfaro.com.br",
        "pelando.com.br",
        "mercadolivre.com.br",
        "shopee.com.br",
        "olx.com.br",
        "enjoei.com.br",
    }
)

# Varejistas e fabricantes confiáveis — usados no prompt de fallback
VAREJISTAS_CONFIAVEIS = (
    "amazon.com.br, kabum.com.br, magazineluiza.com.br, americanas.com.br, "
    "casasbahia.com.br, pontofrio.com.br, extra.com.br, submarino.com.br, "
    "fastshop.com.br, leroy.com.br, havan.com.br"
)

# Instruções fixas do agente
_INSTRUCOES: List[str] = [
    "Você é um especialista em pesquisa de preços no Brasil.",
    "SEMPRE use a ferramenta de busca antes de responder — nunca invente dados.",
    "Faça buscas incluindo os termos 'comprar', 'preço' e o nome exato do produto.",
    "Use APENAS sites oficiais: fabricante oficial ou grandes varejistas reconhecidos "
    f"({VAREJISTAS_CONFIAVEIS}).",
    "NÃO use: buscadores, redes sociais, comparadores de preço (buscape, zoom, bondfaro), "
    "marketplaces (mercado livre, shopee), classificados (olx) ou blogs.",
    "Retorne entre 3 e 5 ofertas de sites DIFERENTES (um por domínio).",
    "Campo 'valor': preço exato em BRL como aparece no site (ex.: 'R$ 89,90'). "
    "Se não houver preço visível, descarte a oferta.",
    "Campo 'nome_especifico': modelo/variação exata do produto.",
    "Campo 'site': URL completa e direta da página do produto (não da loja).",
]

# ---------------------------------------------------------------------------
# Modelos de dados
# ---------------------------------------------------------------------------


class OfertaProduto(BaseModel):
    valor: Optional[str] = Field(
        default=None,
        description="Preço em BRL como aparece no site. Ex.: 'R$ 89,90'. Null se não encontrado.",
    )
    nome_especifico: str = Field(
        description="Nome/modelo exato da oferta."
    )
    site: str = Field(description="URL completa da página do produto.")


class ResultadoPesquisaMercado(BaseModel):
    produto: str = Field(description="Produto pesquisado.")
    ofertas: List[OfertaProduto] = Field(
        description="Melhores ofertas encontradas, máximo 5, uma por domínio."
    )


# ---------------------------------------------------------------------------
# Fábrica de modelo / agente
# ---------------------------------------------------------------------------


def _criar_modelo(provider: str):
    p = provider.strip().lower()

    if p == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Defina GOOGLE_API_KEY no .env para usar Gemini.")
        return Gemini(
            id=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
            api_key=api_key,
            temperature=0,
        )

    if p == "maritalk":
        api_key = os.getenv("MARITALK_API_KEY")
        if not api_key:
            raise ValueError("Defina MARITALK_API_KEY no .env para usar MariTalk.")
        return OpenAILike(
            id=os.getenv("MARITALK_MODEL", "sabia-3.1"),
            name="MariTalk sabia-3.1",
            api_key=api_key,
            base_url="https://chat.maritaca.ai/api",
            temperature=0,
        )

    if p == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("Defina DEEPSEEK_API_KEY no .env para usar DeepSeek.")
        return DeepSeek(
            id=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            api_key=api_key,
            temperature=0,
        )

    raise ValueError(f"Provider inválido: '{provider}'. Use 'gemini', 'maritalk' ou 'deepseek'.")


def _criar_agente(provider: str) -> Agent:
    return Agent(
        model=_criar_modelo(provider),
        tools=[
            DuckDuckGoTools(
                enable_search=True,
                enable_news=False,
                fixed_max_results=10,
            )
        ],
        instructions=_INSTRUCOES,
        expected_output=(
            "JSON com os campos: produto (str), ofertas (lista de até 5 objetos com "
            "valor, nome_especifico e site). Apenas sites oficiais com preço visível."
        ),
        output_schema=ResultadoPesquisaMercado,
        structured_outputs=True,
        markdown=False,
        add_datetime_to_context=True,
        compress_tool_results=True,
        tool_call_limit=6,
        retries=2,
    )


# ---------------------------------------------------------------------------
# Validação de URLs (paralela)
# ---------------------------------------------------------------------------

_UA = "Mozilla/5.0 (AgentePesquisaMercado/2.0)"
_CODIGOS_OK = {200, 301, 302, 401, 403, 405}


def _dominio(url: str) -> str:
    """Retorna o domínio normalizado (sem www.) ou '' em caso de erro."""
    try:
        return (urlparse(url).netloc or "").lower().removeprefix("www.")
    except Exception:
        return ""


def _dominio_bloqueado(url: str) -> bool:
    dom = _dominio(url)
    if not dom:
        return True
    return any(
        dom == b or dom.endswith(f".{b}") for b in DOMINIOS_BLOQUEADOS
    )


def _url_ativa(url: str, timeout: int = 8) -> bool:
    """Verifica se a URL está acessível, tentando HEAD e GET como fallback."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False

    for method in ("HEAD", "GET"):
        try:
            req = Request(url, headers={"User-Agent": _UA}, method=method)
            with urlopen(req, timeout=timeout) as resp:
                return int(getattr(resp, "status", 200)) < 400
        except HTTPError as e:
            if e.code in _CODIGOS_OK:
                return True
            if method == "HEAD":
                continue          # tenta GET
            return False
        except (URLError, OSError):
            return False
        except Exception:
            if method == "HEAD":
                continue
            return False
    return False


def _filtrar_paralelo(
    ofertas: List[OfertaProduto], max_workers: int = 8
) -> List[OfertaProduto]:
    """
    Filtra ofertas em paralelo:
    - Remove domínios bloqueados
    - Remove URLs inativas
    - Mantém no máximo uma oferta por domínio
    """
    # Pré-filtragem rápida (sem I/O)
    candidatos: List[OfertaProduto] = []
    dominios_vistos: set[str] = set()
    for oferta in ofertas:
        site = (oferta.site or "").strip()
        if not site or _dominio_bloqueado(site):
            continue
        dom = _dominio(site)
        if dom in dominios_vistos:
            continue
        dominios_vistos.add(dom)
        candidatos.append(oferta)

    if not candidatos:
        return []

    # Verificação de URLs em paralelo
    validas: List[OfertaProduto] = []
    with ThreadPoolExecutor(max_workers=min(max_workers, len(candidatos))) as pool:
        futuro_para_oferta = {
            pool.submit(_url_ativa, o.site): o for o in candidatos
        }
        for futuro in as_completed(futuro_para_oferta):
            oferta = futuro_para_oferta[futuro]
            try:
                if futuro.result():
                    validas.append(oferta)
            except Exception:
                pass  # URL inacessível — descarta

    # Mantém a ordem original
    ordem = {id(o): i for i, o in enumerate(candidatos)}
    validas.sort(key=lambda o: ordem.get(id(o), 999))
    return validas


# ---------------------------------------------------------------------------
# Parser de resposta do agente
# ---------------------------------------------------------------------------


def _parse_resposta(conteudo, produto: str) -> ResultadoPesquisaMercado:
    """Converte o conteúdo bruto da resposta para ResultadoPesquisaMercado."""
    if isinstance(conteudo, ResultadoPesquisaMercado):
        return conteudo
    if isinstance(conteudo, dict):
        return ResultadoPesquisaMercado.model_validate(conteudo)
    if isinstance(conteudo, str):
        texto = conteudo.strip()
        # Remove blocos de código Markdown (```json ... ```)
        texto = re.sub(r"^```[a-z]*\n?", "", texto, flags=re.IGNORECASE)
        texto = re.sub(r"\n?```$", "", texto).strip()
        return ResultadoPesquisaMercado.model_validate_json(texto)
    raise ValueError(
        f"Não foi possível interpretar a resposta do agente (tipo={type(conteudo)})."
    )


# ---------------------------------------------------------------------------
# Função principal de pesquisa
# ---------------------------------------------------------------------------


def pesquisar_mercado(produto: str, provider: str) -> ResultadoPesquisaMercado:
    agente = _criar_agente(provider)

    prompt_principal = (
        f"Pesquise '{produto}' no Brasil e retorne as melhores ofertas disponíveis hoje. "
        "Inclua preço, modelo exato e URL direta da página do produto. "
        "Priorize páginas com preço visível em BRL."
    )

    resposta = agente.run(prompt_principal)
    resultado = _parse_resposta(resposta.content, produto)
    resultado.ofertas = _filtrar_paralelo(resultado.ofertas)

    # Fallback: se todas as ofertas foram descartadas, tenta busca mais direcionada
    if not resultado.ofertas:
        prompt_fallback = (
            f"Refaça a busca por '{produto}' priorizando estes varejistas: "
            f"{VAREJISTAS_CONFIAVEIS}. "
            "Retorne de 3 a 5 ofertas com preço em BRL, nome exato e URL da página do produto."
        )
        resposta_fb = agente.run(prompt_fallback)
        resultado_fb = _parse_resposta(resposta_fb.content, produto)
        resultado.ofertas = _filtrar_paralelo(resultado_fb.ofertas)

    return resultado


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pesquisa de mercado — retorna ofertas de sites oficiais.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("produto", nargs="?", help="Produto a pesquisar.")
    parser.add_argument(
        "--provider",
        default=None,
        choices=["gemini", "maritalk", "deepseek"],
        help="LLM a usar. Se omitido, será perguntado interativamente.",
    )
    args = parser.parse_args()

    produto = args.produto or input("Digite o produto para pesquisar: ").strip()
    if not produto:
        raise ValueError("Informe um produto válido.")

    _PROVIDERS_VALIDOS = {"gemini", "maritalk", "deepseek"}
    _OPCOES_PROVIDER = {
        "1": "gemini",
        "2": "maritalk",
        "3": "deepseek",
    }

    provider = args.provider
    if not provider:
        env_provider = os.getenv("PESQUISA_MERCADO_PROVIDER", "").strip().lower()
        if env_provider in _PROVIDERS_VALIDOS:
            provider = env_provider
        else:
            print("\nEscolha o modelo de linguagem:")
            print("  [1] Gemini      (Google  — gemini-2.5-flash)")
            print("  [2] MariTalk    (Maritaca AI — sabia-3.1)")
            print("  [3] DeepSeek V3 (DeepSeek  — gratuito / alta qualidade)")
            while True:
                escolha = input("Opção (1, 2 ou 3): ").strip()
                if escolha in _OPCOES_PROVIDER:
                    provider = _OPCOES_PROVIDER[escolha]
                    break
                print("  Opção inválida. Digite 1, 2 ou 3.")
        print(f"\nUsando provider: {provider}\n")

    resultado = pesquisar_mercado(produto=produto, provider=provider)
    print(json.dumps(resultado.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

