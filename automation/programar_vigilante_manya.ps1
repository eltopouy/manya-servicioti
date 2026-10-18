# -*- coding: utf-8 -*-
# Script PowerShell para registrar la tarea programada del Vigilante de Peñarol
# Ejecuta la evaluación periódica de partidos y prensa deportiva respetando el sistema anti-colisión

$taskName = "Manya_Vigilante_Partidos_Y_Prensa"

Write-Host "Configurando tarea programada: $taskName..." -ForegroundColor Cyan

# Eliminar si ya existe
Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue

$pythonExe = "$env:USERPROFILE\AppData\Local\Programs\Python\Python314\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = (Get-Command python.exe).Source
}

$scriptPath = "$env:USERPROFILE\.gemini\antigravity\scratch\manya_servicioti\automation\manya_partidos_daemon.py"
$workingDir = "$env:USERPROFILE\.gemini\antigravity\scratch\manya_servicioti"

# Acción: ejecuta un ciclo con --once
$action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$scriptPath`" --once" -WorkingDirectory $workingDir

# Disparador: Diariamente repetido cada 30 minutos entre las 11:00 y las 23:30 (cubriendo todas las previas, partidos y post-partidos)
$trigger = New-ScheduledTaskTrigger -Daily -At "11:00AM"
$trigger.Repetition = (New-ScheduledTaskTrigger -Once -At "11:00AM" -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Hours 13)).Repetition

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -WakeToRun `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 5) `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Monitoreo continuo de partidos de Peñarol, prensa deportiva y publicación automática en Blogger y GitHub Pages (Manya ServicioTI)" `
    -Force

Write-Host "¡Tarea programada registrada exitosamente para el Vigilante Manya ServicioTI!" -ForegroundColor Green
