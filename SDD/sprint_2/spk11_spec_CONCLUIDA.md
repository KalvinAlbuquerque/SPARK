---
jira: SPK-11
título: US-05 · Pipeline ETL de leitura de XML Lattes
status: Em andamento
responsável: kalvinalbuquerque5
sprint: II
---

## Overview

O pipeline ETL é o mecanismo pelo qual os dados dos currículos Lattes dos pesquisadores da UNEB entram no sistema. Ele lê arquivos XML exportados do CNPq, extrai dados de pesquisadores e produções científicas, e os carrega no banco do SPARK — tornando as produções pesquisáveis pela primeira vez. Sem esse pipeline, o sistema não possui dados para exibir ou buscar.

O pipeline é implementado no **Apache Hop**, a ferramenta de orquestração ETL definida na stack do projeto. Não deve ser reimplementado em Python puro, scripts shell ou qualquer outra ferramenta.

---

## Target Users

**Engenheiro de Dados** — membro da equipe com acesso ao servidor e aos arquivos XML. É quem executa o pipeline em lote para carga inicial e reprocessamentos. Tem familiaridade com ferramentas de ETL e acesso direto ao banco de dados.

---

## Problem Statement

Os dados das produções científicas dos pesquisadores da UNEB existem apenas dentro de arquivos XML individuais exportados do currículo Lattes de cada pesquisador. Não há integração automática com o CNPq. Para que o sistema SPARK funcione, esses dados precisam ser extraídos, normalizados e carregados no banco de forma confiável via Apache Hop — suportando múltiplos arquivos de uma vez e reprocessamentos sem corrupção de dados.

---

## User Journeys

### Jornada 1 — Carga inicial de currículos

1. O Engenheiro de Dados obtém os XMLs manualmente via portal Lattes, preenche os atributos `DEPARTAMENTO="DCET"` e `CAMPUS="Campus I"` na tag `DADOS-GERAIS` de cada arquivo e os coloca em um diretório configurado.
2. Executa o pipeline Apache Hop apontando para esse diretório.
3. O pipeline processa todos os arquivos em sequência via steps `Get Files in Folder` + `Get Data From XML`, extraindo dados do pesquisador e de cada produção científica (artigos, eventos, livros, capítulos).
4. Os dados são normalizados via step `Modified JavaScript Value` e carregados no banco via UPSERT.
5. Ao final, o Engenheiro consulta o registro gerado em `etl_logs` com a contagem de registros processados, inseridos, atualizados e rejeitados — confirmando que a carga foi bem-sucedida ou identificando quais arquivos falharam.

### Jornada 2 — Reprocessamento de currículos existentes

1. O Engenheiro de Dados recebe XMLs atualizados de pesquisadores já cadastrados.
2. Executa o pipeline Apache Hop com os arquivos atualizados.
3. O pipeline identifica os registros existentes pelas chaves de conflito (`lattes_id` para pesquisadores; `pesquisador_id + titulo + ano_publicacao` para produções) e atualiza sem criar duplicatas.
4. Campos já enriquecidos (ex: DOI já preenchido) não são sobrescritos por NULL — o `COALESCE` no UPSERT preserva os valores existentes.
5. O log em `etl_logs` registra quantos registros foram inseridos versus atualizados.

### Jornada 3 — Currículo sem produções

1. O Engenheiro de Dados processa um XML de pesquisador sem produções bibliográficas.
2. O pipeline insere o pesquisador na tabela `pesquisadores`.
3. O pipeline não falha — registra zero produções no log e segue para o próximo arquivo.

### Jornada 4 — Arquivo XML com problema

1. O Engenheiro de Dados inclui acidentalmente um arquivo XML corrompido ou com encoding inesperado.
2. O step de parse do Apache Hop redireciona o registro para a stream de erro (Error Handling do Hop), registra o arquivo problemático no campo `detalhes` de `etl_logs` e continua processando os demais arquivos normalmente.
3. O Engenheiro identifica qual arquivo falhou pelo log e corrige apenas aquele.

---

## Core Features

### F1 — Leitura de diretório de XMLs via Apache Hop

O pipeline usa o step nativo `Get Files in Folder` do Apache Hop para listar todos os arquivos `.xml` do diretório configurado, seguido de `Get Data From XML` para o parse de cada arquivo com encoding `ISO-8859-1` e Loop XPath `/CURRICULO-VITAE`.

### F2 — Extração de dados do pesquisador

Para cada XML, o pipeline extrai via XPath os campos mapeados na Tabela 1 do Roadmap:

| Nó XML | Atributo | Campo no banco |
|---|---|---|
| `CURRICULO-VITAE` | `NUMERO-IDENTIFICADOR` | `pesquisadores.lattes_id` |
| `DADOS-GERAIS` | `NOME-COMPLETO` | `pesquisadores.nome_completo` |
| `DADOS-GERAIS` | `DEPARTAMENTO` | `pesquisadores.departamento` |
| `DADOS-GERAIS` | `CAMPUS` | `pesquisadores.campus` |
| `RESUMO-CV` | `TEXTO-RESUMO-CV-RH` | `pesquisadores.resumo` |

Os atributos `DEPARTAMENTO` e `CAMPUS` não existem no schema padrão do CNPq e são adicionados manualmente no XML antes de cada execução.

### F3 — Extração de produções científicas por tipo

O pipeline trata cada tipo de produção como um fluxo separado no Apache Hop, usando steps `Get Data From XML` com os XPaths correspondentes, e unifica os quatro fluxos ao final com `Append Streams` adicionando o campo discriminador `tipo_producao`:

| Campo destino | ARTIGO | EVENTO | LIVRO | CAPÍTULO |
|---|---|---|---|---|
| `tipo_producao` | `ARTIGO` | `EVENTO` | `LIVRO` | `CAPITULO` |
| `titulo` | `TITULO-DO-ARTIGO` | `TITULO-DO-TRABALHO` | `TITULO-DO-LIVRO` | `TITULO-DO-CAPITULO-DO-LIVRO` |
| `ano_publicacao` | `ANO-DO-ARTIGO` | `ANO-DO-TRABALHO` | `ANO` | `ANO` |
| `doi` | `DOI` | `DOI` | `DOI` | `DOI` |
| `nome_veiculo` | `TITULO-DO-PERIODICO` | (sem campo) | (título) | `TITULO-DO-LIVRO` |
| `issn` | `ISSN` (detalhamento) | (sem campo) | (sem campo) | (sem campo) |

Nota: `TRABALHO-EM-EVENTOS` não possui nó `DETALHAMENTO` na maioria dos currículos. Os campos `qualis`, `jcr` e `resumo` ficam NULL para `tipo=EVENTO`.

### F4 — Normalização via Modified JavaScript Value

Antes da carga, o step `Modified JavaScript Value` do Apache Hop aplica:

- **ISSN**: remover caracteres não numéricos; se resultado = 8 dígitos, inserir hífen na posição 4 (`01234567` → `0123-4567`); se comprimento ≠ 8, gravar NULL e registrar no log
- **Título**: `trim()`, remoção de caracteres de controle e quebras de linha, conversão de encoding ISO-8859-1 para UTF-8. Não aplicar stemming — o CrossRef prefere o título completo

### F5 — Carga sem duplicatas (UPSERT)

A carga usa os steps `Table Output` ou `Execute SQL` do Apache Hop com as queries exatas das seções 6.3 e 6.4 do Roadmap:

**UPSERT de pesquisadores** (chave: `lattes_id`):
```sql
INSERT INTO pesquisadores
  (lattes_id, nome_completo, departamento, campus, resumo, data_atualizacao)
VALUES (?, ?, ?, ?, ?, NOW())
ON CONFLICT (lattes_id) DO UPDATE SET
  nome_completo    = EXCLUDED.nome_completo,
  departamento     = EXCLUDED.departamento,
  campus           = EXCLUDED.campus,
  resumo           = EXCLUDED.resumo,
  data_atualizacao = NOW();
```

**UPSERT de produções** (chave: `pesquisador_id + titulo + ano_publicacao`):
```sql
INSERT INTO producoes
  (pesquisador_id, titulo, tipo_producao, ano_publicacao,
   nome_veiculo, issn, doi, resumo, qualis, jcr)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (pesquisador_id, titulo, ano_publicacao) DO UPDATE SET
  doi          = COALESCE(EXCLUDED.doi, producoes.doi),
  resumo       = COALESCE(EXCLUDED.resumo, producoes.resumo),
  qualis       = COALESCE(EXCLUDED.qualis, producoes.qualis),
  jcr          = COALESCE(EXCLUDED.jcr, producoes.jcr),
  nome_veiculo = EXCLUDED.nome_veiculo;
```

### F6 — Registro de log de execução

Ao final de cada execução, o pipeline registra em `etl_logs` via step `Execute SQL` do Apache Hop:

```sql
INSERT INTO etl_logs
  (iniciado_em, finalizado_em, status,
   total_inseridos, total_atualizados, total_sem_match, detalhes)
VALUES (?, NOW(), ?, ?, ?, ?,
  '{
    "arquivos_processados": N,
    "sem_match_qualis": [...],
    "sem_match_doi": [...],
    "sem_match_jcr": [...],
    "sem_resumo": [...]
  }'::jsonb
);
```

---

## Success Metrics

- Pipeline Apache Hop executa com sucesso sobre ≥ 3 currículos Lattes reais sem erros de carga
- Reprocessamento do mesmo conjunto de XMLs não cria registros duplicados
- Registro gerado em `etl_logs` em 100% das execuções, com sucesso ou falha
- Arquivo XML corrompido não interrompe o processamento dos demais arquivos do lote
- Código do pipeline (arquivos `.hop`) publicado no repositório com README que permita qualquer membro da equipe executar sem assistência

---

## Constraints

- **O pipeline deve ser implementado em Apache Hop — não em Python puro, shell scripts ou qualquer outra ferramenta**
- Os XMLs seguem o padrão oficial do CNPq (encoding ISO-8859-1, tag raiz `CURRICULO-VITAE`) com adição manual de `DEPARTAMENTO` e `CAMPUS`
- Toda escrita no banco deve usar UPSERT com as queries exatas das seções 6.3 e 6.4 do Roadmap — inserção direta sem verificação de conflito é proibida pela constitution
- A conexão com o Supabase é feita via JDBC (host `db.{PROJECT_REF}.supabase.co`, porta 5432, SSL obrigatório)
- Nenhuma credencial pode ser incluída no código ou versionada no repositório — usar variáveis de ambiente (`SUPABASE_DB_PASSWORD`, `ETL_EMAIL`, `INTERNAL_API_KEY`)
- O ambiente de desenvolvimento local deve funcionar sem acesso ao servidor de produção

---

## Assumptions

- Apache Hop está instalado na máquina do Engenheiro de Dados
- Os XMLs são obtidos manualmente via portal Lattes e disponibilizados em diretório acessível antes da execução
- Os atributos `DEPARTAMENTO="DCET"` e `CAMPUS="Campus I"` são inseridos manualmente na tag `DADOS-GERAIS` de cada XML antes do processamento
- O pipeline não valida a presença desses campos nem falha por ausência deles
- O banco de destino já possui o schema criado (tabelas `pesquisadores`, `producoes`, `etl_logs`) antes da primeira execução
- O ambiente local usa Docker e docker-compose para subir o PostgreSQL + pgvector

---

## Out of Scope

Os itens abaixo **não fazem parte desta história** e serão tratados em outros cartões:

- Enriquecimento com Qualis CAPES (Fase 3 do Roadmap — lookup via CSV da Sucupira)
- Enriquecimento com CrossRef (Fase 3 — busca de DOI e resumo por título)
- Enriquecimento com OpenAlex (Fase 3 — Impact Factor via ISSN)
- Atualização das métricas bibliométricas (`total_producoes`, `indice_h`, `total_a1_a2`) — Fase 5 do Roadmap
- Acionamento do worker de geração de embeddings — Fase 6 do Roadmap
- Gatilho do pipeline via interface web (`POST /internal/trigger-etl`) — Seção 7 do Roadmap
- Interface administrativa de upload de XMLs

---

## Subtarefas (SPK-11)

| Chave  | Título                                                              | Status   |
|--------|---------------------------------------------------------------------|----------|
| SPK-36 | Subir PostgreSQL + pgvector via Docker Compose                      | Pendente |
| SPK-37 | Construir pipeline Apache Hop de leitura e transformação dos XMLs  | Pendente |
| SPK-38 | Implementar UPSERT e testar com 3 currículos reais                 | Pendente |
| SPK-39 | Publicar código no Git com README de instalação e execução         | Pendente |

---

## Critérios de Aceitação

- [ ] Pipeline Apache Hop lê diretório com múltiplos arquivos XML via `Get Files in Folder`
- [ ] Campos de `pesquisadores` e `producoes` inseridos nas respectivas tabelas com os mapeamentos da Tabela 1 e Tabela 5 do Roadmap
- [ ] Tratamento de duplicatas com UPSERT e `COALESCE` sem erros em reprocessamento
- [ ] Testado com no mínimo 3 currículos Lattes reais sem erros de carga
- [ ] Código do pipeline (arquivos `.hop`) no Git com README de instalação e execução
- [ ] Registro em `etl_logs` gerado com contagem de processados, inseridos, atualizados e rejeitados

## Definição de Pronto (DoD)

- [ ] Código no Git com commit referenciando esta issue (`feat(SPK-11): ...`)
- [ ] Pipeline Apache Hop executado com sucesso nos currículos de teste
- [ ] README atualizado com instruções de execução
- [ ] Demonstrado e aprovado na Sprint Review

---

## Instruções de Implementação

> Esta seção é dirigida ao agente que vai implementar esta história.
> Leia obrigatoriamente antes de começar:
>
> - `SDD/constitution.md` — regras não negociáveis (especialmente: toda escrita usa UPSERT; sem credenciais no repositório)
> - `SDD/plan.md` — stack, estrutura de diretórios e decisões técnicas
> - `SDD/memory.md` — o que já foi implementado até agora
> - `documentation/Roadmap_para_ETL.pdf` — fonte técnica autoritativa para esta história (seções 3, 4 e 6)

**Ferramenta obrigatória: Apache Hop.** Não implemente este pipeline em Python, shell script ou qualquer outra linguagem. Todos os steps devem ser criados dentro do Apache Hop usando os steps nativos descritos abaixo.

Implemente as 4 subtarefas em ordem. Ao concluir cada uma, marque o checkbox correspondente nos Critérios de Aceitação e atualize `SDD/memory.md`.

### SPK-36 — Ambiente local com Docker Compose

Crie ou atualize `docker-compose.yml` na raiz para subir PostgreSQL 15 com a extensão `pgvector` habilitada. Credenciais devem vir exclusivamente de variáveis de ambiente definidas no `.env` — nunca em hardcode. Valide que o serviço sobe e que `CREATE EXTENSION IF NOT EXISTS vector;` executa sem erro após `docker-compose up`.

### SPK-37 — Pipeline Apache Hop: Extração e Transformação

Crie o pipeline em `etl/pipelines/` com os seguintes steps nativos do Apache Hop, na ordem exata descrita nas seções 3 e 4 do Roadmap:

1. **`Get Files in Folder`** — lista todos os `.xml` do diretório configurado
2. **`Get Data From XML`** — encoding `ISO-8859-1`, Loop XPath `/CURRICULO-VITAE`, extrai `NUMERO-IDENTIFICADOR` → `lattes_id`
3. **Steps adicionais `Get Data From XML`** para os sub-nós:
   - XPath `/CURRICULO-VITAE/DADOS-GERAIS` → `NOME-COMPLETO`, `DEPARTAMENTO`, `CAMPUS`
   - XPath `/CURRICULO-VITAE/DADOS-GERAIS/RESUMO-CV` → `TEXTO-RESUMO-CV-RH`
   - XPath `.//ARTIGO-PUBLICADO` → loop por artigo (campos da Tabela 5 do Roadmap)
   - XPath `.//TRABALHO-EM-EVENTOS` → loop por evento
   - XPath `.//LIVRO-PUBLICADO-OU-ORGANIZADO` → loop por livro
   - XPath `.//CAPITULO-DE-LIVRO-PUBLICADO` → loop por capítulo
4. **`Modified JavaScript Value`** — normalização de ISSN (hífen na posição 4) e título (trim + remoção de caracteres de controle + conversão de encoding), conforme seção 4.1 e 4.2 do Roadmap
5. **`Append Streams`** — unifica os 4 fluxos de produção com campo `tipo_producao` discriminando cada tipo
6. **Error Handling** — configurar stream de erro nos steps de parse para redirecionar arquivos problemáticos sem interromper o batch

Os XMLs dos currículos de teste já estão com `DEPARTAMENTO="DCET"` e `CAMPUS="Campus I"` preenchidos na tag `DADOS-GERAIS`. Não é necessário alterar os XMLs.

### SPK-38 — UPSERT e validação com currículos reais

Configure os steps de carga usando obrigatoriamente as queries exatas das seções 6.3 e 6.4 do Roadmap (transcritas na F5 desta spec). Valide os quatro cenários das jornadas:

- Carga inicial: dados inseridos corretamente nas tabelas `pesquisadores` e `producoes`
- Reprocessamento: sem duplicatas, `COALESCE` preservando campos já preenchidos
- Pesquisador sem produções: inserido sem falha, zero produções no log
- Arquivo XML inválido: registrado em `etl_logs.detalhes`, demais arquivos processados normalmente

### SPK-39 — README e commit

Crie `etl/README.md` cobrindo: pré-requisitos (Apache Hop, Java, Docker), como subir o ambiente local, como preencher `DEPARTAMENTO` e `CAMPUS` nos XMLs, como configurar as variáveis de ambiente e como executar o pipeline. Faça commit de todo o código no formato `feat(SPK-11): pipeline ETL de leitura de XML Lattes`.

### Limite de escopo

Não implemente nesta história: lookup de Qualis, CrossRef ou OpenAlex; atualização de métricas bibliométricas; worker de embeddings; endpoint de trigger web. Esses itens pertencem a outras histórias mapeadas nas Fases 3, 5 e 6 do Roadmap.