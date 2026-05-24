from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas import StatsResponse

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=StatsResponse, response_model_exclude_none=True)
async def estatisticas(pool=Depends(get_db)):
    async with pool.acquire() as conn:
        total_producoes = await conn.fetchval("SELECT COUNT(*) FROM producoes")
        total_pesquisadores = await conn.fetchval("SELECT COUNT(*) FROM pesquisadores")
        total_vetores = await conn.fetchval("SELECT COUNT(*) FROM vetores")
        data_ultima_carga = await conn.fetchval(
            "SELECT MAX(finalizado_em) FROM etl_logs WHERE status = 'sucesso'"
        )

    return StatsResponse(
        total_producoes=int(total_producoes),
        total_pesquisadores=int(total_pesquisadores),
        total_vetores=int(total_vetores),
        data_ultima_carga=data_ultima_carga,
    )
