<#
  register-tasks.ps1 - register The Camel's scheduled jobs with Windows Task Scheduler (S16).

  FOUNDER-RUN, ONCE, from an ELEVATED PowerShell (Task Scheduler registration needs admin).
  This is deliberately not agent-automatable: putting the Camel on a clock is the founder's act.

  Registers two tasks (paper-only; nothing here can flip a phase or move real money):
    Camel Brain Daily    - one governed cycle (ingest -> Edge-gated paper tick -> publish -> poll)
                           every weekday at -DailyAt (default 23:45, after US close in Riyadh time).
    Camel Weekly Safety  - kill-switch self-test + backup + reconcile, Sundays at -WeeklyAt.

  Usage:
    powershell -ExecutionPolicy Bypass -File scripts\register-tasks.ps1
    ... -DailyAt 23:45 -WeeklyAt 10:00      # override times (local clock)
    ... -Unregister                          # remove both tasks
#>
param(
  [string]$DailyAt = "23:45",
  [string]$WeeklyAt = "10:00",
  [switch]$Unregister
)

$ErrorActionPreference = "Stop"
$repo = Split-Path $PSScriptRoot -Parent
$daily = "Camel Brain Daily"
$weekly = "Camel Weekly Safety"

if ($Unregister) {
  foreach ($name in @($daily, $weekly)) {
    try { Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction Stop
          Write-Host "removed: $name" } catch { Write-Host "not present: $name" }
  }
  return
}

$ps = (Get-Command powershell.exe).Source

# Daily brain cycle (weekdays) - runs scripts\run-brain.ps1, which reads .env and skips publish/poll
# gracefully when SUPABASE_* are absent. WorkingDirectory = repo root so relative DBs resolve.
$dailyAction = New-ScheduledTaskAction -Execute $ps `
  -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\run-brain.ps1`"" `
  -WorkingDirectory $repo
$dailyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At $DailyAt
Register-ScheduledTask -TaskName $daily -Action $dailyAction -Trigger $dailyTrigger `
  -Description "The Camel - governed daily paper cycle (ingest, Edge-gated tick, publish, poll). Paper-only." `
  -Force | Out-Null
Write-Host "registered: $daily (weekdays $DailyAt)"

# Weekly safety routine (Sundays) - kill-switch self-test + backup + reconcile.
$weeklyAction = New-ScheduledTaskAction -Execute $ps `
  -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"Set-Location '$repo'; python -m loop.jobs weekly`"" `
  -WorkingDirectory $repo
$weeklyTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $WeeklyAt
Register-ScheduledTask -TaskName $weekly -Action $weeklyAction -Trigger $weeklyTrigger `
  -Description "The Camel - weekly safety: kill-switch self-test, verified backup, ledger reconcile." `
  -Force | Out-Null
Write-Host "registered: $weekly (Sundays $WeeklyAt)"

Write-Host ""
Write-Host "Both tasks registered. Verify in Task Scheduler, or run one now:"
Write-Host "  Start-ScheduledTask -TaskName '$daily'"
