# TextToSpeech Architecture

This document describes the src-based package layout, core data flows, configuration, and extension points for the TextToSpeech repository.

Repository root overview:
- [README.md](README.md)
- [docs/](docs/)
- [src/](src/)
- [config/](config/)
- [data/](data/)
- [examples/](examples/)
- [legacy/](legacy/)
- [tests/](tests/)

Package layout under src/:
- [src/texttospeech/](src/texttospeech/)
  - [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py)
  - [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py)
  - [src/texttospeech/processing/markdown_parser.py](src/texttospeech/processing/markdown_parser.py)
  - [src/texttospeech/processing/ppt_processor.py](src/texttospeech/processing/ppt_processor.py)
  - [src/texttospeech/processing/modality_to_speech.py](src/texttospeech/processing/modality_to_speech.py)
  - [src/texttospeech/tts/interface.py](src/texttospeech/tts/interface.py)
  - [src/texttospeech/tts/azure.py](src/texttospeech/tts/azure.py)
  - [src/texttospeech/tts/elevenlabs.py](src/texttospeech/tts/elevenlabs.py)
  - [src/texttospeech/phonetics/manager.py](src/texttospeech/phonetics/manager.py)
  - [src/texttospeech/phonetics/phonetic_word_manager.py](src/texttospeech/phonetics/phonetic_word_manager.py)
  - [src/texttospeech/phonetics/llm_phonetic_coach.py](src/texttospeech/phonetics/llm_phonetic_coach.py)
  - [src/texttospeech/phonetics/processing.py](src/texttospeech/phonetics/processing.py)

Execution model
- Run CLIs via python -m with PYTHONPATH=src:
  - TTS CLI: python -m texttospeech.cli.tts_cli [options]
  - Phonetics CLI: python -m texttospeech.cli.phonetics_cli [options]
- Config defaults to [config/config.yaml](config/config.yaml); a sample is provided at [config/config.sample.yaml](config/config.sample.yaml).

Core flows
1) TTS voice listing and synthesis
- CLI: [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py)
- TTS service abstraction: [src/texttospeech/tts/interface.py](src/texttospeech/tts/interface.py)
- Azure backend: [src/texttospeech/tts/azure.py](src/texttospeech/tts/azure.py)
- ElevenLabs backend: [src/texttospeech/tts/elevenlabs.py](src/texttospeech/tts/elevenlabs.py)
- The CLI constructs a TTS client based on config/service flag, then:
  - Lists voices (--voices/--voices-short)
  - Synthesizes PPT or Markdown via ModalityToSpeech

2) Markdown and PPT pipelines
- Orchestrator: [src/texttospeech/processing/modality_to_speech.py](src/texttospeech/processing/modality_to_speech.py)
- Markdown parsing: [src/texttospeech/processing/markdown_parser.py](src/texttospeech/processing/markdown_parser.py)
- PPT extraction: [src/texttospeech/processing/ppt_processor.py](src/texttospeech/processing/ppt_processor.py)
- Pipeline steps:
  - Parse input to sections/segments and resolve per-segment voice hints
  - Synthesize each segment to temp files using the selected TTS backend
  - Concatenate to section-level audio files with numpy+soundfile

3) Phonetic lookup and coaching
- Overlay-aware manager: [src/texttospeech/phonetics/manager.py](src/texttospeech/phonetics/manager.py)
- Interactive manager: [src/texttospeech/phonetics/phonetic_word_manager.py](src/texttospeech/phonetics/phonetic_word_manager.py)
- LLM coach: [src/texttospeech/phonetics/llm_phonetic_coach.py](src/texttospeech/phonetics/llm_phonetic_coach.py)
- CLI: [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py)
- Data policy:
  - General lookup tracked: [data/phonetic_lookup.json](data/phonetic_lookup.json)
  - Personal overrides (gitignored): data/phonetic_lookup.personal.json
  - CRUD writes go to the personal overlay only 

Configuration
- Global config at [config/config.yaml](config/config.yaml)
- Select TTS service, default voices, and output formats/quality
- Azure credentials may also be provided via environment variables AZURE_SPEECH_KEY and AZURE_SPEECH_REGION

Dependencies
- Runtime requirements: [requirements.txt](requirements.txt)
- Phonetics/recording extras: [requirements_phonetic.txt](requirements_phonetic.txt)
- Recommend using a virtual environment (.venv) and python -m pip install -r requirements.txt

Tests
- Suite under [tests/](tests/)
- Azure voice listing and synthesis validated via CLI during reorg
- pytest should be run from the virtual environment interpreter:
  - Windows PowerShell: .\.venv\Scripts\python.exe -m pytest -q

Legacy
- Legacy assets retained under [legacy/](legacy/)


Extensibility
- Add new TTS backends under [src/texttospeech/tts/](src/texttospeech/tts/)
- Extend processing (e.g., phonetic preprocessing) via [src/texttospeech/phonetics/processing.py](src/texttospeech/phonetics/processing.py)
- CLI options can be expanded in [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py) and [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py)

Conventions
- Paths are repository-root relative where possible
- Audio artifacts are written next to inputs or under examples/output/ when testing
- Keep personal data and credentials out of version control per .gitignore