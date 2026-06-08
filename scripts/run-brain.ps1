<#
  run-brain.ps1 — drive The Camel "brain" in one command (Windows).

  One cycle = ingest free data -> run the Edge-gated paper tick -> publish state to the web -> run any
  queued web commands. Everything is PAPER. Nothing here flips a phase or moves real money.

  Usage:
    ./scripts/run-brain.ps1                       # one cycle, symbols/series from .env or defaults
    ./scripts/run-brain.ps1 -Loop -Interval 300   # repeat every 5 minutes (Ctrl+C to stop)
    ./scripts/run-brain.ps1 -NoIngest             # skip the data pull (use existing DB data)

  Reads a local .env (KEY=VALUE per line) if present, for:
    SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, CAMEL_FOUNDER_EMAIL, CAMEL_DB_DIR, CAMEL_SYMBOLS, FRED_API_KEY
  (Publishing/polling are skipped automatically if SUPABASE_* aren't set — the tick still runs locally.)
#>
param(
  [string]$Symbols = $env:CAMEL_SYMBOLS,
  [string]$Series  = "FEDFUNDS,DGS2,DGS10,VIXCLS,BAMLH0A0HYM2",
  [string]$Ciks    = "",
  [string]$DbDir   = $env:CAMEL_DB_DIR,
  [switch]$NoIngest,
  [switch]$Loop,
  [int]$Interval   = 300
)

$ErrorActionPreference = "Continue"
Set-Location (Split-Path $PSScriptRoot -Parent)   # repo root

# ---- load .env (simple KEY=VALUE) ----
if (Test-Path ".env") {
  Get-Content ".env" | ForEach-Object {
    if ($_ -match '^\s*([^#=\s]+)\s*=\s*(.*)\s*$') {
      [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
    }
  }
}
if (-not $Symbols) { $Symbols = "SPUS,HLAL" }
if (-not $DbDir)   { $DbDir = "." }
$env:CAMEL_DB_DIR = $DbDir
$env:CAMEL_SYMBOLS = $Symbols
$havePublish = $env:SUPABASE_URL -and $env:SUPABASE_SERVICE_ROLE_KEY

function Invoke-Cycle {
  Write-Host "`n=== Camel brain cycle @ $(Get-Date -Format 'u') ===" -ForegroundColor DarkCyan
  if (-not $NoIngest) {
    Write-Host "[1/4] ingest" -ForegroundColor DarkGray
    python -m data.ingest --symbols $Symbols --series $Series --ciks $Ciks
  }
  Write-Host "[2/4] paper tick (Edge-gated)" -ForegroundColor DarkGray
  python -m loop.jobs tick --symbols $Symbols
  if ($havePublish) {
    Write-Host "[3/4] publish state -> web" -ForegroundColor DarkGray
    python -m ops.publish_state
    Write-Host "[4/4] run queued web commands" -ForegroundColor DarkGray
    python -m ops.command_poller
  } else {
    Write-Host "[3-4] SUPABASE_* not set -> skipping publish/poll (local paper run only)" -ForegroundColor Yellow
  }
}

if ($Loop) {
  Write-Host "Looping every $Interval s. Ctrl+C to stop." -ForegroundColor Green
  while ($true) { Invoke-Cycle; Start-Sleep -Seconds $Interval }
} else {
  Invoke-Cycle
}
