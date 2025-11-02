---
applyTo: '/**'
---

# TextToSpeech - Installation and Build Instructions

This document provides guidance for setting up, building, and running the TextToSpeech application. This system converts text, Markdown, and PowerPoint presentations to speech using Azure or ElevenLabs TTS services.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Project Architecture](#project-architecture)
3. [Quick Start](#quick-start)
4. [Build Scripts](#build-scripts)
5. [Development Workflow](#development-workflow)
6. [Configuration](#configuration)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Tools

1. **Python Environment**
   - Python 3.10+ 
   - pip (comes with Python)

2. **TTS Service Credentials**
   - **Azure**: Speech Service API key and region
   - **ElevenLabs**: API key (optional, if using ElevenLabs)

### Platform Support

- **Primary Platform**: Windows
- **Development Shell**: PowerShell or Command Prompt

## Project Architecture

The project follows a hybrid architecture:

```
igt-procedure-intelligence/
├── Frontend (TypeScript/React)    # Web UI components
│   ├── src/                      # React application source
│   ├── public/                   # Static assets
│   └── package.json              # Node.js dependencies
├── Backend (Rust + Python)       # Core application logic
│   ├── src-tauri/               # Tauri configuration and Rust code
│   │   ├── python/              # Python backend modules
│   │   ├── Cargo.toml           # Rust dependencies

## Project Architecture

```
TextToSpeech/
├── src/texttospeech/          # Main package
│   ├── cli/                   # Command-line interfaces
│   │   ├── tts_cli.py        # Main TTS tool
│   │   └── phonetics_cli.py  # Phonetic management
│   ├── tts/                   # TTS backend implementations
│   │   ├── azure.py          # Azure Speech Service
│   │   └── elevenlabs.py     # ElevenLabs API
│   ├── processing/            # Document processing
│   │   ├── markdown_parser.py
│   │   └── ppt_processor.py
│   └── phonetics/             # Phonetic processing
│       ├── manager.py         # Phonetic lookup
│       └── processing.py      # SSML generation
├── config/
│   ├── config.sample.yaml    # Template configuration
│   └── config.yaml           # Your settings (gitignored)
├── data/
│   ├── phonetic_lookup.json  # Shared pronunciations
│   └── phonetic_lookup.personal.json  # Your pronunciations (gitignored)
├── examples/                  # Sample files
│   ├── sample.md
│   ├── sample.pptx
│   └── output/               # Generated audio (gitignored)
└── build.bat                 # Setup script
```

### Technology Stack

- **Backend**: Python 3.10+
- **TTS Services**: Azure Speech Service, ElevenLabs API
- **Document Processing**: python-pptx, markdown parsing
- **Phonetic Processing**: SSML, IPA notation

## Quick Start

### First-Time Setup

```powershell
# 1. Clone the repository (if not already done)
git clone <repository-url>
cd TextToSpeech

# 2. Run build script (creates venv and installs dependencies)
.\build.bat

# 3. Activate the virtual environment
.\.venv\Scripts\activate

# 4. Copy and configure settings
copy config\config.sample.yaml config\config.yaml
# Edit config\config.yaml with your Azure/ElevenLabs credentials

# 5. Test the installation
python -m texttospeech.cli.tts_cli --help
```

### Manual Setup

If you prefer step-by-step installation:

```powershell
# 1. Create virtual environment
python -m venv .venv

# 2. Activate virtual environment
.\.venv\Scripts\activate

# 3. Install base dependencies
pip install -r requirements.txt

# 4. Install phonetic features (optional)
pip install -r requirements_phonetic.txt

# 5. Configure
copy config\config.sample.yaml config\config.yaml
```

## Build Scripts

### `build.bat` - Setup and Install

**When to use**: First setup, after pulling changes, or when dependencies change

**What it does**:
- Creates Python virtual environment (if missing)
- Activates the environment
- Installs all dependencies from requirements.txt
- Installs optional phonetic dependencies from requirements_phonetic.txt

**Process flow**:
```batch
1. Check/create .venv directory
2. Create virtual environment
3. Activate environment
4. Install base requirements
5. Install phonetic requirements (if present)
```

## Development Workflow

### Environment Activation

**Always activate before running commands:**

```powershell
# PowerShell/Command Prompt
.\.venv\Scripts\activate

# You should see (.venv) in your prompt
```

### Daily Development

```powershell
# 1. Activate environment
.\.venv\Scripts\activate

# 2. Run commands (examples below)
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help

# 3. After pulling new changes
pip install -r requirements.txt
pip install -r requirements_phonetic.txt
```

### Common Tasks

**List available voices:**
```powershell
python -m texttospeech.cli.tts_cli --voices
python -m texttospeech.cli.tts_cli --voices-short  # Condensed view
```

**Convert Markdown to speech:**
```powershell
python -m texttospeech.cli.tts_cli --md examples\sample.md --output-dir examples\output
```

**Convert PowerPoint to speech:**
```powershell
python -m texttospeech.cli.tts_cli --ppt examples\sample.pptx --output-dir examples\output
```

**Manage phonetic pronunciations:**
```powershell
python -m texttospeech.cli.phonetics_cli --interactive
python -m texttospeech.cli.phonetics_cli --list
python -m texttospeech.cli.phonetics_cli --coach tomato
```

## Configuration

### Configuration File

Edit `config/config.yaml` with your credentials:

```yaml
azure:
  api_key: "YOUR_AZURE_KEY"
  region: "eastus"

elevenlabs:
  api_key: "YOUR_ELEVENLABS_KEY"

default_voice: "en-US-JennyNeural"
output_format: "mp3"
```

### Environment Variables

Alternatively, use environment variables:

```powershell
# Azure credentials
$env:AZURE_SPEECH_KEY = "your-key"
$env:AZURE_SPEECH_REGION = "eastus"

# ElevenLabs credentials
$env:ELEVENLABS_API_KEY = "your-key"
```

### Phonetic Lookup Files

Two lookup files for custom pronunciations:

1. **Shared (tracked)**: `data/phonetic_lookup.json`
   - Team-shared pronunciations
   - Committed to repository

2. **Personal (gitignored)**: `data/phonetic_lookup.personal.json`
   - Your personal pronunciations
   - Overrides shared entries
   - Not committed

The system automatically merges both files, with personal entries taking precedence.

## Troubleshooting

### Common Issues

**Issue: "Module not found" errors**
```powershell
# Solution: Ensure environment is activated and dependencies installed
.\.venv\Scripts\activate
pip install -r requirements.txt
```

**Issue: "Invalid API key" or credential errors**
```powershell
# Solution: Check config/config.yaml or environment variables
# Verify credentials are correct for your service
```

**Issue: Audio generation fails**
```powershell
# Solution: Check output directory exists and is writable
mkdir examples\output
```

**Issue: PowerPoint processing fails**
```powershell
# Solution: Ensure PowerPoint file is not open in another program
# Check file permissions
```

### Debug Mode

Enable verbose logging:

```powershell
# Set environment variable for detailed output
$env:TEXTTOSPEECH_DEBUG = "true"
python -m texttospeech.cli.tts_cli --md examples\sample.md
```

### Dependency Issues

If you encounter package conflicts:

```powershell
# Remove and recreate virtual environment
deactivate
rmdir /s .venv
.\build.bat
```

## Essential Commands Reference

```powershell
# Setup
.\build.bat                                    # First-time setup
.\.venv\Scripts\activate                      # Activate environment

# TTS Operations
python -m texttospeech.cli.tts_cli --voices   # List voices
python -m texttospeech.cli.tts_cli --md FILE  # Convert Markdown
python -m texttospeech.cli.tts_cli --ppt FILE # Convert PowerPoint

# Phonetic Management
python -m texttospeech.cli.phonetics_cli --interactive  # Interactive mode
python -m texttospeech.cli.phonetics_cli --list         # Show all pronunciations
python -m texttospeech.cli.phonetics_cli --coach WORD   # Get pronunciation help

# Maintenance
pip install -r requirements.txt               # Update dependencies
deactivate                                    # Exit virtual environment
```

## Project Structure Details

### CLI Applications

- **`tts_cli.py`**: Main text-to-speech conversion tool
  - Markdown processing
  - PowerPoint processing
  - Voice listing and management
  - Audio format configuration

- **`phonetics_cli.py`**: Phonetic pronunciation management
  - Interactive pronunciation editing
  - LLM-powered pronunciation coaching
  - Personal phonetic lookup overlay

### Core Modules

- **`tts/`**: TTS backend implementations
  - Azure Speech Service integration
  - ElevenLabs API integration
  - SSML generation and processing

- **`processing/`**: Document processors
  - Markdown parsing with voice aliases
  - PowerPoint slide extraction
  - Text segmentation

- **`phonetics/`**: Phonetic processing
  - IPA notation validation
  - SSML phoneme tag generation
  - Phonetic lookup management

## Getting Help

For detailed usage of specific features:

```powershell
# General help
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help

# See examples
dir examples\
type examples\sample.md
```

Refer to `docs/README.md` and `docs/README_phonetic.md` for detailed documentation.


## Console scripts (aliases) via pyproject

The project exposes easy-name CLI aliases through [project.scripts](pyproject.toml:47). After an editable install, you can run the tools directly as commands.

- Aliases:
  - tts → [main()](src/texttospeech/cli/tts_cli.py:310)
  - phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:59)

Steps (Windows PowerShell):
1) Create and activate a virtual environment
   - python -m venv .venv
   - .\.venv\Scripts\Activate.ps1
2) Install the project (editable)
   - python -m pip install --upgrade pip
   - python -m pip install -e .
3) Use the console scripts
   - tts --help
   - phonetics --help
   - Examples:
     - tts --service azure --voices-short voices_short.txt
     - tts --md examples\sample.md --voice en-US-JennyNeural --overwrite-audio
     - phonetics --interactive
     - phonetics --coach "Worcestershire" --coach-record

Notes:
- Without activating the venv, you can call the executables directly:
  - .\.venv\Scripts\tts.exe --help
  - .\.venv\Scripts\phonetics.exe --help
- On macOS/Linux:
  - source .venv/bin/activate
  - tts --help
  - phonetics --help
- Alternative (no install): module-run form
  - python -m texttospeech.cli.tts_cli --help
  - python -m texttospeech.cli.phonetics_cli --help

Reference:
- Configuration and packaging are defined in [pyproject.toml](pyproject.toml)
- TTS CLI entrypoint: [main()](src/texttospeech/cli/tts_cli.py:310)
- Phonetics CLI entrypoint: [main()](src/texttospeech/cli/phonetics_cli.py:59)
