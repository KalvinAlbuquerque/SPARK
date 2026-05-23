# ETL — Pipeline Lattes SPARK

Pipeline Apache Hop que extrai dados dos currículos Lattes (XML) e carrega nas tabelas `pesquisadores` e `producoes` do banco PostgreSQL.

---

## Pré-requisitos

| Requisito               | Versão mínima          |
| ----------------------- | ------------------------ |
| Java (JDK)              | 11                       |
| Apache Hop              | 2.x                      |
| Docker + Docker Compose | qualquer versão recente |
| PostgreSQL driver JDBC  | incluído no Hop         |

---

## 1. Subir o banco local (Docker)

**Windows (PowerShell):**

```powershell
# Na raiz do repositório
Copy-Item .env.example .env
# Edite .env e defina POSTGRES_PASSWORD

docker-compose up -d
```

**Linux/macOS:**

```bash
cp .env.example .env
# Edite .env e defina POSTGRES_PASSWORD
docker-compose up -d
```

Aguarde o healthcheck: o banco estará pronto quando `docker-compose ps` mostrar `(healthy)`. O schema é criado automaticamente pelo arquivo `backend/migrations/01_schema_local.sql`.

Para verificar que o pgvector está ativo:

```powershell
docker exec -it <container_id> psql -U spark -d spark -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

---

## 2. Configurar variáveis de ambiente no Apache Hop

### Opção A — Variáveis de ambiente no terminal (antes de executar o Hop)

**Windows (PowerShell):**

```powershell
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB   = "spark"
$env:POSTGRES_USER = "spark"
$env:POSTGRES_PASSWORD = "changeme"
$env:XML_DIR = "C:\caminho\absoluto\para\data\xml"
```

**Linux/macOS (bash):**

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=spark
export POSTGRES_USER=spark
export POSTGRES_PASSWORD=changeme
export XML_DIR=/caminho/absoluto/para/data/xml
```

### Opção B — Ambiente Hop via GUI (recomendado, persiste entre sessões)

Abra o Apache Hop GUI → menu **File → Edit Metadata → Hop Environments** → importe o arquivo `etl/config/spark-env.json` e preencha `POSTGRES_PASSWORD`.

---

## 3. Preparar os XMLs Lattes

### 3.1 Obter os arquivos XML

Os XMLs são exportados manualmente pelo portal Lattes (plataforma.cnpq.br) para cada pesquisador.

### 3.2 Adicionar campos de departamento e campus

Cada XML deve ter os atributos `DEPARTAMENTO` e `CAMPUS` inseridos manualmente na tag `<DADOS-GERAIS>` antes do processamento, pois esses campos não existem no schema padrão do CNPq:

```xml
<!-- Antes -->
<DADOS-GERAIS NOME-COMPLETO="..." ...>

<!-- Depois -->
<DADOS-GERAIS NOME-COMPLETO="..." DEPARTAMENTO="DCET" CAMPUS="Campus I" ...>
```

Os XMLs em `data/xml/` já possuem esses campos preenchidos e podem ser usados como referência.

### 3.3 Colocar os XMLs no diretório

Coloque todos os arquivos `.xml` em um diretório (ex: `data/xml/`) e configure a variável `XML_DIR` apontando para ele.

---

## 4. Configurar a conexão de banco no Hop

### Via GUI

1. Abra o Apache Hop GUI
2. Menu **File → New → Relational Database Connection**
3. Crie uma conexão com o nome exato `spark_db`:
   - **Type:** PostgreSQL
   - **Host:** `${POSTGRES_HOST}` (ou o valor direto)
   - **Port:** `${POSTGRES_PORT}`
   - **Database:** `${POSTGRES_DB}`
   - **Username:** `${POSTGRES_USER}`
   - **Password:** `${POSTGRES_PASSWORD}`
4. Salve em `etl/metadata/rdbms/spark_db.json`

O arquivo `etl/metadata/rdbms/spark_db.json` já existe como template — ele usa variáveis de ambiente. Se o Hop não resolver as variáveis automaticamente, substitua pelos valores diretos (sem commitar no repositório).

---

## 5. Executar o pipeline

### Via workflow (recomendado)

O workflow `spark_etl.hwf` executa os dois pipelines em ordem e registra o log:

**Windows (PowerShell) — defina HOP_HOME antes:**

```powershell
$env:XML_DIR = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\xml"

& "$env:HOP_HOME\hop-run.bat" `
  --runconfig=local `
  --file=workflows/spark_etl.hwf `
  "--parameters=XML_DIR=$env:XML_DIR"
```

**Linux/macOS:**

```bash
export XML_DIR=/caminho/absoluto/para/data/xml

hop-run.sh \
  --runconfig=local \
  --file=workflows/spark_etl.hwf \
  --parameters=XML_DIR=$XML_DIR
```

### Via pipelines individuais

Execute **obrigatoriamente nessa ordem**:

**Windows (PowerShell):**

```powershell
# 1. Pesquisadores
& "$env:HOP_HOME\hop-run.bat" --runconfig=local `
  --file=pipelines/lattes_pesquisadores.hpl `
  "--parameters=XML_DIR=$env:XML_DIR"

# 2. Produções (só depois do passo 1)
& "$env:HOP_HOME\hop-run.bat" --runconfig=local `
  --file=pipelines/lattes_producoes.hpl `
  "--parameters=XML_DIR=$env:XML_DIR"
```

**Linux/macOS:**

```bash
hop-run.sh --runconfig=local \
  --file=pipelines/lattes_pesquisadores.hpl \
  --parameters=XML_DIR=$XML_DIR

hop-run.sh --runconfig=local \
  --file=pipelines/lattes_producoes.hpl \
  --parameters=XML_DIR=$XML_DIR
```

**Atenção:** `lattes_producoes.hpl` depende de `lattes_pesquisadores.hpl` ter sido executado antes, pois faz lookup de `pesquisador_id` por `lattes_id`.

### Via GUI do Apache Hop

1. Abra o Apache Hop GUI
2. Vá em **File → Open** e abra `workflows/spark_etl.hwf`
3. Configure o parâmetro `XML_DIR` no painel de parâmetros
4. Clique em **Run (F9)**

---

## 6. Verificar resultado

```sql
-- Pesquisadores carregados
SELECT lattes_id, nome_completo, departamento, campus FROM pesquisadores;

-- Total de produções por tipo
SELECT tipo_producao, COUNT(*) FROM producoes GROUP BY tipo_producao;

-- Log de execução
SELECT * FROM etl_logs ORDER BY iniciado_em DESC LIMIT 5;
```

---

## 7. Reprocessamento

Executar o pipeline sobre os mesmos arquivos é seguro. O UPSERT garante:

- Pesquisadores existentes são **atualizados** (sem duplicatas)
- Produções existentes têm `doi`, `resumo`, `qualis` e `jcr` preservados via `COALESCE` se já preenchidos
- Nenhum registro é duplicado graças à constraint `UNIQUE (pesquisador_id, titulo, ano_publicacao)`

---

## 8. Estrutura do diretório etl/

```
etl/
├── pipelines/
│   ├── lattes_pesquisadores.hpl   # Extrai e carrega pesquisadores
│   └── lattes_producoes.hpl       # Extrai e carrega produções (4 tipos)
├── workflows/
│   └── spark_etl.hwf              # Orquestra ambos os pipelines + log
├── metadata/
│   └── rdbms/
│       └── spark_db.json          # Template da conexão PostgreSQL
├── config/
│   └── spark-env.json             # Template de variáveis Hop
├── hop-config.json                # Configuração do projeto Hop
└── README.md
```

---

## 9. Tratamento de erros

- Arquivos XML com encoding inválido ou estrutura corrompida são redirecionados para o step `Log Erro Parse` (Error Handling do Hop) e registrados no log — o processamento dos demais arquivos continua normalmente.
- Produções sem `titulo` ou `ano_publicacao` são rejeitadas pela constraint NOT NULL do banco e registradas no log.
- O workflow registra `status='erro'` em `etl_logs` se qualquer pipeline falhar.

---

## 10. Notas de implementação (SPK-11)

- Pipeline implementado em **Apache Hop** conforme constitution.md — não reimplementar em Python ou shell
- Todo UPSERT usa `ON CONFLICT DO UPDATE` conforme obrigado pela constitution
- Credenciais via variáveis de ambiente — nunca hardcoded
- Encoding dos XMLs: `ISO-8859-1` (padrão CNPq)
- `COALESCE` preserva `doi`, `resumo`, `qualis`, `jcr` já enriquecidos em reprocessamentos
