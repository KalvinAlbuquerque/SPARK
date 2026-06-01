from fastapi import APIRouter, Depends, Query

from app.database import get_db
from app.schemas import (
    SearchSemanticRequest,
    SearchSemanticResponse,
    SearchTextRequest,
    SearchTextResponse,
    SuggestResponse,
)
from app.services.semantic_search import search_semantic
from app.services.text_search import search_text

router = APIRouter(prefix="/api/search", tags=["busca"])


@router.post(
    "/text",
    response_model=SearchTextResponse,
    response_model_exclude_none=True,
)
async def busca_textual(body: SearchTextRequest, pool=Depends(get_db)):
    return await search_text(pool, body.query, body.filters, body.page)


@router.post(
    "/semantic",
    response_model=SearchSemanticResponse,
    response_model_exclude_none=True,
)
async def busca_semantica(body: SearchSemanticRequest, pool=Depends(get_db)):
    return await search_semantic(pool, body.query, body.filters)


@router.get("/suggest", response_model=SuggestResponse)
async def suggest(q: str = Query(..., min_length=2), pool=Depends(get_db)):
    pattern = f"%{q}%"
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(
                """
                SELECT DISTINCT titulo
                FROM producoes
                WHERE titulo ILIKE $1
                ORDER BY titulo
                LIMIT 5
                """,
                pattern,
            )
        except Exception:
            rows = []
    return SuggestResponse(sugestoes=[r["titulo"] for r in rows])
