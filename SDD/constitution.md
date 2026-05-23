
# Project Constitution — SPARK

> Search Platform and Research Knowledge
>
> Version: 1.0 | Date: 22/05/2026

---

## Stack e Tecnologias

* Back-end: Python 3.11 com FastAPI e asyncpg
* Banco de dados: Supabase (PostgreSQL 15 gerenciado) com extensão `pgvector` habilitada
* Geração de embeddings: exclusivamente modelo local `all-MiniLM-L6-v2` via `sentence-transformers` — nenhuma API paga ou externa deve ser usada para embeddings
* Front-end: Next.js 14 com TypeScript e Tailwind CSS
* ETL: Apache Hop com conexão JDBC ao Supabase
* Hospedagem: Railway (back-end), Vercel (front-end)
* Containerização local: Docker + docker-compose

---

## Qualidade de Código

* Todo endpoint da API deve ter testes unitários cobrindo ao menos: resultado com dados, resultado vazio e erro de entrada inválida
* Testes unitários são obrigatórios para geração de embeddings e ranqueamento por similaridade antes de qualquer deploy
* Todos os endpoints FastAPI devem ser documentados via decorators do próprio framework — o Swagger em `/docs` deve estar sempre funcional
* Nenhum secret, credencial ou chave de API deve ser commitado no repositório — usar variáveis de ambiente via `.env` (ignorado pelo `.gitignore`)
* Todo commit deve referenciar a issue do Jira no formato `feat(SPK-XX): descrição` ou `fix(SPK-XX): descrição`

---

## Arquitetura

* Nunca calcular métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) em tempo de consulta — usar sempre os campos pré-calculados na tabela `pesquisadores`
* Toda escrita nas tabelas `pesquisadores` e `producoes` deve usar UPSERT (`ON CONFLICT DO UPDATE`) — inserção direta sem verificação de conflito é proibida
* O Worker de embeddings deve ser idempotente: processar apenas produções sem registro na tabela `vetores` e nunca duplicar vetores existentes
* A remoção de um pesquisador deve sempre propagar em cascata para suas produções e vetores associados
* O trigger de `tsvector` em `producoes` não deve ser removido ou desabilitado em nenhuma migration

---

## Segurança e Acesso

* Row Level Security (RLS) deve permanecer ativo em todas as tabelas do Supabase sem exceção
* Leitura pública (sem autenticação) é permitida apenas para `pesquisadores`, `producoes` e `vetores`
* A tabela `etl_logs` é restrita ao papel `admin` — nenhuma policy de leitura pública deve ser criada para ela
* O endpoint `POST /internal/trigger-etl` deve validar autenticação do papel `admin` antes de qualquer processamento — retornar 403 para qualquer requisição não autenticada ou sem o papel correto
* Nenhuma rota do painel administrativo (front-end) pode ser acessada sem sessão ativa do Supabase Auth

---

## Contratos de API

* Endpoints de busca devem retornar HTTP 200 com lista vazia quando não houver resultados — nunca retornar 404 para ausência de dados
* O campo `similarity_score` (valor entre 0 e 1) é obrigatório em toda resposta do endpoint `POST /api/search/semantic`
* Paginação máxima de 20 itens por página em todos os endpoints de listagem
* SLAs de performance não negociáveis: `POST /api/search/text` < 30 s, `POST /api/search/semantic` < 5 s

---

## Front-End

* Filtros de resultados (UC-02) devem ser aplicados sem recarregar a página — full page reload em filtragem é proibido
* Cards de produção devem sempre exibir título, veículo, ano, Qualis e JCR quando disponíveis — campos NULL devem ser omitidos silenciosamente, nunca exibidos como vazios ou "N/A"
* DOI deve sempre ser renderizado como link externo com `target="_blank"` e `rel="noopener noreferrer"`
* O `similarity_score` deve ter representação visual no card quando a busca semântica for utilizada

---

## ETL e Pipeline

* O pipeline Apache Hop deve registrar uma entrada em `etl_logs` ao final de cada execução, independentemente de sucesso ou falha parcial
* O Worker de embeddings deve ser acionado automaticamente após cada carga ETL — nunca depender de acionamento manual em produção
* Falhas de enriquecimento em APIs externas (CrossRef, OpenAlex) devem ser tratadas com fallback para NULL — o pipeline não deve falhar por indisponibilidade de APIs externas
* O campo `resumo` em `producoes` aceita NULL quando o CrossRef não retornar abstract

---

## Simplicity Gate

* Preferir soluções simples e diretas — nenhuma camada de abstração deve ser adicionada sem justificativa explícita no `plan.md`
* Não antecipar funcionalidades fora do escopo da Sprint atual
* Usar recursos nativos do framework antes de buscar bibliotecas externas adicionais
