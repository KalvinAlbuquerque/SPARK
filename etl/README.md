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
$env:XML_DIR = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\xml"
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

## 4. Configurar conexao e registrar o projeto (setup unico)

Execute o script de setup **uma vez** — ele criptografa a senha, grava `spark_db.json` no formato correto do Hop 2.x e registra o projeto `spark` sem abrir a GUI.

| Sistema | Script | Uso |
|---------|--------|-----|
| Windows | `scripts/setup.ps1` | PowerShell |
| Linux/macOS | `scripts/setup.sh` | bash |

**Windows (PowerShell):**

```powershell
cd etl\
.\scripts\setup.ps1
```

Parametros opcionais:

```powershell
.\scripts\setup.ps1 -DbHost "localhost" -DbPort "5432" -DbName "spark" -DbUser "spark" `
                    -HopHome "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
```

**Linux/macOS (bash):**

```bash
cd etl/
chmod +x scripts/setup.sh
./scripts/setup.sh
```

Variaveis de ambiente opcionais:

```bash
HOP_HOME=/opt/apache-hop DB_HOST=localhost DB_PORT=5432 DB_NAME=spark DB_USER=spark \
  ./scripts/setup.sh
```

O script (em ambas as versoes) faz:
1. Pede a senha do PostgreSQL (entrada segura, nao aparece no terminal)
2. Criptografa a senha com `hop-encrypt` (bat ou sh)
3. Grava `etl/metadata/rdbms/spark_db.json` no formato aninhado do Hop 2.x
4. Registra o projeto `spark` via `hop-conf` (sem abrir o Hop GUI)

---

## 5. Executar o pipeline

### Via script (recomendado — sem GUI)

| Sistema | Script | Uso |
|---------|--------|-----|
| Windows | `scripts/run-etl.ps1` | PowerShell |
| Linux/macOS | `scripts/run-etl.sh` | bash |

**Windows (PowerShell):**

```powershell
cd etl\
.\scripts\run-etl.ps1

# Especificar outro diretorio de XMLs:
.\scripts\run-etl.ps1 -XmlDir "C:\outro\caminho\xmls"
```

**Linux/macOS (bash):**

```bash
cd etl/
chmod +x scripts/run-etl.sh
./scripts/run-etl.sh

# Especificar outro diretorio de XMLs:
./scripts/run-etl.sh /outro/caminho/xmls
# ou via variavel:
XML_DIR=/outro/caminho/xmls ./scripts/run-etl.sh
```

Ambos os scripts detectam automaticamente `data/xml/` do repositorio se nenhum diretorio for passado.

### Via hop-run diretamente

**Windows:**

```powershell
$HOP = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
$ETL = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\etl"
$XML = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\xml"

cmd /c """$HOP\hop-run.bat"" --project=spark --runconfig=local --file=""$ETL\workflows\spark_etl.hwf"" ""--parameters=XML_DIR=$XML"""
```

**Linux/macOS:**

```bash
"$HOP_HOME/hop-run.sh" --project=spark --runconfig=local \
  --file="$ETL_DIR/workflows/spark_etl.hwf" \
  "--parameters=XML_DIR=$XML_DIR"
```

### Via GUI do Apache Hop

1. Abra o Apache Hop GUI
2. Va em **File -> Open** e abra `workflows/spark_etl.hwf`
3. Configure o parametro `XML_DIR` no painel de parametros
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
│   └── lattes_producoes.hpl       # Extrai e carrega producoes (4 tipos)
├── workflows/
│   └── spark_etl.hwf              # Orquestra ambos os pipelines + log
├── metadata/
│   └── rdbms/
│       └── spark_db.json          # Conexao PostgreSQL (gerada pelo setup)
├── config/
│   └── spark-env.json             # Template de variaveis Hop (referencia)
├── scripts/
│   ├── setup.ps1                  # Setup unico — Windows (PowerShell)
│   ├── setup.sh                   # Setup unico — Linux/macOS (bash)
│   ├── run-etl.ps1                # Execucao do ETL — Windows (PowerShell)
│   └── run-etl.sh                 # Execucao do ETL — Linux/macOS (bash)
├── project-config.json            # Config do projeto no formato Hop 2.x
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
