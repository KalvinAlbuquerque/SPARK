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

## 4. Configurar conexão e registrar o projeto (setup único)

Execute `setup.ps1` **uma vez** — ele criptografa a senha, grava `spark_db.json` e registra o projeto `spark` no Apache Hop sem abrir a GUI:

```powershell
cd etl\
.\scripts\setup.ps1
```

O script vai:
1. Pedir a senha do PostgreSQL (entrada segura, não aparece no terminal)
2. Criptografar a senha com `hop-encrypt.bat`
3. Gravar `etl/metadata/rdbms/spark_db.json` no formato correto do Hop 2.x
4. Registrar o projeto `spark` via `hop-conf.bat` (atualiza o `hop-config.json` do Hop)

Parâmetros opcionais (caso o banco não seja o padrão):

```powershell
.\scripts\setup.ps1 -DbHost "localhost" -DbPort "5432" -DbName "spark" -DbUser "spark" `
                    -HopHome "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
```

---

## 5. Executar o pipeline

### Via script (recomendado — sem abrir GUI)

```powershell
cd etl\
.\scripts\run-etl.ps1
```

O script detecta automaticamente o diretório `data/xml/` do repositório. Para especificar outro diretório:

```powershell
.\scripts\run-etl.ps1 -XmlDir "C:\outro\caminho\xmls"
```

### Via hop-run.bat diretamente

```powershell
$HOP = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
$ETL = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\etl"
$XML = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\xml"

cmd /c """$HOP\hop-run.bat"" --project=spark --runconfig=local --file=""$ETL\workflows\spark_etl.hwf"" ""--parameters=XML_DIR=$XML"""
```

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
