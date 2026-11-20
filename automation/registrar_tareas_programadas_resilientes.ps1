# -*- coding: utf-8 -*-
<#
.SYNOPSIS
Registrador de Tareas Programadas de Alta Resiliencia para Manya ServicioTI (v10.0).
Configura la ejecución automática 24/7 sin fallos de codificación por el carácter 'é'
y con horarios escalonados para evitar colisiones con GitHub Actions.

.DESCRIPTION
Crea y actualiza 3 tareas en el Programador de Tareas de Windows con -StartWhenAvailable y -WakeToRun:
1. Manya_Vigilante_Partidos_Y_Prensa (Cada 30 min, inicio 06:15):
   Orquestador principal (manya_partidos_daemon.py --once -> sync_manya_hub.py) con hash semántico
   anti-spam y sincronización conflict-free hacia GitHub Pages.
2. Manya_Guardian_Autocorreccion (Cada 60 min, inicio 06:40):
   Guardián de auto-curación (manya_self_healing_watchdog.py): limpia locks huérfanos, ejecuta las
   12 pruebas dinámicas (test_manya_ecosystem.py) y auto-repara automáticamente si detecta desvíos.
3. Manya_Madrugada_0005_Hoy_Juega (Diario a las 00:05 hs UY):
   Activa la edición especial '¡Hoy Juega el Manya!' únicamente cuando Peñarol tiene partido oficial
   ese día calendario en Uruguay (UTC-3).
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== REGISTRANDO TAREAS PROGRAMADAS RESILIENTES DE MANYA SERVICIOTI v10.0 ===" -ForegroundColor Yellow

$pythonCmd = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
if (-not $pythonCmd) {
    $pythonCmd = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"
}

$repoDir = "$env:USERPROFILE\.gemini\antigravity\scratch\manya_servicioti"
$automationDir = "$repoDir\automation"

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType Interactive `
    -RunLevel Limited

# Tarea 1: Manya_Vigilante_Partidos_Y_Prensa (Cada 30 min desde las 06:15)
$action1 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "`"$automationDir\manya_partidos_daemon.py`" --once" -WorkingDirectory $repoDir
$trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6).AddMinutes(15) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "Manya_Vigilante_Partidos_Y_Prensa" -Action $action1 -Trigger $trigger1 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Vigilante_Partidos_Y_Prensa (Cada 30 min, 06:15, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

# Tarea 2: Manya_Guardian_Autocorreccion (Cada 60 min desde las 06:40 — escalonado)
$action2 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "`"$automationDir\manya_self_healing_watchdog.py`"" -WorkingDirectory $repoDir
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6).AddMinutes(40) -RepetitionInterval (New-TimeSpan -Minutes 60) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "Manya_Guardian_Autocorreccion" -Action $action2 -Trigger $trigger2 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Guardian_Autocorreccion (Cada 60 min, 06:40, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

# Tarea 3: Manya_Madrugada_0005_Hoy_Juega (Diario a las 00:05 hs UY)
$action3 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "`"$automationDir\manya_partidos_daemon.py`" --hoy-juega" -WorkingDirectory $repoDir
$trigger3 = New-ScheduledTaskTrigger -Daily -At "00:05:00"
Register-ScheduledTask -TaskName "Manya_Madrugada_0005_Hoy_Juega" -Action $action3 -Trigger $trigger3 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Madrugada_0005_Hoy_Juega (Diario 00:05 hs, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

Write-Host "=== TODAS LAS TAREAS PROGRAMADAS v10.0 QUEDARON ACTIVAS Y RESILIENTES ===" -ForegroundColor Yellow
