# TextToSpeech

Multi-Backend Text-to-Speech with Markdown/PPT processing, phonetic dictionary overlays, and an LLM-powered pronunciation coach.

## Features
- Markdown to Speech with per-section voices
- PowerPoint to Speech via notes extraction
- Multiple TTS backends: Azure Speech, ElevenLabs
- Phonetic overlay dictionaries with normalization
- Unified playback pipeline shared by CLI and coach
- Console scripts for easy usage: tts, phonetics
- Modern packaging via [pyproject.toml](pyproject.toml:1)

## Quick Start

Windows PowerShell:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"  # optional
copy config\config.sample.yaml config\config.yaml
tts --help
phonetics --help
```

macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"
cp config/config.sample.yaml config/config.yaml
tts --help
phonetics --help
```

Alternative module-run:
```bash
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help
```

## CLI Usage

Console aliases are defined in [project.scripts](pyproject.toml:47-50):
- tts → [main()](src/texttospeech/cli/tts_cli.py:310)
- phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)

Text-to-Speech:
```bash
# List voices (concise)
tts --service azure --voices-short

# Process Markdown
tts --md examples/sample.md --voice en-US-JennyNeural --overwrite-audio

# Process PowerPoint
tts --ppt examples/sample.pptx --voice en-US-JennyNeural

# Test multiple voices with same text
tts --test-voices text.txt voices_short.txt --output-dir ./voice_samples
```

Phonetics management:
```bash
# Interactive manager
phonetics --interactive

# Record a word
phonetics --record tomato

# List pronunciations (overlay: general + personal)
phonetics --list

# Test pronunciation
phonetics --test tomato

# Remove personal override
phonetics --remove tomato

# LLM coaching (optional baseline recording)
phonetics --coach "Worcestershire" --coach-record
```

Use a specific config:
```bash
tts --config config/config.yaml --md examples/sample.md
phonetics --config config/config.yaml --interactive
```

## Phonetic Overlay and Unified Pipeline

Overlay dictionaries are managed by [PhoneticLookupManager](src/texttospeech/phonetics/manager.py:50):
- Shared (tracked): [data/phonetic_lookup.json](data/phonetic_lookup.json)
- Personal (gitignored): data/phonetic_lookup.personal.json

Personal entries override shared entries; CRUD writes go only to the personal file. Notations are normalized and wrapped as `[ipa:...]` or `[pron:...]`.

Unified playback pipeline:
- Coach/CLI playback: [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308)
- Single-segment synthesis: [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177)

## LLM Phonetic Coach

The coach generates IPA-tagged options, plays them via the unified pipeline, and guides saving.
- Flags: `--coach WORD` and `--coach-record` in [phonetics CLI](src/texttospeech/cli/phonetics_cli.py:98-106)
- Azure OpenAI setup: [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111)

Configuration placeholders in `config/config.yaml` should be replaced with real credentials. The coach will not initialize when `api_key` equals the placeholder string or the endpoint contains the placeholder resource name.

## Architecture and Project Structure

High-level architecture: [docs/architecture.md](docs/architecture.md)

Key modules:
- Orchestrator: [ModalityToSpeech](src/texttospeech/processing/modality_to_speech.py:18)
- Markdown parser: [process_markdown](src/texttospeech/processing/markdown_parser.py:1)
- Azure TTS client: [AzureTTS](src/texttospeech/tts/azure.py:1)
- ElevenLabs TTS client: [ElevenLabsTTS](src/texttospeech/tts/elevenlabs.py:1)

For install/build details: [.github/instructions/install_and_build.instructions.md](.github/instructions/install_and_build.instructions.md)
For contributor guidance: [.github/instructions/code.instructions.md](.github/instructions/code.instructions.md)

## Testing

After editable install:
```bash
pytest tests/ -v
```
Voice listing and synthesis can also be verified via CLI commands above.

## License

MIT License. See [LICENSE](LICENSE).
