@echo off
REM ���z�����쐬���邩�m�F
if not exist ".venv" (
    echo ���z�����쐬��...
    python -m venv .venv
)

REM ���z����L����
echo ���z����L�������Ă��܂�...
call .venv\Scripts\activate

REM ���W���[�����C���X�g�[��
if exist requirements.txt (
    echo ���W���[�����C���X�g�[����...
    pip install -r requirements.txt
) else (
    echo requirements.txt ��������܂���ł����B�������I�����܂��B
    exit /b 1
)

REM PyInstaller��EXE�t�@�C�����쐬
echo EXE�t�@�C�����쐬��...
pyinstaller komenasne.py --icon=komenasne.ico --onefile --clean

move dist\komenasne.exe ..\

REM ��������
echo �������������܂����B
pause

REM ���z���𖳌���
deactivate
