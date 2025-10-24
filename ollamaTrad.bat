@echo off
REM OllamaTrad Launcher Script for Windows
REM Version: 3.0

title OllamaTrad v3.0 Launcher

REM Définir les couleurs (optionnel, nécessite Windows 10+)
color 0B

REM Afficher le logo
echo.
echo ===============================================
echo.
echo           OllamaTrad v3.0
echo    Intelligent JSON Translation System
echo.
echo ===============================================
echo.

REM Vérifier Python
echo [*] Verification de Python...
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [X] Python n'est pas installe ou pas dans le PATH!
    echo.
    echo Installation requise:
    echo 1. Telecharger Python depuis: https://www.python.org/downloads/windows/
    echo 2. IMPORTANT: Cocher "Add Python to PATH" pendant l'installation
    echo 3. Installer Python 3.9 ou superieur
    echo.
    pause
    exit /b 1
)

REM Obtenir la version de Python
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python trouve: %PYTHON_VERSION%

REM Vérifier tkinter
echo [*] Verification de tkinter...
python -c "import tkinter" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] tkinter n'est pas disponible!
    echo.
    echo Reinstallez Python en cochant l'option "tcl/tk and IDLE"
    echo.
    pause
    exit /b 1
)
echo [OK] tkinter est disponible

REM Vérifier les dépendances Python
echo [*] Verification des dependances...

set MISSING_DEPS=

python -c "import json5" 2>nul
if %ERRORLEVEL% NEQ 0 set MISSING_DEPS=%MISSING_DEPS% json5

python -c "import requests" 2>nul
if %ERRORLEVEL% NEQ 0 set MISSING_DEPS=%MISSING_DEPS% requests

python -c "import aiohttp" 2>nul
if %ERRORLEVEL% NEQ 0 set MISSING_DEPS=%MISSING_DEPS% aiohttp

if not "%MISSING_DEPS%"=="" (
    echo [*] Installation des dependances manquantes: %MISSING_DEPS%
    python -m pip install --user %MISSING_DEPS%

    if %ERRORLEVEL% NEQ 0 (
        echo [X] Erreur lors de l'installation des dependances
        echo.
        echo Essayez manuellement:
        echo    python -m pip install json5 requests aiohttp
        echo.
        pause
        exit /b 1
    )

    echo [OK] Dependances installees avec succes
) else (
    echo [OK] Toutes les dependances sont installees
)

REM Se placer dans le répertoire du script
cd /d "%~dp0"

REM Lancer l'application
echo.
echo [*] Lancement d'OllamaTrad...
echo.

python ollamaTrad.py --gui %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] L'application s'est terminee avec une erreur
    echo.
    echo Consultez les messages d'erreur ci-dessus
    echo.
    pause
    exit /b %ERRORLEVEL%
)

exit /b 0
