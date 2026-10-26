@echo off
setlocal
cd /d "%~dp0"
echo.
echo === Checking package.json ===
node -e "const p=require('./package.json'); if(p.type){console.error('ERROR: package.json still contains type='+p.type); process.exit(1)}; console.log('OK: no type=module')"
if errorlevel 1 goto :fail

echo.
echo === Checking Hardhat version ===
npx hardhat --version
if errorlevel 1 goto :fail

echo.
echo === Compiling ===
npm run compile
if errorlevel 1 goto :fail

echo.
echo SUCCESS: Hardhat setup is working.
goto :end
:fail
echo.
echo FAILED. If this is an old extracted folder, delete it and extract this ZIP again.
exit /b 1
:end
endlocal
