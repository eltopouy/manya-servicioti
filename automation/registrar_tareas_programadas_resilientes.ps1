# -*- coding: utf-8 -*-
<#
.SYNOPSIS
Registrador de Tareas Programadas de Alta Resiliencia para Manya ServicioTI.
Configura la ejecución automática 24/7 sin fallos de codificación por el carácter 'é'.

.DESCRIPTION
Crea y actualiza 3 tareas en el Programador de Tareas de Windows:
1. Manya_Guardian_Autocorreccion (Cada 30 minutos):
   Supervisa salud del portal, aplica la regla de las 48 hs para transicionar de POST_PARTIDO a PREVIA,
   verifica los 66 puntos de la Tabla Anual, corre tests y hace push a GitHub Pages.
2. Manya_Madrugada_0005_Hoy_Juega (Diario a las 00:05 hs UY):
   Apenas inicia el día de partido, activa la edición especial '¡Hoy Juega el Manya!' con clima y accesos.
3. Manya_Vigilante_Partidos_Y_Prensa (Cada 30 minutos):
   Monitorea noticias de prensa deportiva y actualiza el match center.
#>

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=== REGISTRANDO TAREAS PROGRAMADAS RESILIENTES DE MANYA SERVICIOTI ===" -ForegroundColor Yellow

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

# Tarea 1: Manya_Guardian_Autocorreccion
$action1 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "$automationDir\manya_self_healing_watchdog.py" -WorkingDirectory $repoDir
$trigger1 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "Manya_Guardian_Autocorreccion" -Action $action1 -Trigger $trigger1 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Guardian_Autocorreccion (Cada 30 min, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

# Tarea 2: Manya_Madrugada_0005_Hoy_Juega
$action2 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "$automationDir\manya_partidos_daemon.py --hoy-juega" -WorkingDirectory $repoDir
$trigger2 = New-ScheduledTaskTrigger -Daily -At "00:05:00"
Register-ScheduledTask -TaskName "Manya_Madrugada_0005_Hoy_Juega" -Action $action2 -Trigger $trigger2 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Madrugada_0005_Hoy_Juega (Diario 00:05 hs, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

# Tarea 3: Manya_Vigilante_Partidos_Y_Prensa
$action3 = New-ScheduledTaskAction -Execute $pythonCmd -Argument "$automationDir\manya_partidos_daemon.py --once" -WorkingDirectory $repoDir
$trigger3 = New-ScheduledTaskTrigger -Once -At (Get-Date).Date.AddHours(6).AddMinutes(15) -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
Register-ScheduledTask -TaskName "Manya_Vigilante_Partidos_Y_Prensa" -Action $action3 -Trigger $trigger3 -Settings $settings -Principal $principal -Force | Out-Null
Write-Host "✓ Registrada: Manya_Vigilante_Partidos_Y_Prensa (Cada 30 min, StartWhenAvailable, WakeToRun)" -ForegroundColor Green

Write-Host "=== TODAS LAS TAREAS PROGRAMADAS QUEDARON ACTIVAS Y RESILIENTES ===" -ForegroundColor Yellow
