@echo off
REM =============================================================================
REM AcademicLint Build Script (Windows)
REM =============================================================================
REM Automated build, test, and deployment commands for Windows
REM
REM Usage:
REM   build.bat [command]
REM
REM Commands:
REM   install     - Install dependencies
REM   test        - Run tests
REM   lint        - Run linting
REM   build       - Build packages
REM   clean       - Clean artifacts
REM   ci          - Run full CI pipeline
REM   help        - Show help
REM =============================================================================

setlocal enabledelayedexpansion

set PACKAGE=academiclint
set SRC_DIR=src\%PACKAGE%
set TEST_DIR=tests

if "%1"=="" goto help
if "%1"=="help" goto help
if "%1"=="--help" goto help
if "%1"=="-h" goto help
if "%1"=="install" goto install
if "%1"=="test" goto test
if "%1"=="lint" goto lint
if "%1"=="format" goto format
if "%1"=="type-check" goto type_check
if "%1"=="security" goto security
if "%1"=="build" goto build
if "%1"=="clean" goto clean
if "%1"=="ci" goto ci
if "%1"=="release" goto release

echo [ERROR] Unknown command: %1
goto help

:install
echo [INFO] Installing dependencies...
if "%2"=="dev" (
    pip install -e ".[dev]"
    python -m spacy download en_core_web_sm
) else if "%2"=="all" (
    pip install -e ".[all]"
) else (
    pip install -e .
)
echo [SUCCESS] Installation complete!
goto end

:test
echo [INFO] Running tests...
if "%2"=="unit" (
    pytest %TEST_DIR% -v --ignore=%TEST_DIR%\test_integration_linter.py --ignore=%TEST_DIR%\test_integration_api.py --ignore=%TEST_DIR%\test_acceptance.py --ignore=%TEST_DIR%\test_performance.py --ignore=%TEST_DIR%\test_security.py
) else if "%2"=="integration" (
    pytest %TEST_DIR%\test_integration_*.py -v
) else if "%2"=="acceptance" (
    pytest %TEST_DIR%\test_acceptance.py -v
) else if "%2"=="performance" (
    pytest %TEST_DIR%\test_performance.py -v --timeout=300
) else if "%2"=="security" (
    pytest %TEST_DIR%\test_security.py -v
) else if "%2"=="coverage" (
    pytest %TEST_DIR% --cov=%SRC_DIR% --cov-report=term-missing --cov-report=html
) else (
    pytest %TEST_DIR% -v
)
echo [SUCCESS] Tests complete!
goto end

:lint
echo [INFO] Running linting...
if "%2"=="--fix" (
    ruff check %SRC_DIR% --fix
    ruff check %TEST_DIR% --fix
) else (
    ruff check %SRC_DIR%
    ruff check %TEST_DIR%
)
echo [SUCCESS] Linting complete!
goto end

:format
echo [INFO] Formatting code...
if "%2"=="--check" (
    ruff format --check %SRC_DIR%
    ruff format --check %TEST_DIR%
) else (
    ruff format %SRC_DIR%
    ruff format %TEST_DIR%
)
echo [SUCCESS] Formatting complete!
goto end

:type_check
echo [INFO] Running type checker...
mypy %SRC_DIR% --ignore-missing-imports
echo [SUCCESS] Type checking complete!
goto end

:security
echo [INFO] Running security scan...
bandit -r %SRC_DIR% -c pyproject.toml -q
echo [SUCCESS] Security scan complete!
goto end

:build
echo [INFO] Building packages...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
python -m build
echo [SUCCESS] Build complete! Packages in dist\
dir dist
goto end

:clean
echo [INFO] Cleaning artifacts...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
del /s /q *.pyc 2>nul
del /s /q *.pyo 2>nul
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q .pytest_cache 2>nul
rmdir /s /q htmlcov 2>nul
rmdir /s /q .mypy_cache 2>nul
rmdir /s /q .ruff_cache 2>nul
del /q .coverage 2>nul
echo [SUCCESS] Clean complete!
goto end

:ci
echo [INFO] Running CI pipeline...
echo [INFO] Step 1/5: Linting...
call :lint_step
if errorlevel 1 goto ci_fail
echo [INFO] Step 2/5: Format check...
call :format_check_step
if errorlevel 1 goto ci_fail
echo [INFO] Step 3/5: Type checking...
call :type_check_step
if errorlevel 1 goto ci_fail
echo [INFO] Step 4/5: Security scan...
call :security_step
if errorlevel 1 goto ci_fail
echo [INFO] Step 5/5: Running tests with coverage...
pytest %TEST_DIR% --cov=%SRC_DIR% --cov-report=term-missing
if errorlevel 1 goto ci_fail
echo [SUCCESS] CI pipeline complete!
goto end

:ci_fail
echo [ERROR] CI pipeline failed!
exit /b 1

:lint_step
ruff check %SRC_DIR%
ruff check %TEST_DIR%
exit /b %errorlevel%

:format_check_step
ruff format --check %SRC_DIR%
ruff format --check %TEST_DIR%
exit /b %errorlevel%

:type_check_step
mypy %SRC_DIR% --ignore-missing-imports
exit /b %errorlevel%

:security_step
bandit -r %SRC_DIR% -c pyproject.toml -q
exit /b %errorlevel%

:release
echo [INFO] Preparing release...
call :ci
if errorlevel 1 goto end
call :build
echo [SUCCESS] Release preparation complete!
echo [INFO] To publish, run: twine upload dist\*
goto end

:help
echo.
echo AcademicLint Build Script (Windows)
echo.
echo Usage: build.bat [command] [options]
echo.
echo Commands:
echo   install [dev^|all]     Install dependencies
echo   test [type]           Run tests (unit^|integration^|acceptance^|performance^|security^|coverage)
echo   lint [--fix]          Run linting
echo   format [--check]      Format code
echo   type-check            Run type checker
echo   security              Run security scan
echo   build                 Build packages
echo   clean                 Clean artifacts
echo   ci                    Run full CI pipeline
echo   release               Prepare release
echo   help                  Show this help
echo.
goto end

:end
endlocal
