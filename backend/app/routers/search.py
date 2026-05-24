from fastapi import APIRouter, Depends

from app.database import get_db
from app.schemas import (
    SearchSemanticRequest,
    SearchSemanticResponse,
    SearchTextRequest,
    SearchTextResponse,
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
