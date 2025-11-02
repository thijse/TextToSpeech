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
- Unified playback pipeline:
  - Coach and CLI playback route through [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308) → [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177) using [PhoneticProcessor.preprocess_text()](src/texttospeech/phonetics/processing.py:353)
- Coach baseline integration:
  - Optional baseline recording via phonetics CLI flag --coach-record; injected at session start in [LLMPhoneticCoach.start_coaching_session()](src/texttospeech/phonetics/llm_phonetic_coach.py:153)
- CLI: [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py) (supports --interactive, --record, --list, --test, --remove, --coach, and --coach-record)
- Data policy:
  - General lookup tracked: [data/phonetic_lookup.json](data/phonetic_lookup.json)
  - Personal overrides (gitignored): data/phonetic_lookup.personal.json
  - CRUD writes go to the personal overlay only

Configuration
- Global config at [config/config.yaml](config/config.yaml)
- Select TTS service, default voices, and output formats/quality
- Azure credentials may also be provided via environment variables AZURE_SPEECH_KEY and AZURE_SPEECH_REGION
- Azure OpenAI (LLM Coach) configuration:
  - Configure azure_openai: { api_key, endpoint, deployment_name, model, api_version } in config.yaml
  - Initialization and validation live in [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111)
  - Install SDK: python -m pip install openai

Dependencies
- Primary packaging: [pyproject.toml](pyproject.toml)
- Preferred install (editable):
  - python -m venv .venv
  - .\.venv\Scripts\Activate
  - python -m pip install --upgrade pip
  - python -m pip install -e .
- SDKs for optional features:
  - Azure Speech SDK: python -m pip install azure-cognitiveservices-speech
  - OpenAI SDK: python -m pip install openai
- Note: legacy requirements files are being deprecated in favor of pyproject-based installation

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
File summaries under src/texttospeech

- [src/texttospeech/__init__.py](src/texttospeech/__init__.py) — Package initializer; may expose high-level imports for convenience.
- [src/texttospeech/cli/__init__.py](src/texttospeech/cli/__init__.py) — CLI package marker.
- [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py) — TTS CLI entrypoint; lists voices, processes Markdown/PPT, batch tests voices; constructs ModalityToSpeech with phonetic support.
- [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py) — Phonetics CLI entrypoint; interactive manager, record/list/test/remove operations; starts LLM coach; supports --coach-record baseline.

- [src/texttospeech/phonetics/__init__.py](src/texttospeech/phonetics/__init__.py) — Phonetics package marker.
- [src/texttospeech/phonetics/manager.py](src/texttospeech/phonetics/manager.py) — Overlay-aware PhoneticLookupManager for general+personal dictionaries; normalization, sanitization, and apply-to-text helpers.
- [src/texttospeech/phonetics/phonetic_word_manager.py](src/texttospeech/phonetics/phonetic_word_manager.py) — Interactive manager for recording audio, extracting phonetics via Azure Speech, unified playback, and saving entries.
- [src/texttospeech/phonetics/llm_phonetic_coach.py](src/texttospeech/phonetics/llm_phonetic_coach.py) — Azure OpenAI-driven coach; generates tagged phonetic options, plays and guides saves; integrates PhoneticProcessor; supports baseline injection.
- [src/texttospeech/phonetics/processing.py](src/texttospeech/phonetics/processing.py) — Core phonetic pipeline: markup parser, notation validator, SSML/hint generators, PhoneticProcessor, and wrapper-aware process_phonetic_for_tts.

- [src/texttospeech/processing/__init__.py](src/texttospeech/processing/__init__.py) — Processing package marker.
- [src/texttospeech/processing/markdown_parser.py](src/texttospeech/processing/markdown_parser.py) — Parses Markdown into sections and voice segments; alias and inline voice tag handling.
- [src/texttospeech/processing/modality_to_speech.py](src/texttospeech/processing/modality_to_speech.py) — Orchestrates Markdown/PPT to speech; segment synthesis, concatenation; unified single-segment synthesis; automatic phonetics application.
- [src/texttospeech/processing/ppt_processor.py](src/texttospeech/processing/ppt_processor.py) — Extracts PPT notes/titles to Markdown; controls inclusion settings and script generation.

- [src/texttospeech/tts/__init__.py](src/texttospeech/tts/__init__.py) — TTS package marker.
- [src/texttospeech/tts/interface.py](src/texttospeech/tts/interface.py) — Abstract TTSInterface defining text_to_speech and get_voices contracts.
- [src/texttospeech/tts/azure.py](src/texttospeech/tts/azure.py) — Azure Speech TTS client; voice retrieval and SSML-based synthesis; output format mapping.
- [src/texttospeech/tts/elevenlabs.py](src/texttospeech/tts/elevenlabs.py) — ElevenLabs TTS client; synthesis with text hints; model/voice configuration.