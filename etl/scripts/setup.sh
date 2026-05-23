#!/usr/bin/env bash
# setup.sh - Configuracao unica do projeto SPARK no Apache Hop (Linux/macOS)
# Execute uma vez antes do primeiro run-etl.sh
set -euo pipefail

HOP_HOME="${HOP_HOME:-/opt/apache-hop}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-spark}"
DB_USER="${DB_USER:-spark}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETL_DIR="$(dirname "$SCRIPT_DIR")"

echo ""
echo "=== SPARK ETL - Setup ==================================================="
echo "Hop:     $HOP_HOME"
echo "Projeto: $ETL_DIR"
echo "Banco:   $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
echo "========================================================================="
echo ""

# 1. Solicitar senha do banco
read -rsp "Senha do PostgreSQL ($DB_USER): " PLAIN_PWD
echo ""

if [[ -z "$PLAIN_PWD" ]]; then
    echo "ERRO: Senha nao pode estar vazia." >&2
    exit 1
fi

# 2. Criptografar a senha com hop-encrypt.sh
echo "Criptografando senha..."
ENC_RAW=$("$HOP_HOME/hop-encrypt.sh" -hop "$PLAIN_PWD" 2>&1)
PLAIN_PWD=""   # limpar da memoria

ENC_PASSWORD=$(echo "$ENC_RAW" | grep "^Encrypted " | tail -1)

if [[ -z "$ENC_PASSWORD" ]]; then
    echo "ERRO: Falha ao criptografar a senha. Saida do hop-encrypt:" >&2
    echo "$ENC_RAW" >&2
    exit 1
fi

echo "Senha criptografada com sucesso."

# 3. Escrever spark_db.json no formato correto do Hop 2.x
META_DIR="$ETL_DIR/metadata/rdbms"
mkdir -p "$META_DIR"

cat > "$META_DIR/spark_db.json" <<EOF
{
  "virtualPath": "",
  "rdbms": {
    "POSTGRESQL": {
      "databaseName": "$DB_NAME",
      "pluginId": "POSTGRESQL",
      "accessType": 0,
      "hostname": "$DB_HOST",
      "password": "$ENC_PASSWORD",
      "pluginName": "PostgreSQL",
      "port": "$DB_PORT",
      "attributes": {
        "SUPPORTS_TIMESTAMP_DATA_TYPE": "Y",
        "QUOTE_ALL_FIELDS": "N",
        "SUPPORTS_BOOLEAN_DATA_TYPE": "Y",
        "FORCE_IDENTIFIERS_TO_LOWERCASE": "N",
        "PRESERVE_RESERVED_WORD_CASE": "Y",
        "SQL_CONNECT": "",
        "FORCE_IDENTIFIERS_TO_UPPERCASE": "N",
        "PREFERRED_SCHEMA_NAME": "public"
      },
      "manualUrl": "",
      "username": "$DB_USER"
    }
  },
  "name": "spark_db"
}
EOF

echo "Conexao salva em: $META_DIR/spark_db.json"

# 4. Registrar projeto 'spark' no Apache Hop via hop-conf.sh
echo ""
echo "Registrando projeto 'spark' no Hop..."
"$HOP_HOME/hop-conf.sh" -p=spark -pc -ph="$ETL_DIR" -pf=project-config.json

echo ""
echo "=== Setup concluido! ===================================================="
echo "Agora execute:  ./scripts/run-etl.sh"
echo "========================================================================="
