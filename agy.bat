@echo off
if "%~1"=="gui" goto :run_python
if "%~1"=="uacc" goto :run_python
if "%~1"=="voice" goto :run_python
if "%~1"=="execute" goto :run_python

"C:\Users\kasiv\AppData\Local\agy\bin\agy_core.exe" %*
exit /b %errorlevel%

:run_python
python "C:\Users\kasiv\AppData\Local\agy\bin\agy_cli.py" %*
exit /b %errorlevel%
