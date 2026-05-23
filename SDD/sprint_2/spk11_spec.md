---
jira: SPK-11
título: US-05 · Pipeline ETL de leitura de XML Lattes
status: Em andamento
responsável: kalvinalbuquerque5
sprint: II
---
## Overview

O pipeline ETL é o mecanismo pelo qual os dados dos currículos Lattes dos pesquisadores da UNEB entram no sistema. Ele lê arquivos XML exportados do CNPq, extrai dados de pesquisadores e produções científicas, e os carrega no banco do SPARK — tornando as produções pesquisáveis pela primeira vez. Sem esse pipeline, o sistema não possui dados para exibir ou buscar.

---

## Target Users

**Engenheiro de Dados** — membro da equipe com acesso ao servidor e aos arquivos XML. É quem executa o pipeline em lote para carga inicial e reprocessamentos. Tem familiaridade com ferramentas de ETL e acesso direto ao banco de dados.

---

## Problem Statement

Os dados das produções científicas dos pesquisadores da UNEB existem apenas dentro de arquivos XML individuais exportados do currículo Lattes de cada pesquisador. Não há integração automática com o CNPq. Para que o sistema SPARK funcione, esses dados precisam ser extraídos, normalizados e carregados no banco de forma confiável — suportando múltiplos arquivos de uma vez e reprocessamentos sem corrupção de dados.

---

## User Journeys

### Jornada 1 — Carga inicial de currículos

1. O Engenheiro de Dados reúne os arquivos XML dos currículos Lattes dos pesquisadores, adiciona manualmente os campos `DEPARTAMENTO` e `CAMPUS` na tag `DADOS-GERAIS` de cada arquivo e os coloca em um diretório.
2. Executa o pipeline apontando para esse diretório.
3. O pipeline processa todos os arquivos em sequência, extraindo dados do pesquisador e de cada produção científica (artigos, eventos, livros, capítulos).
4. Os dados são normalizados e carregados no banco.
5. Ao final, o Engenheiro recebe um log de execução com a contagem de registros processados, inseridos e rejeitados — confirmando que a carga foi bem-sucedida ou identificando quais arquivos falharam.

### Jornada 2 — Reprocessamento de currículos existentes

1. O Engenheiro de Dados recebe XMLs atualizados de pesquisadores já cadastrados no sistema.
2. Executa o pipeline com os arquivos atualizados.
3. O pipeline identifica os registros existentes pela chave de identidade e atualiza os dados sem criar duplicatas.
4. Produções já existentes com campos enriquecidos (ex: DOI já preenchido) não têm esses valores sobrescritos por NULL.
5. O log registra quantos registros foram atualizados versus inseridos.

### Jornada 3 — Currículo sem produções

1. O Engenheiro de Dados processa um XML de pesquisador recém-cadastrado, sem produções bibliográficas.
2. O pipeline insere o pesquisador na base com métricas zeradas.
3. O pipeline não falha — registra zero produções no log e segue para o próximo arquivo.

### Jornada 4 — Arquivo XML com problema

1. O Engenheiro de Dados inclui acidentalmente um arquivo XML corrompido ou com encoding inesperado no diretório.
2. O pipeline detecta o erro no arquivo problemático, registra-o no log de execução e continua processando os demais arquivos normalmente.
3. O Engenheiro consegue identificar qual arquivo falhou pelo log e corrigir apenas aquele.

---

## Core Features

### F1 — Leitura de diretório de XMLs

O pipeline deve processar todos os arquivos XML presentes em um diretório configurado, tratando cada arquivo como o currículo de um pesquisador. Deve suportar múltiplos arquivos em uma única execução.

### F2 — Extração de dados do pesquisador

Para cada XML, o pipeline extrai: identificador Lattes, nome completo, departamento, campus e resumo do currículo. Os campos `departamento` e `campus` são atributos inseridos manualmente no XML antes do processamento.

### F3 — Extração de produções científicas

O pipeline extrai produções de quatro tipos: artigos publicados, trabalhos em eventos, livros e capítulos de livro. Para cada produção, extrai: título, ano de publicação, tipo, nome do veículo, ISSN e DOI (quando disponíveis).

### F4 — Normalização de dados

Antes da carga, os dados são normalizados: ISSN formatado com hífen, títulos limpos (sem caracteres de controle ou espaços extras), encoding convertido de ISO-8859-1 para UTF-8.

### F5 — Carga sem duplicatas (UPSERT)

A inserção de pesquisadores e produções deve ser idempotente. Reprocessar o mesmo XML não deve criar registros duplicados. Campos já enriquecidos não devem ser sobrescritos por NULL em reprocessamentos.

### F6 — Registro de log de execução

Ao final de cada execução, o pipeline registra no banco: timestamp de início e fim, status (sucesso/falha), contagem de registros processados, inseridos, atualizados e rejeitados, além de detalhes sobre arquivos com erro.

### F7 — Ambiente local de desenvolvimento

O ambiente de desenvolvimento local (banco de dados com extensão vetorial habilitada) deve ser provisionado via contêiner, sem dependência de configuração manual de banco.

---

## Success Metrics

- Pipeline executa com sucesso sobre ≥ 3 currículos Lattes reais sem erros de carga
- Reprocessamento do mesmo conjunto de XMLs não cria registros duplicados
- Log de execução gerado em 100% das execuções, com sucesso ou falha
- Arquivo XML corrompido não interrompe o processamento dos demais arquivos do lote
- Código publicado no repositório com README que permita qualquer membro da equipe executar o pipeline sem assistência

---

## Constraints

- Os XMLs seguem o padrão oficial do CNPq (encoding ISO-8859-1, tag raiz `CURRICULO-VITAE`) com adição manual dos campos `DEPARTAMENTO` e `CAMPUS`
- Os campos `departamento` e `campus` não existem no schema padrão do CNPq — devem ser adicionados manualmente antes de cada execução
- Toda escrita no banco deve usar UPSERT — inserção direta sem verificação de conflito é proibida pela constitution
- Nenhuma credencial pode ser incluída no código ou versionada no repositório
- O ambiente de desenvolvimento local deve funcionar sem acesso ao servidor de produção

---

## Assumptions

- Os XMLs dos currículos são obtidos manualmente via portal Lattes e disponibilizados em diretório acessível antes da execução
- Os campos `DEPARTAMENTO` e `CAMPUS` são preenchidos manualmente no XML antes do processamento — o pipeline não valida a presença desses campos nem falha por ausência deles
- O banco de destino já possui o schema criado (tabelas `pesquisadores`, `producoes`, `etl_logs`) antes da primeira execução do pipeline
- O ambiente local de desenvolvimento usa Docker e docker-compose

---

## Out of Scope

Os itens abaixo **não fazem parte desta história** e serão tratados em outros cartões:

- Enriquecimento com Qualis CAPES (lookup por ISSN no CSV da Sucupira)
- Enriquecimento com CrossRef (busca de DOI e resumo por título)
- Enriquecimento com OpenAlex (Impact Factor via ISSN)
- Atualização das métricas bibliométricas dos pesquisadores (`total_producoes`, `indice_h`, `total_a1_a2`)
- Acionamento do worker de geração de embeddings
- Gatilho do pipeline via interface web (`POST /internal/trigger-etl`)
- Interface administrativa de upload de XMLs

---

## Subtarefas (SPK-11)

| Chave  | Título                                                             | Status   |
| ------ | ------------------------------------------------------------------- | -------- |
| SPK-36 | Subir PostgreSQL + pgvector via Docker Compose                      | Pendente |
| SPK-37 | Construir pipeline Apache Hop de leitura e transformação dos XMLs | Pendente |
| SPK-38 | Implementar UPSERT e testar com 10 currículos reais                | Pendente |
| SPK-39 | Publicar código no Git com README de instalação e execução     | Pendente |

---

## Critérios de Aceitação (do cartão Jira)

- [ ] Pipeline lê diretório com múltiplos arquivos XML
- [ ] Campos de Pesquisador e Producoes inseridos nas respectivas tabelas
- [ ] Tratamento de duplicatas com UPSERT sem erros em reprocessamento
- [ ] Testado com no mínimo 3 currículos Lattes reais sem erros de carga
- [ ] Código no Git com README de instalação e execução
- [ ] Log de execução gerado com contagem de registros processados, inseridos e rejeitados

## Definição de Pronto (DoD)

- [ ] Código no Git com commit referenciando esta issue (`feat(SPK-11): ...`)
- [ ] Pipeline executado com sucesso nos 10 currículos de teste
- [ ] README atualizado com instruções de execução
- [ ] Demonstrado e aprovado na Sprint Review

---

## Instruções de Implementação

> Esta seção é dirigida ao agente que vai implementar esta história.
> Se você está lendo este arquivo, leia também antes de começar:
> - `SDD/constitution.md` — regras não negociáveis
> - `SDD/plan.md` — stack, estrutura de diretórios e decisões técnicas
> - `SDD/memory.md` — o que já foi implementado até agora
> - `documentation/Roadmap_para_ETL.pdf` — detalhes técnicos das fases 1, 2 e 4 do pipeline (seções 3, 4 e 6 do documento)

Implemente as 4 subtarefas abaixo em ordem. Ao concluir cada uma, marque o checkbox correspondente nos Critérios de Aceitação e atualize `SDD/memory.md`.

### SPK-36 — Ambiente local com Docker Compose

Crie ou atualize `docker-compose.yml` na raiz para subir PostgreSQL 15 com a extensão `pgvector` habilitada. Credenciais devem vir de variáveis de ambiente definidas no `.env` — nunca em hardcode. Valide que o serviço sobe e que a extensão `vector` está disponível após `docker-compose up`.

### SPK-37 — Pipeline Apache Hop de extração e transformação

Crie o pipeline em `etl/pipelines/` seguindo o mapeamento da Tabela 1 e Tabela 5 do Roadmap:

- `Get Files in Folder` para listar todos os `.xml` do diretório configurado
- `Get Data From XML` com encoding `ISO-8859-1` e XPath `/CURRICULO-VITAE` para extrair `lattes_id`, `nome_completo`, `departamento`, `campus` e `resumo` do pesquisador
- Steps adicionais de `Get Data From XML` para os 4 tipos de produção: `ARTIGO-PUBLICADO`, `TRABALHO-EM-EVENTOS`, `LIVRO-PUBLICADO-OU-ORGANIZADO`, `CAPITULO-DE-LIVRO-PUBLICADO`
- `Modified JavaScript Value` para normalização: ISSN com hífen na posição 4, título com `trim()` + remoção de caracteres de controle + conversão de encoding
- `Append Streams` para unificar os 4 fluxos com o campo `tipo_producao` discriminando cada tipo

### SPK-38 — UPSERT e validação com currículos reais

Configure os steps de carga usando as queries exatas das seções 6.3 e 6.4 do Roadmap: `pesquisadores` com chave `lattes_id`, `producoes` com chave `(pesquisador_id, titulo, ano_publicacao)` e `COALESCE` para preservar campos já preenchidos em reprocessamentos. Valide os três cenários das jornadas: carga duplicada sem criar duplicatas, pesquisador sem produções inserido sem falha, arquivo XML inválido registrado no log sem interromper o batch.

### SPK-39 — README e commit

Crie `etl/README.md` cobrindo: pré-requisitos, como subir o ambiente local, como adicionar `DEPARTAMENTO` e `CAMPUS` nos XMLs, e como executar o pipeline. Faça commit de todo o código no formato `feat(SPK-11): pipeline ETL de leitura de XML Lattes`.

### Limite de escopo

Não implemente nesta história: enriquecimento com Qualis, CrossRef ou OpenAlex; atualização de métricas bibliométricas; worker de embeddings; endpoint de trigger web. Esses itens pertencem a outras histórias.
