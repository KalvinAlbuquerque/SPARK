from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.database import get_db
from app.schemas import ProducaoDetalhe, PesquisadorNested, TipoProducaoItem

router = APIRouter(prefix="/api/producoes", tags=["producoes"])


@router.get(
    "/tipos",
    response_model=List[TipoProducaoItem],
)
async def listar_tipos(pool=Depends(get_db)):
    sql = """
        SELECT tipo_producao AS tipo, COUNT(*) AS total
        FROM producoes
        GROUP BY tipo_producao
        ORDER BY total DESC
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)
    return [TipoProducaoItem(tipo=r["tipo"], total=r["total"]) for r in rows]


@router.get(
    "/{producao_id}",
    response_model=ProducaoDetalhe,
    response_model_exclude_none=True,
)
async def detalhe_producao(producao_id: int, pool=Depends(get_db)):
    sql = """
        SELECT
            p.id, p.titulo, p.tipo_producao, p.ano_publicacao, p.nome_veiculo,
            p.issn, p.doi, p.resumo, p.qualis, p.jcr,
            pe.id AS pesquisador_id, pe.nome_completo, pe.departamento, pe.campus,
            pe.total_producoes, pe.indice_h, pe.total_a1_a2
        FROM producoes p
        JOIN pesquisadores pe ON pe.id = p.pesquisador_id
        WHERE p.id = $1
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, producao_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Produção não encontrada")

    return ProducaoDetalhe(
        id=row["id"],
        titulo=row["titulo"],
        tipo_producao=row["tipo_producao"],
        ano_publicacao=row["ano_publicacao"],
        nome_veiculo=row["nome_veiculo"] or None,
        issn=row["issn"] or None,
        doi=row["doi"] or None,
        resumo=row["resumo"] or None,
        qualis=row["qualis"] or None,
        jcr=float(row["jcr"]) if row["jcr"] is not None else None,
        pesquisador=PesquisadorNested(
            id=row["pesquisador_id"],
            nome_completo=row["nome_completo"],
            departamento=row["departamento"] or None,
            campus=row["campus"] or None,
            total_producoes=row["total_producoes"],
            indice_h=row["indice_h"],
            total_a1_a2=row["total_a1_a2"],
        ),
    )
