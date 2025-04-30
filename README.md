# Multi-Backend Text-to-Speech Generator

A flexible application and library that converts text in different formats to speech using multiple TTS backends. The application features:

- **Multiple TTS Backends**: Support for both ElevenLabs and Azure Speech Services
- **Markdown to Speech**: Process markdown documents with a custom dialect that maps sections to separate audio files
- **PowerPoint to Speech**: Extract PowerPoint notes, convert them to Markdown, and then to speech
- **Configuration-Driven**: All settings controlled through a single YAML configuration file

## Setup

1. Create a virtual environment:
   ```
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - Windows:
     ```
     .venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Configure your TTS services:
   - Open `config.yaml`
   - Set your ElevenLabs API key and preferred voice
   - Set your Azure Speech Service API key, region, and preferred voice
   - Configure default output format and quality

## Usage

Run the application:
```
python main.py
```

This will fetch and display a list of all available voices from the ElevenLabs API.

## Project Structure

- `config.yaml`: Configuration file for all TTS services and output settings
- `tts_interface.py`: Interface that all TTS implementations must follow
- `tts_elevenlabs.py`: ElevenLabs implementation of the TTS interface
- `tts_azure.py`: Azure Speech Service implementation of the TTS interface
- `modality_to_speech.py`: Handles converting different modalities (Markdown, PowerPoint) to speech
- `markdown_parser.py`: Parser for Markdown documents with custom file annotations
- `ppt_processor.py`: Processor for PowerPoint presentations
- `main.py`: Main application with CLI interface
- `requirements.txt`: List of Python dependencies

## Features

### Multiple TTS Backends

The application supports multiple TTS backends through a common interface:

```python
# Using ElevenLabs
from tts_elevenlabs import ElevenLabsTTS
tts_client = ElevenLabsTTS(api_key="your_api_key", model_id="eleven_monolingual_v1")

# Using Azure
from tts_azure import AzureTTS
tts_client = AzureTTS(api_key="your_api_key", region="westus", voice_name="en-US-JennyNeural")

# Both implementations follow the same interface
voices = tts_client.get_voices()
for voice in voices.voices:
    print(f"Voice: {voice.name} (ID: {voice.voice_id})")
```

### Configuration-Driven Settings

All settings are controlled through the `config.yaml` file:

```yaml
# Select the default TTS service
tts_service: "elevenlabs"  # or "azure"

# ElevenLabs Configuration
elevenlabs:
  api_key: "your_api_key_here"
  voice_name: "Sarah"  # Default voice name
  model_id: "eleven_monolingual_v1"  # Model ID options

# Azure Speech Service Configuration
azure:
  api_key: "your_api_key_here"
  region: "westus"
  voice_name: "en-US-JennyNeural"

# Output Configuration
output:
  format: "mp3"  # mp3, wav, ogg, webm
  quality: "high"  # high, medium, low
```

### Text-to-Speech with Any Backend

```python
# Initialize the TTS client (either ElevenLabs or Azure)
from tts_elevenlabs import ElevenLabsTTS
tts_client = ElevenLabsTTS(api_key="your_api_key", model_id="eleven_monolingual_v1")

# Generate speech using the common interface
tts_client.text_to_speech(
    text="Hello, this is a test of the text-to-speech functionality.",
    voice_name="Sarah",
    output_path="output/speech.mp3",
    output_format="mp3_44100_128"  # Format depends on the backend
)
```

### PowerPoint Processing
The application can extract notes from PowerPoint presentations and convert them to speech using any TTS backend:

```python
# Initialize the TTS client (either ElevenLabs or Azure)
from tts_elevenlabs import ElevenLabsTTS
tts_client = ElevenLabsTTS(api_key="your_api_key", model_id="eleven_monolingual_v1")

# Initialize the modality processor with the TTS client
from modality_to_speech import ModalityToSpeech
modality_processor = ModalityToSpeech(tts_client)

# Process a PowerPoint presentation
modality_processor.process_powerpoint(
    ppt_path="presentation.pptx",
    default_voice_name="Sarah",
    include_empty_notes=False,  # Skip slides with no notes
    output_format="mp3_44100_128"  # Format depends on the backend
)
```

This will:
1. Create an output directory as a subdirectory of where the PowerPoint is located
   - The subdirectory name is the sanitized version (spaces to underscores) of the PowerPoint filename
2. Extract notes from each slide in the PowerPoint
3. Convert the presentation to a Markdown document where:
   - The main header (#) is the PowerPoint filename
   - Each subsection (##) includes the slide number and title (if available)
   - The default voice is added as an annotation to the first slide subsection
   - Text is sanitized to remove special characters and control characters
4. Save the Markdown file to the output directory (if it doesn't already exist)
5. Process the Markdown document to generate audio files
6. Save the audio files to the output directory

#### Command Line Usage

The application supports several command-line options:

1. **Select TTS service**:
   ```
   python main.py --service elevenlabs  # Use ElevenLabs TTS
   python main.py --service azure       # Use Azure Speech Service
   ```

2. **Process PowerPoint files**:
   ```
   python main.py --ppt "path/to/presentation.pptx" "VoiceName"
   ```
   
   You can also use these additional options:
   ```
   python main.py --ppt "path/to/presentation.pptx" --no-titles        # Skip slide titles in section headers
   python main.py --ppt "path/to/presentation.pptx" --overwrite-script  # Regenerate the Markdown script
   python main.py --ppt "path/to/presentation.pptx" --overwrite-audio   # Regenerate all audio files
   python main.py --service azure --ppt "path/to/presentation.pptx"     # Process with Azure TTS
   ```
   
   **Note**: By default, the application:
   - Uses existing Markdown script if available
   - Only generates audio files that don't already exist
   - This allows you to delete specific audio files to regenerate only those, while keeping others

2. **Save available voices to a file**:
   ```
   python main.py --voices "output_filename.txt"
   ```
   If no filename is provided, it defaults to "voices.txt":
   ```
   python main.py --voices
   ```

3. **Display usage information**:
   ```
   python main.py --help
   ```
   This will display usage information and examples for all available commands.

4. **Run in interactive mode**:
   ```
   python main.py
   ```
   This will display usage information and prompt to continue to interactive mode.

### Markdown Processing for Audiobooks
The application supports a custom Markdown format that allows you to define sections that should be saved as separate audio files, with optional voice selection and automatic file name generation:

```markdown
# My Audiobook

## Introduction {file=intro.mp3, voice=Aria}

This is the introduction to my audiobook.
It will be saved as intro.mp3 and narrated by Aria.

## Chapter 1: The Beginning {file=chapter1.mp3}

This is the first chapter of my audiobook.
It will be saved as chapter1.mp3 and inherit Aria's voice from the previous section.

## Chapter 2: The Adventure {file=chapter2.mp3 voice=Brian}

This is the second chapter of my audiobook.
It will be saved as chapter2.mp3 and narrated by Brian.

## Chapter 3: The Conclusion

This is the third chapter of my audiobook.
The filename will be automatically generated as 'my_audiobook_chapter_3_the_conclusion.mp3'.
It will inherit Brian's voice from the previous section.

# Advanced Topics

## Machine Learning

This section will have an automatically generated filename based on the section hierarchy.
The filename will be 'advanced_topics_machine_learning.mp3'.
```

To process this Markdown document:

```python
# Initialize the TTS client (either ElevenLabs or Azure)
from tts_elevenlabs import ElevenLabsTTS
tts_client = ElevenLabsTTS(api_key="your_api_key", model_id="eleven_monolingual_v1")

# Initialize the modality processor with the TTS client
from modality_to_speech import ModalityToSpeech
modality_processor = ModalityToSpeech(tts_client)

# Read the Markdown document
with open("audiobook.md", "r") as f:
    markdown_text = f.read()

# Process the document and generate audio files
modality_processor.process_markdown_document(
    markdown_text=markdown_text,
    default_voice_name="Sarah",  # Default voice if none specified
    output_dir="audiobook_output",
    output_format="mp3_44100_128"  # Format depends on the backend
)
```

#### Features

- **Per-section voice selection**: Specify a different voice for each section using the `voice=VoiceName` parameter
- **Voice inheritance**: If no voice is specified for a section, it inherits the voice from the previous section
- **Default voice**: The first section with no voice specified uses the default voice provided to the method
- **Automatic file name generation**: If no file name is specified, one is generated from the section hierarchy
  - Example: `# Section Name` → `section_name.mp3`
  - Example: `# Section Name` → `## Subsection Name` → `section_name_subsection_name.mp3`
- **Flexible syntax**: Parameters can be separated by spaces or commas: `{file=output.mp3, voice=Aria}` or `{file=output.mp3 voice=Aria}`

This will:
1. Parse the Markdown document
2. Extract sections with file annotations
3. Generate audio for each section
4. Save the audio files to the specified paths

#### Available Output Formats
- `mp3_44100_128` (default) - MP3 at 44.1kHz, 128kbps
- `mp3_44100_192` - MP3 at 44.1kHz, 192kbps (higher quality)
- `mp3_44100_64` - MP3 at 44.1kHz, 64kbps (smaller file size)
- `mp3_44100_32` - MP3 at 44.1kHz, 32kbps (smallest file size)
- `mp3_22050_32` - MP3 at 22.05kHz, 32kbps
- And various other formats including PCM, OPUS, etc.

## Future Enhancements

This implementation includes support for ElevenLabs and Azure TTS backends, but can be extended with:
- Additional TTS backends (Google Cloud TTS, Amazon Polly, etc.)
- Voice customization and fine-tuning
- Advanced audio settings (stability, clarity, etc.)
- Batch processing for multiple files
- Web-based user interface
- SSML support for more precise control over speech synthesis
