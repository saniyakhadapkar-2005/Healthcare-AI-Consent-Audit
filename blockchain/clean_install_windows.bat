@echo off
setlocal
cd /d "%~dp0"
echo Removing old dependencies...
if exist node_modules rmdir /s /q node_modules
if exist package-lock.json del /f /q package-lock.json

echo Checking package.json...
node -e "const p=require('./package.json'); if(p.type){console.error('ERROR: Remove type=module from package.json before continuing.'); process.exit(1)}; console.log('OK')"
if errorlevel 1 exit /b 1

echo Installing Hardhat 2 dependencies...
npm install
if errorlevel 1 exit /b 1

echo.
echo Running compile...
npm run compile
if errorlevel 1 exit /b 1

echo.
echo DONE. Run: npm run node
endlocal
