@echo off
setlocal EnableExtensions EnableDelayedExpansion


REM Find Conda installation root
for /f "delims=" %%A in ('conda info --base 2^>nul') do set "CONDA_ROOT=%%A"

if not defined CONDA_ROOT (
    echo ERROR: Could not determine Conda root directory.
    pause
    exit /b 1
)

echo Conda root - %CONDA_ROOT%


cd /d "%~dp0"
set ENV_NAME=tool-launcher


echo -------------------------------
echo Generic Tool Launcher - Setup
echo -------------------------------
echo.

REM ------------------
REM Initialize Conda
REM ------------------

echo Initializing Conda...

call "%CONDA_ROOT%\Scripts\activate.bat"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to initialize Conda.
    echo.
    pause
    exit /b 1
)

echo Conda initialized.
echo.


REM ------------
REM Check Conda
REM ------------

echo Conda version:
call conda --version

if errorlevel 1 (
    echo.
    echo ERROR: Conda is not working.
    echo.
    pause
    exit /b 1
)

echo.


REM ----------------------------------
REM Check if Conda environment exists
REM ----------------------------------

echo Checking for Conda environment "%ENV_NAME%"...

call conda env list | findstr /I /R /C:"^[^#].*%ENV_NAME%" >nul

if %ERRORLEVEL% EQU 0 (
	echo Environment already exists.
) else (
	echo Environment does not exist.
	echo Creating environment "%ENV_NAME%"...

	call conda create -n %ENV_NAME% python=3.13 -y

	if %ERRORLEVEL% NEQ 0 (
		echo.
		echo ERROR: Failed to create Conda environment.
		exit /b 1
	)
)

echo.

REM ---------------------------
REM Upgrade pip
REM ---------------------------

echo Upgrading pip...

call conda run --no-capture-output -n %ENV_NAME% python -m pip install --upgrade pip

if %ERRORLEVEL% NEQ 0 (
	echo.
	echo ERROR: Failed to upgrade pip.
	exit /b 1
)

echo.

REM ---------------------------
REM Install dependencies
REM ---------------------------

echo Installing Python dependencies...

call conda run --no-capture-output -n %ENV_NAME% python -m pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
	echo.
	echo ERROR: Failed to install Python dependencies.
	exit /b 1
)

echo.


REM ---------------------------
REM Verify PySide6
REM ---------------------------

echo --------------------------------
echo Checking PySide6 installation
echo --------------------------------
echo.

echo Checking QtCore...

call conda run --no-capture-output -n %ENV_NAME% python -c "from PySide6 import QtCore; print('QtCore OK - version:', QtCore.__version__)"

if %ERRORLEVEL% NEQ 0 (
	echo.
	echo ERROR: PySide6 QtCore test failed.
	echo.
	pause
	exit /b 1
)

echo.

echo Checking QtWidgets...

call conda run --no-capture-output -n %ENV_NAME% python -c "from PySide6 import QtWidgets; print('QtWidgets OK')"

if %ERRORLEVEL% NEQ 0 (
	echo.
	echo ERROR: PySide6 QtWidgets test failed.
	echo.
	pause
	exit /b 1
)

echo.


REM -----------------------------
REM Test application import
REM -----------------------------

echo -------------------------
echo Testing application
echo -------------------------
echo.

call conda run --no-capture-output -n "%ENV_NAME%" python -c "import app.main; print('Application import OK')"

if %ERRORLEVEL% NEQ 0 (
	echo.
	echo ERROR: Could not import app.main
	echo.
	pause
	exit /b 1
)

echo.

echo Testing Qt platform...
call conda run --no-capture-output -n %ENV_NAME% python -c "from PySide6.QtWidgets import QApplication; import sys; app=QApplication(sys.argv); print('QApplication OK'); print('Platform:', app.platformName()); app.quit()"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: QApplication initialization failed.
    pause
    exit /b 1
)


REM -------------------
REM Start GUI
REM -------------------

echo ---------------------
echo All checks passed!
echo ---------------------
echo.
echo Starting Generic Tool Launcher...
echo.

echo Running:
call conda run --no-capture-output -n %ENV_NAME% python -m app.main

set GUI_EXIT_CODE=%ERRORLEVEL%


echo.
echo ------------------
echo GUI exited
echo ------------------
echo.
echo Exit code: %GUI_EXIT_CODE%
echo.

if not %GUI_EXIT_CODE% EQU 0 (
	echo.
	echo ERROR: GUI exited with an error.
	echo.
	pause
)


endlocal
exit /b %GUI_EXIT_CODE%


