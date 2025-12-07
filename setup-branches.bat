@echo off
REM BEACON - SIH Branch Setup Script (Windows)
REM This script creates round-1, round-2, and round-3 branches with proper feature flags

echo.
echo ========================================
echo BEACON - Setting up SIH branches...
echo ========================================
echo.

REM Get current branch
for /f "tokens=*" %%i in ('git branch --show-current') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%
echo.

REM Ask for confirmation
set /p CONFIRM="This will create round-1, round-2, and round-3 branches. Continue? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Aborted.
    exit /b
)

echo.
echo ========================================
echo Creating round-1 branch...
echo ========================================

git checkout -b round-1 2>nul || git checkout round-1

REM Update feature flag to Round 1
powershell -Command "(Get-Content frontend/src/config/featureFlags.js) -replace 'const CURRENT_ROUND = [0-9];', 'const CURRENT_ROUND = 1;' | Set-Content frontend/src/config/featureFlags.js"

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 1 - MVP with core features only (35-40%%)" 2>nul

echo [OK] Round 1 branch created
echo.

echo ========================================
echo Creating round-2 branch...
echo ========================================

git checkout -b round-2 2>nul || git checkout round-2

REM Update feature flag to Round 2
powershell -Command "(Get-Content frontend/src/config/featureFlags.js) -replace 'const CURRENT_ROUND = [0-9];', 'const CURRENT_ROUND = 2;' | Set-Content frontend/src/config/featureFlags.js"

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 2 - Enable workflows, approvals, multilingual (75-80%%)" 2>nul

echo [OK] Round 2 branch created
echo.

echo ========================================
echo Creating round-3 branch...
echo ========================================

git checkout -b round-3 2>nul || git checkout round-3

REM Update feature flag to Round 3
powershell -Command "(Get-Content frontend/src/config/featureFlags.js) -replace 'const CURRENT_ROUND = [0-9];', 'const CURRENT_ROUND = 3;' | Set-Content frontend/src/config/featureFlags.js"

git add frontend/src/config/featureFlags.js
git commit -m "feat: Round 3 - Production ready with all features (95-100%%)" 2>nul

echo [OK] Round 3 branch created
echo.

echo ========================================
echo All branches created successfully!
echo ========================================
echo.
echo Available branches:
git branch
echo.
echo Usage:
echo   Round 1 Demo: git checkout round-1
echo   Round 2 Demo: git checkout round-2
echo   Round 3 Demo: git checkout round-3
echo.
echo Note: Backend is identical across all branches
echo       Only frontend feature flags change
echo.
echo Read GIT_BRANCH_STRATEGY.txt for detailed instructions
echo.

REM Return to original branch
git checkout %CURRENT_BRANCH%
echo Returned to original branch: %CURRENT_BRANCH%
echo.
pause
