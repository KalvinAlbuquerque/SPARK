param(
    [string]$HopHome  = "C:\Users\glend\Downloads\apache-hop-client-2.15.0\hop",
    [string]$DbHost   = "localhost",
    [string]$DbPort   = "5432",
    [string]$DbName   = "spark",
    [string]$DbUser   = "spark",
    [string]$DbPassword = ""
)

$ErrorActionPreference = "Stop"

$ETL_DIR = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "=== SPARK ETL - Setup ==================================================="
Write-Host "Hop:     $HopHome"
Write-Host "Projeto: $ETL_DIR"
Write-Host "Banco:   $DbUser@${DbHost}:${DbPort}/$DbName"
Write-Host "========================================================================="
Write-Host ""

# 1. Obter a senha: parametro > variavel de ambiente > prompt interativo
if (-not [string]::IsNullOrWhiteSpace($DbPassword)) {
    $plainPwd = $DbPassword
    Write-Host "Usando senha via parametro -DbPassword."
} elseif (-not [string]::IsNullOrWhiteSpace($env:POSTGRES_PASSWORD)) {
    $plainPwd = $env:POSTGRES_PASSWORD
    Write-Host "Usando senha de POSTGRES_PASSWORD."
} else {
    $securePwd = Read-Host "Senha do PostgreSQL ($DbUser)" -AsSecureString
    $BSTR      = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($securePwd)
    $plainPwd  = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
}

if ([string]::IsNullOrWhiteSpace($plainPwd)) {
    Write-Error "Senha nao pode estar vazia. Defina POSTGRES_PASSWORD ou use -DbPassword."
    exit 1
}

# 2. Criptografar a senha com hop-encrypt.bat
Write-Host "Criptografando senha..."
$encRaw = cmd /c """$HopHome\hop-encrypt.bat"" -hop ""$plainPwd""" 2>&1
$plainPwd = $null

$encPassword = ($encRaw | Where-Object { $_ -match "^Encrypted " } | Select-Object -Last 1)

if ([string]::IsNullOrWhiteSpace($encPassword)) {
    Write-Error "Falha ao criptografar a senha. Saida do hop-encrypt:`n$encRaw"
    exit 1
}

Write-Host "Senha criptografada com sucesso."

# 3. Escrever spark_db.json no formato correto do Hop 2.x
$metaDir = Join-Path $ETL_DIR "metadata\rdbms"
New-Item -ItemType Directory -Force $metaDir | Out-Null

$connJson = @"
{
  "virtualPath": "",
  "rdbms": {
    "POSTGRESQL": {
      "databaseName": "$DbName",
      "pluginId": "POSTGRESQL",
      "accessType": 0,
      "hostname": "$DbHost",
      "password": "$encPassword",
      "pluginName": "PostgreSQL",
      "port": "$DbPort",
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
      "username": "$DbUser"
    }
  },
  "name": "spark_db"
}
"@

$connPath = Join-Path $metaDir "spark_db.json"
[System.IO.File]::WriteAllText($connPath, $connJson, [System.Text.Encoding]::UTF8)
Write-Host "Conexao salva em: $connPath"

# 4. Registrar projeto 'spark' no Apache Hop via hop-conf.bat
Write-Host ""
Write-Host "Registrando projeto 'spark' no Hop..."
$regOutput = cmd /c """$HopHome\hop-conf.bat"" -p=spark -pc -ph=""$ETL_DIR"" -pf=project-config.json" 2>&1
Write-Host $regOutput

Write-Host ""
Write-Host "=== Setup concluido! ===================================================="
Write-Host "Agora execute:  .\scripts\run-etl.ps1"
Write-Host "========================================================================="
