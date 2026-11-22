@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
  echo Python launcher not found. Install Python 3.11+.
  pause
  exit /b 1
)
py -m venv .venv || goto :error
.venv\Scripts\python.exe -m pip install --upgrade pip || goto :error
.venv\Scripts\python.exe -m pip install -r requirements.txt pyinstaller || goto :error
.venv\Scripts\python.exe -m unittest discover -s tests -v || goto :error
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --windowed --onedir --name CrashFlightPro --collect-all PySide6 --collect-all PySide6_Addons main.py || goto :error
echo.
echo Build complete: dist\CrashFlightPro\CrashFlightPro.exe
pause
exit /b 0
:error
echo Build failed. Review errors above.
pause
exit /b 1
