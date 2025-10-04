# Standalone Phonetic Word Manager

A complete standalone tool for recording custom word pronunciations, extracting phonetic notations, and managing a phonetic lookup database for Text-to-Speech applications.

## Features

🎙️ **Audio Recording** - Record pronunciation samples with countdown timer  
🔍 **Phonetic Extraction** - Convert audio to IPA-compatible phonetic notation using Azure Speech Recognition  
📚 **Phonetic Database** - Store and manage custom pronunciations  
🔊 **TTS Playback** - Test phonetic pronunciations using Azure TTS with SSML  
⚡ **Interactive Workflow** - Easy step-by-step process for managing pronunciations  
🗂️ **SSML Integration** - Generate SSML markup for Azure TTS or ElevenLabs-compatible text

## Installation

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements_phonetic.txt
   ```

2. **Set up Azure Speech Services:**
   - Get an Azure Speech Services API key and region
   - Copy `config/config.sample.yaml` to `config/config.yaml`
   - Fill in your Azure credentials:
     ```yaml
     azure:
       api_key: "your_azure_api_key"
       region: "your_azure_region"  # e.g., "westus"
       voice_name: "en-US-JennyNeural"
     ```

3. **Ensure you have a microphone** connected to your system

## Usage

### Interactive Mode (Recommended)
```bash
python -m texttospeech.cli.phonetics_cli --interactive
```

This launches a menu-driven interface where you can:
1. Record new word pronunciations
2. List existing pronunciations  
3. Remove pronunciations
4. Test pronunciation playback
5. Add manual pronunciations

### Command Line Mode

**Record a specific word:**
```bash
python -m texttospeech.cli.phonetics_cli --record tomato
```

**List all pronunciations:**
```bash
python -m texttospeech.cli.phonetics_cli --list
```

**Test a pronunciation:**
```bash
python -m texttospeech.cli.phonetics_cli --test tomato
```

**Remove a pronunciation:**
```bash
python -m texttospeech.cli.phonetics_cli --remove tomato
```

**Show help:**
```bash
python -m texttospeech.cli.phonetics_cli --help
```

## Recording Workflow

When you record a word, the system follows this workflow:

1. **Enter the word** to record
2. **Check existing** - If the word exists, ask if you want to overwrite
3. **Record audio** - 3-second countdown, then record your pronunciation
4. **Extract phonetics** - Azure Speech Recognition converts audio to phonetic notation
5. **Review & edit** - View the generated phonetics and optionally edit them
6. **Test playback** - Hear how the phonetics sound using Azure TTS
7. **Save decision** - Choose whether to save the pronunciation to your database

## Output

The tool creates:
- **`phonetic_lookup.json`** - Your custom phonetic pronunciation database
- **Temporary audio files** - Automatically cleaned up after processing

## Phonetic Database Format

The database stores pronunciations in JSON format:

```json
{
  "tomato": {
    "word": "tomato",
    "phonetic": "təˈmeɪtoʊ",
    "source": "recorded",
    "confidence": 1.0,
    "created_date": "2025-08-25T10:30:00"
  }
}
```

## Integration with TTS Systems

### Azure TTS (SSML)
```python
from texttospeech.phonetics.manager import PhoneticLookupManager

manager = PhoneticLookupManager()
text = "I like tomato soup"
ssml_text = manager.apply_to_text_azure(text)
# Result: <speak version="1.0"...><phoneme alphabet="ipa" ph="təˈmeɪtoʊ">tomato</phoneme>...</speak>
```

### ElevenLabs
```python
text = "I like tomato soup"
elevenlabs_text = manager.apply_to_text_elevenlabs(text)
# Result: "I like tomato (təˈmeɪtoʊ) soup"
```

## Dependencies

- **azure-cognitiveservices-speech** - Azure Speech Services SDK
- **sounddevice** - Audio recording capabilities
- **soundfile** - Audio file handling
- **PyYAML** - Configuration file parsing

## Troubleshooting

**Import errors:** Install dependencies with `pip install -r requirements_phonetic.txt`

**Audio recording issues:** 
- Check microphone permissions
- Ensure microphone is connected and working
- Try adjusting microphone volume

**Azure authentication errors:**
- Verify your API key and region in `config/config.yaml`
- Check your Azure subscription status
- Ensure the Speech Services resource is active

**No sound during playback:**
- Check system audio output
- Verify speakers/headphones are connected
- Try adjusting system volume

## Examples

### Recording "Worcestershire"
```bash
python -m texttospeech.cli.phonetics_cli --record worcestershire
```
1. System prompts you to record
2. You pronounce "Worcestershire"
3. Azure recognizes it and generates: `wʊstərʃər`
4. You can edit to: `ˈwʊstər.ʃər` 
5. System plays back the pronunciation
6. You save it to the database

### Batch Processing
For multiple words, use interactive mode:
```bash
python -m texttospeech.cli.phonetics_cli --interactive
```
Then select option 1 repeatedly for each word.

## License

This tool is part of the TextToSpeech project. See LICENSE file for details.
