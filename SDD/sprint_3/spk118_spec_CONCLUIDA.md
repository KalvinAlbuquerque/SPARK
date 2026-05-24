# SPK-118 · Dockerfile da API e integração no docker-compose

**Sprint:** 3 | **Épico:** EP-03 · Back-End Python, API REST e Deploy
**Jira:** SPK-118 | **Story Points:** 3

---

## 1. Overview

O ambiente de desenvolvimento local do SPARK hoje exige que o banco de dados e a API sejam iniciados em processos separados. Esta história integra a API ao ambiente containerizado existente, de modo que qualquer desenvolvedor consiga subir o stack completo — banco e API — com um único comando, sem configuração manual adicional. Além da conteinerização, a história inclui testes de integração que exercitam os endpoints reais contra o banco Docker, validando o comportamento end-to-end sem mocks.

---

## 2. Target Users

| Persona | Contexto de uso |
|---------|----------------|
| **Desenvolvedor do projeto** | Precisa de um ambiente local funcional e reproduzível para desenvolver e testar endpoints |
| **Avaliador / professor** | Clona o repositório e quer validar o funcionamento da API sem instalar dependências Python manualmente |

---

## 3. Problem Statement

Atualmente o `docker-compose.yml` sobe apenas o banco de dados. Para rodar a API, o desenvolvedor precisa instalar as dependências Python no sistema local, configurar variáveis de ambiente manualmente e iniciar o servidor em um terminal separado — e ainda garantir que o banco já esteja pronto antes de tentar conectar. Isso aumenta o atrito de onboarding e torna o ambiente não reproduzível entre máquinas diferentes.

---

## 4. User Journeys

### UC-01 · Desenvolvedor sobe o stack pela primeira vez

1. Desenvolvedor clona o repositório e copia `.env.example` para `.env`.
2. Preenche apenas a senha do banco no `.env`.
3. Executa um único comando para subir o ambiente.
4. Aguarda os serviços iniciarem (banco primeiro, depois a API).
5. Abre o navegador em `http://localhost:8000/docs` e vê o Swagger funcional.
6. Realiza chamadas nos endpoints sem qualquer configuração adicional.

### UC-02 · Desenvolvedor itera no código da API

1. Com o ambiente já rodando, o desenvolvedor edita um arquivo Python da API.
2. O servidor detecta a mudança e reinicia automaticamente.
3. O desenvolvedor recarrega o Swagger e testa o comportamento atualizado — sem precisar parar e reiniciar o ambiente.

### UC-03 · Desenvolvedor executa os testes de integração

1. Com o ambiente Docker rodando (`docker compose up`), o desenvolvedor executa a suíte de testes de integração.
2. Os testes fazem chamadas HTTP reais para a API em `http://localhost:8000`, que por sua vez consulta o banco Docker.
3. Os resultados refletem os dados reais presentes no banco — sem nenhum mock ou substituição.
4. O desenvolvedor vê quais endpoints passaram e quais falharam, com a resposta real retornada pela API.

### UC-05 · Desenvolvedor reinicia o ambiente após pausa

1. Desenvolvedor executa o comando de subida novamente.
2. O banco retoma com os dados persistidos do volume anterior.
3. A API conecta ao banco sem erros de inicialização.

---

## 5. Core Features

### 5.1 Ambiente unificado

- O stack completo (banco + API) sobe com um único comando a partir da raiz do repositório.
- O banco permanece o ponto de entrada e a API não tenta conectar antes de o banco estar saudável.

### 5.2 Isolamento de dependências

- A API roda dentro de um container com todas as suas dependências isoladas — nenhuma biblioteca Python precisa ser instalada no sistema do desenvolvedor para executar a API.

### 5.3 Desenvolvimento sem rebuild

- Alterações nos arquivos de código da API são refletidas no servidor em execução sem necessidade de reconstruir a imagem ou reiniciar o ambiente manualmente.

### 5.4 Configuração por variáveis de ambiente

- Todas as configurações sensíveis (credenciais do banco, etc.) são injetadas via arquivo `.env` — nenhum valor é fixo na imagem ou no arquivo de composição.

### 5.5 Persistência de dados

- Os dados do banco sobrevivem a reinicializações do ambiente — um `docker compose down` sem remoção de volumes não apaga os dados.

### 5.6 Testes de integração contra o banco real

- Existe uma suíte de testes que faz chamadas HTTP reais para a API com o ambiente Docker rodando — sem mocks de banco ou de pool de conexões.
- Os testes cobrem todos os endpoints públicos implementados no SPK-92, verificando: código HTTP correto, estrutura da resposta, ausência de campos NULL nas respostas, e comportamentos de borda (ID inexistente → 404, query vazia → 422, busca sem resultados → 200 com lista vazia).
- A busca semântica é validada confirmando que `similarity_score` está presente em cada item retornado e seu valor está entre 0 e 1.
- Os testes são independentes da ordem de execução e não alteram dados do banco (apenas leitura).

---

## 6. Success Metrics

| Métrica | Critério de aceite |
|---------|--------------------|
| Stack sobe com um comando | `docker compose up` a partir da raiz inicia banco e API sem erros manuais adicionais |
| API acessível após subida | `http://localhost:8000/docs` responde com Swagger funcional |
| API aguarda o banco | A API não lança erros de conexão durante a inicialização do banco |
| Hot-reload funcional | Editar um arquivo `.py` da API reflete no servidor sem rebuild |
| Sem credenciais na imagem | Nenhum secret está hardcoded no Dockerfile ou no docker-compose |
| Dados persistem | `docker compose down && docker compose up` mantém os dados do banco |
| Testes de integração passando | `pytest tests/integration/` com ambiente Docker rodando: todos os endpoints cobertos, zero falhas |
| Testes não alteram dados | Estado do banco é idêntico antes e após a execução dos testes |

---

## 7. Constraints

- O `docker-compose.yml` existente não pode quebrar o funcionamento atual do serviço `db` — a integração é aditiva.
- O ambiente de desenvolvimento local é o único escopo desta história — não é deploy em produção.
- O modelo de embedding (`all-MiniLM-L6-v2`) já está em cache na máquina host; o container deve reutilizar esse cache para não baixar o modelo a cada rebuild.
- A imagem da API deve ser construída a partir do código local (`./backend`), não de um registry externo.
- Os testes de integração só podem rodar com o ambiente Docker no ar — não há modo offline para eles.

---

## 8. Assumptions

- O desenvolvedor tem Docker e Docker Compose instalados na máquina.
- O arquivo `.env` é criado manualmente a partir do `.env.example` antes de subir o ambiente — não é gerado automaticamente.
- A porta `8000` está disponível no host para a API e a porta `5432` para o banco.
- O modelo de embedding está em cache em `~/.cache/huggingface/hub/` no host.
- Os dados de teste no banco (carregados nos Sprints 1 e 2) estão presentes: ao menos 1 pesquisador e 1 produção existem para os testes de integração de leitura.

---

## 9. Out of Scope

- Deploy em produção (Railway, Vercel ou qualquer cloud).
- Imagem multi-stage otimizada para produção.
- Container para o front-end Next.js.
- Container para o worker de embeddings (coberto em história separada).
- CI/CD pipeline ou build automatizado.
- Configuração de rede além do ambiente local.
- Testes de carga ou performance (os testes de integração verificam apenas corretude).

---

## Prompt de implementação

Leia esta spec do início ao fim antes de qualquer ação. Em seguida:

1. Leia `SDD/constitution.md` e `SDD/plan.md` para confirmar restrições arquiteturais.
2. Leia `SDD/memory.md` para entender o estado atual do ambiente Docker e da API implementada (SPK-92).
3. Leia o `docker-compose.yml` atual na raiz — ele tem apenas o serviço `db`.
4. Leia `backend/requirements.txt` para saber as dependências da API.
5. Crie `backend/Dockerfile` com a imagem da API (base Python, instalação de dependências, comando de start com hot-reload).
6. Adicione o serviço `api` ao `docker-compose.yml` com: build apontando para `./backend`, porta `8000`, `depends_on` com `condition: service_healthy` no `db`, volume do código-fonte para hot-reload, volume do cache HuggingFace do host, e todas as variáveis de ambiente necessárias via `.env`.
7. Valide subindo o ambiente com `docker compose up --build` e confirmando que `http://localhost:8000/docs` responde.
8. Crie `backend/tests/integration/test_api.py` com testes que fazem chamadas HTTP reais para `http://localhost:8000` (use `httpx.Client` ou `requests`). Cubra: `GET /api/stats`, `GET /api/producoes/tipos`, `GET /api/producoes/{id}` (200 + 404), `POST /api/search/text` (200 com dados, 422 com query vazia, 200 com lista vazia), `POST /api/search/semantic` (200 com `similarity_score` em cada item), `GET /api/pesquisadores/{id}` (200 + 404), `GET /api/pesquisadores/{id}/producoes`, `GET /api/pesquisadores/{id}/stats`.
9. Execute `pytest tests/integration/ -v` com o Docker rodando e confirme que todos passam.
10. Ao finalizar, atualize `SDD/memory.md` e renomeie este arquivo para `spk118_spec_CONCLUIDA.md`.
