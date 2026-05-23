# ETL — Pipeline Lattes SPARK

Pipeline Apache Hop que extrai dados dos currículos Lattes (XML), carrega nas tabelas `pesquisadores` e `producoes` do banco PostgreSQL, e enriquece o campo `qualis` via planilha Qualis CAPES.

---

## Pré-requisitos

| Requisito               | Versão mínima | Versão validada |
| ----------------------- | ------------- | --------------- |
| Java (JDK)              | 11            | 21.0.9          |
| Apache Hop              | 2.x           | 2.15.0          |
| Docker + Docker Compose | qualquer      | Docker 27.x     |
| PostgreSQL              | 15            | 15 (pgvector/pgvector:pg15) |
| PostgreSQL driver JDBC  | incluído no Hop | — |

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
docker exec spark-db-1 psql -U spark -d spark -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```

---

## 2. Configurar variáveis de ambiente

As credenciais do banco são passadas ao script `setup.ps1`/`setup.sh` que as criptografa internamente — **não é necessário exportar variáveis para o Hop manualmente**. Basta definir `POSTGRES_PASSWORD` antes de rodar o setup (veja seção 4).

Se quiser exportar manualmente (ex: testes ou uso da GUI do Hop):

**Windows (PowerShell):**

```powershell
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
$env:POSTGRES_DB   = "spark"
$env:POSTGRES_USER = "spark"
$env:POSTGRES_PASSWORD = "sua_senha"
$env:XML_DIR = "C:\caminho\para\data\xml"
```

**Linux/macOS (bash):**

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=spark
export POSTGRES_USER=spark
export POSTGRES_PASSWORD=sua_senha
export XML_DIR=/caminho/absoluto/para/data/xml
```

### Via GUI do Apache Hop (persiste entre sessões)

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

### 3.4 Obter a planilha Qualis CAPES (para enriquecimento SPK-12)

O campo `qualis` é preenchido a partir da planilha oficial da Plataforma Sucupira. Não existe API — o download é manual:

1. Acesse [https://sucupira.capes.gov.br/sucupira/](https://sucupira.capes.gov.br/sucupira/)
2. Vá em **Coleta Capes → Qualis → Consultar Classificação de Periódicos**
3. Selecione o quadriênio desejado (referência: **2017–2020**) e exporte a planilha
4. Converta o arquivo XLSX para CSV com cabeçalho: `ISSN,Titulo,Area,Estrato`
5. Salve como `data/qualis/qualis_capes.csv` (UTF-8)

O repositório já contém o arquivo `data/qualis/qualis_capes.csv` gerado a partir do quadriênio 2017–2020 (154.518 linhas, 31.350 ISSNs únicos). Para usar outro quadriênio, substitua o arquivo ou passe o caminho via parâmetro `QUALIS_CSV`.

---

## 4. Configurar conexao e registrar o projeto (setup unico)

Execute o script de setup **uma vez** — ele criptografa a senha, grava `spark_db.json` no formato correto do Hop 2.x e registra o projeto `spark` sem abrir a GUI.

| Sistema | Script | Uso |
|---------|--------|-----|
| Windows | `scripts/setup.ps1` | PowerShell |
| Linux/macOS | `scripts/setup.sh` | bash |

### Modo automatico (sem prompt)

Defina `POSTGRES_PASSWORD` antes de executar — o script usa a variavel e nao pede nada interativamente:

**Windows (PowerShell):**

```powershell
$env:POSTGRES_PASSWORD = "changeme"
cd etl\
.\scripts\setup.ps1
```

Ou via parametro direto:

```powershell
cd etl\
.\scripts\setup.ps1 -DbPassword "changeme"
```

**Linux/macOS (bash):**

```bash
cd etl/
chmod +x scripts/setup.sh
POSTGRES_PASSWORD=changeme ./scripts/setup.sh
```

### Modo interativo

Se `POSTGRES_PASSWORD` nao estiver definida (e `-DbPassword` nao for passado), o script pede a senha no terminal com entrada segura (nao aparece na tela).

### Parametros/variaveis opcionais

**Windows:**

```powershell
.\scripts\setup.ps1 -DbHost "localhost" -DbPort "5432" -DbName "spark" -DbUser "spark" `
                    -HopHome "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
```

**Linux/macOS:**

```bash
HOP_HOME=/opt/apache-hop DB_HOST=localhost DB_PORT=5432 DB_NAME=spark DB_USER=spark \
  POSTGRES_PASSWORD=changeme ./scripts/setup.sh
```

O script (em ambas as versoes) faz:
1. Obtem a senha via variavel de ambiente, parametro ou prompt interativo
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

# Especificar outro diretorio de XMLs ou outra planilha Qualis:
.\scripts\run-etl.ps1 -XmlDir "C:\outro\caminho\xmls"
.\scripts\run-etl.ps1 -QualisCSV "C:\outro\caminho\qualis_capes.csv"

# Ambos ao mesmo tempo:
.\scripts\run-etl.ps1 -XmlDir "C:\outro\caminho\xmls" -QualisCSV "C:\outro\caminho\qualis_capes.csv"
```

**Linux/macOS (bash):**

```bash
cd etl/
chmod +x scripts/run-etl.sh
./scripts/run-etl.sh

# Especificar outro diretorio de XMLs ou outra planilha Qualis:
./scripts/run-etl.sh /outro/caminho/xmls
./scripts/run-etl.sh /outro/caminho/xmls /outro/caminho/qualis_capes.csv
# ou via variaveis:
XML_DIR=/outro/caminho/xmls QUALIS_CSV=/outro/caminho/qualis.csv ./scripts/run-etl.sh
```

Os scripts detectam automaticamente `data/xml/` e `data/qualis/qualis_capes.csv` se nenhum caminho for passado.

### Via hop-run diretamente

**Windows:**

```powershell
$HOP    = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop"
$ETL    = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\etl"
$XML    = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\xml"
$QUALIS = "C:\Users\glend\Desktop\UNEB\TOPICOS\Repositorio\SPARK\data\qualis\qualis_capes.csv"

cmd /c """$HOP\hop-run.bat"" --project=spark --runconfig=local --file=""$ETL\workflows\spark_etl.hwf"" ""--parameters=XML_DIR=$XML,QUALIS_CSV=$QUALIS"""
```

**Linux/macOS:**

```bash
"$HOP_HOME/hop-run.sh" --project=spark --runconfig=local \
  --file="$ETL_DIR/workflows/spark_etl.hwf" \
  "--parameters=XML_DIR=$XML_DIR,QUALIS_CSV=$QUALIS_CSV"
```

### Via GUI do Apache Hop

1. Abra o Apache Hop GUI
2. Va em **File -> Open** e abra `workflows/spark_etl.hwf`
3. Configure o parametro `XML_DIR` no painel de parametros
4. Clique em **Run (F9)**

---

## 6. Verificar resultado

```powershell
# Conectar no banco via Docker:
docker exec spark-db-1 psql -U spark -d spark -c "SELECT lattes_id, nome_completo, departamento, campus FROM pesquisadores;"
```

```sql
-- Pesquisadores carregados
SELECT lattes_id, nome_completo, departamento, campus FROM pesquisadores;

-- Total de producoes por tipo
SELECT tipo_producao, COUNT(*) FROM producoes GROUP BY tipo_producao;

-- Distribuicao Qualis dos artigos
SELECT qualis, COUNT(*) FROM producoes
WHERE tipo_producao = 'ARTIGO' AND qualis IS NOT NULL
GROUP BY qualis ORDER BY qualis;

-- Taxa de match Qualis
SELECT
  COUNT(*) FILTER (WHERE tipo_producao = 'ARTIGO') AS total_artigos,
  COUNT(*) FILTER (WHERE tipo_producao = 'ARTIGO' AND qualis IS NOT NULL) AS com_qualis,
  ROUND(COUNT(*) FILTER (WHERE tipo_producao = 'ARTIGO' AND qualis IS NOT NULL)::numeric /
        NULLIF(COUNT(*) FILTER (WHERE tipo_producao = 'ARTIGO'), 0) * 100, 1) AS taxa_pct
FROM producoes;

-- Log de execucao
SELECT id, iniciado_em, finalizado_em, status, detalhes->>'arquivos_processados' as arquivos
FROM etl_logs ORDER BY iniciado_em DESC LIMIT 5;
```

**Resultado esperado com os 8 XMLs de `data/xml/`:**

| Tipo | Qtd |
|------|-----|
| ARTIGO | 247 |
| EVENTO | 161 |
| CAPITULO | 40 |
| LIVRO | 14 |
| **Total** | **462** |

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
│   ├── lattes_pesquisadores.hpl     # Extrai e carrega pesquisadores (SPK-11)
│   ├── lattes_producoes.hpl         # Extrai e carrega producoes - 4 tipos (SPK-11)
│   └── qualis_enriquecimento.hpl    # Enriquece qualis via planilha CAPES (SPK-12)
├── workflows/
│   └── spark_etl.hwf                # Orquestra os 3 pipelines + log
├── metadata/
│   └── rdbms/
│       └── spark_db.json            # Conexao PostgreSQL (gerada pelo setup)
├── config/
│   └── spark-env.json               # Template de variaveis Hop (referencia)
├── scripts/
│   ├── setup.ps1                    # Setup unico — Windows (PowerShell)
│   ├── setup.sh                     # Setup unico — Linux/macOS (bash)
│   ├── run-etl.ps1                  # Execucao do ETL — Windows (PowerShell)
│   └── run-etl.sh                   # Execucao do ETL — Linux/macOS (bash)
├── docs/
│   └── upsert_proof_of_work.md      # Prova de idempotencia do UPSERT
├── project-config.json              # Config do projeto no formato Hop 2.x
└── README.md
```

---

## 9. Tratamento de erros

- Arquivos XML com encoding inválido ou estrutura corrompida são redirecionados para o step `Log Erro Parse` (Error Handling do Hop) e registrados no log — o processamento dos demais arquivos continua normalmente.
- Produções sem `titulo` ou `ano_publicacao` são rejeitadas pela constraint NOT NULL do banco e registradas no log.
- O workflow registra `status='erro'` em `etl_logs` se qualquer pipeline falhar.

> **Nota sobre o `Log Erro Parse`:** No Hop 2.x com `distribute=N` (modo cópia), o step de log de erros recebe uma cópia de todas as linhas, mesmo sem falhas reais. Isso é comportamento interno do Hop e não indica problema nos dados — verifique o step `UPSERT Pesquisadores` (deve mostrar `R=8, W=8` para 8 XMLs) e a tabela `etl_logs` (deve mostrar `status='sucesso'`) para confirmar que o pipeline funcionou corretamente.

---

## 10. O que o ETL extrai dos XMLs Lattes

### Pesquisadores

| Campo no banco | Fonte no XML |
|----------------|-------------|
| `lattes_id` | `CURRICULO-VITAE/@NUMERO-IDENTIFICADOR` |
| `nome_completo` | `DADOS-GERAIS/@NOME-COMPLETO` |
| `departamento` | `DADOS-GERAIS/@DEPARTAMENTO` (adicionado manualmente — ver seção 3.2) |
| `campus` | `DADOS-GERAIS/@CAMPUS` (adicionado manualmente — ver seção 3.2) |
| `resumo` | `DADOS-GERAIS/RESUMO-CV/@TEXTO-RESUMO-CV-RH` |

Campos **não preenchidos pelo ETL** (calculados em sprint futura): `total_producoes`, `indice_h`, `total_a1_a2`.

### Produções

| Campo no banco | Fonte no XML |
|----------------|-------------|
| `titulo` | `TITULO-DO-ARTIGO` / `TITULO-DO-TRABALHO` / `TITULO-DO-LIVRO` / `TITULO-DO-CAPITULO-DO-LIVRO` |
| `tipo_producao` | Constante por fluxo: `ARTIGO`, `EVENTO`, `LIVRO`, `CAPITULO` |
| `ano_publicacao` | `ANO-DO-ARTIGO` / `ANO-DO-TRABALHO` / `ANO` |
| `nome_veiculo` | Nome do periódico, evento ou livro pai |
| `issn` | `@ISSN` (quando disponível) |
| `doi` | `@DOI` (quando disponível) |
| `texto_busca` | Preenchido automaticamente por trigger do banco |

Campo `qualis` é preenchido pelo pipeline `qualis_enriquecimento.hpl` (SPK-12). Campos **não preenchidos**: `resumo` das produções (campo `RESUMO-DA-PRODUCAO` não extraído), `jcr` (enriquecimento via OpenAlex — SPK-14).

---

## 11. Notas de implementação

### SPK-11 (lattes_pesquisadores + lattes_producoes)

- Pipeline implementado em **Apache Hop 2.15.0** conforme constitution.md — não reimplementar em Python ou shell
- Todo UPSERT usa `ON CONFLICT DO UPDATE` conforme obrigado pela constitution
- Credenciais via variáveis de ambiente — nunca hardcoded
- Encoding dos XMLs: `ISO-8859-1` (padrão CNPq) — lido automaticamente pelo Hop via declaração no cabeçalho XML
- `COALESCE` preserva `doi`, `resumo`, `qualis`, `jcr` já enriquecidos em reprocessamentos

### SPK-12 (qualis_enriquecimento)

- Lookup por ISSN com fallback por nome do periódico (`nome_veiculo`)
- Melhor estrato por ISSN via `SortRows` (ISSN asc, Estrato asc) + `UniqueRows` — a ordenação alfabética dos estratos (A1 < A2 < … < C) coincide com a ordem de qualidade decrescente, tornando desnecessária a conversão numérica
- Taxa de correspondência validada: **93.1% dos 247 artigos** (acima do critério mínimo de 70%)
- UPSERT via `UPDATE … SET qualis = COALESCE(?, qualis)` — não sobrescreve valor já preenchido quando não há nova correspondência
- Artigos sem correspondência logados via `WriteToLog` sem interromper o processamento
