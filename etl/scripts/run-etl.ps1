param(
    [string]$HopHome   = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop",
    [string]$XmlDir    = "",
    [string]$QualisCSV = ""
)

$ErrorActionPreference = "Stop"

$ETL_DIR   = Split-Path -Parent $PSScriptRoot
$REPO_ROOT = Split-Path -Parent $ETL_DIR

# Carrega .env da raiz do repositório (não sobrescreve vars já exportadas no terminal)
$envFile = Join-Path $REPO_ROOT ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | Where-Object { $_ -notmatch '^\s*#' -and $_ -match '=' } | ForEach-Object {
        $kv = $_ -split '=', 2
        $k  = $kv[0].Trim()
        $v  = if ($kv.Length -gt 1) { $kv[1].Trim() } else { "" }
        if ($k -and -not (Get-Item "env:$k" -ErrorAction SilentlyContinue)) {
            Set-Item "env:$k" $v
        }
    }
}

if ([string]::IsNullOrWhiteSpace($XmlDir)) {
    $XmlDir = if ($env:XML_DIR) { $env:XML_DIR } else { "$REPO_ROOT\data\xml" }
}

if ([string]::IsNullOrWhiteSpace($QualisCSV)) {
    $QualisCSV = if ($env:QUALIS_CSV) { $env:QUALIS_CSV } else { "$REPO_ROOT\data\qualis\qualis_capes.csv" }
}

$EtlEmail    = if ($env:ETL_EMAIL)       { $env:ETL_EMAIL }       else { "" }
$OpenAlexKey = if ($env:OPENALEX_APIKEY) { $env:OPENALEX_APIKEY } else { "" }

$WORKFLOW = "$ETL_DIR\workflows\spark_etl.hwf"

Write-Host ""
Write-Host "=== SPARK ETL ==================================================="
Write-Host "Hop:       $HopHome"
Write-Host "Projeto:   $ETL_DIR"
Write-Host "XMLs:      $XmlDir"
Write-Host "Qualis:    $QualisCSV"
Write-Host "ETL Email: $EtlEmail"
Write-Host "OpenAlex:  $(if ($OpenAlexKey) { '(configurado)' } else { '(nao configurado)' })"
Write-Host "================================================================="
Write-Host ""

if (-not (Test-Path "$ETL_DIR\metadata\rdbms\spark_db.json")) {
    Write-Error "Conexao nao configurada. Execute setup.ps1 primeiro."
    exit 1
}

if (-not (Test-Path $XmlDir)) {
    Write-Error "Diretorio de XMLs nao encontrado: $XmlDir"
    exit 1
}

if (-not (Test-Path $QualisCSV)) {
    Write-Error "Arquivo Qualis nao encontrado: $QualisCSV. Obtenha a planilha da Plataforma Sucupira e coloque em data\qualis\qualis_capes.csv ou passe -QualisCSV <caminho>."
    exit 1
}

$xmlCount = (Get-ChildItem "$XmlDir\*.xml" -ErrorAction SilentlyContinue).Count
Write-Host "Arquivos XML encontrados: $xmlCount"
Write-Host ""
Write-Host "Iniciando workflow..."
Write-Host ""

$startTime = Get-Date

# Usa o truststore do Windows para que o JVM do Hop confie em certificados modernos (Let's Encrypt, etc.)
$env:_JAVA_OPTIONS = "-Djavax.net.ssl.trustStoreType=Windows-ROOT -Djavax.net.ssl.trustStoreProvider=SunMSCAPI"

cmd /c """$HopHome\hop-run.bat"" --project=spark --runconfig=local --file=""$WORKFLOW"" ""--parameters=XML_DIR=$XmlDir,QUALIS_CSV=$QualisCSV,ETL_EMAIL=$EtlEmail,OPENALEX_APIKEY=$OpenAlexKey"""

$exitCode  = $LASTEXITCODE
$duration  = [int]((Get-Date) - $startTime).TotalSeconds

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "=== ETL concluido em ${duration}s ==========================="
} else {
    Write-Host "=== ETL finalizado com erro (codigo $exitCode) =========================="
    Write-Host "Verifique os logs acima e a tabela etl_logs no banco."
    exit $exitCode
}
