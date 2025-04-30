"""
Text-to-Speech API Demo

This script demonstrates how to use various TTS APIs to fetch available voices
and process PowerPoint presentations for text-to-speech conversion.
"""

import os
import sys
import yaml
from modality_to_speech import ModalityToSpeech


def load_config(config_path="config.yaml"):
    """
    Load configuration from a YAML file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: The configuration data.
    """
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def display_voice_info(voice):
    """
    Display information about a voice.

    Args:
        voice: The voice object to display information for.
    """
    print(f"Voice ID: {voice.voice_id}")
    print(f"Name: {voice.name}")
    print(f"Category: {getattr(voice, 'category', 'N/A')}")
    
    # Get description safely, handling None values
    description = getattr(voice, 'description', None)
    print(f"Description: {description if description else 'N/A'}")
    
    # Display labels if available
    if hasattr(voice, 'labels') and voice.labels:
        print("Labels:")
        for key, value in voice.labels.items():
            print(f"  - {key}: {value}")
    
    print("-" * 50)


def format_voice_info(voice):
    """
    Format voice information as a string.

    Args:
        voice: The voice object to format information for.

    Returns:
        str: Formatted voice information.
    """
    lines = []
    lines.append(f"Voice ID: {voice.voice_id}")
    lines.append(f"Name: {voice.name}")
    lines.append(f"Category: {getattr(voice, 'category', 'N/A')}")
    
    # Get description safely, handling None values
    description = getattr(voice, 'description', None)
    lines.append(f"Description: {description if description else 'N/A'}")
    
    # Format labels if available
    if hasattr(voice, 'labels') and voice.labels:
        lines.append("Labels:")
        for key, value in voice.labels.items():
            lines.append(f"  - {key}: {value}")
    
    lines.append("-" * 50)
    return "\n".join(lines)


def save_voices_to_file(tts_client, output_file="voices.txt"):
    """
    Save all available voices to a text file.
    
    Args:
        tts_client (TTSInterface): The TTS client.
        output_file (str, optional): Path to the output file. Defaults to "voices.txt".
    """
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


def process_powerpoint_demo(modality_processor, ppt_path=None, voice_name=None, include_slide_titles=True,
                          overwrite_script=False, overwrite_audio=False, output_format=None):
    """
    Demonstrate PowerPoint processing functionality.
    
    Args:
        modality_processor (ModalityToSpeech): The modality processor.
        ppt_path (str, optional): Path to the PowerPoint file. If None, user will be prompted.
        voice_name (str, optional): Name of the voice to use. If None, the default voice from config will be used.
        include_slide_titles (bool, optional): Whether to include slide titles in section headers.
                                             Defaults to True.
        overwrite_script (bool, optional): Whether to overwrite the existing Markdown script.
                                         Defaults to False.
        overwrite_audio (bool, optional): Whether to overwrite existing audio files.
                                        Defaults to False.
        output_format (str, optional): The output format to use. If None, the format from config will be used.
    """
    # If no PowerPoint path provided, prompt the user
    if not ppt_path:
        print("\nPowerPoint Processing Demo")
        print("=========================")
        print("Enter the path to a PowerPoint file (or press Enter to use the default test file):")
        user_input = input("> ").strip()
        
        if user_input:
            ppt_path = user_input
        else:
            ppt_path = "Input/Interesting presentation.pptx"
            print(f"Using default test file: {ppt_path}")
    
    # Check if the file exists
    if not os.path.exists(ppt_path):
        print(f"Error: File not found: {ppt_path}")
        return
    
    print(f"\nProcessing PowerPoint: {ppt_path}")
    print(f"Using voice: {voice_name}")
    print("Output directory will be created as a subdirectory of the PowerPoint location")
    
    # Process the PowerPoint presentation
    results = modality_processor.process_powerpoint(
        ppt_path=ppt_path,
        default_voice_name=voice_name,
        include_empty_notes=True,  # Include slides with empty notes
        include_slide_titles=include_slide_titles,
        overwrite_script=overwrite_script,
        overwrite_audio=overwrite_audio,
        output_format=output_format
    )
    
    # Check results
    if results:
        print("\nPowerPoint processing completed.")
        print("Generated audio files:")
        for file_path, success in results.items():
            status = "Success" if success else "Failed"
            print(f"  - {file_path}: {status}")
    else:
        print("PowerPoint processing failed.")


def display_usage():
    """
    Display usage information and examples for the command-line arguments.
    """
    print("Text-to-Speech API Demo")
    print("========================\n")
    print("Usage: python main.py [options]\n")
    
    print("Available options:")
    print("  --help, -h                  Display this help message")
    print("  --service [name]            Select TTS service (elevenlabs, azure)")
    print("  --voices [filename]         Save all available voices to a file (default: voices.txt)")
    print("  --ppt [path] [voice]        Process a PowerPoint file with the specified voice")
    print("  --no-titles                 Skip slide titles in section headers (use with --ppt)")
    print("  --overwrite-script          Overwrite existing Markdown script (use with --ppt)")
    print("  --overwrite-audio           Overwrite existing audio files (use with --ppt)")
    print("  (no arguments)              Interactive mode: Display voices and prompt for actions\n")
    
    print("Examples:")
    print("  python main.py --help                   Display this help message")
    print("  python main.py --service azure          Use Azure TTS service")
    print("  python main.py --service elevenlabs     Use ElevenLabs TTS service")
    print("  python main.py --voices                 Save voices to voices.txt")
    print("  python main.py --voices custom.txt      Save voices to custom.txt")
    print("  python main.py --ppt                    Process a PowerPoint file (will prompt for path)")
    print("  python main.py --ppt presentation.pptx  Process the specified PowerPoint file")
    print("  python main.py --ppt presentation.pptx CustomVoice  Process with a custom voice")
    print("  python main.py --ppt presentation.pptx --no-titles  Process without slide titles")
    print("  python main.py --ppt presentation.pptx --overwrite-script  Regenerate the Markdown script")
    print("  python main.py --ppt presentation.pptx --overwrite-audio   Regenerate the audio files")
    print("  python main.py --service azure --ppt presentation.pptx  Process with Azure TTS")
    print("  python main.py                          Run in interactive mode\n")


def main():
    """
    Main function to demonstrate the Text-to-Speech API.
    """
    # Load configuration
    config = load_config()
    
    # Get the TTS service from config or default to elevenlabs
    tts_service = config.get("tts_service", "elevenlabs")
    
    # Check for service override in command line
    if len(sys.argv) > 2 and sys.argv[1] == "--service":
        tts_service = sys.argv[2]
        # Remove the service arguments for further processing
        sys.argv = [sys.argv[0]] + sys.argv[3:]
    
    # Get output settings
    output_config = config.get("output", {})
    output_format = output_config.get("format", "mp3")
    output_quality = output_config.get("quality", "high")
    
    # Map quality to specific format parameters for ElevenLabs
    if output_format.lower() == "mp3":
        if output_quality == "high":
            elevenlabs_format = "mp3_44100_128"
        elif output_quality == "medium":
            elevenlabs_format = "mp3_44100_64"
        else:  # low
            elevenlabs_format = "mp3_44100_32"
    else:
        # Default to high quality MP3
        elevenlabs_format = "mp3_44100_128"
    
    # Initialize the appropriate TTS client
    if tts_service.lower() == "azure":
        from tts_azure import AzureTTS
        azure_config = config.get("azure", {})
        api_key = azure_config.get("api_key")
        region = azure_config.get("region")
        voice_name = azure_config.get("voice_name")
        
        if not api_key or not region:
            print("Please set your Azure API key and region in config.yaml")
            return
            
        if not voice_name:
            print("Please set a default voice_name in the azure section of config.yaml")
            return
        
        # Map output format and quality to Azure format
        if output_format.lower() == "mp3":
            if output_quality == "high":
                azure_format = "audio-24khz-160kbitrate-mono-mp3"
            elif output_quality == "medium":
                azure_format = "audio-24khz-96kbitrate-mono-mp3"
            else:  # low
                azure_format = "audio-24khz-48kbitrate-mono-mp3"
        elif output_format.lower() == "wav":
            azure_format = "riff-24khz-16bit-mono-pcm"
        elif output_format.lower() == "ogg":
            azure_format = "ogg-24khz-16bit-mono-opus"
        elif output_format.lower() == "webm":
            azure_format = "webm-24khz-16bit-mono-opus"
        else:
            # Default to high quality MP3
            azure_format = "audio-24khz-160kbitrate-mono-mp3"
            
        tts_client = AzureTTS(api_key=api_key, region=region, voice_name=voice_name)
        print(f"Using Azure TTS service with voice: {voice_name}")
        print(f"Output format: {output_format}, quality: {output_quality}")
        default_voice = voice_name
    else:
        # Default to ElevenLabs
        from tts_elevenlabs import ElevenLabsTTS
        elevenlabs_config = config.get("elevenlabs", {})
        api_key = elevenlabs_config.get("api_key")
        voice_name = elevenlabs_config.get("voice_name")
        model_id = elevenlabs_config.get("model_id", "eleven_monolingual_v1")
        
        if not api_key or api_key == "your_api_key_here":
            print("Please set your ElevenLabs API key in config.yaml")
            return
            
        if not voice_name:
            print("Please set a default voice_name in the elevenlabs section of config.yaml")
            return
            
        tts_client = ElevenLabsTTS(api_key=api_key, model_id=model_id)
        print(f"Using ElevenLabs TTS service with voice: {voice_name}, model: {model_id}")
        print(f"Output format: {output_format}, quality: {output_quality}")
        default_voice = voice_name
    
    # Initialize the modality processor
    modality_processor = ModalityToSpeech(tts_client)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            # Display usage information
            display_usage()
            return
        elif sys.argv[1] == "--ppt" or sys.argv[1] == "--powerpoint":
            # PowerPoint processing mode
            ppt_path = None
            voice_name = default_voice
            include_slide_titles = True
            overwrite_script = False
            overwrite_audio = False
            
            # Parse arguments
            arg_index = 2
            while arg_index < len(sys.argv):
                if sys.argv[arg_index] == "--no-titles":
                    include_slide_titles = False
                elif sys.argv[arg_index] == "--overwrite-script":
                    overwrite_script = True
                elif sys.argv[arg_index] == "--overwrite-audio":
                    overwrite_audio = True
                elif ppt_path is None and not sys.argv[arg_index].startswith("--"):
                    ppt_path = sys.argv[arg_index]
                elif voice_name == default_voice and not sys.argv[arg_index].startswith("--"):
                    voice_name = sys.argv[arg_index]
                arg_index += 1
            
            # Process the PowerPoint
            # For Azure, use azure_format; for ElevenLabs, use elevenlabs_format
            output_fmt = azure_format if tts_service.lower() == "azure" else elevenlabs_format
            process_powerpoint_demo(
                modality_processor, 
                ppt_path, 
                voice_name, 
                include_slide_titles,
                overwrite_script,
                overwrite_audio,
                output_fmt
            )
            return
        elif sys.argv[1] == "--voices" or sys.argv[1] == "--list-voices":
            # List voices mode
            output_file = sys.argv[2] if len(sys.argv) > 2 else "voices.txt"
            save_voices_to_file(tts_client, output_file)
            return
        else:
            # Unknown argument
            print(f"Unknown argument: {sys.argv[1]}")
            display_usage()
            return
    else:
        # No arguments provided, display usage information
        display_usage()
        
        # Ask if user wants to continue to interactive mode
        print("Would you like to continue to interactive mode? (y/n)")
        user_input = input("> ").strip().lower()
        
        if user_input != "y" and user_input != "yes":
            return
    
    # Interactive mode: Fetch and display voices
    print("\nFetching available voices...")
    response = tts_client.get_voices()
    
    if not response or not hasattr(response, 'voices'):
        print("No voices found or error occurred.")
        return
    
    voices = response.voices
    print(f"\nFound {len(voices)} voices:\n")
    
    for voice in voices:
        display_voice_info(voice)
    
    # Ask if user wants to process a PowerPoint
    print("\nWould you like to process a PowerPoint presentation? (y/n)")
    user_input = input("> ").strip().lower()
    
    if user_input == "y" or user_input == "yes":
        # For Azure, use azure_format; for ElevenLabs, use elevenlabs_format
        output_fmt = azure_format if tts_service.lower() == "azure" else elevenlabs_format
        process_powerpoint_demo(modality_processor, output_format=output_fmt)


if __name__ == "__main__":
    main()
