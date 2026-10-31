# Script de registro en el Programador de Tareas de Windows
# Cumple con las reglas de resiliencia de Andrés (ServicioTI): -StartWhenAvailable, -WakeToRun
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$TaskName = "Manya_Madrugada_0005_Hoy_Juega"
$PythonPath = "C:\Users\Andrés\AppData\Local\Programs\Python\Python314\python.exe"
$ScriptPath = "C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti\automation\manya_partidos_daemon.py"
$WorkingDir = "C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti"

Write-Output "Configurando Tarea Programada: $TaskName..."

# 1. Crear Trigger diario a las 00:05 hs (5 minutos después de medianoche)
$Trigger = New-ScheduledTaskTrigger -Daily -At "00:05"

# 2. Definir Acción
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`" --once" -WorkingDirectory $WorkingDir

# 3. Configurar Opciones de Resiliencia (-StartWhenAvailable, -WakeToRun)
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

# 4. Registrar la tarea (sobrescribir si existe)
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description "Manya ServicioTI: Edicion Especial 'Hoy Juega el Manya' disparada a las 00:05 hs de cada dia de partido." -Force | Out-Null
    Write-Output "OK: Tarea '$TaskName' registrada exitosamente para ejecutarse todos los dias a las 00:05 hs."
} catch {
    Write-Warning "Aviso registrando la tarea: $_"
}
