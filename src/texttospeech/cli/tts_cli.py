"""
TTS CLI (package entrypoint)

Usage via module:
  python -m texttospeech.cli.tts_cli [options]

This CLI wraps the TTS processing flows:
  - list/save voices
  - process Markdown
  - process PowerPoint
  - batch test voices

Canonical processing pipeline lives under:
  texttospeech.processing.modality_to_speech
"""

import os
import sys
import argparse
import yaml

from texttospeech.processing.modality_to_speech import ModalityToSpeech
from texttospeech.phonetics.processing import PhoneticProcessor
from texttospeech.tts.azure import AzureTTS
from texttospeech.tts.elevenlabs import ElevenLabsTTS


def load_config(config_path: str = "config/config.yaml") -> dict:
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def display_voice_info(voice) -> None:
    print(f"Voice ID: {voice.voice_id}")
    print(f"Name: {voice.name}")
    print(f"Category: {getattr(voice, 'category', 'N/A')}")
    description = getattr(voice, 'description', None)
    print(f"Description: {description if description else 'N/A'}")
    if hasattr(voice, 'labels') and voice.labels:
        print("Labels:")
        for key, value in voice.labels.items():
            print(f"  - {key}: {value}")
    print("-" * 50)


def format_voice_info(voice) -> str:
    lines = []
    lines.append(f"Voice ID: {voice.voice_id}")
    lines.append(f"Name: {voice.name}")
    lines.append(f"Category: {getattr(voice, 'category', 'N/A')}")
    description = getattr(voice, 'description', None)
    lines.append(f"Description: {description if description else 'N/A'}")
    if hasattr(voice, 'labels') and voice.labels:
        lines.append("Labels:")
        for key, value in voice.labels.items():
            lines.append(f"  - {key}: {value}")
    lines.append("-" * 50)
    return "\n".join(lines)


def save_voices_to_file(tts_client, output_file: str = "voices.txt") -> bool:
    print(f"Fetching available voices to save to {output_file}...")
    response = tts_client.get_voices()
    if not response or not hasattr(response, 'voices'):
        print("No voices found or error occurred.")
        return False
    voices = response.voices
    print(f"Found {len(voices)} voices.")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"TTS Voices ({len(voices)} total)\n")
            f.write("=" * 50 + "\n\n")
            for voice in voices:
                f.write(format_voice_info(voice) + "\n")
        print(f"Successfully saved {len(voices)} voices to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving voices to file: {e}")
        return False


def save_voices_to_file_short(tts_client, output_file: str = "voices_short.txt") -> bool:
    print(f"Fetching available voices to save to {output_file}...")
    response = tts_client.get_voices()
    if not response or not hasattr(response, 'voices'):
        print("No voices found or error occurred.")
        return False
    voices = response.voices
    print(f"Found {len(voices)} voices.")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for voice in voices:
                voice_id = voice.voice_id
                category = getattr(voice, 'category', 'N/A')
                locale = "Unknown"
                gender = "Unknown"
                if hasattr(voice, 'labels') and voice.labels:
                    locale = voice.labels.get('locale', locale)
                    gender = voice.labels.get('gender', gender)
                f.write(f"{voice_id} # {category}, {locale}, {gender}\n")
        print(f"Successfully saved {len(voices)} voices to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving voices to file: {e}")
        return False


def test_voices(tts_client, text_file: str, voice_list_file: str, output_dir: str = None, output_format: str = None):
    if not output_dir:
        output_dir = "voice_test"
    os.makedirs(output_dir, exist_ok=True)

    try:
        with open(text_file, 'r', encoding='utf-8') as f:
            text = f.read()
        print(f"Read text from {text_file} ({len(text)} characters)")
    except Exception as e:
        print(f"Error reading text file: {e}")
        return {}

    voice_ids = []
    try:
        with open(voice_list_file, 'r', encoding='utf-8') as f:
            for line in f:
                # Strip comments, whitespace, and any BOM characters on the first line
                line = line.split('#', 1)[0].strip()
                if line.startswith('\ufeff'):
                    line = line.lstrip('\ufeff')
                if line:
                    voice_ids.append(line)
        print(f"Found {len(voice_ids)} voices to test")
    except Exception as e:
        print(f"Error reading voice list file: {e}")
        return {}

    available_voices = {}
    try:
        response = tts_client.get_voices()
        if response and hasattr(response, 'voices'):
            for voice in response.voices:
                # Index by both display name and voice_id in lowercase for robust matching
                available_voices[voice.name.lower()] = voice.voice_id
                available_voices[getattr(voice, 'voice_id', voice.name).lower()] = voice.voice_id
        print(f"Retrieved {len(available_voices)} available voices")
    except Exception as e:
        print(f"Warning: Could not retrieve available voices: {e}")

    results = {}
    for voice_id in voice_ids:
        print(f"Processing voice: {voice_id}")
        key = voice_id.lower()
        if available_voices and key not in available_voices:
            print(f"Warning: Voice '{voice_id}' does not exist in the available voices. Skipping.")
            continue
        # Map to canonical voice_id if available
        resolved_voice_id = available_voices.get(key, voice_id)
        safe_filename = voice_id.replace('/', '_').replace('\\', '_').replace(':', '_')
        output_file = os.path.join(output_dir, f"voice_test_{safe_filename}.mp3")
        try:
            success = tts_client.text_to_speech( 
                text=text,
                voice_name=resolved_voice_id,
                output_path=output_file,
                output_format=output_format
            )
            results[output_file] = success
            if success:
                print(f"Successfully generated: {output_file}")
            else:
                print(f"Failed to generate: {output_file}")
        except Exception as e:
            print(f"Error generating speech for voice '{voice_id}': {e}")
            results[output_file] = False

    successful = sum(1 for success in results.values() if success)
    print(f"\nProcessed {len(results)} voices: {successful} successful, {len(results) - successful} failed.")
    return results


def process_markdown_demo(modality_processor: ModalityToSpeech, md_path: str = None, voice_name: str = None,
                          output_dir: str = None, overwrite_audio: bool = False, output_format: str = None,
                          auto_phonetics: bool = False) -> None:
    if not md_path:
        print("\nMarkdown Processing")
        print("===================")
        print("Enter the path to a Markdown file (or press Enter to cancel):")
        user_input = input("> ").strip()
        if not user_input:
            print("No file provided.")
            return
        md_path = user_input

    if not os.path.exists(md_path):
        print(f"Error: File not found: {md_path}")
        return

    if not output_dir:
        md_dir = os.path.dirname(os.path.abspath(md_path))
        md_filename = os.path.basename(md_path)
        md_name_without_ext = os.path.splitext(md_filename)[0]
        sanitized_name = md_name_without_ext.replace(' ', '_')
        output_dir = os.path.join(md_dir, sanitized_name)

    os.makedirs(output_dir, exist_ok=True)
    print(f"\nProcessing Markdown: {md_path}")
    print(f"Using voice: {voice_name}")
    print(f"Output directory: {output_dir}")

    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            markdown_text = f.read()
    except Exception as e:
        print(f"Error reading Markdown file: {e}")
        return

    # Apply automatic phonetic processing if enabled
    if auto_phonetics:
        print("Applying automatic phonetic detection...")
        markdown_text = modality_processor.apply_automatic_phonetics(markdown_text)

    results = modality_processor.process_markdown_document(
        markdown_text=markdown_text,
        default_voice_name=voice_name,
        output_dir=output_dir,
        output_format=output_format,
        overwrite_audio=overwrite_audio
    )

    if results:
        print("\nMarkdown processing completed.")
        print("Generated audio files:")
        for file_path, success in results.items():
            status = "Success" if success else "Failed"
            print(f"  - {file_path}: {status}")
    else:
        print("Markdown processing failed.")


def process_powerpoint_demo(modality_processor: ModalityToSpeech, ppt_path: str = None, voice_name: str = None,
                            include_slide_titles: bool = True, overwrite_script: bool = False,
                            overwrite_audio: bool = False, output_format: str = None) -> None:
    if not ppt_path:
        print("\nPowerPoint Processing")
        print("=====================")
        print("Enter the path to a PowerPoint file (or press Enter to cancel):")
        user_input = input("> ").strip()
        if not user_input:
            print("No file provided.")
            return
        ppt_path = user_input

    if not os.path.exists(ppt_path):
        print(f"Error: File not found: {ppt_path}")
        return

    print(f"\nProcessing PowerPoint: {ppt_path}")
    print(f"Using voice: {voice_name}")
    print("Output directory will be created as a subdirectory of the PowerPoint location")

    results = modality_processor.process_powerpoint(
        ppt_path=ppt_path,
        default_voice_name=voice_name,
        include_empty_notes=True,
        include_slide_titles=include_slide_titles,
        overwrite_script=overwrite_script,
        overwrite_audio=overwrite_audio,
        output_format=output_format
    )

    if results:
        print("\nPowerPoint processing completed.")
        print("Generated audio files:")
        for file_path, success in results.items():
            status = "Success" if success else "Failed"
            print(f"  - {file_path}: {status}")
    else:
        print("PowerPoint processing failed.")


def display_usage():
    print("Text-to-Speech CLI")
    print("==================\n")
    print("Usage: python -m texttospeech.cli.tts_cli [options]\n")
    print("Options:")
    print("  --help, -h                  Show this help")
    print("  --service NAME              Select TTS service (elevenlabs, azure)")
    print("  --voices [filename]         Save all available voices to a file (default: voices.txt)")
    print("  --voices-short [filename]   Save voices in concise format (default: voices_short.txt)")
    print("  --ppt PATH                  Process a PowerPoint file at PATH")
    print("  --md PATH                   Process a Markdown file at PATH")
    print("  --voice NAME                Override default voice name")
    print("  --auto-phonetics            Automatically detect and apply phonetic markup to text")
    print("  --no-titles                 Skip slide titles in PPT section headers")
    print("  --overwrite-script          Overwrite generated Markdown from PPT")
    print("  --overwrite-audio           Overwrite generated audio files")
    print("  --output-dir PATH           Output directory for Markdown processing or test voices")
    print("  --test-voices TEXT VOICES   Test multiple voices with input TEXT and VOICES list file")
    print("  --config, -c CONFIG_FILE    Path to configuration (default: config/config.yaml)\n")
    print("Examples:")
    print("  python -m texttospeech.cli.tts_cli --service azure --voices")
    print("  python -m texttospeech.cli.tts_cli --md ./doc.md --voice en-US-JennyNeural --overwrite-audio")
    print("  python -m texttospeech.cli.tts_cli --ppt ./slides.pptx --voice en-US-GuyNeural --no-titles")
    print("  python -m texttospeech.cli.tts_cli --test-voices ./text.txt ./voices_short.txt --output-dir ./voice_samples\n")


def main():
    parser = argparse.ArgumentParser(
        description="Text-to-Speech CLI (package)",
        add_help=False,
    )
    parser.add_argument("--service", choices=["elevenlabs", "azure"], help="Select TTS service")
    parser.add_argument("--voices", nargs="?", const="voices.txt", help="Save voices to file")
    parser.add_argument("--voices-short", dest="voices_short", nargs="?", const="voices_short.txt", help="Save voices to concise file")
    parser.add_argument("--ppt", metavar="PATH", help="Process a PowerPoint file")
    parser.add_argument("--md", metavar="PATH", help="Process a Markdown file")
    parser.add_argument("--voice", metavar="NAME", help="Override default voice name")
    parser.add_argument("--no-titles", action="store_true", help="Skip slide titles in PPT")
    parser.add_argument("--overwrite-script", action="store_true", help="Overwrite PPT-generated Markdown")
    parser.add_argument("--overwrite-audio", action="store_true", help="Overwrite audio files")
    parser.add_argument("--output-dir", metavar="PATH", help="Output directory")
    parser.add_argument("--test-voices", nargs=2, metavar=("TEXT_FILE", "VOICE_LIST_FILE"), help="Test multiple voices")
    parser.add_argument("--auto-phonetics", action="store_true", help="Automatically detect and apply phonetic markup")
    parser.add_argument("--config", "-c", default="config/config.yaml", help="Path to configuration file")
    parser.add_argument("--help", "-h", action="store_true", help="Show help")

    args = parser.parse_args()

    if args.help or (
        not args.voices and
        not args.voices_short and
        not args.ppt and
        not args.md and
        not args.test_voices
    ):
        display_usage()
        return

    # Load configuration
    config = load_config(args.config)

    # Determine service
    tts_service = config.get("tts_service", "elevenlabs")
    if args.service:
        tts_service = args.service

    # Output format mapping
    output_config = config.get("output", {})
    output_format = output_config.get("format", "mp3")
    output_quality = output_config.get("quality", "high")

    if output_format.lower() == "mp3":
        if output_quality == "high":
            elevenlabs_format = "mp3_44100_128"
        elif output_quality == "medium":
            elevenlabs_format = "mp3_44100_64"
        else:
            elevenlabs_format = "mp3_44100_32"
    else:
        elevenlabs_format = "mp3_44100_128"

    if output_format.lower() == "mp3":
        if output_quality == "high":
            azure_format = "audio-24khz-160kbitrate-mono-mp3"
        elif output_quality == "medium":
            azure_format = "audio-24khz-96kbitrate-mono-mp3"
        else:
            azure_format = "audio-24khz-48kbitrate-mono-mp3"
    elif output_format.lower() == "wav":
        azure_format = "riff-24khz-16bit-mono-pcm"
    elif output_format.lower() == "ogg":
        azure_format = "ogg-24khz-16bit-mono-opus"
    elif output_format.lower() == "webm":
        azure_format = "webm-24khz-16bit-mono-opus"
    else:
        azure_format = "audio-24khz-160kbitrate-mono-mp3"

    # Initialize TTS client and defaults
    if tts_service.lower() == "azure":
        azure_cfg = config.get("azure", {})
        api_key = azure_cfg.get("api_key")
        region = azure_cfg.get("region")

        # Fallback to environment variables if not set in config
        env_api_key = os.getenv("AZURE_SPEECH_KEY") or os.getenv("SPEECH_KEY") or os.getenv("AZURE_TTS_KEY")
        env_region = os.getenv("AZURE_SPEECH_REGION") or os.getenv("SPEECH_REGION") or os.getenv("AZURE_TTS_REGION")
        if not api_key:
            api_key = env_api_key
        if not region:
            region = env_region

        # Default voice is optional for listing voices; provide a sane default if unspecified
        default_voice = azure_cfg.get("voice_name") or "en-US-JennyNeural"

        # Validate credentials (avoid placeholder values)
        if (not api_key or not region or str(api_key).startswith("<") or str(region).startswith("<")):
            print("Azure credentials missing. Set azure.api_key and azure.region in config/config.yaml, or set "
                  "AZURE_SPEECH_KEY and AZURE_SPEECH_REGION environment variables.")
            return

        tts_client = AzureTTS(api_key=api_key, region=region, voice_name=default_voice)
        output_fmt = azure_format
    else:
        el_cfg = config.get("elevenlabs", {})
        api_key = el_cfg.get("api_key")
        default_voice = el_cfg.get("voice_name")
        model_id = el_cfg.get("model_id", "eleven_monolingual_v1")
        if not api_key or api_key == "your_api_key_here":
            print("Please set your ElevenLabs API key in config/config.yaml")
            return
        if not default_voice:
            print("Please set a default voice_name in the elevenlabs section of config/config.yaml")
            return
        tts_client = ElevenLabsTTS(api_key=api_key, model_id=model_id)
        output_fmt = elevenlabs_format

    # Voice override if provided
    voice_name = args.voice or default_voice

    # Create phonetic processor for the backend
    phonetic_processor = PhoneticProcessor(
        backend="azure" if isinstance(tts_client, AzureTTS) else "elevenlabs",
        voice_name=voice_name,
        accepts_ssml=True
    )

    # Create modality processor with phonetic support
    modality_processor = ModalityToSpeech(tts_client, phonetic_processor)

    # Handle actions
    if args.voices:
        save_voices_to_file(tts_client, args.voices)
        return

    if args.voices_short:
        save_voices_to_file_short(tts_client, args.voices_short)
        return

    if args.ppt:
        process_powerpoint_demo(
            modality_processor,
            ppt_path=args.ppt,
            voice_name=voice_name,
            include_slide_titles=not args.no_titles,
            overwrite_script=args.overwrite_script,
            overwrite_audio=args.overwrite_audio,
            output_format=output_fmt
        )
        return

    if args.md:
        process_markdown_demo(
            modality_processor,
            md_path=args.md,
            voice_name=voice_name,
            output_dir=args.output_dir,
            overwrite_audio=args.overwrite_audio,
            output_format=output_fmt,
            auto_phonetics=args.auto_phonetics
        )
        return

    if args.test_voices:
        text_file, voice_list_file = args.test_voices
        test_voices(
            tts_client,
            text_file,
            voice_list_file,
            args.output_dir,
            output_fmt
        )
        return

    # Fallback
    display_usage()


if __name__ == "__main__":
    main()
