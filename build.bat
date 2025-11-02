@echo off
echo Building TextToSpeech environment...

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
call venv\Scripts\activate
if errorlevel 1 (
    echo Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Upgrade pip to latest version
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install package in editable mode from pyproject.toml
if exist "pyproject.toml" (
    echo Installing package and dependencies from pyproject.toml...
    pip install -e .
    if errorlevel 1 (
        echo Failed to install package and dependencies.
        pause
        exit /b 1
    )
    echo Package and dependencies installed successfully.
) else (
    echo pyproject.toml not found! Cannot install dependencies.
    pause
    exit /b 1
)

REM Install optional development dependencies
echo.
set /p INSTALL_DEV="Install development dependencies? (y/n): "
if /i "%INSTALL_DEV%"=="y" (
    echo Installing development dependencies...
    pip install -e ".[dev]"
    if errorlevel 1 (
        echo Warning: Failed to install development dependencies.
    ) else (
        echo Development dependencies installed successfully.
    )
)

echo.
echo Build completed successfully!
echo Virtual environment is activated and ready to use.
echo.
echo You can now run:
echo   - tts --help           (Main TTS CLI)
echo   - phonetics --help     (Phonetics management CLI)

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
