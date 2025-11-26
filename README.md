# Multi-Backend Text-to-Speech Generator

A flexible Python application and library that converts text in different formats to speech using multiple TTS backends. The application features:

- **Markdown to Speech**: Process markdown documents with a custom dialect that maps sections to separate audio files
- **PowerPoint to Speech**: Extract PowerPoint notes, convert them to Markdown, and then to speech
- **Multiple TTS Backends**: Support for both ElevenLabs and Azure Speech Services
- **Phonetics**: If words are not pronounced correctly phonetics can be generated based on voice recording or description via LLM 

## Setup

## Quick Start

Automatic setup:

```powershell
.\build.bat
```

or manually:

```powershell
python -m venv venv
venv\Scripts\Activate
python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install -e ".[dev]"  # optional
copy config\config.sample.yaml config\config.yaml
tts --help
phonetics --help
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
tts
```

The application supports several command-line options:

1. **Select TTS service**:

   ```
   tts --service elevenlabs  # Use ElevenLabs TTS
   tts --service azure       # Use Azure Speech Service
   ```

2. **Process PowerPoint files**:

   ```
   tts --ppt "path/to/presentation.pptx" "VoiceName"
   ```

   You can also use these additional options:

   ```
   tts --ppt "path/to/presentation.pptx" --no-titles        # Skip slide titles in section headers
   tts --ppt "path/to/presentation.pptx" --overwrite-script  # Regenerate the Markdown script
   tts --ppt "path/to/presentation.pptx" --overwrite-audio   # Regenerate all audio files
   tts --service azure --ppt "path/to/presentation.pptx"     # Process with Azure TTS
   ```

   **Note**: By default, the application:
   - Uses existing Markdown script if available
   - Only generates audio files that don't already exist
   - This allows you to delete specific audio files to regenerate only those, while keeping others

3. **Process Markdown files directly**:

   ```
   tts --md "path/to/document.md" "VoiceName"
   ```

   You can also use these additional options:

   ```
   tts --md "path/to/document.md" --overwrite-audio   # Regenerate all audio files
   tts --md "path/to/document.md" --output-dir ./output  # Specify output directory
   tts --service azure --md "path/to/document.md"     # Process with Azure TTS
   ```

   This allows you to directly convert Markdown files to speech without going through PowerPoint first.

4. **Test multiple voices with the same text**:

   ```
   tts --test-voices "text_file.txt" "voice_list_file.txt"
   ```

   This command reads text from a file and processes it with multiple voices listed in another file.
   
   You can also specify an output directory:

   ```
   tts --test-voices "text_file.txt" "voice_list_file.txt" --output-dir ./voice_samples
   ```

   The voice list file should contain one voice ID per line. Lines can include comments starting with `#`:

   ```
   en-US-JennyNeural # American female voice
   en-GB-SoniaNeural # British female voice
   # This line is a comment and will be ignored
   en-AU-NatashaNeural # Australian female voice
   ```

   This is useful for comparing how different voices sound when reading the same text.

5. **Export voices in a concise format**:

   ```
   tts --voices-short "output_filename.txt"
   ```

   If no filename is provided, it defaults to "voices_short.txt":

   ```
   tts --voices-short
   ```

   This exports all available voices in a concise format (one line per voice):

   ```
   voice-id # category, locale, gender
   ```

   The output of this command can be used as input for the `--test-voices` command.

6. **Save detailed voice information to a file**:

   ```
   tts --voices "output_filename.txt"
   ```

   If no filename is provided, it defaults to "voices.txt":

   ```
   tts --voices
   ```

7. **Display usage information**:

   ```
   tts --help
   ```

   This will display usage information and examples for all available commands.

8. **Run in interactive mode**:

   ```
   tts
   ```

   This will display usage information and prompt to continue to interactive mode.

This will fetch and display a list of all available voices from the ElevenLabs API.



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

### Markdown Processing for sectioned text

The application supports a custom Markdown format that allows you to define sections that should be saved as separate audio files, with flexible voice switching and automatic file name generation.

#### Basic Example (Automatic file naming)

```markdown
# My Audiobook

## Introduction

[voice:Aria]
This is the introduction to my audiobook.
It will be saved as 'introduction.mp3' and narrated by Aria.

## Chapter 1: The Beginning

[voice:Aria]
This is the first chapter of my audiobook.
It will be saved as 'chapter_1_the_beginning.mp3' and narrated by Aria.

## Chapter 2: The Adventure

[voice:Brian]
This is the second chapter of my audiobook.
It will be saved as 'chapter_2_the_adventure.mp3' and narrated by Brian.

## Chapter 3: The Conclusion

[voice:Brian]
This is the third chapter of my audiobook.
The filename will be automatically generated as 'chapter_3_the_conclusion.mp3'.

# Advanced Topics

## Machine Learning

[voice:Aria]
This section will have an automatically generated filename based on the section hierarchy.
The filename will be 'advanced_topics_machine_learning.mp3'.
```

> **Note**: The legacy syntax with voice annotations in section headers (`## Section {voice=VoiceName}`) is no longer supported. Please use the inline voice switching syntax with `[voice:VoiceName]` tags instead.

#### Advanced: Inline Voice Switching with Aliases

You can now switch voices within a section using `[voice:AliasOrVoiceName]` tags, and define aliases at the top of your markdown for easy voice management.

**Example:**

```markdown
# Title

[alias:John=Aria]
[alias:Jane=Sarah]

## Slide 1

[voice:John]
This is John's part.

[voice:Jane]
Now Jane speaks.

[voice:Aria]
Now John speaks as well, only not using the alias.
```

- **Alias definitions** (`[alias:John=Aria]`) must appear before the first section header.
- **Voice switching** is done inline with `[voice:Alias]` or `[voice:VoiceName]` tags.
- Only text within sections (after a header like `## Slide 1`) is spoken.
- Each section's audio is generated by concatenating the segments with different voices in the order they appear.

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
  - Example: `# Chapter 1` → `chapter_1.mp3` (numbers are preserved in filenames)
  - Example: `# Section 2.3: Advanced Topics` → `section_2_3_advanced_topics.mp3`


This will:

1. Parse the Markdown document
2. Extract sections with file annotations
3. Generate audio for each section
4. Save the audio files to the specified paths

## Architecture and Project Structure

High-level architecture: [docs/architecture.md](docs/architecture.md)

Key modules:
- modalitt to speech conversion: [ModalityToSpeech](src/texttospeech/processing/modality_to_speech.py:18)
- Markdown parser: [process_markdown](src/texttospeech/processing/markdown_parser.py:1)
- Azure TTS client: [AzureTTS](src/texttospeech/tts/azure.py:1)
- ElevenLabs TTS client: [ElevenLabsTTS](src/texttospeech/tts/elevenlabs.py:1)

For install/build details: [.github/instructions/install_and_build.instructions.md](.github/instructions/install_and_build.instructions.md)
For coding guidance: [.github/instructions/code.instructions.md](.github/instructions/code.instructions.md)

## License

MIT License. See [LICENSE](LICENSE).

## Future Enhancements

This implementation includes support for ElevenLabs and Azure TTS backends, but may be extended with:

- LLM integration to rewrite text for optimal speech creation
- Additional TTS backends (Google Cloud TTS, Amazon Polly, etc.)
- Voice customization and fine-tuning
- Batch processing for multiple files
## Timed cues and scheduled starts

The markdown dialect supports scheduled start times for narration to align audio with external timelines (e.g., video). This includes explicit tags and bare timestamp lines, a section-level clock reset, and a default overflow policy.

Accepted syntax
- Explicit tag: [start:MM:SS(.mmm)] or [start:Ns] schedules the next text block (until the next blank line).
- Bare timestamp line: a line containing “MM:SS(.mmm)” or “Ns” acts identically to [start:…] for the following paragraph.
- Reset: [timestamp_reset] resets the section’s clock to 0. The clock also resets implicitly at the start of each file and at every “## …” section.

Overflow policy (default: skip)
- If a synthesized clip would overlap a later requested start, skip the intervening text until encountering a cue with a start strictly after the current end.
- Non‑monotonic cues (start ≤ current clock) are ignored under skip policy.

Example (bare timestamps)
```markdown
# Chapter 1

[alias:Narrator=en-US-JennyNeural]

## Introduction

[voice:Narrator]

0:04
In today's interventional lab, clinicians face growing complexity, staff shortages, and the constant pressure to deliver more without compromise.

0:16
Our customers tell us they need technology that truly helps making procedures safer, faster, and more consistent while reducing administrative burden.
```

Equivalent example (explicit tags)
```markdown
## Introduction

[voice:Narrator]

[start:0:04]
In today's interventional lab, clinicians face growing complexity, staff shortages, and the constant pressure to deliver more without compromise.

[start:16s]
Our customers tell us they need technology that truly helps making procedures safer, faster, and more consistent while reducing administrative burden.
```

Renderer implications
- Clips are pre‑synthesized to obtain actual durations, then scheduled against the section clock.
- When desired_start > current_end, silence is inserted for desired_start − current_end before placing the clip.
- Untimed text before any cue renders sequentially; after the first cue, untimed text may be skipped when overflow skip applies.

References
- Parser (tags and bare timestamp lines): [python.MarkdownParser.split_into_voice_segments()](src/texttospeech/processing/markdown_parser.py:96)
- Section parsing and alias handling: [python.MarkdownParser.parse()](src/texttospeech/processing/markdown_parser.py:182)
- Scheduler and overflow skip behavior: [python.ModalityToSpeech.process_markdown_document()](src/texttospeech/processing/modality_to_speech.py:34)
- Full spec and authoring guidelines: [markdown.enhanced_markdown.md](docs/enhanced_markdown.md:49)