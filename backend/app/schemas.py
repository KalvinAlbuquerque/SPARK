from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ── Shared nested models ──────────────────────────────────────────────────────

class PesquisadorSummary(BaseModel):
    id: int
    nome_completo: str
    departamento: Optional[str] = None
    campus: Optional[str] = None


class PesquisadorNested(BaseModel):
    id: int
    nome_completo: str
    departamento: Optional[str] = None
    campus: Optional[str] = None
    total_producoes: int
    indice_h: int
    total_a1_a2: int


# ── Search ────────────────────────────────────────────────────────────────────

class SearchFilters(BaseModel):
    ano_min: Optional[int] = None
    ano_max: Optional[int] = None
    qualis: Optional[List[str]] = None
    jcr_min: Optional[float] = None
    jcr_max: Optional[float] = None
    jcr_nulo: bool = False
    tipos: Optional[List[str]] = None
    pesquisador_id: Optional[int] = None


class SearchTextRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)
    page: int = Field(1, ge=1)


class SearchSemanticRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)


class ProducaoCard(BaseModel):
    id: int
    titulo: str
    tipo_producao: str
    ano_publicacao: Optional[int] = None
    nome_veiculo: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    qualis: Optional[str] = None
    jcr: Optional[float] = None
    pesquisador: PesquisadorSummary
    similarity_score: Optional[float] = None


class SearchTextResponse(BaseModel):
    total: int
    page: int
    total_pages: int
    resultados: List[ProducaoCard]


class SearchSemanticResponse(BaseModel):
    resultados: List[ProducaoCard]


# ── Producoes ─────────────────────────────────────────────────────────────────

class TipoProducaoItem(BaseModel):
    tipo: str
    total: int


class ProducaoDetalhe(BaseModel):
    id: int
    titulo: str
    tipo_producao: str
    ano_publicacao: Optional[int] = None
    nome_veiculo: Optional[str] = None
    issn: Optional[str] = None
    doi: Optional[str] = None
    resumo: Optional[str] = None
    qualis: Optional[str] = None
    jcr: Optional[float] = None
    pesquisador: PesquisadorNested


# ── Pesquisadores ─────────────────────────────────────────────────────────────

class PesquisadorProfile(BaseModel):
    id: int
    lattes_id: str
    nome_completo: str
    departamento: Optional[str] = None
    campus: Optional[str] = None
    resumo: Optional[str] = None
    data_atualizacao: Optional[datetime] = None
    total_producoes: int
    indice_h: int
    total_a1_a2: int


class PesquisadorProducaoItem(BaseModel):
    id: int
    titulo: str
    tipo_producao: str
    ano_publicacao: Optional[int] = None
    nome_veiculo: Optional[str] = None
    qualis: Optional[str] = None
    jcr: Optional[float] = None


class PesquisadorProducoesResponse(BaseModel):
    total: int
    page: int
    total_pages: int
    resultados: List[PesquisadorProducaoItem]


class AnoStat(BaseModel):
    ano: int
    total: int


class QualisStat(BaseModel):
    qualis: str
    total: int


class PesquisadorStatsResponse(BaseModel):
    por_ano: List[AnoStat]
    por_qualis: List[QualisStat]


# ── Stats ─────────────────────────────────────────────────────────────────────

class StatsResponse(BaseModel):
    total_producoes: int
    total_pesquisadores: int
    total_vetores: int
    data_ultima_carga: Optional[datetime] = None


# ── Internal ──────────────────────────────────────────────────────────────────

class TriggerEmbeddingsResponse(BaseModel):
    vetores_gerados: int


class TriggerEtlResponse(BaseModel):
    pesquisadores: int
    producoes: int
    qualis_match: int
    doi_fill: int
    resumo_fill: int
    jcr_fill: int
    vetores_gerados: int
    erros: List[str]


class PesquisadorAdminItem(BaseModel):
    id: int
    lattes_id: str
    nome_completo: str
    departamento: Optional[str] = None
    campus: Optional[str] = None
    total_producoes: int
    data_atualizacao: Optional[datetime] = None


class PesquisadorAdminListResponse(BaseModel):
    total: int
    resultados: List[PesquisadorAdminItem]


class PesquisadorCreateRequest(BaseModel):
    lattes_id: str = Field(..., min_length=1, max_length=16)
    nome_completo: str = Field(..., min_length=1, max_length=255)
    departamento: Optional[str] = Field(None, max_length=255)
    campus: Optional[str] = Field(None, max_length=100)
