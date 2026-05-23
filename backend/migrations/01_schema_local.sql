-- ============================================================
-- SPARK -- Schema local para desenvolvimento com Docker
-- Adaptado do SPK-79_ddl.sql (sem dependência de auth.users)
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- ============================================================
-- TABELA: pesquisadores
-- ============================================================
CREATE TABLE IF NOT EXISTS pesquisadores (
  id               SERIAL       PRIMARY KEY,
  lattes_id        VARCHAR(16)  NOT NULL UNIQUE,
  nome_completo    VARCHAR(255) NOT NULL,
  departamento     VARCHAR(255),
  campus           VARCHAR(100),
  resumo           TEXT,
  total_producoes  INTEGER      NOT NULL DEFAULT 0,
  indice_h         INTEGER      NOT NULL DEFAULT 0,
  total_a1_a2      INTEGER      NOT NULL DEFAULT 0,
  data_atualizacao TIMESTAMP    DEFAULT NOW()
);


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
  resumo           TEXT,
  qualis           VARCHAR(5),
  jcr              NUMERIC(6, 3),
  texto_busca      TSVECTOR,
  created_at       TIMESTAMP    DEFAULT NOW()
);

ALTER TABLE producoes ADD CONSTRAINT uq_producao
  UNIQUE (pesquisador_id, titulo, ano_publicacao);

CREATE INDEX IF NOT EXISTS idx_producoes_texto_busca
  ON producoes USING GIN (texto_busca);

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
