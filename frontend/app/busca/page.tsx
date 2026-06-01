'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import Link from 'next/link';
import {
  Search, ListFilter, FileText, UserRound, Settings2,
  ArrowLeft, ArrowRight, ChevronLeft, ChevronRight,
  Type, Sparkles, LogIn, LogOut, Shield, ShieldCheck,
  BarChart3, Info, X, ExternalLink, Upload, Wand2, RefreshCw,
} from 'lucide-react';
import {
  api,
  ProducaoCard, ProducaoDetalhe, PesquisadorProfile,
  PesquisadorProducaoItem, PesquisadorStats,
  SearchFilters, GlobalStats, TriggerEtlResponse, PesquisadorAdminItem,
} from '../../lib/api';

/* ─── Types ─── */
type Screen = 'busca' | 'resultados' | 'detalhes' | 'perfil' | 'admin';
type SearchMode = 'text' | 'sem';

/* ─── Helpers ─── */
const SparkGlyph = () => (
  <svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" fill="currentColor" style={{ width: '100%', height: '100%', display: 'block' }}>
    <path d="M16 0 L17.5 13 C 17.6 13.9 18.3 14.6 19.2 14.7 L32 16 L19.2 17.3 C 18.3 17.4 17.6 18.1 17.5 19 L16 32 L14.5 19 C 14.4 18.1 13.7 17.4 12.8 17.3 L0 16 L12.8 14.7 C 13.7 14.6 14.4 13.9 14.5 13 Z" />
  </svg>
);

function initials(name: string) {
  return name.split(' ').slice(0, 2).map(w => w[0]).join('').toUpperCase();
}

function qualisBadge(q?: string) {
  if (!q) return null;
  const cls = q.toLowerCase().replace(/[^a-z0-9]/g, '');
  const map: Record<string, string> = { a1: 'badge-a1', a2: 'badge-a2', a3: 'badge-a3', a4: 'badge-a4', b1: 'badge-b1', b2: 'badge-b2' };
  return <span className={`badge ${map[cls] ?? 'badge-outline'}`}>{q}</span>;
}

/* ─── Main component ─── */
export default function BuscaPage() {
  /* Screen state */
  const [screen, setScreen] = useState<Screen>('busca');
  const [adminAuthed, setAdminAuthed] = useState(false);
  const [showLogin, setShowLogin] = useState(false);

  /* Search state */
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<SearchMode>('text');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<ProducaoCard[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchedQuery, setSearchedQuery] = useState('');

  /* Detail state */
  const [detalhe, setDetalhe] = useState<ProducaoDetalhe | null>(null);
  const [detalheLoading, setDetalheLoading] = useState(false);
  const [capaUrl, setCapaUrl] = useState<string | null>(null);
  const [capaLoading, setCapaLoading] = useState(false);
  const [capaError, setCapaError] = useState<string | null>(null);

  /* Profile state */
  const [perfil, setPerfil] = useState<PesquisadorProfile | null>(null);
  const [perfilProducoes, setPerfilProducoes] = useState<PesquisadorProducaoItem[]>([]);
  const [perfilStats, setPerfilStats] = useState<PesquisadorStats | null>(null);
  const [perfilPage, setPerfilPage] = useState(1);
  const [perfilTotalPages, setPerfilTotalPages] = useState(1);
  const [perfilTab, setPerfilTab] = useState<'prod' | 'ind' | 'sobre'>('prod');
  const [perfilLoading, setPerfilLoading] = useState(false);
  const [perfilPhotoError, setPerfilPhotoError] = useState(false);

  /* Admin state */
  const [stats, setStats] = useState<GlobalStats | null>(null);
  const [adminTab, setAdminTab] = useState<'pesquisadores' | 'etl'>('pesquisadores');
  const [adminSearchQ, setAdminSearchQ] = useState('');
  const [etlFiles, setEtlFiles] = useState<FileList | null>(null);
  const [etlLoading, setEtlLoading] = useState(false);
  const [etlResult, setEtlResult] = useState<TriggerEtlResponse | null>(null);
  const [etlError, setEtlError] = useState<string | null>(null);
  const [loginEmail, setLoginEmail] = useState('admin@spark.uneb.br');
  const [loginPass, setLoginPass] = useState('spark2026');
  const [loginError, setLoginError] = useState(false);

  /* Refs */
  const homeInputRef = useRef<HTMLInputElement>(null);

  /* Load global stats on mount */
  useEffect(() => {
    api.getStats().then(setStats).catch(() => {});
  }, []);

  /* ── Navigation ── */
  function goTo(s: Screen) {
    if (s === 'admin') {
      if (adminAuthed) {
        setScreen('admin');
        loadStats();
      } else {
        setShowLogin(true);
      }
      return;
    }
    setScreen(s);
  }

  /* ── Search ── */
  async function doSearch(q: string, m: SearchMode, p = 1) {
    if (!q.trim()) return;
    setLoading(true);
    setScreen('resultados');
    setSearchedQuery(q);
    setPage(p);
    try {
      const filters: SearchFilters = {};
      if (m === 'text') {
        const res = await api.searchText(q, filters, p);
        setResults(res.resultados);
        setTotal(res.total);
        setTotalPages(res.total_pages);
      } else {
        const res = await api.searchSemantic(q, filters);
        setResults(res.resultados);
        setTotal(res.resultados.length);
        setTotalPages(1);
      }
    } catch {
      setResults([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }

  /* ── Load production detail ── */
  async function loadDetalhe(id: number) {
    setDetalheLoading(true);
    setScreen('detalhes');
    setCapaUrl(null);
    setCapaError(null);
    try {
      const d = await api.getProducao(id);
      setDetalhe(d);
    } catch {
      setDetalhe(null);
    } finally {
      setDetalheLoading(false);
    }
  }

  /* ── Generate AI cover ── */
  async function handleGerarCapa() {
    if (!detalhe) return;
    setCapaLoading(true);
    setCapaError(null);
    try {
      const res = await api.gerarCapa(detalhe.titulo, detalhe.resumo);
      setCapaUrl(res.capa_url);
    } catch {
      setCapaError('Não foi possível gerar a capa. Verifique a chave GEMINI_API_KEY.');
    } finally {
      setCapaLoading(false);
    }
  }

  /* ── Load researcher profile ── */
  const loadPerfil = useCallback(async (id: number, p = 1) => {
    setPerfilLoading(true);
    setScreen('perfil');
    setPerfilTab('prod');
    setPerfilPhotoError(false);
    try {
      const [profile, prods, statsData] = await Promise.all([
        api.getPesquisador(id),
        api.getPesquisadorProducoes(id, p),
        api.getPesquisadorStats(id),
      ]);
      setPerfil(profile);
      setPerfilProducoes(prods.resultados);
      setPerfilTotalPages(prods.total_pages);
      setPerfilPage(p);
      setPerfilStats(statsData);
    } catch {
      setPerfil(null);
    } finally {
      setPerfilLoading(false);
    }
  }, []);

  async function loadPerfilPage(p: number) {
    if (!perfil) return;
    const prods = await api.getPesquisadorProducoes(perfil.id, p);
    setPerfilProducoes(prods.resultados);
    setPerfilPage(p);
    setPerfilTotalPages(prods.total_pages);
  }

  /* ── Load stats ── */
  async function loadStats() {
    try {
      const s = await api.getStats();
      setStats(s);
    } catch {
      setStats(null);
    }
  }

  /* ── ETL upload ── */
  async function handleEtlUpload() {
    if (!etlFiles || etlFiles.length === 0) return;
    setEtlLoading(true);
    setEtlResult(null);
    setEtlError(null);
    try {
      const fd = new FormData();
      Array.from(etlFiles).forEach(f => fd.append('files', f));
      const result = await api.triggerEtl(fd);
      setEtlResult(result);
      api.getStats().then(setStats).catch(() => {});
    } catch {
      setEtlError('Erro ao processar. Verifique se o servidor está acessível e os XMLs são válidos.');
    } finally {
      setEtlLoading(false);
    }
  }

  /* ── Login ── */
  function handleLogin() {
    if (loginEmail === 'admin@spark.uneb.br' && loginPass === 'spark2026') {
      setAdminAuthed(true);
      setShowLogin(false);
      setLoginError(false);
      setScreen('admin');
      loadStats();
    } else {
      setLoginError(true);
    }
  }

  function handleLogout() {
    setAdminAuthed(false);
    setScreen('busca');
  }

  /* ── Topbar info ── */
  const screenMeta: Record<Screen, { title: string; crumb: string; icon: React.ReactNode }> = {
    busca:      { title: 'busca',         crumb: 'spark / busca',       icon: <Search size={16} /> },
    resultados: { title: 'resultados',    crumb: 'spark / resultados',   icon: <ListFilter size={16} /> },
    detalhes:   { title: 'produção',      crumb: 'spark / produção',     icon: <FileText size={16} /> },
    perfil:     { title: 'pesquisador',   crumb: 'spark / pesquisador',  icon: <UserRound size={16} /> },
    admin:      { title: 'painel admin',  crumb: 'spark / admin',        icon: <Settings2 size={16} /> },
  };

  const meta = screenMeta[screen];

  /* ── Pagination helper ── */
  function Pagination({ cur, total: tot, onChange }: { cur: number; total: number; onChange: (p: number) => void }) {
    if (tot <= 1) return null;
    const pages: (number | '…')[] = [];
    if (tot <= 7) {
      for (let i = 1; i <= tot; i++) pages.push(i);
    } else {
      pages.push(1);
      if (cur > 3) pages.push('…');
      for (let i = Math.max(2, cur - 1); i <= Math.min(tot - 1, cur + 1); i++) pages.push(i);
      if (cur < tot - 2) pages.push('…');
      pages.push(tot);
    }
    return (
      <div className="pagination-row">
        <div className="pagination">
          <button onClick={() => onChange(cur - 1)} disabled={cur === 1}><ChevronLeft size={14} /></button>
          {pages.map((p, i) =>
            p === '…' ? <button key={`e${i}`} disabled>…</button>
              : <button key={p} className={p === cur ? 'active' : ''} onClick={() => onChange(p as number)}>{p}</button>
          )}
          <button onClick={() => onChange(cur + 1)} disabled={cur === tot}><ChevronRight size={14} /></button>
        </div>
      </div>
    );
  }

  /* ════════════════════ RENDER ════════════════════ */
  return (
    <div className="app">

      {/* ── Login overlay ── */}
      {showLogin && (
        <div className="login-overlay">
          <div className="login-card">
            <div className="login-brand">
              <div className="login-brand-mark">
                <SparkGlyph />
              </div>
              <div className="login-brand-word">spark<span>.</span></div>
            </div>

            <div className="login-role-tag">
              <Shield size={11} />
              acesso restrito · admin
            </div>

            <div className="login-title">entrar no painel</div>
            <div className="login-sub">Acesse com as credenciais de administrador para gerenciar pesquisadores e orquestrar o ETL.</div>

            {loginError && (
              <div className="login-error visible">
                E-mail ou senha incorretos. Tente novamente.
              </div>
            )}

            <div className="login-field">
              <label>e-mail</label>
              <input type="email" value={loginEmail} onChange={e => setLoginEmail(e.target.value)} placeholder="admin@spark.uneb.br" />
            </div>
            <div className="login-field">
              <label>senha</label>
              <input type="password" value={loginPass} onChange={e => setLoginPass(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} placeholder="••••••••" />
            </div>

            <button className="btn btn-primary" style={{ width: '100%', marginTop: 8 }} onClick={handleLogin}>
              <LogIn size={14} />
              entrar
            </button>

            <div className="login-hint">
              protótipo · credenciais de demonstração<br />
              admin@spark.uneb.br · spark2026
            </div>

            <button style={{ position: 'absolute', top: 16, right: 16, background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-3)' }} onClick={() => setShowLogin(false)}>
              <X size={18} />
            </button>
          </div>
        </div>
      )}

      <div className="app-shell">

        {/* ── Left Rail ── */}
        <nav className="rail">
          <Link className="rail-brand" href="/" title="spark.">
            <SparkGlyph />
          </Link>

          <div className="rail-nav">
            <button className={`rail-item ${screen === 'busca' ? 'active' : ''}`} onClick={() => goTo('busca')}>
              <Search size={20} />
              <span className="rail-item-tip">busca</span>
            </button>
            <button className={`rail-item ${screen === 'resultados' ? 'active' : ''}`} onClick={() => goTo('resultados')}>
              <ListFilter size={20} />
              <span className="rail-item-tip">resultados</span>
            </button>
            <button className={`rail-item ${screen === 'detalhes' ? 'active' : ''}`} onClick={() => goTo('detalhes')}>
              <FileText size={20} />
              <span className="rail-item-tip">produção</span>
            </button>
            <button className={`rail-item ${screen === 'perfil' ? 'active' : ''}`} onClick={() => goTo('perfil')}>
              <UserRound size={20} />
              <span className="rail-item-tip">pesquisador</span>
            </button>
            <button className={`rail-item ${screen === 'admin' ? 'active' : ''}`} onClick={() => goTo('admin')}>
              <Settings2 size={20} />
              <span className="rail-item-tip">admin</span>
            </button>
          </div>
        </nav>

        {/* ── Main ── */}
        <main className="app-main">

          {/* Topbar */}
          <header className="topbar">
            <div className="topbar-page-title">
              {meta.icon}
              {meta.title}
            </div>
            <div className="topbar-crumbs">{meta.crumb}</div>
            <div className="topbar-search">
              <Search size={14} />
              <input
                type="text"
                placeholder="buscar produções, autores, periódicos..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && doSearch(query, mode)}
              />
            </div>
          </header>

          {/* ════ TELA 1 · BUSCA ════ */}
          <section className={`screen ${screen === 'busca' ? 'active' : ''}`}>
            <div className="home-page">
              <div className="home-hero">
                <div>
                  <span className="home-hero-eyebrow">
                    <span className="dot"></span>
                    base atualizada · {new Date().toLocaleDateString('pt-BR')}
                  </span>
                  <h1 className="home-headline">o que você quer <span className="ser">descobrir</span> hoje?</h1>
                  <p className="home-sub-text">
                    Combine palavras-chave e linguagem natural sobre as produções dos
                    pesquisadores da UNEB — com filtros por Qualis, JCR, área e ano.
                  </p>
                </div>

                <aside className="home-side-card">
                  <div className="home-side-head">
                    <span>base de dados · UNEB</span>
                    <span className="live"><span className="ldot"></span>indexada</span>
                  </div>
                  <div className="home-side-stat">{stats?.total_producoes ?? '—'}</div>
                  <div className="home-side-stat-sub">produções científicas indexadas</div>
                  <div className="home-side-feed" style={{ marginTop: 16 }}>
                    <div className="home-side-feed-item">
                      <div className="av" style={{ background: 'var(--primary-50)', color: 'var(--primary-600)' }}>
                        <UserRound size={10} />
                      </div>
                      <span>{stats?.total_pesquisadores ?? '—'} pesquisadores cadastrados</span>
                    </div>
                    <div className="home-side-feed-item">
                      <div className="av" style={{ background: 'var(--primary-50)', color: 'var(--primary-600)' }}>
                        <Sparkles size={10} />
                      </div>
                      <span>{stats?.total_vetores ?? '—'} embeddings vetoriais gerados</span>
                    </div>
                    <div className="home-side-feed-item">
                      <div className="av" style={{ background: 'var(--ok-50)', color: 'var(--ok-fg)' }}>
                        <Search size={10} />
                      </div>
                      <span>
                        {stats?.data_ultima_carga
                          ? `atualizado ${new Date(stats.data_ultima_carga).toLocaleDateString('pt-BR')}`
                          : 'busca semântica em menos de 5s'}
                      </span>
                    </div>
                  </div>
                </aside>
              </div>

              <div className="search-mega">
                <Search size={20} className="lead-icon" />
                <input
                  ref={homeInputRef}
                  type="text"
                  placeholder="tente: aprendizado de máquina aplicado em saúde pública..."
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && doSearch(query, mode)}
                />
                <button className="btn btn-primary" onClick={() => doSearch(query, mode)}>
                  buscar
                  <ArrowRight size={14} />
                </button>
              </div>

              <div className="search-meta-row">
                <div className="mode-toggle">
                  <button className={`mode-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => setMode('text')}>
                    <Type size={12} />
                    textual · FTS
                  </button>
                  <button className={`mode-btn ${mode === 'sem' ? 'active' : ''}`} onClick={() => setMode('sem')}>
                    <Sparkles size={12} />
                    semântica · embeddings
                  </button>
                </div>
              </div>

              <div style={{ marginTop: '-38px', marginBottom: 48, fontSize: 12, color: 'var(--text-3)', fontFamily: 'var(--font-mono)' }}>
                <Info size={12} style={{ verticalAlign: 'middle', marginRight: 5 }} />
                no modo textual, use operadores:
                {' '}<span style={{ background: 'var(--ink-50)', padding: '2px 7px', borderRadius: 4, margin: '0 3px' }}>AND</span>
                <span style={{ background: 'var(--ink-50)', padding: '2px 7px', borderRadius: 4, margin: '0 3px' }}>OR</span>
                <span style={{ background: 'var(--ink-50)', padding: '2px 7px', borderRadius: 4, margin: '0 3px' }}>NOT</span>
                {' '}para refinar a busca por palavras-chave.
              </div>
            </div>
          </section>

          {/* ════ TELA 2 · RESULTADOS ════ */}
          <section className={`screen ${screen === 'resultados' ? 'active' : ''}`}>
            <div className="results-page">
              <div className="results-head">
                <div className="results-head-row">
                  <div>
                    <h1 className="results-title">resultados para <em>&ldquo;{searchedQuery}&rdquo;</em></h1>
                    <div className="results-title-sub">
                      {loading ? 'buscando...' : mode === 'text'
                        ? `${total} produções · 20 por página · ordenadas por relevância`
                        : `${total} produções · top-${results.length} semânticos`}
                    </div>
                  </div>
                  <div className="results-controls">
                    <div className="mode-toggle">
                      <button className={`mode-btn ${mode === 'text' ? 'active' : ''}`} onClick={() => { setMode('text'); doSearch(searchedQuery, 'text'); }}>
                        <Type size={12} />textual
                      </button>
                      <button className={`mode-btn ${mode === 'sem' ? 'active' : ''}`} onClick={() => { setMode('sem'); doSearch(searchedQuery, 'sem'); }}>
                        <Sparkles size={12} />semântica
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <div className="results-layout">
                <div>
                  {loading ? (
                    <div className="empty-state">
                      <div className="spinner" />
                      buscando produções...
                    </div>
                  ) : results.length === 0 ? (
                    <div className="empty-state">
                      <div className="empty-state-icon"><Search size={24} /></div>
                      <div className="empty-state-title">Nenhuma produção encontrada.</div>
                      <div className="empty-state-sub">Tente termos mais gerais ou use o modo semântico.</div>
                    </div>
                  ) : (
                    <div className="result-list">
                      {results.map(r => (
                        <article
                          key={r.id}
                          className={`result-row ${r.similarity_score && r.similarity_score > 0.85 ? 'featured' : ''} ${!r.similarity_score ? 'no-sim' : ''}`}
                          style={{ cursor: 'pointer' }}
                          onClick={() => loadDetalhe(r.id)}
                        >
                          {r.similarity_score && (
                            <div>
                              <div className="result-row-sim">{r.similarity_score.toFixed(2)}</div>
                              <div className="result-row-sim-lbl">match</div>
                            </div>
                          )}
                          <div className="result-row-body">
                            {r.nome_veiculo && <div className="result-row-venue">{r.nome_veiculo}</div>}
                            <div className="result-row-title">{r.titulo}</div>
                            <div className="result-row-meta">
                              {qualisBadge(r.qualis)}
                              {r.jcr && <span className="badge badge-jcr">JCR {r.jcr.toFixed(1)}</span>}
                              <span className="badge badge-outline">{r.tipo_producao}</span>
                            </div>
                          </div>
                          <div className="result-row-aside">
                            <span className="author">
                              <span className="avatar-mini">{initials(r.pesquisador.nome_completo)}</span>
                              {r.pesquisador.nome_completo}
                            </span>
                            {r.doi && <span className="meta-dim">DOI: {r.doi.slice(0, 20)}…</span>}
                            {r.ano_publicacao && <span className="meta-dim">{r.ano_publicacao}</span>}
                          </div>
                        </article>
                      ))}
                    </div>
                  )}

                  {!loading && mode === 'text' && (
                    <Pagination cur={page} total={totalPages} onChange={p => doSearch(searchedQuery, 'text', p)} />
                  )}
                </div>

                {/* Filter panel — cosmetic for now */}
                <aside className="filter-panel">
                  <div className="filter-panel-head">
                    <span>refinar</span>
                  </div>
                  <div className="filter-group">
                    <div className="filter-label">tipo de busca</div>
                    <label className="filter-option">
                      <input type="radio" name="mode" checked={mode === 'text'} onChange={() => { setMode('text'); doSearch(searchedQuery, 'text'); }} /> textual (FTS)
                    </label>
                    <label className="filter-option">
                      <input type="radio" name="mode" checked={mode === 'sem'} onChange={() => { setMode('sem'); doSearch(searchedQuery, 'sem'); }} /> semântica
                    </label>
                  </div>
                </aside>
              </div>
            </div>
          </section>

          {/* ════ TELA 3 · DETALHES ════ */}
          <section className={`screen ${screen === 'detalhes' ? 'active' : ''}`}>
            <div className="detail-page">
              <button className="back-link" onClick={() => setScreen('resultados')}>
                <ArrowLeft size={14} />
                voltar aos resultados
              </button>

              {detalheLoading ? (
                <div className="empty-state"><div className="spinner" />carregando produção...</div>
              ) : !detalhe ? (
                <div className="empty-state">
                  <div className="empty-state-title">Selecione uma produção nos resultados.</div>
                </div>
              ) : (
                <>
                  {/* ── AI Cover ── */}
                  <div className={`detail-cover ${capaLoading ? 'loading' : ''}`}>
                    {capaUrl ? (
                      <>
                        <img className="detail-cover-img" src={capaUrl} alt="Capa gerada por IA" />
                        <div className="detail-cover-overlay" />
                        <button className="detail-cover-regen btn btn-ghost" onClick={handleGerarCapa} disabled={capaLoading}>
                          <RefreshCw size={12} />
                          regenerar
                        </button>
                      </>
                    ) : capaLoading ? (
                      <div className="detail-cover-placeholder">
                        <div className="spinner" />
                        <span>gerando capa com IA...</span>
                      </div>
                    ) : (
                      <div className="detail-cover-placeholder">
                        <Wand2 size={28} style={{ opacity: 0.3 }} />
                        <span style={{ fontSize: 13, color: 'var(--text-3)' }}>nenhuma capa gerada</span>
                        <button className="btn btn-primary detail-cover-gen-btn" onClick={handleGerarCapa}>
                          <Wand2 size={13} />
                          gerar capa com IA
                        </button>
                        {capaError && (
                          <span style={{ fontSize: 11, color: 'var(--err-fg)', maxWidth: 360, textAlign: 'center', marginTop: 4 }}>
                            {capaError}
                          </span>
                        )}
                      </div>
                    )}
                  </div>

                  <div className="detail-hero">
                    <div className="detail-venue">
                      {detalhe.nome_veiculo ?? '—'} {detalhe.ano_publicacao ? `· ${detalhe.ano_publicacao}` : ''}
                    </div>
                    <h1 className="detail-title" dangerouslySetInnerHTML={{ __html: detalhe.titulo }} />
                    <div className="detail-badges">
                      {qualisBadge(detalhe.qualis)}
                      {detalhe.jcr && <span className="badge badge-jcr">JCR {detalhe.jcr.toFixed(1)}</span>}
                      <span className="badge badge-outline">{detalhe.tipo_producao}</span>
                    </div>
                  </div>

                  {detalhe.jcr && (
                    <div className="metric-strip">
                      <div className="metric-cell accent">
                        <div className="metric-cell-n">{detalhe.jcr.toFixed(1)}</div>
                        <div className="metric-cell-l">JCR</div>
                      </div>
                    </div>
                  )}

                  <div className="detail-grid">
                    <div>
                      {detalhe.resumo && (
                        <div className="detail-section">
                          <div className="detail-section-title">resumo</div>
                          <div className="detail-abstract">{detalhe.resumo}</div>
                        </div>
                      )}

                      <div className="detail-section">
                        <div className="detail-section-title">metadados bibliográficos</div>
                        <div className="meta-table">
                          {detalhe.nome_veiculo && (
                            <div className="meta-row">
                              <span className="meta-lbl">periódico</span>
                              <span className="meta-val">{detalhe.nome_veiculo}</span>
                            </div>
                          )}
                          {detalhe.issn && (
                            <div className="meta-row">
                              <span className="meta-lbl">ISSN</span>
                              <span className="meta-val mono">{detalhe.issn}</span>
                            </div>
                          )}
                          {detalhe.doi && (
                            <div className="meta-row">
                              <span className="meta-lbl">DOI</span>
                              <span className="meta-val">
                                <a href={`https://doi.org/${detalhe.doi}`} target="_blank" rel="noopener noreferrer">
                                  <span className="mono">{detalhe.doi}</span>
                                  <ExternalLink size={11} style={{ marginLeft: 4 }} />
                                </a>
                              </span>
                            </div>
                          )}
                          <div className="meta-row">
                            <span className="meta-lbl">tipo de produção</span>
                            <span className="meta-val">{detalhe.tipo_producao}</span>
                          </div>
                          {detalhe.qualis && (
                            <div className="meta-row">
                              <span className="meta-lbl">Qualis CAPES</span>
                              <span className="meta-val">{qualisBadge(detalhe.qualis)}</span>
                            </div>
                          )}
                          {detalhe.jcr && (
                            <div className="meta-row">
                              <span className="meta-lbl">fator de impacto</span>
                              <span className="meta-val mono">{detalhe.jcr.toFixed(1)}</span>
                            </div>
                          )}
                          {detalhe.ano_publicacao && (
                            <div className="meta-row">
                              <span className="meta-lbl">ano de publicação</span>
                              <span className="meta-val">{detalhe.ano_publicacao}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <aside>
                      <div className="aside-card">
                        <div className="aside-card-title">pesquisador principal</div>
                        <div className="aside-author" style={{ cursor: 'pointer' }} onClick={() => loadPerfil(detalhe.pesquisador.id)}>
                          <div className="avatar">{initials(detalhe.pesquisador.nome_completo)}</div>
                          <div>
                            <div className="aside-author-name">{detalhe.pesquisador.nome_completo}</div>
                            <div className="aside-author-sub">
                              UNEB{detalhe.pesquisador.departamento ? ` · ${detalhe.pesquisador.departamento}` : ''}
                              {detalhe.pesquisador.campus ? ` · ${detalhe.pesquisador.campus}` : ''}
                            </div>
                            <span className="aside-author-link">
                              ver perfil <ArrowRight size={11} />
                            </span>
                          </div>
                        </div>
                        <div className="aside-kv">
                          <span className="aside-kv-lbl">produções totais</span>
                          <span className="aside-kv-val">{detalhe.pesquisador.total_producoes}</span>
                        </div>
                        <div className="aside-kv">
                          <span className="aside-kv-lbl">índice H</span>
                          <span className="aside-kv-val">{detalhe.pesquisador.indice_h}</span>
                        </div>
                        <div className="aside-kv">
                          <span className="aside-kv-lbl">A1 + A2</span>
                          <span className="aside-kv-val">{detalhe.pesquisador.total_a1_a2}</span>
                        </div>
                      </div>
                    </aside>
                  </div>
                </>
              )}
            </div>
          </section>

          {/* ════ TELA 4 · PERFIL ════ */}
          <section className={`screen ${screen === 'perfil' ? 'active' : ''}`}>
            <div className="profile-page">
              {perfilLoading ? (
                <div className="empty-state"><div className="spinner" />carregando perfil...</div>
              ) : !perfil ? (
                <div className="empty-state">
                  <div className="empty-state-title">Selecione um pesquisador nos detalhes de uma produção.</div>
                </div>
              ) : (
                <>
                  <div className="profile-cover">
                    <button className="profile-cover-back" onClick={() => setScreen('detalhes')}>
                      <ArrowLeft size={14} />
                      voltar
                    </button>

                    <div className="profile-head">
                      {!perfilPhotoError ? (
                        <img
                          className="profile-photo lg"
                          src={`/api/foto-pesquisador/${perfil.lattes_id}`}
                          alt={perfil.nome_completo}
                          onError={() => setPerfilPhotoError(true)}
                        />
                      ) : (
                        <div className="avatar lg">{initials(perfil.nome_completo)}</div>
                      )}
                      <div>
                        <h1 className="profile-name">{perfil.nome_completo}</h1>
                        <div className="profile-role">
                          UNEB{perfil.departamento ? ` · ${perfil.departamento}` : ''}
                          {perfil.campus ? ` · ${perfil.campus}` : ''}
                        </div>
                        <div className="profile-links">
                          <a href={`http://lattes.cnpq.br/${perfil.lattes_id}`} target="_blank" rel="noopener noreferrer" className="profile-link">
                            <ExternalLink size={11} />lattes/cnpq
                          </a>
                        </div>
                      </div>
                    </div>

                    <div className="profile-cover-stats">
                      <div className="profile-cover-stat"><div className="n">{perfil.total_producoes}</div><div className="l">produções</div></div>
                      <div className="profile-cover-stat"><div className="n">{perfil.total_a1_a2}</div><div className="l">A1 + A2</div></div>
                      <div className="profile-cover-stat"><div className="n">h{perfil.indice_h}</div><div className="l">índice H</div></div>
                    </div>
                  </div>

                  <div className="profile-tabs">
                    <button className={`profile-tab ${perfilTab === 'prod' ? 'active' : ''}`} onClick={() => setPerfilTab('prod')}>
                      <FileText size={14} />produções
                    </button>
                    <button className={`profile-tab ${perfilTab === 'ind' ? 'active' : ''}`} onClick={() => setPerfilTab('ind')}>
                      <BarChart3 size={14} />indicadores
                    </button>
                    <button className={`profile-tab ${perfilTab === 'sobre' ? 'active' : ''}`} onClick={() => setPerfilTab('sobre')}>
                      <UserRound size={14} />sobre
                    </button>
                  </div>

                  <div className="profile-content">
                    {/* Tab: produções */}
                    <div className={`profile-pane ${perfilTab === 'prod' ? 'active' : ''}`}>
                      <div className="section-head">
                        <h3>produções <span className="ser">recentes</span></h3>
                      </div>
                      <div className="mini-list">
                        {perfilProducoes.map(p => (
                          <div key={p.id} className="mini-row" style={{ cursor: 'pointer' }} onClick={() => loadDetalhe(p.id)}>
                            <div className="mini-row-body">
                              <div className="mini-row-title">{p.titulo}</div>
                              <div className="mini-row-meta">
                                {p.nome_veiculo && <span>{p.nome_veiculo}</span>}
                                {p.nome_veiculo && <span>·</span>}
                                {p.ano_publicacao && <span>{p.ano_publicacao}</span>}
                                {qualisBadge(p.qualis)}
                                {p.jcr && <span className="badge badge-jcr">JCR {p.jcr.toFixed(1)}</span>}
                              </div>
                            </div>
                            <ChevronRight size={14} className="muted" />
                          </div>
                        ))}
                      </div>
                      <Pagination cur={perfilPage} total={perfilTotalPages} onChange={p => loadPerfilPage(p)} />
                    </div>

                    {/* Tab: indicadores */}
                    <div className={`profile-pane ${perfilTab === 'ind' ? 'active' : ''}`}>
                      {perfilStats && (
                        <>
                          <div className="chart-card">
                            <div className="chart-head">
                              <div>
                                <div className="chart-title">publicações por <span className="ser">ano</span></div>
                                <div className="chart-title-sub">{perfil.total_producoes} produções</div>
                              </div>
                            </div>
                            <YearBars data={perfilStats.por_ano} />
                          </div>

                          <div className="qualis-dist">
                            <div className="chart-head">
                              <div>
                                <div className="chart-title">distribuição por <span className="ser">Qualis CAPES</span></div>
                                <div className="chart-title-sub">{perfil.total_producoes} produções</div>
                              </div>
                            </div>
                            <QualisBars data={perfilStats.por_qualis} total={perfil.total_producoes} />
                          </div>
                        </>
                      )}
                    </div>

                    {/* Tab: sobre */}
                    <div className={`profile-pane ${perfilTab === 'sobre' ? 'active' : ''}`}>
                      <div className="sobre-card">
                        <div className="sobre-header">
                          <div style={{ flexShrink: 0 }}>
                            {!perfilPhotoError ? (
                              <img
                                className="profile-photo lg"
                                src={`/api/foto-pesquisador/${perfil.lattes_id}`}
                                alt={perfil.nome_completo}
                                onError={() => setPerfilPhotoError(true)}
                              />
                            ) : (
                              <div className="avatar lg">{initials(perfil.nome_completo)}</div>
                            )}
                          </div>
                          <div>
                            <div className="sobre-name">{perfil.nome_completo}</div>
                            <div className="sobre-role">
                              UNEB{perfil.departamento ? ` · ${perfil.departamento}` : ''}
                              {perfil.campus ? ` · ${perfil.campus}` : ''}
                            </div>
                            {perfil.data_atualizacao && (
                              <div className="sobre-updated">
                                currículo extraído do lattes em {new Date(perfil.data_atualizacao).toLocaleDateString('pt-BR')}
                              </div>
                            )}
                            <a
                              href={`http://lattes.cnpq.br/${perfil.lattes_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="sobre-lattes-link"
                            >
                              <ExternalLink size={11} />
                              ver currículo lattes
                            </a>
                          </div>
                        </div>

                        <div className="sobre-stats-row">
                          <div className="sobre-stat">
                            <div className="sobre-stat-n">{perfil.total_producoes}</div>
                            <div className="sobre-stat-l">produções</div>
                          </div>
                          <div className="sobre-stat">
                            <div className="sobre-stat-n">h{perfil.indice_h}</div>
                            <div className="sobre-stat-l">índice H</div>
                          </div>
                          <div className="sobre-stat">
                            <div className="sobre-stat-n">{perfil.total_a1_a2}</div>
                            <div className="sobre-stat-l">A1 + A2</div>
                          </div>
                        </div>

                        <div className="sobre-bio-section">
                          <div className="sobre-bio-label">resumo do currículo</div>
                          <div className="sobre-bio-text">
                            {perfil.resumo ?? 'Resumo não disponível para este pesquisador.'}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </div>
          </section>

          {/* ════ TELA 5 · ADMIN ════ */}
          <section className={`screen ${screen === 'admin' ? 'active' : ''}`}>
            <div className="admin-page">
              <div className="admin-header">
                <div className="admin-title-block">
                  <h1 className="admin-title">painel <em>admin</em></h1>
                  <div className="admin-sub">orquestre a base, monitore o pipeline e gerencie pesquisadores</div>
                </div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                  <span className="badge badge-ok" style={{ padding: '6px 12px', fontSize: 11 }}>
                    <ShieldCheck size={11} />
                    admin autenticado
                  </span>
                  <button className="btn btn-ghost" onClick={handleLogout}>
                    <LogOut size={14} />sair
                  </button>
                </div>
              </div>

              {stats && (
                <div className="stat-grid-4">
                  <div className="stat-tile">
                    <UserRound size={20} className="stat-tile-icon" />
                    <div className="stat-tile-n">{stats.total_pesquisadores}</div>
                    <div className="stat-tile-l">pesquisadores</div>
                  </div>
                  <div className="stat-tile">
                    <FileText size={20} className="stat-tile-icon" />
                    <div className="stat-tile-n">{stats.total_producoes}</div>
                    <div className="stat-tile-l">produções</div>
                  </div>
                  <div className="stat-tile">
                    <Sparkles size={20} className="stat-tile-icon" />
                    <div className="stat-tile-n">{stats.total_vetores}</div>
                    <div className="stat-tile-l">embeddings</div>
                  </div>
                  {stats.data_ultima_carga && (
                    <div className="stat-tile">
                      <div className="stat-tile-n" style={{ fontSize: 14 }}>
                        {new Date(stats.data_ultima_carga).toLocaleDateString('pt-BR')}
                      </div>
                      <div className="stat-tile-l">última carga</div>
                    </div>
                  )}
                </div>
              )}

              <div className="admin-tabs">
                <button className={`admin-tab ${adminTab === 'pesquisadores' ? 'active' : ''}`} onClick={() => setAdminTab('pesquisadores')}>
                  <UserRound size={14} />
                  pesquisadores
                </button>
                <button className={`admin-tab ${adminTab === 'etl' ? 'active' : ''}`} onClick={() => setAdminTab('etl')}>
                  <Upload size={14} />
                  importar XMLs
                </button>
              </div>

              {/* Tab: pesquisadores */}
              <div className={`admin-section ${adminTab === 'pesquisadores' ? 'active' : ''}`}>
                <div className="table-toolbar">
                  <div className="table-search">
                    <Search size={14} />
                    <input
                      type="text"
                      placeholder="buscar por nome..."
                      value={adminSearchQ}
                      onChange={e => setAdminSearchQ(e.target.value)}
                    />
                  </div>
                </div>

                <div className="data-table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>nome</th>
                        <th>departamento</th>
                        <th>campus</th>
                        <th>produções</th>
                      </tr>
                    </thead>
                    <tbody>
                      <AdminResearcherRows q={adminSearchQ} />
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Tab: ETL */}
              <div className={`admin-section ${adminTab === 'etl' ? 'active' : ''}`}>
                <div className="etl-upload-card">
                  <div className="etl-upload-title">importar currículos Lattes</div>
                  <div className="etl-upload-sub">
                    Selecione um ou mais arquivos XML exportados do CNPq. O pipeline executa extração,
                    enriquecimento (Qualis, CrossRef, OpenAlex) e geração de embeddings automaticamente.
                  </div>

                  <div className="etl-file-row">
                    <label className={`etl-file-label ${etlFiles && etlFiles.length > 0 ? 'has-files' : ''}`}>
                      <Upload size={14} />
                      {etlFiles && etlFiles.length > 0
                        ? `${etlFiles.length} arquivo${etlFiles.length > 1 ? 's' : ''} selecionado${etlFiles.length > 1 ? 's' : ''}`
                        : 'escolher XMLs'}
                      <input
                        type="file"
                        accept=".xml"
                        multiple
                        style={{ display: 'none' }}
                        onChange={e => { setEtlFiles(e.target.files); setEtlResult(null); setEtlError(null); }}
                      />
                    </label>
                    <button
                      className="btn btn-primary"
                      onClick={handleEtlUpload}
                      disabled={!etlFiles || etlFiles.length === 0 || etlLoading}
                    >
                      <Upload size={14} />
                      {etlLoading ? 'processando...' : 'executar ETL'}
                    </button>
                  </div>

                  {etlError && (
                    <div className="login-error" style={{ marginTop: 14 }}>{etlError}</div>
                  )}

                  {etlResult && (
                    <div className="etl-result">
                      <div className="etl-result-grid">
                        <div className="etl-result-cell">
                          <div className="etl-result-n">{etlResult.pesquisadores}</div>
                          <div className="etl-result-l">pesquisadores</div>
                        </div>
                        <div className="etl-result-cell">
                          <div className="etl-result-n">{etlResult.producoes}</div>
                          <div className="etl-result-l">produções</div>
                        </div>
                        <div className="etl-result-cell">
                          <div className="etl-result-n">{etlResult.vetores_gerados}</div>
                          <div className="etl-result-l">embeddings</div>
                        </div>
                        <div className="etl-result-cell">
                          <div className="etl-result-n">{etlResult.qualis_match}</div>
                          <div className="etl-result-l">qualis match</div>
                        </div>
                      </div>
                      {etlResult.erros.length > 0 && (
                        <div>
                          <div className="etl-result-l" style={{ marginBottom: 6 }}>avisos</div>
                          {etlResult.erros.map((e, i) => (
                            <div key={i} className="login-error" style={{ marginBottom: 4, fontSize: 12 }}>{e}</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </section>

        </main>
      </div>
    </div>
  );
}

/* ── Sub-components ── */

function YearBars({ data }: { data: { ano: number; total: number }[] }) {
  if (!data.length) return null;
  const max = Math.max(...data.map(d => d.total));
  return (
    <div className="year-bars">
      {data.sort((a, b) => a.ano - b.ano).map(d => (
        <div key={d.ano} className="year-bar" title={`${d.ano}: ${d.total} produções`}>
          <div className="year-bar-track" style={{ height: `${(d.total / max) * 100}px` }}>
            <span className="year-bar-val">{d.total}</span>
          </div>
          <div className="year-bar-label">{String(d.ano).slice(2)}</div>
        </div>
      ))}
    </div>
  );
}

function QualisBars({ data, total }: { data: { qualis: string; total: number }[]; total: number }) {
  const order = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2'];
  const sorted = [...data].sort((a, b) => {
    const ia = order.indexOf(a.qualis);
    const ib = order.indexOf(b.qualis);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });
  const colorMap: Record<string, string> = {
    A1: 'var(--q-a1-fg)', A2: 'var(--q-a2-fg)', A3: 'var(--q-a3-fg)',
    A4: 'var(--q-a4-fg)', B1: 'var(--q-b1-fg)', B2: 'var(--q-b2-fg)',
  };
  const labelMap: Record<string, string> = { A1: 'a1', A2: 'a2', A3: 'a3', A4: 'a4', B1: 'bx', B2: 'bx' };
  return (
    <div className="qualis-bars">
      {sorted.map(d => (
        <div key={d.qualis} className="qualis-bar-row">
          <span className={`qualis-bar-label ${labelMap[d.qualis] ?? 'bx'}`}>{d.qualis}</span>
          <div className="qualis-bar-track">
            <div className="qualis-bar-fill" style={{ width: `${(d.total / total) * 100}%`, background: colorMap[d.qualis] ?? 'var(--ink-200)' }} />
          </div>
          <span className="qualis-bar-count">{d.total}</span>
        </div>
      ))}
    </div>
  );
}

function AdminResearcherRows({ q }: { q: string }) {
  const [rows, setRows] = useState<PesquisadorAdminItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.listInternalPesquisadores(q || undefined)
      .then(r => setRows(r.resultados))
      .catch(() => setRows([]))
      .finally(() => setLoading(false));
  }, [q]);

  if (loading) {
    return (
      <tr>
        <td colSpan={4} style={{ textAlign: 'center', padding: 28 }}>
          <div className="spinner" style={{ margin: '0 auto', marginBottom: 0 }} />
        </td>
      </tr>
    );
  }

  if (!rows.length) {
    return (
      <tr>
        <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-3)', padding: 24 }}>
          Nenhum pesquisador encontrado.
        </td>
      </tr>
    );
  }

  return (
    <>
      {rows.map(r => (
        <tr key={r.id}>
          <td>{r.nome_completo}</td>
          <td>{r.departamento ?? '—'}</td>
          <td>{r.campus ?? '—'}</td>
          <td className="mono">{r.total_producoes}</td>
        </tr>
      ))}
    </>
  );
}
