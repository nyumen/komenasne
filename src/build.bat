@echo off
REM 仮想環境を作成するか確認
if not exist ".venv" (
    echo 仮想環境を作成中...
    python -m venv .venv
)

REM 仮想環境を有効化
echo 仮想環境を有効化しています...
call .venv\Scripts\activate

REM モジュールをインストール
if exist requirements.txt (
    echo モジュールをインストール中...
    pip install -r requirements.txt
) else (
    echo requirements.txt が見つかりませんでした。処理を終了します。
    exit /b 1
)

REM PyInstallerでEXEファイルを作成
echo EXEファイルを作成中...
pyinstaller komenasne.py --icon=komenasne.ico --onefile --clean

move dist\komenasne.exe ..\

REM 処理完了
echo 処理が完了しました。
pause

REM 仮想環境を無効化
deactivate
