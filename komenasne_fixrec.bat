@echo off
setlocal enabledelayedexpansion

rem �o�b�`�t�@�C���̃f�B���N�g�����擾
set "currentDir=%~dp0"

if "%~1"=="" (
    rem �t�@�C�����h���b�O����Ȃ������ꍇ�̏���
    :input_filename
    set /p filename=XML�t�@�C��������͂��Ă��������i��: NHK����_20240414_000946_30_���M�����[�ԑg�ւ̓� �Ő[���{�����`�O���l���m�̖ځ`[��].xml�j: 
) else (
    rem �h���b�O���ꂽ�t�@�C���̖��O��\��
    for %%i in (%*) do (
        set "file=%%~i"
        set "filename=%%~nxi"
        echo �h���b�O���ꂽ�t�@�C����: !filename!
    )
)

:input_minutes
set /p minutes=������͂��Ă��������i��: 30�j: 
rem ���͂������ł��邱�Ƃ��m�F
set "isnum=1"
for /l %%i in (0,1,9) do (
    if "!minutes:~%%i,1!" geq "0" if "!minutes:~%%i,1!" leq "9" (
        rem �������Ȃ�
    ) else (
        set "isnum=0"
    )
)

if "!isnum!"=="1" (
    goto run_command
) else (
    echo ��������͂��Ă��������B
    goto input_minutes
)

:run_command
rem �h���b�O���h���b�v���ꂽ�t�@�C��������
if "%~1"=="" (
    rem ���[�U�[�����͂����t�@�C��������
    echo Running: "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
    "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
) else (
    rem �h���b�O���h���b�v���ꂽ�t�@�C��������
    for %%i in (%*) do (
        set "file=%%~i"
        set "filename=%%~nxi"
        echo Running: "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
        "%currentDir%komenasne.exe" --fixrec !minutes! "!filename!"
    )
)

pause
endlocal
