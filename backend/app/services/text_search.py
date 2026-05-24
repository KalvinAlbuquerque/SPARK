from __future__ import annotations

import math
import re
from typing import Any

import asyncpg

from app.schemas import (
    PesquisadorSummary,
    ProducaoCard,
    SearchFilters,
    SearchTextResponse,
)

PAGE_SIZE = 20

QUALIS_B1_PLUS = ["B1", "B2", "B3", "B4", "B5", "C"]


def normalize_query(query: str) -> str:
    """Translate explicit AND/NOT operators to websearch_to_tsquery format."""
    q = query.strip()
    # AND is implicit in websearch_to_tsquery; remove it
    q = re.sub(r"\bAND\b\s*", " ", q, flags=re.IGNORECASE)
    # NOT word → -word (websearch_to_tsquery NOT operator)
    q = re.sub(r"\bNOT\s+", "-", q, flags=re.IGNORECASE)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def expand_qualis(qualis_list: list[str]) -> list[str]:
    """Expand 'B1+' shortcut to all strata from B1 downwards."""
    result: list[str] = []
    for q in qualis_list:
        if q == "B1+":
            result.extend(QUALIS_B1_PLUS)
        else:
            result.append(q)
    return list(dict.fromkeys(result))


def _build_filters(filters: SearchFilters, params: list[Any], idx: int) -> tuple[str, int]:
    """Append filter conditions to params and return the SQL fragment + next idx."""
    conditions: list[str] = []

    if filters.ano_min is not None:
        conditions.append(f"p.ano_publicacao >= ${idx}")
        params.append(filters.ano_min)
        idx += 1

    if filters.ano_max is not None:
        conditions.append(f"p.ano_publicacao <= ${idx}")
        params.append(filters.ano_max)
        idx += 1

    if filters.qualis:
        expanded = expand_qualis(filters.qualis)
        ph = ", ".join(f"${idx + i}" for i in range(len(expanded)))
        conditions.append(f"p.qualis IN ({ph})")
        params.extend(expanded)
        idx += len(expanded)

    if filters.tipos:
        ph = ", ".join(f"${idx + i}" for i in range(len(filters.tipos)))
        conditions.append(f"p.tipo_producao IN ({ph})")
        params.extend(filters.tipos)
        idx += len(filters.tipos)

    jcr_parts: list[str] = []
    if filters.jcr_min is not None:
        jcr_parts.append(f"p.jcr >= ${idx}")
        params.append(filters.jcr_min)
        idx += 1
    if filters.jcr_max is not None:
        jcr_parts.append(f"p.jcr <= ${idx}")
        params.append(filters.jcr_max)
        idx += 1

    if jcr_parts:
        jcr_clause = " AND ".join(jcr_parts)
        if filters.jcr_nulo:
            conditions.append(f"({jcr_clause} OR p.jcr IS NULL)")
        else:
            conditions.append(f"({jcr_clause})")
    elif filters.jcr_nulo:
        conditions.append("p.jcr IS NULL")

    if filters.pesquisador_id is not None:
        conditions.append(f"p.pesquisador_id = ${idx}")
        params.append(filters.pesquisador_id)
        idx += 1

    sql = (" AND " + " AND ".join(conditions)) if conditions else ""
    return sql, idx


def _row_to_card(row: Any) -> ProducaoCard:
    return ProducaoCard(
        id=row["id"],
        titulo=row["titulo"],
        tipo_producao=row["tipo_producao"],
        ano_publicacao=row["ano_publicacao"],
        nome_veiculo=row["nome_veiculo"] or None,
        issn=row["issn"] or None,
        doi=row["doi"] or None,
        qualis=row["qualis"] or None,
        jcr=float(row["jcr"]) if row["jcr"] is not None else None,
        pesquisador=PesquisadorSummary(
            id=row["pesquisador_id"],
            nome_completo=row["nome_completo"],
            departamento=row["departamento"] or None,
            campus=row["campus"] or None,
        ),
    )


async def search_text(
    pool: asyncpg.Pool,
    query: str,
    filters: SearchFilters,
    page: int,
) -> SearchTextResponse:
    normalized = normalize_query(query)
    offset = (page - 1) * PAGE_SIZE

    params: list[Any] = [normalized]
    filter_sql, next_idx = _build_filters(filters, params, 2)
    params.append(PAGE_SIZE)
    params.append(offset)
    limit_ph = f"${next_idx}"
    offset_ph = f"${next_idx + 1}"

    sql = f"""
        SELECT
            p.id, p.titulo, p.tipo_producao, p.ano_publicacao, p.nome_veiculo,
            p.issn, p.doi, p.qualis, p.jcr,
            pe.id AS pesquisador_id, pe.nome_completo, pe.departamento, pe.campus,
            ts_rank(p.texto_busca, websearch_to_tsquery('portuguese', $1)) AS rank,
            COUNT(*) OVER() AS total_count
        FROM producoes p
        JOIN pesquisadores pe ON pe.id = p.pesquisador_id
        WHERE p.texto_busca @@ websearch_to_tsquery('portuguese', $1)
        {filter_sql}
        ORDER BY rank DESC
        LIMIT {limit_ph} OFFSET {offset_ph}
    """

    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(sql, *params)
        except Exception:
            rows = []

    total = int(rows[0]["total_count"]) if rows else 0
    total_pages = math.ceil(total / PAGE_SIZE) if total > 0 else 0

    return SearchTextResponse(
        total=total,
        page=page,
        total_pages=total_pages,
        resultados=[_row_to_card(r) for r in rows],
    )
