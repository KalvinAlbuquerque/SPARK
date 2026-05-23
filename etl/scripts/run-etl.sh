#!/usr/bin/env bash
# run-etl.sh - Executa o pipeline ETL SPARK via Apache Hop (Linux/macOS)
# Pre-requisito: setup.sh ja executado ao menos uma vez
set -euo pipefail

HOP_HOME="${HOP_HOME:-/opt/apache-hop}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETL_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$ETL_DIR")"

# Carrega .env da raiz do repositório (não sobrescreve vars já exportadas no terminal)
ENV_FILE="$REPO_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r k v; do
        [[ "$k" =~ ^[[:space:]]*# ]] && continue
        k="${k// /}"
        [[ -z "$k" ]] && continue
        [[ -z "${!k+x}" ]] && export "$k=$v"
    done < "$ENV_FILE"
fi

XML_DIR="${XML_DIR:-$REPO_ROOT/data/xml}"
QUALIS_CSV="${QUALIS_CSV:-$REPO_ROOT/data/qualis/qualis_capes.csv}"
ETL_EMAIL="${ETL_EMAIL:-}"
OPENALEX_APIKEY="${OPENALEX_APIKEY:-}"

# Permite sobrescrever via argumentos posicionais: $1=XML_DIR, $2=QUALIS_CSV
if [[ $# -ge 1 ]]; then
    XML_DIR="$1"
fi
if [[ $# -ge 2 ]]; then
    QUALIS_CSV="$2"
fi

WORKFLOW="$ETL_DIR/workflows/spark_etl.hwf"

echo ""
echo "=== SPARK ETL ==================================================="
echo "Hop:       $HOP_HOME"
echo "Projeto:   $ETL_DIR"
echo "XMLs:      $XML_DIR"
echo "Qualis:    $QUALIS_CSV"
echo "ETL Email: $ETL_EMAIL"
echo "OpenAlex:  $([ -n "$OPENALEX_APIKEY" ] && echo '(configurado)' || echo '(nao configurado)')"
echo "================================================================="
echo ""

if [[ ! -f "$ETL_DIR/metadata/rdbms/spark_db.json" ]]; then
    echo "ERRO: Conexao nao configurada. Execute setup.sh primeiro." >&2
    exit 1
fi

if [[ ! -d "$XML_DIR" ]]; then
    echo "ERRO: Diretorio de XMLs nao encontrado: $XML_DIR" >&2
    exit 1
fi

if [[ ! -f "$QUALIS_CSV" ]]; then
    echo "ERRO: Arquivo Qualis nao encontrado: $QUALIS_CSV. Obtenha a planilha da Plataforma Sucupira e coloque em data/qualis/qualis_capes.csv ou passe o caminho como segundo argumento." >&2
    exit 1
fi

xml_count=$(find "$XML_DIR" -maxdepth 1 -name "*.xml" | wc -l)
echo "Arquivos XML encontrados: $xml_count"
echo ""
echo "Iniciando workflow..."
echo ""

start_ts=$(date +%s)

"$HOP_HOME/hop-run.sh" \
    --project=spark \
    --runconfig=local \
    --file="$WORKFLOW" \
    "--parameters=XML_DIR=$XML_DIR,QUALIS_CSV=$QUALIS_CSV,ETL_EMAIL=$ETL_EMAIL,OPENALEX_APIKEY=$OPENALEX_APIKEY"

exit_code=$?
end_ts=$(date +%s)
duration=$(( end_ts - start_ts ))

echo ""
if [[ $exit_code -eq 0 ]]; then
    echo "=== ETL concluido em ${duration}s ==========================="
else
    echo "=== ETL finalizado com erro (codigo $exit_code) =========================="
    echo "Verifique os logs acima e a tabela etl_logs no banco."
    exit $exit_code
fi
