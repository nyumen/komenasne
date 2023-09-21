rmdir /s /q exe
del komenasne.exe
mkdir exe
cd exe
pipenv --rm
pipenv --python 3.10.5
pipenv shell
REM ↓続きはこっからコピペ
copy ..\requirements.txt .
pipenv install -r requirements.txt
pip install pyinstaller
copy ..\komenasne.py .
copy ..\komenasne.ico .
pyinstaller komenasne.py --icon=komenasne.ico --onefile --clean
move dist\komenasne.exe ..\
pipenv --rm
pause
