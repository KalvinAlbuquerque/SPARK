#!/usr/bin/env bash
# run-etl.sh - Executa o pipeline ETL SPARK via Apache Hop (Linux/macOS)
# Pre-requisito: setup.sh ja executado ao menos uma vez
set -euo pipefail

HOP_HOME="${HOP_HOME:-/opt/apache-hop}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETL_DIR="$(dirname "$SCRIPT_DIR")"
REPO_ROOT="$(dirname "$ETL_DIR")"

XML_DIR="${XML_DIR:-$REPO_ROOT/data/xml}"

# Permite sobrescrever XML_DIR via argumento posicional
if [[ $# -ge 1 ]]; then
    XML_DIR="$1"
fi

WORKFLOW="$ETL_DIR/workflows/spark_etl.hwf"

echo ""
echo "=== SPARK ETL ==================================================="
echo "Hop:     $HOP_HOME"
echo "Projeto: $ETL_DIR"
echo "XMLs:    $XML_DIR"
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
    "--parameters=XML_DIR=$XML_DIR"

exit_code=$?
end_ts=$(date +%s)
duration=$(( end_ts - start_ts ))

echo ""
if [[ $exit_code -eq 0 ]]; then
    echo "=== ETL concluido com sucesso em ${duration}s ==========================="
else
    echo "=== ETL finalizado com erro (codigo $exit_code) =========================="
    echo "Verifique os logs acima e a tabela etl_logs no banco."
    exit $exit_code
fi
