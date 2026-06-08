import Link from 'next/link';
import { Search, ArrowRight, ArrowDown, Sparkles, TextSearch, Award, UserRound } from 'lucide-react';

const SparkGlyph = () => (
  <svg viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" fill="currentColor">
    <path d="M16 0 L17.5 13 C 17.6 13.9 18.3 14.6 19.2 14.7 L32 16 L19.2 17.3 C 18.3 17.4 17.6 18.1 17.5 19 L16 32 L14.5 19 C 14.4 18.1 13.7 17.4 12.8 17.3 L0 16 L12.8 14.7 C 13.7 14.6 14.4 13.9 14.5 13 Z" />
  </svg>
);

export default function LandingPage() {
  return (
    <div className="landing">

      {/* Topbar */}
      <header className="l-topbar">
        <Link href="/" className="brand dark">
          <span className="brand-mark"><SparkGlyph /></span>
          <span className="brand-word">spark<span className="brand-dot">.</span></span>
        </Link>
        <nav className="l-nav">
          <a href="#como-funciona">Como funciona</a>
          <a href="#recursos">Recursos</a>
        </nav>
        <div className="l-topbar-right">
          <Link className="btn btn-dark" href="/busca">
            <Search size={14} />
            Entrar
          </Link>
          <Link className="btn btn-bright" href="/busca">
            Abrir spark
            <ArrowRight size={14} />
          </Link>
        </div>
      </header>

      <main className="l-content">

        {/* HERO */}
        <section className="l-hero">
          <div>
            <span className="l-eyebrow">SEARCH PLATFORM AND RESEARCH KNOWLEDGE</span>
            <h1 className="l-title">
              A faísca que <span className="ser">acende</span> a produção científica.
            </h1>
            <p className="l-sub">
              Spark orquestra a extração de currículos Lattes em XML, popula um banco relacional e
              uma base vetorial — habilitando busca por palavras-chave <em className="serif-it">e</em>{' '}
              por linguagem natural sobre os títulos das produções da UNEB.
            </p>
            <div className="l-cta-row">
              <Link className="btn btn-bright btn-lg" href="/busca">
                <Search size={14} />
                Começar a buscar
              </Link>
              <a className="btn btn-dark btn-lg" href="#como-funciona">
                Como funciona
                <ArrowDown size={14} />
              </a>
            </div>
          </div>

          {/* Side panel: live search preview */}
          <aside className="l-hero-aside">
            <div className="l-hero-aside-head">
              <span>POST /api/search/semantic</span>
              <span className="live"><span className="ldot"></span>live</span>
            </div>
            <div className="l-hero-aside-query">
              &gt; vigilância genômica de arboviroses<span className="cursor">▍</span>
            </div>
            <div className="l-hero-aside-results">
              <div className="l-hero-result">
                <div className="l-hero-result-sim">0.92</div>
                <div className="l-hero-result-body">
                  <div className="l-hero-result-title">A new lineage nomenclature to aid genomic surveillance of dengue virus</div>
                  <div className="l-hero-result-meta">PLOS BIOLOGY · 2024 · Qualis A1</div>
                </div>
              </div>
              <div className="l-hero-result">
                <div className="l-hero-result-sim">0.89</div>
                <div className="l-hero-result-body">
                  <div className="l-hero-result-title">Shifting patterns of dengue three years after Zika emergence in Brazil</div>
                  <div className="l-hero-result-meta">NATURE COMMS · 2024 · Qualis A1</div>
                </div>
              </div>
              <div className="l-hero-result">
                <div className="l-hero-result-sim">0.86</div>
                <div className="l-hero-result-body">
                  <div className="l-hero-result-title">Vector competence of Aedes aegypti for dengue serotype 3 in NE Brazil</div>
                  <div className="l-hero-result-meta">MEM. INST. OSWALDO CRUZ · 2023 · Qualis A2</div>
                </div>
              </div>
            </div>
          </aside>
        </section>

        {/* Stat strip */}
        <div className="l-stats-wrap">
          <div className="l-stats-row">
            <div className="l-stat">
              <div className="l-stat-n">918</div>
              <div className="l-stat-l">Produções indexadas</div>
            </div>
            <div className="l-stat">
              <div className="l-stat-n">8</div>
              <div className="l-stat-l">Pesquisadores</div>
            </div>
            <div className="l-stat">
              <div className="l-stat-n">444+</div>
              <div className="l-stat-l">Embeddings gerados</div>
            </div>
            <div className="l-stat">
              <div className="l-stat-n">&lt;5s</div>
              <div className="l-stat-l">Busca semântica</div>
            </div>
          </div>
        </div>

        {/* COMO FUNCIONA */}
        <section className="l-section" id="como-funciona">
          <div className="l-section-head">
            <div>
              <div className="l-section-eyebrow">Como funciona</div>
              <h2 className="l-section-title">Da sua <span className="ser">pergunta</span> ao artigo, em segundos.</h2>
            </div>
            <p className="l-section-sub right" style={{ maxWidth: '38ch' }}>
              Você pesquisa, o SPARK entende e ranqueia os resultados mais relevantes na produção
              científica da UNEB, com Qualis, JCR e tudo o que importa.
            </p>
          </div>

          <div className="arch-flow" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
            <div className="arch-step">
              <div className="arch-bubble">
                <span className="arch-num">1</span>
                <Search size={24} />
              </div>
              <div className="arch-step-tag">VOCÊ PESQUISA</div>
              <div className="arch-step-name">Pergunte</div>
              <div className="arch-step-desc">Use palavras-chave ou uma frase em linguagem natural — como falar com um colega.</div>
            </div>
            <div className="arch-step">
              <div className="arch-bubble">
                <span className="arch-num">2</span>
                <Sparkles size={24} />
              </div>
              <div className="arch-step-tag">SPARK ENTENDE</div>
              <div className="arch-step-name">Interpretamos</div>
              <div className="arch-step-desc">Reconhecemos o sentido da sua busca, mesmo que você não use as palavras exatas dos títulos.</div>
            </div>
            <div className="arch-step">
              <div className="arch-bubble">
                <span className="arch-num">3</span>
                <TextSearch size={24} />
              </div>
              <div className="arch-step-tag">BUSCAMOS</div>
              <div className="arch-step-name">Encontramos</div>
              <div className="arch-step-desc">Procuramos em centenas de produções dos pesquisadores da UNEB, indexadas e enriquecidas.</div>
            </div>
            <div className="arch-step">
              <div className="arch-bubble">
                <span className="arch-num">4</span>
                <Award size={24} />
              </div>
              <div className="arch-step-tag">VOCÊ EXPLORA</div>
              <div className="arch-step-name">Descubra</div>
              <div className="arch-step-desc">Veja resultados rankeados com Qualis e JCR. Acesse detalhes da produção e o perfil completo do pesquisador.</div>
            </div>
          </div>
        </section>

        {/* RECURSOS */}
        <section className="l-section" id="recursos">
          <div className="l-section-head">
            <div>
              <div className="l-section-eyebrow">Recursos</div>
              <h2 className="l-section-title">Quatro recursos<br />para <span className="ser">descobrir</span> produções.</h2>
            </div>
          </div>

          <div className="feat-bento">
            <article className="feat-cell feat-hero span-3">
              <div className="feat-icon"><Sparkles size={24} /></div>
              <div className="feat-title">Busca <span className="ser">semântica</span> em linguagem natural</div>
              <p className="feat-desc">
                Consultas convertidas em vetores via Sentence-Transformers; similaridade de cosseno
                via pgvector. Top-10 retornados em menos de 5 segundos.
              </p>
              <div className="feat-mockup">
                <div className="feat-mockup-bar"><span>vigilância genômica de dengue<small>0.92</small></span></div>
                <div className="feat-mockup-bar"><span>shifting patterns of dengue<small>0.89</small></span></div>
                <div className="feat-mockup-bar"><span>vector competence Aedes aegypti<small>0.86</small></span></div>
                <div className="feat-mockup-bar"><span>spatial-temporal dengue analyses<small>0.74</small></span></div>
              </div>
            </article>

            <article className="feat-cell span-3">
              <div className="feat-icon"><TextSearch size={24} /></div>
              <div className="feat-title">Busca textual com <span className="ser">FTS</span></div>
              <p className="feat-desc">
                Full-Text Search via tsvector do PostgreSQL. Operadores AND, OR e NOT.
                Resultados paginados em até 30 segundos.
              </p>
            </article>

            <article className="feat-cell span-2">
              <div className="feat-icon"><Award size={24} /></div>
              <div className="feat-title">Métricas bibliométricas</div>
              <p className="feat-desc">
                Filtre por Qualis CAPES, fator de impacto JCR, ano, área e tipo.
              </p>
            </article>

            <article className="feat-cell span-2">
              <div className="feat-icon"><UserRound size={24} /></div>
              <div className="feat-title">Perfil do <span className="ser">pesquisador</span></div>
              <p className="feat-desc">
                Veja a trajetória completa: produções, distribuição por Qualis, índice H e linha do tempo de publicações.
              </p>
            </article>
          </div>
        </section>

        {/* CTA STRIP */}
        <section className="l-cta-strip">
          <h2>Pronto para <span className="ser">acender</span> sua próxima descoberta?</h2>
          <p>Acesse o protótipo agora — dados reais da base UNEB, acesso público.</p>
          <div className="l-cta-row" style={{ justifyContent: 'center' }}>
            <Link className="btn btn-bright btn-lg" href="/busca">
              Abrir spark
              <ArrowRight size={14} />
            </Link>
          </div>
        </section>

        {/* FOOTER */}
        <footer className="l-footer">
          <div className="l-footer-grid">
            <div className="l-footer-brand">
              <Link href="/" className="brand dark">
                <span className="brand-mark"><SparkGlyph /></span>
                <span className="brand-word">spark<span className="brand-dot">.</span></span>
              </Link>
              <p className="l-footer-tag">
                Busca inteligente da produção científica da UNEB — ETL Lattes, busca textual e semântica.
              </p>
            </div>
            <div className="l-footer-col">
              <div className="l-footer-col-title">Projeto</div>
              <a href="#como-funciona">Como funciona</a>
              <a href="#recursos">Recursos</a>
              <Link href="/busca">Aplicação</Link>
            </div>
            <div className="l-footer-col">
              <div className="l-footer-col-title">Docs</div>
              <a href="#">API Swagger</a>
              <a href="#">Pipeline Hop</a>
              <a href="#">Modelo de dados</a>
            </div>
            <div className="l-footer-col">
              <div className="l-footer-col-title">UNEB</div>
              <a href="#">Pós-graduação</a>
              <a href="#">Lattes/CNPq</a>
              <a href="#">CAPES / Qualis</a>
            </div>
          </div>
          <div className="l-footer-bottom">
            <span>© 2026 · Projeto SPARK</span>
            <span>v1.0.0 — Protótipo</span>
          </div>
        </footer>

      </main>
    </div>
  );
}
