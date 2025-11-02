# Phonetic Word Manager

A complete tool for recording custom word pronunciations, extracting phonetic notations, and managing a phonetic lookup database for Text-to-Speech applications. Integrated with the unified TTS pipeline and an optional LLM-based pronunciation coach.

## Key Features

- 🎙️ Audio Recording – Record pronunciation samples with a countdown timer
- 🔍 Phonetic Extraction – Approximate IPA-compatible phonetic notation via Azure Speech recognition
- 📚 Overlay Phonetic Database – Team-shared + personal overrides with normalization
- 🔊 TTS Playback – Test pronunciations using the unified pipeline (SSML-aware for Azure)
- ⚡ Interactive Workflow – Menu-driven recording and management
- 🧠 LLM Coach – Conversational guidance, baseline injection, and save workflows

## Installation

Recommended: editable install with console scripts.

Windows PowerShell:
```powershell
# Create and activate a virtual environment
python -m venv venv
venv\Scripts\Activate.ps1

# Upgrade pip and install the project
python -m pip install --upgrade pip
python -m pip install -e .

# (Optional) developer extras
python -m pip install -e ".[dev]"

# Copy sample config and fill credentials
copy config\config.sample.yaml config\config.yaml
```

macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"
cp config/config.sample.yaml config/config.yaml
```

Console scripts (defined in [pyproject.toml](pyproject.toml:47-50)):
- tts → [main()](src/texttospeech/cli/tts_cli.py:310)
- phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)

Alternative module-run form:
```bash
python -m texttospeech.cli.phonetics_cli --help
```

## Configuration

Edit `config/config.yaml`:
- Azure Speech: `azure.api_key`, `azure.region`, `azure.voice_name`
- ElevenLabs (optional): `elevenlabs.api_key`, `elevenlabs.voice_name`, `elevenlabs.model_id`
- Azure OpenAI (LLM Coach): `azure_openai` block (endpoint, api_key, deployment_name/model, api_version)

The LLM Coach avoids initialization if the API key is the placeholder or the endpoint contains the placeholder resource name (see [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111)).

## Usage

Primary usage via console alias:
```bash
phonetics --help
```

Common commands:
```bash
# Interactive mode (recommended)
phonetics --interactive

# Record a specific word
phonetics --record tomato

# List pronunciations (overlaid: general + personal)
phonetics --list

# Test a pronunciation
phonetics --test tomato

# Remove a PERSONAL override (general remains intact)
phonetics --remove tomato

# LLM coaching for a word
phonetics --coach "worcestershire"

# LLM coaching with baseline recording injection
phonetics --coach "worcestershire" --coach-record

# Use a specific config
phonetics --config config\config.yaml
```

Module form (alternative):
```bash
python -m texttospeech.cli.phonetics_cli --interactive
```

## Recording Workflow

When you record a word:
1. Enter the word to record
2. Existing-check – if present, choose whether to overwrite
3. Record audio – 3-second countdown, then capture
4. Extract phonetics – Azure Speech recognition + heuristic approximation
5. Review & edit – optionally edit phonetics
6. Test playback – hear the result via the unified TTS pipeline
7. Save decision – write to your personal overlay dictionary

## Output and Dictionary Overlay

The tool uses an overlay-capable phonetic lookup managed by [src/texttospeech/phonetics/manager.py](src/texttospeech/phonetics/manager.py:50):

- Shared (tracked): `data/phonetic_lookup.json`
- Personal (gitignored): `data/phonetic_lookup.personal.json`

Rules:
- Personal entries override shared entries
- CRUD writes go to the personal file only
- Notations are normalized and wrapped as `[ipa:...]` or `[pron:...]` for consistent processing

## LLM Phonetic Coach

- Start with: `phonetics --coach WORD`
- Optional baseline injection: `--coach-record` to record a short attempt; automatically normalized and injected as an option
- Coach integrates unified playback and dictionary-aware options
- Unified playback path: [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308) → [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177)

Coach initialization and Azure OpenAI configuration:
- See [LLMPhoneticCoach._setup_azure_openai()](src/texttospeech/phonetics/llm_phonetic_coach.py:111)

## Integration with TTS Systems

Apply dictionary phonetics to text before synthesis:

Azure (SSML):
```python
from texttospeech.phonetics.manager import PhoneticLookupManager

manager = PhoneticLookupManager()
text = "I like tomato soup"
ssml_text = manager.apply_to_text_azure(text)
# e.g., <speak ...><phoneme alphabet="ipa" ph="təˈmeɪtoʊ">tomato</phoneme>...</speak>
```

ElevenLabs (plain text with inline hints):
```python
from texttospeech.phonetics.manager import PhoneticLookupManager

manager = PhoneticLookupManager()
text = "I like tomato soup"
elevenlabs_text = manager.apply_to_text_elevenlabs(text)
# e.g., "I like tomato (təˈmeɪtoʊ) soup"
```

## Dependencies

Installed via [pyproject.toml](pyproject.toml:27-38):
- azure-cognitiveservices-speech (Azure Speech)
- sounddevice (recording)
- soundfile (audio I/O)
- numpy (audio concatenation / processing)
- pyyaml (config)
- openai (LLM Coach)

## Troubleshooting

- Import errors:
  - Ensure venv is active and the package is installed: `python -m pip install -e .`

- Audio recording issues:
  - Check microphone permissions and device availability
  - Adjust input levels; try different microphones

- Azure authentication errors:
  - Verify `azure.api_key` and `azure.region` in `config/config.yaml`
  - Alternatively set env vars: `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION`

- No sound during playback:
  - Check system output devices and volume
  - Confirm the generated temp files can be played

- LLM Coach not available or not configured:
  - Install deps via editable install (OpenAI SDK is included)
  - Fill `azure_openai` in config; placeholders are treated as unconfigured

## Examples

Recording "Worcestershire":
```bash
phonetics --record worcestershire
```
1) System prompts to record
2) You pronounce "Worcestershire"
3) System generates an approximation (e.g., `wʊstərʃər`)
4) You can edit to: `ˈwʊstər.ʃər`
5) Playback for confirmation
6) Save to your personal dictionary

LLM Coaching with baseline:
```bash
phonetics --coach "Worcestershire" --coach-record
```

Batch entry (manual) – use interactive mode and select option 1 repeatedly:
```bash
phonetics --interactive
```

## Related

- Architecture and data flows: [docs/architecture.md](docs/architecture.md)
- Unified playback implementation: [InteractivePhoneticManager._play_phonetic_unified()](src/texttospeech/phonetics/phonetic_word_manager.py:308), [ModalityToSpeech.synthesize_single_segment()](src/texttospeech/processing/modality_to_speech.py:177)
- CLI entrypoints:
  - tts → [main()](src/texttospeech/cli/tts_cli.py:310)
  - phonetics → [main()](src/texttospeech/cli/phonetics_cli.py:62)
