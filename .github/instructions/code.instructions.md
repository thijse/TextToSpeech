---
applyTo: '**'
---

# TextToSpeech Code Instructions

Guidance for contributing code to the TextToSpeech repository. This project is packaged via [pyproject.toml](pyproject.toml:1) with console scripts and a src-based layout.

## Project layout and key entry points

- Package root: [src/texttospeech/](src/texttospeech/__init__.py:1)
  - CLIs:
    - TTS CLI: [main()](src/texttospeech/cli/tts_cli.py:310)
    - Phonetics CLI: [main()](src/texttospeech/cli/phonetics_cli.py:62)
  - Processing:
    - Markdown parser: [process_markdown](src/texttospeech/processing/markdown_parser.py:1)
    - Modality orchestrator: [ModalityToSpeech](src/texttospeech/processing/modality_to_speech.py:18)
  - TTS backends:
    - Azure: [AzureTTS](src/texttospeech/tts/azure.py:1)
    - ElevenLabs: [ElevenLabsTTS](src/texttospeech/tts/elevenlabs.py:1)
  - Phonetics:
    - Lookup/overlay manager: [PhoneticLookupManager](src/texttospeech/phonetics/manager.py:50)
    - Interactive manager: [InteractivePhoneticManager](src/texttospeech/phonetics/phonetic_word_manager.py:199)
    - LLM coach: [LLMPhoneticCoach](src/texttospeech/phonetics/llm_phonetic_coach.py:72)

Tests live under [tests/](tests/test_tts.py:1).

## Environment and installation

Use a dedicated virtual environment. Standardize on venv across docs and scripts:

Windows PowerShell:
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
# Optional dev tools
python -m pip install -e ".[dev]"
```

macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"
```

Copy and edit config:
- Copy [config/config.sample.yaml](config/config.sample.yaml:1) to config/config.yaml
- Fill Azure/ElevenLabs credentials, and optionally azure_openai for the coach

## Running and debugging

Console scripts (preferred):
- tts → [main()](src/texttospeech/cli/tts_cli.py:310)
- phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)

Examples:
```powershell
tts --service azure --voices-short
tts --md examples\sample.md --voice en-US-JennyNeural --overwrite-audio
tts --ppt examples\sample.pptx --voice en-US-JennyNeural

phonetics --interactive
phonetics --list
phonetics --coach "Worcestershire" --coach-record
```

Module form (alternative):
```powershell
python -m texttospeech.cli.tts_cli --help
python -m texttospeech.cli.phonetics_cli --help
```

Run tests:
```powershell
pytest tests/ -v
```

## Configuration notes

- TTS selection via config tts_service or --service flag
- Azure credentials can use env vars: AZURE_SPEECH_KEY and AZURE_SPEECH_REGION (see [main()](src/texttospeech/cli/tts_cli.py:388))
- LLM coach checks placeholders to avoid initializing without real credentials (see [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111))

## Phonetic overlay and unified pipeline

- Dictionaries:
  - Shared tracked: [data/phonetic_lookup.json](data/phonetic_lookup.json:1)
  - Personal overlay (gitignored): data/phonetic_lookup.personal.json
- Unified playback path for coach and CLI:
  - [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308)
  - → [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177)

## Adding features

- New TTS backends under [src/texttospeech/tts/](src/texttospeech/tts/interface.py:1); implement the [TTSInterface](src/texttospeech/tts/interface.py:1) methods
- Extend processing or phonetics within:
  - [markdown_parser](src/texttospeech/processing/markdown_parser.py:1)
  - [modality_to_speech](src/texttospeech/processing/modality_to_speech.py:18)
  - [phonetics/processing](src/texttospeech/phonetics/processing.py:1)

Coordinate CLI switches in:
- TTS CLI: [main()](src/texttospeech/cli/tts_cli.py:310)
- Phonetics CLI: [main()](src/texttospeech/cli/phonetics_cli.py:62)

## Code style and conventions

- Keep repo-root relative paths where possible
- Prefer console scripts in examples; include python -m alternatives
- Ensure clickable references use the format [label](path/to/file.py:line) for functions and filenames
- Avoid committing personal data/credentials (.gitignore guards overlay/personal files)

## Appendix: Async programming patterns (optional)

For asynchronous tools or background tasks, use anyio:

Basic sleep:
```python
import anyio

async def my_async_function():
    await anyio.sleep(1.0)
```

Task groups:
```python
import anyio

async def run_concurrent_tasks():
    async with anyio.create_task_group() as tg:
        tg.start_soon(task1)
        tg.start_soon(task2)
```

Event sync:
```python
import anyio

class MyModule:
    def __init__(self):
        self.connected = anyio.Event()

    async def wait_for_connection(self):
        await self.connected.wait()

    def on_connected(self):
        self.connected.set()
```

Cancellation:
```python
import anyio

async def cancellable_operation():
    try:
        while True:
            await anyio.sleep(1)
    except anyio.get_cancelled_exc_class():
        # cleanup
        raise
```

Background worker:
```python
import anyio

class ServiceModule:
    async def start_background_service(self):
        async with anyio.create_task_group() as tg:
            tg.start_soon(self._background_worker)

    async def _background_worker(self):
        while True:
            try:
                await self._do_work()
                await anyio.sleep(0.1)
            except anyio.get_cancelled_exc_class():
                break
```

## References

- Packaging and scripts: [pyproject.toml](pyproject.toml:1)
- Architecture overview: [docs/architecture.md](docs/architecture.md:1)
- Phonetic README (canonical): [README_phonetic.md](README_phonetic.md:1)
