@echo off
REM Builds McCoyTrucking.exe (one file, double-click to run). Needs Python 3.11+ and Node.js on this PC, one time only.
cd /d "%~dp0\.."
cd frontend
call npx --yes yarn install || exit /b 1
set REACT_APP_BACKEND_URL=
call npx --yes yarn build || exit /b 1
cd ..\backend
python -m pip install -r requirements-desktop.txt pyinstaller || exit /b 1
python -m PyInstaller --noconfirm --onefile --windowed --name McCoyTrucking ^
  --add-data "..\frontend\build;frontend_build" ^
  --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on ^
  desktop.py || exit /b 1
echo.
echo Done! Your program is at backend\dist\McCoyTrucking.exe
pause
