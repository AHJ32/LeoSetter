@echo off
setlocal enabledelayedexpansion
REM Build LeoSetter MVP executable for Windows using PyInstaller
REM Usage: scripts\build_mvp_windows.bat [--onefile]

set HERE=%~dp0..
cd /d "%HERE%"

if not exist venv (
  echo [i] Creating virtualenv at venv
  py -3 -m venv venv
)

call venv\Scripts\python -m pip install --upgrade pip setuptools wheel >nul
call venv\Scripts\pip install pyinstaller >nul

set NAME=leosetter
set ENTRY=run_mvp.py

REM Data paths on Windows use src;dest with semicolon
set ADD1=mvp\templates\templates.json;mvp\templates
REM Bundle Windows exiftool.exe into tools/ inside the app
set ADD2=mvp\tools\exiftool.exe;tools

set FLAGS=--name %NAME% --noconsole --clean --add-data "%ADD1%" --add-binary "%ADD2%"

if "%1"=="--onefile" (
  set FLAGS=%FLAGS% --onefile
)

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM If --onefile requested, always build from scratch to honor the flag
if "%1"=="--onefile" (
  echo [i] Building ONEFILE from scratch with explicit flags
  call venv\Scripts\pyinstaller %FLAGS% %ENTRY%
) else (
  REM Use spec file if it exists, otherwise build from scratch
  if exist leosetter.spec (
    echo [i] Using existing leosetter.spec file
    call venv\Scripts\pyinstaller leosetter.spec
  ) else (
    echo [i] No leosetter.spec found, building from scratch
    call venv\Scripts\pyinstaller %FLAGS% %ENTRY%
  )
)

echo [✓] Build complete. See dist\%NAME%\ (or dist\%NAME%.exe when --onefile).
endlocal
