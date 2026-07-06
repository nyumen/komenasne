@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ============================================================
echo  komenasne 定期記録タスクのセットアップ
echo  5分ごとにバックグラウンドで実行し、nasneで再生中の番組の
echo  実況コメントXMLを自動保存します（ウィンドウは表示されません）
echo ============================================================
echo.
echo   [1] タスクを登録する
echo   [2] タスクを解除する
echo.
set /p sel=番号を入力してください: 

if "%sel%"=="1" goto register
if "%sel%"=="2" goto unregister
echo 1 か 2 を入力してください。
pause
exit /b 1

:register
schtasks /create /tn "komenasne_silent" /sc minute /mo 5 /tr "wscript.exe \"%~dp0komenasne_silent.vbs\"" /f
if errorlevel 1 (
    echo タスクの登録に失敗しました。
) else (
    echo 登録しました。5分ごとに再生中の番組を記録します。
    echo 保存先: %~dp0kakolog\
)
pause
exit /b 0

:unregister
schtasks /delete /tn "komenasne_silent" /f
if errorlevel 1 (
    echo タスクが見つからないか、解除に失敗しました。
) else (
    echo タスクを解除しました。
)
pause
exit /b 0
