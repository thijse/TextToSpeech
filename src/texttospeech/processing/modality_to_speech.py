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
from .markdown_parser import process_markdown, MarkdownSection, VoiceSegment
from .ppt_processor import PowerPointProcessor
from ..tts.interface import TTSInterface
from ..phonetics.processing import PhoneticProcessor

class ModalityToSpeech:
    """
    Converts different modalities (Markdown, PowerPoint) to speech.
    """

    def __init__(self, tts_client: TTSInterface, phonetic_processor: Optional[PhoneticProcessor] = None):
        """
        Initialize with a TTS client.
 
        Args:
            tts_client (TTSInterface): The TTS client to use for speech generation.
        """
        self.tts_client = tts_client
        # Optional pass-through for future phonetic preprocessing (no behavior change yet)
        self.phonetic_processor = phonetic_processor

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
            # Parse the Markdown document with default voice fallback
            aliases, sections = process_markdown(markdown_text, default_voice_name)

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

                # Synthesize each segment and collect entries with timing metadata
                # Maintain index alignment with section.segments for scheduling later
                entries: List[Dict[str, Any]] = []
                for j, segment in enumerate(section.segments):
                    if not getattr(segment, "text", "").strip():
                        entries.append({"success": False, "temp_path": None, "start_ms": getattr(segment, "start_ms", None)})
                        continue

                    # Resolve voice per segment (fallback to default)
                    voice_name = getattr(segment, "voice", None) or default_voice_name

                    # Apply phonetic processing if available
                    text_to_speak = segment.text
                    is_ssml = False
                    if self.phonetic_processor:
                        try:
                            is_ssml, text_to_speak = self.phonetic_processor.preprocess_text(segment.text)
                            if is_ssml:
                                print(f"  Using phonetic SSML for: {segment.text[:30]}...")
                        except Exception as e:
                            print(f"  Warning: Phonetic processing failed for segment {j+1}: {e}")
                            # Fallback to original text
                            text_to_speak = segment.text
                            is_ssml = False

                    # Create temp file target
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tf:
                        temp_path = tf.name

                    ok = self.tts_client.text_to_speech(
                        text=text_to_speak,
                        voice_name=voice_name,
                        output_path=temp_path,
                        output_format=output_format,
                        is_ssml=is_ssml
                    )

                    if not ok:
                        print(f"Failed to synthesize segment {j+1} in section '{section.title}' with voice '{voice_name}'.")
                        # Clean up the failed temp file if created
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                        entries.append({"success": False, "temp_path": None, "start_ms": getattr(segment, "start_ms", None)})
                    else:
                        entries.append({"success": True, "temp_path": temp_path, "start_ms": getattr(segment, "start_ms", None)})

                # Read audio for successful entries and schedule with [start:...] cues (overflow policy = skip)
                try:
                    sample_rate = None
                    channels = None

                    # Load audio for each entry preserving index alignment
                    for idx, entry in enumerate(entries):
                        if not entry.get("success"):
                            entry["audio"] = None
                            continue
                        temp_path = entry["temp_path"]
                        try:
                            data, rate = sf.read(temp_path)
                            entry["audio"] = data
                            entry["rate"] = rate
                            if sample_rate is None:
                                sample_rate = rate
                                channels = data.shape[1] if hasattr(data, "ndim") and getattr(data, "ndim", 1) > 1 else (data.shape[1] if len(getattr(data, "shape", [])) > 1 else 1)
                            elif rate != sample_rate:
                                print(f"Warning: Sample rate mismatch in {temp_path}. Expected {sample_rate}, got {rate}")
                                # Proceed anyway; simple resample not implemented; this may cause drift
                        except Exception as e:
                            print(f"Warning: Failed reading temp audio for segment {idx+1}: {e}")
                            entry["audio"] = None

                    if sample_rate is None:
                        print(f"No audio data to assemble for section '{section.title}'")
                        results[output_path] = False
                    else:
                        # Helper to create silence buffer
                        def make_silence(n_samples: int):
                            if n_samples <= 0:
                                return None
                            if channels and channels != 1:
                                return np.zeros((n_samples, channels), dtype=np.float32)
                            return np.zeros(n_samples, dtype=np.float32)

                        def ms_to_samples(ms: int) -> int:
                            return int(round((ms / 1000.0) * sample_rate))

                        combined_chunks: List[np.ndarray] = []
                        current_end = 0  # in samples
                        skip_mode = False  # when True, skip untimed segments until a timed cue after current_end

                        # Build a list of indices for cleanup of temp files after scheduling
                        temp_paths_to_cleanup = [e["temp_path"] for e in entries if e.get("success") and e.get("temp_path")]

                        for idx, entry in enumerate(entries):
                            audio = entry.get("audio", None)
                            if audio is None:
                                continue  # failed synthesis or read; skip
                            seg = section.segments[idx]
                            start_ms = getattr(seg, "start_ms", None)
                            seg_len = len(audio)

                            if start_ms is not None:
                                desired_start = ms_to_samples(int(start_ms))
                                if desired_start <= current_end:
                                    # Overflow; skip this timed segment and enter skip mode
                                    skip_mode = True
                                    continue
                                # This timed cue is after current_end; exit skip mode if set
                                if skip_mode:
                                    skip_mode = False
                                # Insert silence if gap exists
                                gap = desired_start - current_end
                                if gap > 0:
                                    silence = make_silence(gap)
                                    if silence is not None:
                                        combined_chunks.append(silence)
                                combined_chunks.append(audio)
                                current_end = desired_start + seg_len
                            else:
                                # Untimed segment
                                if skip_mode:
                                    # Skip untimed text until we hit a timed cue after current_end
                                    continue
                                # Append immediately at current_end
                                combined_chunks.append(audio)
                                current_end += seg_len

                        if len(combined_chunks) == 0:
                            print(f"No scheduled audio produced for section '{section.title}'")
                            results[output_path] = False
                        else:
                            combined_audio = np.concatenate(combined_chunks) if len(combined_chunks) > 1 else combined_chunks[0]
                            # Ensure output directory exists
                            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                            sf.write(output_path, combined_audio, sample_rate)
                            print(f"Section audio saved to: {output_path}")
                            results[output_path] = True

                    # Cleanup all temp files
                    for entry in entries:
                        tp = entry.get("temp_path")
                        if tp:
                            try:
                                os.remove(tp)
                            except Exception:
                                pass

                except Exception as e:
                    print(f"Error assembling scheduled audio for section '{section.title}': {e}")
                    results[output_path] = False
                    # Cleanup any remaining temp files
                    for entry in entries:
                        tp = entry.get("temp_path")
                        if tp:
                            try:
                                os.remove(tp)
                            except Exception:
                                pass

            # Print summary
            successful = sum(1 for success in results.values() if success)
            print(f"\nProcessed {len(results)} sections: {successful} successful, {len(results) - successful} failed.")

            return results
        except Exception as e:
            print(f"Error processing Markdown document: {e}")
            return {}

    def synthesize_single_segment(self, text: str, voice_name: str, 
                                 output_path: str, apply_phonetics: bool = True) -> bool:
        """
        Synthesize a single text segment with single voice.
        Used by both main pipeline and LLM Coach for consistent processing.
        
        Args:
            text (str): The text to synthesize (may contain phonetic markup)
            voice_name (str): The voice to use for synthesis
            output_path (str): Path where the audio file should be saved
            apply_phonetics (bool): Whether to apply phonetic processing
            
        Returns:
            bool: True if synthesis was successful, False otherwise
        """
        try:
            # Apply phonetic processing if requested and processor is available
            text_to_speak = text
            is_ssml = False
            
            if apply_phonetics and self.phonetic_processor:
                try:
                    is_ssml, text_to_speak = self.phonetic_processor.preprocess_text(text)
                except Exception as e:
                    print(f"⚠️  Warning: Phonetic processing failed: {e}")
                    # Fallback to original text
                    text_to_speak = text
                    is_ssml = False
            
            # Generate audio using TTS client
            success = self.tts_client.text_to_speech(
                text=text_to_speak,
                voice_name=voice_name,
                output_path=output_path,
                is_ssml=is_ssml
            )
            
            return success
            
        except Exception as e:
            print(f"❌ Error synthesizing single segment: {e}")
            return False

    def apply_automatic_phonetics(self, text: str) -> str:
        """
        Apply automatic phonetic detection to text by wrapping known phonetic entries
        with appropriate markup tags.
        
        Args:
            text (str): The input text to process
            
        Returns:
            str: Text with automatic phonetic markup applied
        """
        if not self.phonetic_processor:
            print("⚠️  Warning: PhoneticProcessor not available for auto-phonetics")
            return text
            
        try:
            # Import and use PhoneticLookupManager to get phonetic data
            from texttospeech.phonetics.manager import PhoneticLookupManager
            
            lookup_manager = PhoneticLookupManager(
                general_path="data/phonetic_lookup.json",
                personal_path="data/phonetic_lookup.personal.json",
                verbose=False
            )
            
            phonetic_data = lookup_manager.combined
            if not phonetic_data:
                print("⚠️  Warning: No phonetic lookup data available")
                return text
            
            processed_text = text
            modifications_count = 0
            
            # Sort entries by length (longest first) to avoid partial matches
            sorted_entries = sorted(phonetic_data.items(), key=lambda x: len(x[0]), reverse=True)
            
            for word, phonetic_entry in sorted_entries:
                # Skip if word is already wrapped in phonetic markup
                if f"]{word}[/" in processed_text:
                    continue
                    
                # Check if word appears in text (case-insensitive, word boundaries)
                import re
                pattern = r'\b' + re.escape(word) + r'\b'
                matches = re.finditer(pattern, processed_text, re.IGNORECASE)
                
                for match in reversed(list(matches)):  # Process in reverse to maintain positions
                    matched_word = match.group()
                    start, end = match.span()
                    
                    # Determine the appropriate markup based on phonetic classification
                    try:
                        from texttospeech.phonetics.processing import PhoneticNotationValidator
                        # Extract core to avoid double-wrapping like [ipa:[ipa:...]]
                        try:
                            core = lookup_manager._extract_core(phonetic_entry.phonetic)
                        except Exception:
                            core = phonetic_entry.phonetic.strip()
                        notation_type = PhoneticNotationValidator.classify_notation(phonetic_entry.phonetic)
                        if notation_type.value == 'ipa':
                            replacement = f"[ipa:{core}]{matched_word}[/ipa]"
                        elif notation_type.value == 'syllabic':
                            replacement = f"[pron:{core}]{matched_word}[/pron]"
                        else:
                            # Default to pronunciation markup for other types
                            replacement = f"[pron:{core}]{matched_word}[/pron]"
                        
                        # Replace the matched word with marked up version
                        processed_text = processed_text[:start] + replacement + processed_text[end:]
                        modifications_count += 1
                        
                    except Exception as e:
                        print(f"⚠️  Warning: Failed to classify phonetic notation for '{word}': {e}")
                        continue
            
            if modifications_count > 0:
                print(f"✅ Applied automatic phonetic markup to {modifications_count} words")
            else:
                print("ℹ️  No phonetic entries found in text for automatic markup")
                
            return processed_text
            
        except Exception as e:
            print(f"❌ Error applying automatic phonetics: {e}")
            return text

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