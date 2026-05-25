"""
Pipeline ETL em Python — SPK-93 (trigger-etl).

Replica as 6 fases do Apache Hop para uso via endpoint HTTP:
  1. Extração + transformação (XML → pesquisadores + produções)
  2. Enriquecimento Qualis (CSV)
  3. Enriquecimento CrossRef (DOI + resumo)
  4. Enriquecimento OpenAlex (JCR)
  5. Métricas bibliométricas
  6. Embeddings (chama o worker)
"""
from __future__ import annotations

import csv
import io
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import asyncpg
import httpx

MODEL_NAME = "all-MiniLM-L6-v2"


# ── Resultado acumulado ───────────────────────────────────────────────────────

@dataclass
class EtlResult:
    pesquisadores: int = 0
    producoes: int = 0
    qualis_match: int = 0
    doi_fill: int = 0
    resumo_fill: int = 0
    jcr_fill: int = 0
    vetores_gerados: int = 0
    erros: List[str] = field(default_factory=list)


# ── Helpers XML ───────────────────────────────────────────────────────────────

def _attr(elem: ET.Element, path: str) -> str:
    """Extrai atributo via 'CHILD/@ATTR' ou '@ATTR'."""
    if "/@" in path:
        child_tag, attr_name = path.split("/@", 1)
        child = elem.find(child_tag)
        return (child.get(attr_name) or "") if child is not None else ""
    if path.startswith("@"):
        return elem.get(path[1:]) or ""
    return ""


def _norm_issn(raw: str) -> Optional[str]:
    if not raw:
        return None
    # Remove tudo que não é dígito nem X (idêntico ao Hop: /[^0-9Xx]/g)
    s = re.sub(r"[^0-9Xx]", "", raw)
    if len(s) == 8:
        return f"{s[:4]}-{s[4:]}"
    return None


def _norm_title(raw: str) -> str:
    # Remove controles e colapsa espaços múltiplos (idêntico ao Hop: .trim().replace(/\s+/g,' '))
    s = re.sub(r"[\x00-\x1f\x7f]", "", raw)
    return re.sub(r"\s+", " ", s).strip()


# ── Configuração dos tipos de produção ────────────────────────────────────────

_PROD_CONFIGS: List[Dict] = [
    {
        "tipo": "ARTIGO",
        "loop": ".//ARTIGO-PUBLICADO",
        "titulo": "DADOS-BASICOS-DO-ARTIGO/@TITULO-DO-ARTIGO",
        "ano": "DADOS-BASICOS-DO-ARTIGO/@ANO-DO-ARTIGO",
        "doi": "DADOS-BASICOS-DO-ARTIGO/@DOI",
        "veiculo": "DETALHAMENTO-DO-ARTIGO/@TITULO-DO-PERIODICO-OU-REVISTA",
        "issn": "DETALHAMENTO-DO-ARTIGO/@ISSN",
    },
    {
        "tipo": "EVENTO",
        "loop": ".//TRABALHO-EM-EVENTOS",
        "titulo": "DADOS-BASICOS-DO-TRABALHO/@TITULO-DO-TRABALHO",
        "ano": "DADOS-BASICOS-DO-TRABALHO/@ANO-DO-TRABALHO",
        "doi": "DADOS-BASICOS-DO-TRABALHO/@DOI",
        "veiculo": "DETALHAMENTO-DO-TRABALHO/@NOME-DO-EVENTO",
        "issn": None,
    },
    {
        "tipo": "LIVRO",
        "loop": ".//LIVRO-PUBLICADO-OU-ORGANIZADO",
        "titulo": "DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO",
        "ano": "DADOS-BASICOS-DO-LIVRO/@ANO",
        "doi": "DADOS-BASICOS-DO-LIVRO/@DOI",
        "veiculo": "DADOS-BASICOS-DO-LIVRO/@TITULO-DO-LIVRO",
        "issn": None,
    },
    {
        "tipo": "CAPITULO",
        "loop": ".//CAPITULO-DE-LIVRO-PUBLICADO",
        "titulo": "DADOS-BASICOS-DO-CAPITULO/@TITULO-DO-CAPITULO-DO-LIVRO",
        "ano": "DADOS-BASICOS-DO-CAPITULO/@ANO",
        "doi": "DADOS-BASICOS-DO-CAPITULO/@DOI",
        "veiculo": "DETALHAMENTO-DO-CAPITULO/@TITULO-DO-LIVRO",
        "issn": None,
    },
]


# ── Fase 1 + 2: Extração e transformação XML ──────────────────────────────────

async def _fase_extracao(
    pool: asyncpg.Pool,
    xml_bytes_list: List[bytes],
    result: EtlResult,
) -> List[int]:
    """Parseia XMLs, faz UPSERT em pesquisadores e produções. Retorna IDs dos pesquisadores."""

    sql_pesq = """
        INSERT INTO pesquisadores
            (lattes_id, nome_completo, departamento, campus, resumo, data_atualizacao)
        VALUES ($1, $2, $3, $4, $5, NOW())
        ON CONFLICT (lattes_id) DO UPDATE SET
            nome_completo    = EXCLUDED.nome_completo,
            departamento     = EXCLUDED.departamento,
            campus           = EXCLUDED.campus,
            resumo           = EXCLUDED.resumo,
            data_atualizacao = NOW()
        RETURNING id
    """

    sql_prod = """
        INSERT INTO producoes
            (pesquisador_id, titulo, tipo_producao, ano_publicacao, nome_veiculo, issn, doi)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
        ON CONFLICT (pesquisador_id, titulo, ano_publicacao) DO UPDATE SET
            nome_veiculo = EXCLUDED.nome_veiculo,
            issn         = COALESCE(EXCLUDED.issn, producoes.issn),
            doi          = COALESCE(EXCLUDED.doi, producoes.doi)
    """

    pesquisador_ids: List[int] = []

    for xml_bytes in xml_bytes_list:
        try:
            root = ET.fromstring(xml_bytes)
        except ET.ParseError as exc:
            result.erros.append(f"XML inválido: {exc}")
            continue

        lattes_id = root.get("NUMERO-IDENTIFICADOR", "").strip()
        dados = root.find("DADOS-GERAIS")
        if dados is None or not lattes_id:
            result.erros.append("XML sem NUMERO-IDENTIFICADOR ou DADOS-GERAIS")
            continue

        nome = _norm_title(dados.get("NOME-COMPLETO", "") or "")
        depto = (dados.get("DEPARTAMENTO") or "").strip() or None
        campus = (dados.get("CAMPUS") or "").strip() or None
        resumo_elem = dados.find("RESUMO-CV")
        resumo = (
            (resumo_elem.get("TEXTO-RESUMO-CV-RH") or "").strip() or None
            if resumo_elem is not None else None
        )

        async with pool.acquire() as conn:
            row = await conn.fetchrow(sql_pesq, lattes_id, nome, depto, campus, resumo)

        pesq_id = row["id"]
        pesquisador_ids.append(pesq_id)
        result.pesquisadores += 1

        for cfg in _PROD_CONFIGS:
            for prod_elem in root.findall(cfg["loop"]):
                titulo = _norm_title(_attr(prod_elem, cfg["titulo"]))
                if not titulo:
                    continue
                ano_raw = _attr(prod_elem, cfg["ano"])
                try:
                    ano = int(ano_raw) if ano_raw else None
                except ValueError:
                    ano = None
                doi = (_attr(prod_elem, cfg["doi"]) or "").strip() or None
                veiculo = (_attr(prod_elem, cfg["veiculo"]) or "").strip() or None
                issn = _norm_issn(_attr(prod_elem, cfg["issn"])) if cfg["issn"] else None

                try:
                    async with pool.acquire() as conn:
                        await conn.execute(
                            sql_prod, pesq_id, titulo, cfg["tipo"], ano, veiculo, issn, doi
                        )
                    result.producoes += 1
                except Exception as exc:  # noqa: BLE001
                    result.erros.append(f"Produção '{titulo[:60]}': {exc}")

    return pesquisador_ids


# ── Fase 3: Qualis ────────────────────────────────────────────────────────────

def _load_qualis(csv_path: str) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Retorna (issn_map, titulo_map) com melhor estrato por ISSN/título."""
    issn_map: Dict[str, str] = {}
    titulo_map: Dict[str, str] = {}

    try:
        with open(csv_path, encoding="utf-8-sig", errors="replace", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = sorted(
                reader,
                key=lambda r: (r.get("ISSN", "").strip(), r.get("Estrato", "").strip()),
            )
        for row in rows:
            issn = _norm_issn(row.get("ISSN", "").strip())
            estrato = row.get("Estrato", "").strip()
            titulo = (row.get("Título") or row.get("Titulo", "")).strip()
            if issn and issn not in issn_map:
                issn_map[issn] = estrato
            if titulo and titulo not in titulo_map:
                titulo_map[titulo] = estrato
    except FileNotFoundError:
        pass  # Fase será pulada — erros registrados pelo chamador

    return issn_map, titulo_map


async def _fase_qualis(
    pool: asyncpg.Pool,
    result: EtlResult,
) -> None:
    qualis_csv = os.getenv("QUALIS_CSV_PATH", "")
    if not qualis_csv or not os.path.isfile(qualis_csv):
        result.erros.append(f"QUALIS_CSV_PATH não encontrado: {qualis_csv!r} — fase Qualis ignorada")
        return

    issn_map, titulo_map = _load_qualis(qualis_csv)
    if not issn_map and not titulo_map:
        result.erros.append("CSV Qualis vazio ou inválido")
        return

    sql_fetch = """
        SELECT id, issn, nome_veiculo
        FROM producoes
        WHERE tipo_producao = 'ARTIGO' AND qualis IS NULL
    """
    sql_update = "UPDATE producoes SET qualis = COALESCE($1, qualis) WHERE id = $2"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql_fetch)

    for row in rows:
        estrato = None
        issn = row["issn"]
        if issn:
            estrato = issn_map.get(issn)
        if not estrato and row["nome_veiculo"]:
            estrato = titulo_map.get(row["nome_veiculo"].strip())
        if estrato:
            async with pool.acquire() as conn:
                await conn.execute(sql_update, estrato, row["id"])
            result.qualis_match += 1


# ── Fase 4: CrossRef ──────────────────────────────────────────────────────────

_HTML_TAG = re.compile(r"<[^>]+>")


async def _fase_crossref(
    pool: asyncpg.Pool,
    result: EtlResult,
    client: httpx.AsyncClient,
) -> None:
    etl_email = os.getenv("ETL_EMAIL", "spark@email.com")
    headers = {"User-Agent": f"SPARK-ETL/1.0 (mailto:{etl_email})"}

    sql_fetch = """
        SELECT id, titulo, doi
        FROM producoes
        WHERE tipo_producao = 'ARTIGO'
    """
    sql_update = "UPDATE producoes SET doi = COALESCE($1, doi), resumo = COALESCE($2, resumo) WHERE id = $3"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql_fetch)

    for row in rows:
        new_doi: Optional[str] = None
        new_resumo: Optional[str] = None

        try:
            if row["doi"] is not None:
                # Ramo A: busca por DOI direto
                url = f"https://api.crossref.org/works/{row['doi']}?mailto={etl_email}"
                resp = await client.get(url, headers=headers, timeout=15)
                if resp.status_code == 200:
                    data = resp.json().get("message", {})
                    abstract = data.get("abstract", "")
                    if abstract:
                        new_resumo = _HTML_TAG.sub("", abstract).strip() or None
            else:
                # Ramo B: busca por título
                params = {"query.bibliographic": row["titulo"], "rows": "1", "mailto": etl_email}
                resp = await client.get(
                    "https://api.crossref.org/works", params=params, headers=headers, timeout=15
                )
                if resp.status_code == 200:
                    items = resp.json().get("message", {}).get("items", [])
                    if items and items[0].get("score", 0) > 70:
                        doi_raw = items[0].get("DOI", "")
                        new_doi = doi_raw.strip() or None
                        abstract = items[0].get("abstract", "")
                        if abstract:
                            new_resumo = _HTML_TAG.sub("", abstract).strip() or None
        except Exception:  # noqa: BLE001
            continue  # falha individual não interrompe o pipeline

        if new_doi or new_resumo:
            async with pool.acquire() as conn:
                await conn.execute(sql_update, new_doi, new_resumo, row["id"])
            if new_doi:
                result.doi_fill += 1
            if new_resumo:
                result.resumo_fill += 1


# ── Fase 5: OpenAlex ──────────────────────────────────────────────────────────

async def _fase_openalex(
    pool: asyncpg.Pool,
    result: EtlResult,
    client: httpx.AsyncClient,
) -> None:
    api_key = os.getenv("OPENALEX_APIKEY", "")

    sql_fetch = """
        SELECT DISTINCT issn
        FROM producoes
        WHERE issn IS NOT NULL AND issn != ''
    """
    sql_update = "UPDATE producoes SET jcr = COALESCE($1, jcr) WHERE issn = $2"

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql_fetch)

    for row in rows:
        issn = row["issn"]
        try:
            url = f"https://api.openalex.org/sources/issn:{issn}"
            params: Dict[str, str] = {"select": "issn_l,display_name,summary_stats"}
            if api_key:
                params["api_key"] = api_key
            resp = await client.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                jcr = (data.get("summary_stats") or {}).get("2yr_mean_citedness")
                if jcr is not None:
                    async with pool.acquire() as conn:
                        await conn.execute(sql_update, float(jcr), issn)
                    result.jcr_fill += 1
        except Exception:  # noqa: BLE001
            continue


# ── Fase 6: Métricas ──────────────────────────────────────────────────────────

_SQL_METRICAS = """
    UPDATE pesquisadores SET
        total_producoes = (SELECT COUNT(*)       FROM producoes WHERE pesquisador_id = $1),
        total_a1_a2     = (SELECT COUNT(*)       FROM producoes WHERE pesquisador_id = $2 AND qualis IN ('A1','A2')),
        indice_h        = (
            SELECT COUNT(*) FROM (
                SELECT jcr, ROW_NUMBER() OVER (ORDER BY jcr DESC) AS pos
                FROM producoes WHERE pesquisador_id = $3 AND jcr IS NOT NULL
            ) ranked WHERE jcr >= pos
        )
    WHERE id = $4
"""


async def _fase_metricas(
    pool: asyncpg.Pool,
    pesquisador_ids: List[int],
    result: EtlResult,
) -> None:
    for pid in pesquisador_ids:
        try:
            async with pool.acquire() as conn:
                await conn.execute(_SQL_METRICAS, pid, pid, pid, pid)
        except Exception as exc:  # noqa: BLE001
            result.erros.append(f"Métricas pesquisador {pid}: {exc}")


# ── Orquestrador principal ────────────────────────────────────────────────────

async def run_pipeline(
    pool: asyncpg.Pool,
    xml_bytes_list: List[bytes],
) -> EtlResult:
    """Executa as 6 fases do pipeline ETL e retorna o resultado acumulado."""
    from worker.embeddings_worker import run_worker  # import lazy para evitar circular

    result = EtlResult()

    # Fase 1 + 2: extração
    pesquisador_ids = await _fase_extracao(pool, xml_bytes_list, result)

    # Fase 3: Qualis
    await _fase_qualis(pool, result)

    # Fases 4 + 5: CrossRef + OpenAlex
    async with httpx.AsyncClient(follow_redirects=True) as client:
        await _fase_crossref(pool, result, client)
        await _fase_openalex(pool, result, client)

    # Fase 6: métricas
    await _fase_metricas(pool, pesquisador_ids, result)

    # Fase 7: embeddings
    try:
        result.vetores_gerados = await run_worker(pool)
    except Exception as exc:  # noqa: BLE001
        result.erros.append(f"Worker embeddings: {exc}")

    return result
