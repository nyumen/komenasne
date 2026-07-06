@echo off
rem Local build script (output: dist\komenasne\)
cd /d "%~dp0.."

if not exist ".venv" (
    echo Creating venv...
    python -m venv .venv
)

call .venv\Scripts\activate

echo Installing dependencies...
pip install .
pip install pyinstaller

echo Building (onedir)...
pyinstaller src\komenasne.py --name komenasne --paths src --icon src\komenasne.ico --clean --noconfirm

echo Done: dist\komenasne\
pause
deactivate
