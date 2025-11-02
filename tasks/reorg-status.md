# Repository Reorganization Status and Test Plan

This document tracks the reorganization progress and validation steps. It reflects the latest integration work including the LLM coach baseline, wrapper-aware phonetics, and pyproject-based packaging.

Status summary (completed)
- Migrated to src/ layout with package name texttospeech:
  - CLI: [src/texttospeech/cli/tts_cli.py](../src/texttospeech/cli/tts_cli.py), [src/texttospeech/cli/phonetics_cli.py](../src/texttospeech/cli/phonetics_cli.py)
  - TTS: [src/texttospeech/tts/interface.py](../src/texttospeech/tts/interface.py), [src/texttospeech/tts/azure.py](../src/texttospeech/tts/azure.py), [src/texttospeech/tts/elevenlabs.py](../src/texttospeech/tts/elevenlabs.py)
  - Processing: [src/texttospeech/processing/markdown_parser.py](../src/texttospeech/processing/markdown_parser.py), [src/texttospeech/processing/ppt_processor.py](../src/texttospeech/processing/ppt_processor.py), [src/texttospeech/processing/modality_to_speech.py](../src/texttospeech/processing/modality_to_speech.py)
  - Phonetics: [src/texttospeech/phonetics/manager.py](../src/texttospeech/phonetics/manager.py), [src/texttospeech/phonetics/phonetic_word_manager.py](../src/texttospeech/phonetics/phonetic_word_manager.py), [src/texttospeech/phonetics/llm_phonetic_coach.py](../src/texttospeech/phonetics/llm_phonetic_coach.py), [src/texttospeech/phonetics/processing.py](../src/texttospeech/phonetics/processing.py)
- LLM Coach baseline integration:
  - CLI adds baseline recording with --coach-record (see [phonetics_cli.py](../src/texttospeech/cli/phonetics_cli.py))
  - Baseline is injected at session start in [LLMPhoneticCoach.start_coaching_session()](../src/texttospeech/phonetics/llm_phonetic_coach.py)
- Phonetics robustness:
  - Auto-phonetics avoids double-wrapping by extracting core before markup in [ModalityToSpeech.apply_automatic_phonetics()](../src/texttospeech/processing/modality_to_speech.py)
  - Wrapper-aware single-phonetic processing in [process_phonetic_for_tts()](../src/texttospeech/phonetics/processing.py) respects existing [ipa:] / [pron:] tags
- Configuration and data policy:
  - Global config under [config/config.sample.yaml](../config/config.sample.yaml) with environment fallback
  - Phonetic overlay: tracked general [data/phonetic_lookup.json](../data/phonetic_lookup.json) + personal overlay (gitignored) data/phonetic_lookup.personal.json
- Packaging:
  - Pyproject-based setup via [pyproject.toml](../pyproject.toml). Requirements files are scheduled for removal; quick install now prefers editable install.

Status summary (in progress / pending)
- Documentation updates:
  - Expand [docs/architecture.md](../docs/architecture.md) to include LLM Coach baseline, Azure OpenAI configuration, and pyproject-based install
- Packaging migration:
  - Remove legacy requirements.txt and requirements_phonetic.txt in favor of pyproject; update build instructions accordingly
- Automated test hardening:
  - Add conditional skips/importorskip for Azure Speech/OpenAI dependent tests
- End-to-end validation:
  - Re-run CLI flows and tests under pyproject-based install to ensure everything works post-migration

Installation and packaging
- Preferred: editable install using pyproject
  - Windows PowerShell:
    - python -m venv .venv
    - .\.venv\Scripts\Activate.ps1
    - python -m pip install --upgrade pip
    - python -m pip install -e .
- Alternative instructions are documented in [.github/instructions/install_and_build.instructions.md](../.github/instructions/install_and_build.instructions.md) and [build.bat](../build.bat)
- Note: PYTHONPATH=src is no longer required after editable install

Automated test plan (pytest)
- Command (after editable install):
  - python -m pytest -q
- Dependencies:
  - Azure Speech SDK: python -m pip install azure-cognitiveservices-speech
  - OpenAI SDK: python -m pip install openai
- Conditional skips:
  - Use pytest.importorskip for azure.cognitiveservices.speech in Azure-dependent tests
  - Use pytest.importorskip for openai and environment checks in LLM coach tests
- Acceptance criteria:
  - All tests collect without import errors
  - Azure/OpenAI-dependent tests either pass with credentials or skip gracefully

Manual CLI validation plan

A) Voice listing (Azure)
- Short list:
  - python -m texttospeech.cli.tts_cli --service azure --voices-short voices_short.txt
- Full list (heavy):
  - python -m texttospeech.cli.tts_cli --service azure --voices voices.txt
- Expected:
  - Output files contain voice names and IDs; no authentication errors.

B) Synthesis sanity with a subset of voices (Azure)
- Prepare:
  - Ensure output folder exists and create test subset + text
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --test-voices examples\output\test_text.txt examples\output\voice_subset.txt --output-dir examples\output\voice_samples
- Expected:
  - MP3s generated for each valid voice; robust matching on names/ids.

C) Markdown pipeline
- Input: [examples/sample.md](../examples/sample.md)
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --md examples/sample.md --voice en-US-JennyNeural --overwrite-audio
- Expected:
  - Section audio files created; concatenation completes without errors.

D) PowerPoint pipeline
- Input: [examples/sample.pptx](../examples/sample.pptx)
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --ppt examples/sample.pptx --voice en-US-JennyNeural --overwrite-audio
- Expected:
  - Per-slide audio files generated with PPT extraction + synthesis.

E) Phonetics CLI and Coach
- List entries:
  - python -m texttospeech.cli.phonetics_cli --list
- Record and coach baseline:
  - python -m texttospeech.cli.phonetics_cli --coach "Worcestershire" --coach-record
- Save flow:
  - In the coach session, use commands like:
    - "1" to play option 1
    - "save" to save the last played option
    - "save 3" to save option number 3
    - "save [ipa:ˈwʊstəʃə]" to save a specific notation
- Expected:
  - Baseline option injected at top when recorded; playback uses unified pipeline; saved entries persist to personal overlay.

Known issues and follow-ups
- Ensure Azure/OpenAI credentials present for dependent operations
- Confirm soundfile/numpy concatenation on Windows
- Remove legacy requirements files after confirming all installs work via pyproject
- Update README files to reflect pyproject install and CLI usage

Action checklist
- [x] Integrate LLM coach baseline (--coach-record) and wrapper-aware phonetics
- [-] Update docs ([docs/architecture.md](../docs/architecture.md)) with LLM Coach, Azure OpenAI config, and pyproject instructions
- [-] Migrate installation docs to pyproject; plan removal of legacy requirements files
- [ ] Update [README.md](../README.md) and [docs/README_phonetic.md](../docs/README_phonetic.md) with final instructions and examples