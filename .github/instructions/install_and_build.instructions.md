---
applyTo: '/**'
---

# TextToSpeech - Installation and Build Instructions

This document provides guidance for setting up, building, and running the TextToSpeech application. The system converts Markdown documents and PowerPoint presentations to speech using Azure Speech or ElevenLabs TTS services, with optional phonetic coaching and dictionary overlays.

## Table of Contents

1. Prerequisites
2. Quick Start
3. Console Scripts
4. Development Workflow
5. Configuration
6. Phonetic Lookup Overlay
7. Troubleshooting
8. Essential Commands

## Prerequisites

- Python 3.8+ (project supports 3.8 through 3.12 as configured in [pyproject.toml](pyproject.toml:10-24))
- A virtual environment tool (built-in venv)
- Optional TTS credentials:
  - Azure Speech Service: API key and region
  - ElevenLabs: API key

## Quick Start

Recommended: editable install via pyproject with console scripts.

Windows PowerShell:

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# 2. Upgrade pip and install project in editable mode
python -m pip install --upgrade pip
python -m pip install -e .

# 3. (Optional) install dev dependencies
python -m pip install -e ".[dev]"

# 4. Copy and configure settings
copy config\config.sample.yaml config\config.yaml
# Edit config\config.yaml with your Azure/ElevenLabs credentials

# 5. Verify console scripts
tts --help
phonetics --help
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"  # optional

cp config/config.sample.yaml config/config.yaml
tts --help
phonetics --help
```

Alternative (module-run form):

```powershell
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help
```

## Console Scripts

Console aliases are defined under [project.scripts](pyproject.toml:47-50):

- tts → [main()](src/texttospeech/cli/tts_cli.py:310)
- phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)

Examples:

```powershell
# List voices (concise)
tts --service azure --voices-short

# Process Markdown
tts --md examples\sample.md --voice en-US-JennyNeural --overwrite-audio

# Process PowerPoint
tts --ppt examples\sample.pptx --voice en-US-JennyNeural

# Phonetic manager interactive mode
phonetics --interactive

# LLM coaching with baseline recording
phonetics --coach "Worcestershire" --coach-record
```

## Development Workflow

- Always activate your virtual environment before running commands:
  - Windows: venv\Scripts\Activate.ps1
  - macOS/Linux: source venv/bin/activate

- Update dependencies after pulling changes:
  - python -m pip install -e .
  - python -m pip install -e ".[dev]"  # optional

- Run tests (if dev extras are installed):
  - pytest tests/ -v

## Configuration

Edit [config/config.yaml](config/config.yaml) (copy from [config/config.sample.yaml](config/config.sample.yaml:1)):

Minimal example:

```yaml
tts_service: "azure"  # Options: "elevenlabs", "azure"

elevenlabs:
  api_key: "your_api_key_here"
  voice_name: "Sarah"
  model_id: "eleven_monolingual_v1"

azure:
  api_key: "<Azure API key>"
  region: "eastus"
  voice_name: "en-US-JennyNeural"

azure_openai:
  endpoint: "https://your-resource-name.openai.azure.com/"
  api_key: "your-azure-openai-api-key-here"
  api_version: "2025-04-01-preview"
  deployment_name: "gpt-5"
  model: "gpt-5"
  max_tokens: 1000
  temperature: 1.0
  enable_fallback: true

output:
  format: "mp3"   # mp3, wav, ogg, webm
  quality: "high" # high, medium, low
```

Environment variables (Azure Speech):

```powershell
$env:AZURE_SPEECH_KEY = "your-key"
$env:AZURE_SPEECH_REGION = "eastus"
```

The TTS CLI also reads legacy env names: SPEECH_KEY/SPEECH_REGION and AZURE_TTS_KEY/AZURE_TTS_REGION (see [main()](src/texttospeech/cli/tts_cli.py:388-396)).

## Phonetic Lookup Overlay

Pronunciation dictionaries use overlay semantics managed by [PhoneticLookupManager](src/texttospeech/phonetics/manager.py:50):

- Shared (tracked): [data/phonetic_lookup.json](data/phonetic_lookup.json)
- Personal (gitignored): data/phonetic_lookup.personal.json

Personal entries override shared entries; CRUD writes go only to the personal file. The manager also normalizes wrapper tags to [ipa:...] or [pron:...] for consistent processing.

LLM Phonetic Coach integrates unified playback and dictionary-aware suggestions:
- CLI flags: --coach WORD and optional --coach-record for baseline (see [phonetics CLI options](src/texttospeech/cli/phonetics_cli.py:98-106))
- Baseline injection and Azure OpenAI setup: [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111)
- Unified playback pipeline: [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308) → [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177)

## Troubleshooting

- Module not found:
  - Ensure the venv is activated and project installed: python -m pip install -e .

- Azure credentials missing:
  - Set azure.api_key and azure.region in config, or use environment variables
  - TTS CLI credential validation: [main()](src/texttospeech/cli/tts_cli.py:383-404)

- ElevenLabs key missing:
  - Set elevenlabs.api_key in config/config.yaml
  - Validation: [main()](src/texttospeech/cli/tts_cli.py:407-417)

- Audio generation or output directory issues:
  - Ensure the output directory exists and is writable
  - See Markdown/PPT processing flows: [ModalityToSpeech.process_markdown_document()](src/texttospeech/processing/modality_to_speech.py:34) and [process_powerpoint()](src/texttospeech/processing/modality_to_speech.py:306)

- LLM coach configuration:
  - Install OpenAI SDK is included via [pyproject dependencies](pyproject.toml:27-38)
  - Configure azure_openai placeholder values; the coach intentionally avoids initialization when API key is "your-azure-openai-api-key-here" or endpoint contains "your-resource-name" (see [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:121-130))

## Essential Commands

```powershell
# Setup
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install -e ".[dev]"  # optional
copy config\config.sample.yaml config\config.yaml

# Console scripts
tts --help
phonetics --help

# TTS Operations
tts --voices-short
tts --md examples\sample.md --voice en-US-JennyNeural
tts --ppt examples\sample.pptx --voice en-US-JennyNeural

# Phonetics Management
phonetics --interactive
phonetics --list
phonetics --coach "Worcestershire" --coach-record

# Module-run fallback
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help
```

For architectural details, data flows, and extension points, see [docs/architecture.md](docs/architecture.md).
