# ============================================================
# run-etl.ps1 — Executa o pipeline ETL SPARK via Apache Hop
# Pré-requisito: setup.ps1 já executado ao menos uma vez
# ============================================================

param(
    [string]$HopHome = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop",
    [string]$XmlDir  = ""   # se vazio, usa o valor do project-config.json
)

$ErrorActionPreference = "Stop"

$ETL_DIR   = Split-Path -Parent $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $ETL_DIR

# Diretório de XMLs: parâmetro > variável de ambiente > padrão do repositório
if ([string]::IsNullOrWhiteSpace($XmlDir)) {
    $XmlDir = if ($env:XML_DIR) { $env:XML_DIR } else { "$REPO_ROOT\data\xml" }
}

$WORKFLOW  = "$ETL_DIR\workflows\spark_etl.hwf"

Write-Host ""
Write-Host "=== SPARK ETL — Execução ================================================"
Write-Host "Hop:     $HopHome"
Write-Host "Projeto: $ETL_DIR"
Write-Host "XMLs:    $XmlDir"
Write-Host "========================================================================"
Write-Host ""

# Verificar pré-requisitos
if (-not (Test-Path "$ETL_DIR\metadata\rdbms\spark_db.json")) {
    Write-Error "Conexão não configurada. Execute setup.ps1 primeiro."
    exit 1
}
if (-not (Test-Path $XmlDir)) {
    Write-Error "Diretório de XMLs não encontrado: $XmlDir"
    exit 1
}

$xmlCount = (Get-ChildItem "$XmlDir\*.xml" -ErrorAction SilentlyContinue).Count
if ($xmlCount -eq 0) {
    Write-Warning "Nenhum arquivo .xml encontrado em: $XmlDir"
}
else {
    Write-Host "Arquivos XML encontrados: $xmlCount"
}

Write-Host ""
Write-Host "Iniciando workflow..."
Write-Host ""

# Executar o workflow via hop-run.bat
$startTime = Get-Date

cmd /c """$HopHome\hop-run.bat"" --project=spark --runconfig=local --file=""$WORKFLOW"" ""--parameters=XML_DIR=$XmlDir"""

$exitCode = $LASTEXITCODE
$duration = (Get-Date) - $startTime

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "=== ETL concluído com sucesso em $([int]$duration.TotalSeconds)s ============================"
}
else {
    Write-Host "=== ETL finalizado com erro (código $exitCode) ==============================="
    Write-Host "Verifique os logs acima e a tabela etl_logs no banco."
    exit $exitCode
}
