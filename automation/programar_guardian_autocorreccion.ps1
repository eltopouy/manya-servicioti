# Programador de Tareas de Windows para el Guardián de Auto-Corrección y Salud Manya ServicioTI
# Cumple con las reglas de resiliencia de Andrés (ServicioTI): -StartWhenAvailable, -WakeToRun
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$TaskName = "Manya_Guardian_Autocorreccion"
$PythonPath = "C:\Users\Andrés\AppData\Local\Programs\Python\Python314\python.exe"
$ScriptPath = "C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti\automation\manya_self_healing_watchdog.py"
$WorkingDir = "C:\Users\Andrés\.gemini\antigravity\scratch\manya_servicioti"

Write-Output "Configurando Tarea Programada: $TaskName..."

# Trigger: Repetición continua cada 30 minutos
$Trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).ToString("HH:mm") -RepetitionInterval (New-TimeSpan -Minutes 30)

# Definir Acción
$Action = New-ScheduledTaskAction -Execute $PythonPath -Argument "`"$ScriptPath`"" -WorkingDirectory $WorkingDir

# Configurar Opciones de Resiliencia
$Settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Minutes 15)

# Registrar la tarea
try {
    Register-ScheduledTask -TaskName $TaskName -Trigger $Trigger -Action $Action -Settings $Settings -Description "Guardián de Auto-Corrección Continua: ejecuta pruebas y auto-repara inconsistencias del ecosistema Manya ServicioTI cada 30 min." -Force | Out-Null
    Write-Output "OK: Tarea '$TaskName' registrada exitosamente para ejecutarse cada 30 minutos."
} catch {
    Write-Warning "Aviso registrando la tarea: $_"
}
