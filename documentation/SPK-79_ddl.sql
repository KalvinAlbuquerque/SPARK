-- ============================================================
-- SPARK -- Sistema de Busca de Informações de Pesquisadores
-- DDL SQL -- Supabase (PostgreSQL)
-- Sprint I -- SPK-79
-- ============================================================

-- ------------------------------------------------------------
-- EXTENSÕES
-- ------------------------------------------------------------

-- Habilita busca vetorial (embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Habilita geração de UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- TABELA: perfis
-- Estende o auth.users do Supabase com role e nome de exibição
-- ============================================================
CREATE TABLE IF NOT EXISTS perfis (
  id              UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  role            VARCHAR(20) NOT NULL DEFAULT 'usuario'
                              CHECK (role IN ('usuario', 'admin')),
  nome_exibicao   VARCHAR(255),
  created_at      TIMESTAMP   NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE  perfis            IS 'Perfis de usuário que estendem o auth.users do Supabase.';
COMMENT ON COLUMN perfis.role       IS 'Papel do usuário no sistema: usuario ou admin.';


-- ============================================================
-- TABELA: pesquisadores
-- ============================================================
CREATE TABLE IF NOT EXISTS pesquisadores (
  id               SERIAL       PRIMARY KEY,
  lattes_id        VARCHAR(16)  NOT NULL UNIQUE,
  nome_completo    VARCHAR(255) NOT NULL,
  resumo           TEXT,
  data_atualizacao TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE  pesquisadores                  IS 'Dados dos pesquisadores extraídos do currículo Lattes.';
COMMENT ON COLUMN pesquisadores.lattes_id        IS 'Identificador único do currículo Lattes (16 dígitos).';
COMMENT ON COLUMN pesquisadores.data_atualizacao IS 'Data da última carga ETL para este pesquisador.';


-- ============================================================
-- TABELA: producoes
-- ============================================================
CREATE TABLE IF NOT EXISTS producoes (
  id               SERIAL       PRIMARY KEY,
  pesquisador_id   INTEGER      NOT NULL REFERENCES pesquisadores(id) ON DELETE CASCADE,
  titulo           VARCHAR(500) NOT NULL,
  tipo_producao    VARCHAR(50)  NOT NULL
                                CHECK (tipo_producao IN ('ARTIGO', 'EVENTO', 'LIVRO', 'CAPITULO', 'TECNICO')),
  ano_publicacao   INTEGER,
  nome_veiculo     VARCHAR(255),
  issn             VARCHAR(9),
  doi              VARCHAR(255),
  qualis           VARCHAR(5),
  jcr              NUMERIC(6, 3),
  texto_busca      TSVECTOR,
  created_at       TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE  producoes               IS 'Produções científicas dos pesquisadores.';
COMMENT ON COLUMN producoes.tipo_producao IS 'Tipo da produção: ARTIGO, EVENTO, LIVRO, CAPITULO ou TECNICO.';
COMMENT ON COLUMN producoes.issn          IS 'ISSN do periódico, usado para lookup no Qualis e JCR.';
COMMENT ON COLUMN producoes.doi           IS 'Digital Object Identifier obtido via XML Lattes ou CrossRef.';
COMMENT ON COLUMN producoes.qualis        IS 'Estrato Qualis CAPES do periódico (ex: A1, A2, B1).';
COMMENT ON COLUMN producoes.jcr           IS 'Fator de Impacto do periódico via OpenAlex (2yr_mean_citedness).';
COMMENT ON COLUMN producoes.texto_busca   IS 'Índice Full-Text Search gerado a partir do título.';

-- Constraint de deduplicação para UPSERT do pipeline ETL (SPK-73)
ALTER TABLE producoes ADD CONSTRAINT uq_producao
  UNIQUE (pesquisador_id, titulo, ano_publicacao);

-- Índice para Full-Text Search
CREATE INDEX IF NOT EXISTS idx_producoes_texto_busca
  ON producoes USING GIN (texto_busca);

-- Trigger para popular texto_busca automaticamente ao inserir/atualizar
CREATE OR REPLACE FUNCTION fn_atualiza_texto_busca()
RETURNS TRIGGER AS $$
BEGIN
  NEW.texto_busca := to_tsvector('portuguese', COALESCE(NEW.titulo, ''));
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_texto_busca
  BEFORE INSERT OR UPDATE ON producoes
  FOR EACH ROW EXECUTE FUNCTION fn_atualiza_texto_busca();


-- ============================================================
-- TABELA: vetores
-- ============================================================
CREATE TABLE IF NOT EXISTS vetores (
  id           SERIAL       PRIMARY KEY,
  producao_id  INTEGER      NOT NULL UNIQUE REFERENCES producoes(id) ON DELETE CASCADE,
  embedding    VECTOR(384)  NOT NULL,
  modelo_llm   VARCHAR(100) NOT NULL,
  created_at   TIMESTAMP    DEFAULT NOW()
);

COMMENT ON TABLE  vetores            IS 'Embeddings vetoriais das produções para busca semântica.';
COMMENT ON COLUMN vetores.embedding  IS 'Vetor de 384 dimensões gerado pelo modelo all-MiniLM-L6-v2 (Sentence-Transformers).';
COMMENT ON COLUMN vetores.modelo_llm IS 'Nome do modelo usado (ex: all-MiniLM-L6-v2).';

-- Índice vetorial para busca por similaridade de cosseno
CREATE INDEX IF NOT EXISTS idx_vetores_embedding
  ON vetores USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);


-- ============================================================
-- TABELA: etl_logs
-- ============================================================
CREATE TABLE IF NOT EXISTS etl_logs (
  id                  SERIAL      PRIMARY KEY,
  iniciado_em         TIMESTAMP   NOT NULL DEFAULT NOW(),
  finalizado_em       TIMESTAMP,
  status              VARCHAR(20) NOT NULL DEFAULT 'em_andamento'
                                  CHECK (status IN ('em_andamento', 'sucesso', 'erro')),
  total_inseridos     INTEGER     DEFAULT 0,
  total_atualizados   INTEGER     DEFAULT 0,
  total_sem_match     INTEGER     DEFAULT 0,
  detalhes            JSONB       DEFAULT '{}'
);

COMMENT ON TABLE  etl_logs          IS 'Histórico de execuções do pipeline ETL.';
COMMENT ON COLUMN etl_logs.status   IS 'Status da execução: em_andamento, sucesso ou erro.';
COMMENT ON COLUMN etl_logs.detalhes IS 'Detalhes da execução em JSON (erros, arquivos processados, etc).';


-- ============================================================
-- ROW LEVEL SECURITY (RLS) -- Supabase
-- ============================================================

-- perfis: cada usuário gerencia o próprio perfil
ALTER TABLE perfis ENABLE ROW LEVEL SECURITY;

CREATE POLICY perfis_select ON perfis
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY perfis_update ON perfis
  FOR UPDATE USING (auth.uid() = id);

-- producoes e pesquisadores: leitura pública
ALTER TABLE pesquisadores ENABLE ROW LEVEL SECURITY;
CREATE POLICY pesquisadores_select ON pesquisadores
  FOR SELECT USING (true);

ALTER TABLE producoes ENABLE ROW LEVEL SECURITY;
CREATE POLICY producoes_select ON producoes
  FOR SELECT USING (true);

-- etl_logs: apenas admin lê e escreve
ALTER TABLE etl_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY etl_logs_admin ON etl_logs
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM perfis
      WHERE perfis.id = auth.uid()
      AND perfis.role = 'admin'
    )
  );