@echo off
chcp 65001 > nul
echo ===========================================================================
echo  VIGILANTE DE PARTIDOS Y PRENSA MANYA - SERVICIOTI (1891)
echo ===========================================================================
cd /d "%~dp0\.."

if "%1"=="--daemon" (
    echo [*] Iniciando vigilante en modo servicio continuo (daemon)...
    python automation/manya_partidos_daemon.py --daemon
) else (
    echo [*] Ejecutando evaluacion inmediata de partidos y prensa deportiva...
    python automation/manya_partidos_daemon.py --once
)

echo ===========================================================================
echo  EJECUCION FINALIZADA
echo ===========================================================================
