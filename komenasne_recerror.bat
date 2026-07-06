@echo off
chcp 65001 >nul
cd /d "%~dp0"

set /p keyword=検索する録画タイトルの一部を入力（空Enterで全件表示）: 
if "%keyword%"=="" (
    "%~dp0komenasne.exe" --recerror
) else (
    "%~dp0komenasne.exe" --recerror "%keyword%"
)

pause
