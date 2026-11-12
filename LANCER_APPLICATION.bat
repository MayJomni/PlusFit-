@echo off
title PlusFit - Miroir de Reeducation
color 0A
echo.
echo  ============================================
echo   PlusFit - Miroir de Reeducation IA
echo  ============================================
echo.
echo  [1] Application GUI (fenetre avec camera)
echo  [2] Dashboard web (navigateur)
echo  [3] Mode demo (sans camera)
echo  [4] Tout lancer
echo.
set /p choix="Votre choix (1-4) : "

if "%choix%"=="1" goto GUI
if "%choix%"=="2" goto DASHBOARD
if "%choix%"=="3" goto DEMO
if "%choix%"=="4" goto TOUT

:GUI
echo Lancement de la GUI...
cd /d "%~dp0"
start "" .\venv\Scripts\python.exe launch_gui.py
goto FIN

:DASHBOARD
echo Lancement du Dashboard Streamlit...
cd /d "%~dp0"
start "" .\venv\Scripts\python.exe -m streamlit run dashboard/app.py
timeout /t 3
start "" http://localhost:8501
goto FIN

:DEMO
echo Lancement du mode demo...
cd /d "%~dp0"
.\venv\Scripts\python.exe run_demo.py
pause
goto FIN

:TOUT
echo Lancement de tout...
cd /d "%~dp0"
start "" .\venv\Scripts\python.exe launch_gui.py
start "" .\venv\Scripts\python.exe -m streamlit run dashboard/app.py
timeout /t 4
start "" http://localhost:8501
goto FIN

:FIN
echo.
echo  Applications lancees !
echo  Dashboard : http://localhost:8501
echo.
pause
