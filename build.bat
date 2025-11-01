@echo off
echo Building Application environment...

REM Check if venv directory exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment. Make sure Python is installed and accessible.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip to latest version
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements if requirements.txt exists and is not empty
if exist "requirements.txt" (
    echo Installing requirements from requirements.txt...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Failed to install requirements.
        pause
        exit /b 1
    )
    echo Requirements installed successfully.
) else (
    echo requirements.txt not found, skipping package installation.
)

echo Build completed successfully!
echo Virtual environment is activated and ready to use.

REM Check if we're already in an activated virtual environment
if "%VIRTUAL_ENV%"=="" (
    echo.
    echo Starting new command prompt with activated virtual environment...
    echo Type 'exit' to close this window.
    echo.
    cmd /k
) else (
    echo.
    echo Virtual environment is already active in current session.
    echo You can continue working in this environment.
    pause
)
