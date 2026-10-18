@echo off
chcp 65001 > nul
echo ===========================================================================
echo  ACTUALIZADOR AUTOMATICO DIARIO - MANYA.SERVICIOTI.COM.UY (PEÑAROL)
echo ===========================================================================
cd /d "%~dp0\.."
python automation/actualizar_manya_completo.py
python automation/blogger_manya_publisher.py
python automation/desplegar_github_pages.py
echo ===========================================================================
echo  PROCESO COMPLETADO CON EXITO
echo ===========================================================================
