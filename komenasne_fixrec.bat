@echo off
setlocal enabledelayedexpansion

rem バッチファイルのディレクトリを取得
set "currentDir=%~dp0"

if "%~1"=="" (
    rem ファイルがドラッグされなかった場合の処理
    :input_filename
    set /p filename=XMLファイル名を入力してください（例: NHK総合_20240414_000946_30_レギュラー番組への道 最深日本研究～外国人博士の目～[字].xml）: 
) else (
    rem ドラッグされたファイルの名前を表示
    for %%i in (%*) do (
        set "file=%%~i"
        set "filename=%%~nxi"
        echo ドラッグされたファイル名: !filename!
    )
)

:input_minutes
set /p minutes=分を入力してください（例: 30）: 
rem 入力が数字であることを確認
set "isnum=1"
for /l %%i in (0,1,9) do (
    if "!minutes:~%%i,1!" geq "0" if "!minutes:~%%i,1!" leq "9" (
        rem 何もしない
    ) else (
        set "isnum=0"
    )
)

if "!isnum!"=="1" (
    goto run_command
) else (
    echo 数字を入力してください。
    goto input_minutes
)

:run_command
rem ドラッグ＆ドロップされたファイルを処理
if "%~1"=="" (
    rem ユーザーが入力したファイルを処理
    echo Running: "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
    "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
) else (
    rem ドラッグ＆ドロップされたファイルを処理
    for %%i in (%*) do (
        set "file=%%~i"
        set "filename=%%~nxi"
        echo Running: "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
        "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
    )
)

pause
endlocal
