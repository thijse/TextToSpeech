# Repository Reorganization Status and Test Plan

This document tracks how far the reorganization has progressed and outlines the tests still required to validate the new structure and flows.

Status summary (completed)
- Migrated to src/ layout with package name texttospeech:
  - CLI: [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py), [src/texttospeech/cli/phonetics_cli.py](src/texttospeech/cli/phonetics_cli.py)
  - TTS: [src/texttospeech/tts/interface.py](src/texttospeech/tts/interface.py), [src/texttospeech/tts/azure.py](src/texttospeech/tts/azure.py), [src/texttospeech/tts/elevenlabs.py](src/texttospeech/tts/elevenlabs.py)
  - Processing: [src/texttospeech/processing/markdown_parser.py](src/texttospeech/processing/markdown_parser.py), [src/texttospeech/processing/ppt_processor.py](src/texttospeech/processing/ppt_processor.py), [src/texttospeech/processing/modality_to_speech.py](src/texttospeech/processing/modality_to_speech.py)
  - Phonetics: [src/texttospeech/phonetics/manager.py](src/texttospeech/phonetics/manager.py), [src/texttospeech/phonetics/phonetic_word_manager.py](src/texttospeech/phonetics/phonetic_word_manager.py), [src/texttospeech/phonetics/llm_phonetic_coach.py](src/texttospeech/phonetics/llm_phonetic_coach.py)
- Standardized configuration at [config/config.yaml](config/config.yaml) with sample at [config/config.sample.yaml](config/config.sample.yaml). Code falls back to AZURE_SPEECH_KEY and AZURE_SPEECH_REGION when config is missing.
- Cleaned up legacy assets under [legacy/](legacy/); corrected a mistaken file move and retained artifact at [legacy/old_root/old_root_mistake](legacy/old_root/old_root_mistake).
- BOM/case-insensitive handling for TTS test-voices file in [src/texttospeech/cli/tts_cli.py](src/texttospeech/cli/tts_cli.py).
- Verified Azure voices listing and small synthesis samples manually via CLI using config credentials.

Status summary (in progress / pending)
- Run and stabilize automated tests in [tests/](tests/). Current blocker: azure SDK missing in the active interpreter during pytest collection.
- End-to-end flow checks for:
  - Markdown-to-speech via [src/texttospeech/processing/modality_to_speech.py](src/texttospeech/processing/modality_to_speech.py)
  - PPT-to-speech via [src/texttospeech/processing/ppt_processor.py](src/texttospeech/processing/ppt_processor.py)
- Documentation pass to reflect final commands in [README.md](README.md) and [README_phonetic.md](README_phonetic.md).
- Review and update examples and any referenced paths under [examples/](examples/).

Environment and prerequisites
- Use a virtual environment and install dependencies:
  - Windows PowerShell:
    - python -m venv .venv
    - .\.venv\Scripts\Activate.ps1
    - python -m pip install --upgrade pip 
    - python -m pip install -r requirements.txt
    - Optional phonetics extras: python -m pip install -r requirements_phonetic.txt
- Ensure config:
  - Copy [config/config.sample.yaml](config/config.sample.yaml) to [config/config.yaml](config/config.yaml) and fill Azure keys (or set env vars AZURE_SPEECH_KEY, AZURE_SPEECH_REGION).
- Set PYTHONPATH for module runs and pytest:
  - Windows PowerShell (per-session): $env:PYTHONPATH = "src"

Automated test plan (pytest)
- Command:
  - $env:PYTHONPATH = "src"; python -m pytest -q
- Current issues to resolve:
  - tests/test_azure_tts.py and tests/test_tts.py import azure.cognitiveservices.speech directly.
  - If ModuleNotFoundError: No module named 'azure' occurs, install the SDK:
    - python -m pip install azure-cognitiveservices-speech
  - Consider future-proofing tests to skip when Azure SDK or credentials are missing using pytest.importorskip and/or environment checks.
- Acceptance criteria:
  - All tests in [tests/](tests/) collect and run without import errors.
  - Azure-dependent tests either pass with provisioned keys or are skipped gracefully when not provisioned.

Manual CLI validation plan

A) Voice listing (Azure)
- Short list:
  - python -m texttospeech.cli.tts_cli --service azure --voices-short --out examples/output/voices_short.txt
- Full list (heavy):
  - python -m texttospeech.cli.tts_cli --service azure --voices --out examples/output/voices.txt
- Expected:
  - Output files exist and contain voice names and voice IDs; no authentication errors.

B) Synthesis sanity with a subset of voices (Azure)
- Prepare inputs:
  - Ensure folder exists: New-Item -ItemType Directory -Force -Path examples\output | Out-Null
  - Set-Content -Path examples\output\voice_subset.txt -Value "en-GB-AdaMultilingualNeural`r`nen-US-JennyNeural"
  - Set-Content -Path examples\output\test_text.txt -Value "Hello from TextToSpeech. This is a voice test."
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --test-voices --voices-file examples\output\voice_subset.txt --text-file examples\output\test_text.txt --out-dir examples\output\voice_samples
- Expected:
  - MP3 files appear in examples/output/voice_samples/ for both voices; no missing-voice errors.

C) Markdown pipeline
- Input: [examples/sample.md](examples/sample.md)
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --markdown examples/sample.md --out examples/output/sample_md --voice en-US-JennyNeural
- Expected:
  - Section audio files created under examples/output/sample_md (or nested structure as implemented), concatenation completes without errors.

D) PowerPoint pipeline
- Input: [examples/sample.pptx](examples/sample.pptx)
- Run:
  - python -m texttospeech.cli.tts_cli --service azure --ppt examples/sample.pptx --out examples/output/sample_ppt --voice en-US-JennyNeural
- Expected:
  - Per-slide audio files generated under examples/output/sample_ppt with successful PPT text extraction and synthesis.

E) Phonetics CLI
- List existing entries:
  - python -m texttospeech.cli.phonetics_cli --list
- Add and remove an entry (example):
  - python -m texttospeech.cli.phonetics_cli --add "Thijs" --ipa "tɛis"
  - python -m texttospeech.cli.phonetics_cli --remove "Thijs"
- Expected:
  - List shows sources (general/personal). Add/remove adjusts personal overlay at data/phonetic_lookup.personal.json (gitignored). No exceptions thrown.

Known issues and follow-ups
- Pytest collection currently fails due to missing Azure SDK; fix by installing azure-cognitiveservices-speech or implement conditional skips in tests.
- Ensure Windows-friendly file creation and line endings when preparing voice subset and test text (use PowerShell Set-Content as shown).
- Confirm that soundfile and numpy-based concatenation runs on the target system (the prebuilt soundfile wheel should ship libsndfile for Windows).
- Review and finalize documentation in [README.md](README.md) and [README_phonetic.md](README_phonetic.md) to reflect python -m usage and PYTHONPATH=src.

Action checklist
- [x] Create architecture overview at [docs/architecture.md](../docs/architecture.md)
- [x] Create this reorg status and test plan at [tasks/reorg-status.md](reorg-status.md)
- [ ] Install and verify azure-cognitiveservices-speech in the active environment
- [ ] Re-run automated tests: $env:PYTHONPATH = "src"; python -m pytest -q
- [ ] Add conditional skips for Azure-dependent tests when SDK/credentials are missing
- [ ] Validate Markdown and PPT end-to-end CLI flows (see commands above)
- [ ] Update [README.md](../README.md) and [README_phonetic.md](../README_phonetic.md) with final instructions and examples
- [ ] Review and update [tasks/reorg-plan.md](reorg-plan.md) with python -m equivalents, ensuring consistency

References
- Architecture: [docs/architecture.md](../docs/architecture.md)
- Code entry points:
  - TTS CLI: [src/texttospeech/cli/tts_cli.py](../src/texttospeech/cli/tts_cli.py)
  - Phonetics CLI: [src/texttospeech/cli/phonetics_cli.py](../src/texttospeech/cli/phonetics_cli.py)
- Tests: [tests/](../tests/)