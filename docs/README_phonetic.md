# Phonetic Word Manager Documentation

Canonical documentation lives at [README_phonetic.md](README_phonetic.md).

This file is a pointer to avoid duplication and ensure updates remain consistent with the current architecture and CLI implementation.

Quick usage:

- Install package in editable mode and use console aliases from [pyproject.toml](pyproject.toml:47):
  - tts → [main()](src/texttospeech/cli/tts_cli.py:310)
  - phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)

Examples:

- phonetics --interactive
- phonetics --list
- phonetics --coach tomato --coach-record

For architecture and data flow details, see [docs/architecture.md](docs/architecture.md).

For the unified playback pipeline, see [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308) and [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177).
