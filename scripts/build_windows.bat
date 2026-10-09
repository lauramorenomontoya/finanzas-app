@echo off
REM ===================================================
REM Compilación de Montu para Windows
REM ===================================================
REM Cambiar al directorio raíz del proyecto
cd /d "%~dp0\.."
echo =============================================
echo        Compilando Montu para Windows         
echo =============================================

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no está instalado o no se encuentra en el PATH.
    pause
    exit /b 1
)

REM Instalar dependencias
echo Instalando dependencias necesarias...
pip install -r requirements.txt
pip install pyinstaller pyarmor

REM Limpiar builds previos
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Ofuscar código fuente con PyArmor
echo Ofuscando código fuente con PyArmor...
pyarmor gen -O build\obf -r main.py controllers core database services ui

REM Compilar con PyInstaller
echo Empaquetando aplicación ejecutable (.exe)...
pyinstaller montu.spec --noconfirm --clean

REM Comprimir carpeta de distribución en ZIP
echo Generando archivo ZIP para compartir...
powershell -Command "Compress-Archive -Path 'dist\montu' -DestinationPath 'dist\Montu_Windows.zip' -Force"

echo =============================================
echo [OK] ¡Compilación completada exitosamente!
echo Archivo listo para compartir:
echo dist\Montu_Windows.zip
echo =============================================
pause
