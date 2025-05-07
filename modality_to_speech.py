"""
Modality to Speech Module

This module provides functionality to convert different modalities (Markdown, PowerPoint)
to speech using a TTS implementation.
"""

import os
import tempfile
import numpy as np
import soundfile as sf
from typing import Dict, Optional, Any, List
from markdown_parser import process_markdown, MarkdownSection, VoiceSegment
from ppt_processor import PowerPointProcessor
from tts_interface import TTSInterface

class ModalityToSpeech:
    """
    Converts different modalities (Markdown, PowerPoint) to speech.
    """

    def __init__(self, tts_client: TTSInterface):
        """
        Initialize with a TTS client.

        Args:
            tts_client (TTSInterface): The TTS client to use for speech generation.
        """
        self.tts_client = tts_client

    def process_markdown_document(self, markdown_text: str, default_voice_name: str, output_dir: str = "output",
                                 output_format: str = "mp3_44100_128", overwrite_audio: bool = False) -> Dict[str, bool]:
        """
        Process a Markdown document with alias and inline voice tags and generate audio files.

        Args:
            markdown_text (str): The Markdown document text.
            default_voice_name (str): The default voice to use if no voice is specified.
            output_dir (str, optional): The directory where audio files will be saved if paths are relative.
                                       Defaults to "output".
            output_format (str, optional): The audio format to use.
                                          Defaults to "mp3_44100_128".
            overwrite_audio (bool, optional): Whether to overwrite existing audio files.
                                            Defaults to False.

        Returns:
            Dict[str, bool]: A dictionary mapping file paths to success status.
        """
        try:
            # Parse the Markdown document
            aliases, sections = process_markdown(markdown_text)

            if not sections:
                print("No sections with voice segments found in the document.")
                return {}

            os.makedirs(output_dir, exist_ok=True)
            results = {}

            for i, section in enumerate(sections):
                print(f"\nProcessing section {i+1}/{len(sections)}: {section.title}")

                # Determine the output path
                if os.path.isabs(section.file_path):
                    output_path = section.file_path
                else:
                    output_path = os.path.join(output_dir, section.file_path)

                # Check if the audio file exists and should be skipped
                if not overwrite_audio and os.path.exists(output_path):
                    print(f"Audio file already exists: {output_path}")
                    print("Skipping generation. Use --overwrite-audio to regenerate.")
                    results[output_path] = True
                    continue

                # Synthesize each segment and collect temp file paths
                temp_files = []
                segment_success = []
                for j, segment in enumerate(section.segments):
                    if not segment.text.strip():
                        continue
                    # Use the segment's voice, or fallback to default
                    voice_name = segment.voice or default_voice_name
                    
                    
                    # Create a temp file for this segment
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                        temp_path = tf.name
                    success = self.tts_client.text_to_speech(
                        text=segment.text,
                        voice_name=voice_name,
                        output_path=temp_path,
                        output_format=output_format
                    )
                    segment_success.append(success)
                    if success:
                        temp_files.append(temp_path)
                    else:
                        print(f"Failed to synthesize segment {j+1} in section '{section.title}' with voice '{voice_name}'.")

                # Concatenate all temp files into the final output
                if all(segment_success) and temp_files:
                    try:
                        # Concatenate audio files using soundfile and numpy
                        audio_data = []
                        sample_rate = None
                        
                        # Read all audio files
                        for temp_path in temp_files:
                            data, rate = sf.read(temp_path)
                            if sample_rate is None:
                                sample_rate = rate
                            elif rate != sample_rate:
                                print(f"Warning: Sample rate mismatch in {temp_path}. Expected {sample_rate}, got {rate}")
                            audio_data.append(data)
                        
                        # Concatenate audio data
                        if audio_data:
                            combined_audio = np.concatenate(audio_data)
                            
                            # Create output directory if it doesn't exist
                            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                            
                            # Write the combined audio to the output file
                            sf.write(output_path, combined_audio, sample_rate)
                            print(f"Section audio saved to: {output_path}")
                            results[output_path] = True
                        else:
                            print(f"No audio data to concatenate for section '{section.title}'")
                            results[output_path] = False
                    except Exception as e:
                        print(f"Error concatenating audio for section '{section.title}': {e}")
                        results[output_path] = False
                    finally:
                        # Clean up temp files
                        for temp_path in temp_files:
                            try:
                                os.remove(temp_path)
                            except Exception:
                                pass
                else:
                    print(f"Section '{section.title}' failed: not all segments could be synthesized.")
                    results[output_path] = False
                    # Clean up any temp files
                    for temp_path in temp_files:
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass

            # Print summary
            successful = sum(1 for success in results.values() if success)
            print(f"\nProcessed {len(results)} sections: {successful} successful, {len(results) - successful} failed.")

            return results
        except Exception as e:
            print(f"Error processing Markdown document: {e}")
            return {}

    def process_powerpoint(self, ppt_path: str, default_voice_name: str,
                          include_empty_notes: bool = False, include_slide_titles: bool = True,
                          overwrite_script: bool = False, overwrite_audio: bool = False,
                          output_format: str = "mp3_44100_128") -> Dict[str, bool]:
        """
        Process a PowerPoint presentation and convert its notes to speech.

        The output directory is created as a subdirectory of where the input PowerPoint is located.
        The subdirectory name is the sanitized version (spaces to underscores) of the PowerPoint filename.

        Args:
            ppt_path (str): The path to the PowerPoint file.
            default_voice_name (str): The default voice to use.
            include_empty_notes (bool, optional): Whether to include slides with empty notes.
                                                Defaults to False.
            include_slide_titles (bool, optional): Whether to include slide titles in section headers.
                                                 Defaults to True.
            overwrite_script (bool, optional): Whether to overwrite the existing Markdown script.
                                             Defaults to False.
            overwrite_audio (bool, optional): Whether to overwrite existing audio files.
                                            Defaults to False.
            output_format (str, optional): The audio format to use.
                                          Defaults to "mp3_44100_128".

        Returns:
            Dict[str, bool]: A dictionary mapping file paths to success status.
        """
        try:
            # Get the directory where the PowerPoint file is located
            ppt_dir = os.path.dirname(os.path.abspath(ppt_path))

            # Get the PowerPoint filename without extension
            ppt_filename = os.path.basename(ppt_path)
            ppt_name_without_ext = os.path.splitext(ppt_filename)[0]

            # Create sanitized directory name (spaces to underscores)
            sanitized_name = ppt_name_without_ext.replace(' ', '_')

            # Create output directory as subdirectory of PowerPoint location
            output_dir = os.path.join(ppt_dir, sanitized_name)
            os.makedirs(output_dir, exist_ok=True)

            # Define markdown file path
            markdown_path = os.path.join(output_dir, f"{sanitized_name}.md")

            # Check if markdown file already exists
            markdown_exists = os.path.exists(markdown_path)

            if not markdown_exists or overwrite_script:
                # Process PowerPoint to Markdown if it doesn't exist or overwrite_script is True
                ppt_processor = PowerPointProcessor()
                markdown_text = ppt_processor.process_presentation(
                    ppt_path=ppt_path,
                    default_voice_name=default_voice_name,
                    include_empty_notes=include_empty_notes,
                    include_slide_titles=include_slide_titles
                )

                if not markdown_text:
                    print("Failed to process PowerPoint file or no notes found.")
                    return {}

                # Save the Markdown file
                ppt_processor.save_markdown(markdown_text, markdown_path)
                if markdown_exists:
                    print(f"Markdown file overwritten: {markdown_path}")
                else:
                    print(f"Markdown file created: {markdown_path}")
            else:
                print(f"Using existing Markdown file: {markdown_path}")
                with open(markdown_path, 'r', encoding='utf-8') as f:
                    markdown_text = f.read()

            # Process the Markdown document
            return self.process_markdown_document(
                markdown_text=markdown_text,
                default_voice_name=default_voice_name,
                output_dir=output_dir,
                output_format=output_format,
                overwrite_audio=overwrite_audio
            )
        except Exception as e:
            print(f"Error processing PowerPoint file: {e}")
            return {}
