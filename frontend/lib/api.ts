const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'https://spark-production-1903.up.railway.app';

export interface PesquisadorSummary {
  id: number;
  nome_completo: string;
  departamento?: string;
  campus?: string;
}

export interface PesquisadorNested extends PesquisadorSummary {
  total_producoes: number;
  indice_h: number;
  total_a1_a2: number;
}

export interface ProducaoCard {
  id: number;
  titulo: string;
  tipo_producao: string;
  ano_publicacao?: number;
  nome_veiculo?: string;
  issn?: string;
  doi?: string;
  qualis?: string;
  jcr?: number;
  pesquisador: PesquisadorSummary;
  similarity_score?: number;
}

export interface ProducaoDetalhe {
  id: number;
  titulo: string;
  tipo_producao: string;
  ano_publicacao?: number;
  nome_veiculo?: string;
  issn?: string;
  doi?: string;
  resumo?: string;
  qualis?: string;
  jcr?: number;
  pesquisador: PesquisadorNested;
}

export interface PesquisadorProfile {
  id: number;
  lattes_id: string;
  nome_completo: string;
  departamento?: string;
  campus?: string;
  resumo?: string;
  data_atualizacao?: string;
  total_producoes: number;
  indice_h: number;
  total_a1_a2: number;
}

export interface PesquisadorProducaoItem {
  id: number;
  titulo: string;
  tipo_producao: string;
  ano_publicacao?: number;
  nome_veiculo?: string;
  qualis?: string;
  jcr?: number;
}

export interface SearchFilters {
  ano_min?: number;
  ano_max?: number;
  anos?: number[];
  qualis?: string[];
  jcr_min?: number;
  jcr_max?: number;
  jcr_nulo?: boolean;
  tipos?: string[];
}

export interface FacetItem {
  valor: string;
  total: number;
}

export interface SearchFacetas {
  qualis: FacetItem[];
  tipos: FacetItem[];
  anos: FacetItem[];
}

export interface TextSearchResult {
  total: number;
  page: number;
  total_pages: number;
  resultados: ProducaoCard[];
  facetas?: SearchFacetas;
}

export interface SemanticSearchResult {
  resultados: ProducaoCard[];
  facetas?: SearchFacetas;
}

export interface PesquisadorStats {
  por_ano: { ano: number; total: number }[];
  por_qualis: { qualis: string; total: number }[];
}

export interface GlobalStats {
  total_producoes: number;
  total_pesquisadores: number;
  total_vetores: number;
  data_ultima_carga?: string;
}

export interface PesquisadorProducoesResponse {
  total: number;
  page: number;
  total_pages: number;
  resultados: PesquisadorProducaoItem[];
}

export interface PesquisadorAdminItem {
  id: number;
  lattes_id: string;
  nome_completo: string;
  departamento?: string;
  campus?: string;
  total_producoes: number;
  data_atualizacao?: string;
}

export interface PesquisadorAdminListResponse {
  total: number;
  resultados: PesquisadorAdminItem[];
}

export interface SuggestResponse {
  sugestoes: string[];
}

export interface TriggerEtlResponse {
  pesquisadores: number;
  producoes: number;
  qualis_match: number;
  doi_fill: number;
  resumo_fill: number;
  jcr_fill: number;
  vetores_gerados: number;
  erros: string[];
}

export interface ReprocessarResponse {
  qualis_match: number;
  doi_fill: number;
  resumo_fill: number;
  jcr_fill: number;
  vetores_gerados: number;
  erros: string[];
}

export interface PesquisadorCreateRequest {
  lattes_id: string;
  nome_completo: string;
  departamento?: string;
  campus?: string;
}

export interface PesquisadorUpdateRequest {
  nome_completo?: string;
  departamento?: string;
  campus?: string;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function proxyGet<T>(path: string): Promise<T> {
  const res = await fetch(path, { cache: 'no-store' });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function proxyPost<T>(path: string, body: FormData): Promise<T> {
  const res = await fetch(path, { method: 'POST', body });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function proxyPostJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    let msg = `${res.status} ${res.statusText}`;
    try { const j = await res.json(); if (j.error) msg = j.error; } catch { /* ignore */ }
    throw new Error(msg);
  }
  return res.json();
}

async function proxyPut<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

async function proxyDelete(path: string): Promise<void> {
  const res = await fetch(path, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error(`${res.status} ${res.statusText}`);
}

export const api = {
  searchText: (query: string, filters: SearchFilters = {}, page = 1) =>
    post<TextSearchResult>('/api/search/text', { query, filters, page }),

  searchSemantic: (query: string, filters: SearchFilters = {}) =>
    post<SemanticSearchResult>('/api/search/semantic', { query, filters }),

  getProducao: (id: number) =>
    get<ProducaoDetalhe>(`/api/producoes/${id}`),

  getPesquisador: (id: number) =>
    get<PesquisadorProfile>(`/api/pesquisadores/${id}`),

  getPesquisadorProducoes: (id: number, page = 1) =>
    get<PesquisadorProducoesResponse>(`/api/pesquisadores/${id}/producoes?page=${page}`),

  getPesquisadorStats: (id: number) =>
    get<PesquisadorStats>(`/api/pesquisadores/${id}/stats`),

  getStats: () =>
    get<GlobalStats>('/api/stats'),

  listInternalPesquisadores: (q?: string) =>
    proxyGet<PesquisadorAdminListResponse>(
      `/api/internal/pesquisadores${q ? `?q=${encodeURIComponent(q)}` : ''}`
    ),

  createInternalPesquisador: (body: PesquisadorCreateRequest) =>
    proxyPostJSON<PesquisadorAdminItem>('/api/internal/pesquisadores', body),

  updateInternalPesquisador: (id: number, body: PesquisadorUpdateRequest) =>
    proxyPut<PesquisadorAdminItem>(`/api/internal/pesquisadores/${id}`, body),

  deleteInternalPesquisador: (id: number) =>
    proxyDelete(`/api/internal/pesquisadores/${id}`),

  reprocessarPesquisador: (id: number) =>
    proxyPostJSON<ReprocessarResponse>(`/api/internal/pesquisadores/${id}/reprocessar`, {}),

  triggerEtl: (formData: FormData) =>
    proxyPost<TriggerEtlResponse>('/api/internal/trigger-etl', formData),

  suggest: (q: string) =>
    get<SuggestResponse>(`/api/search/suggest?q=${encodeURIComponent(q)}`),
};
