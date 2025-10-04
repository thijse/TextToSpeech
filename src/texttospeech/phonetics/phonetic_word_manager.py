"""
Interactive Phonetic Word Manager

This module provides an interactive interface for recording custom word pronunciations,
extracting phonetics, and managing a phonetic lookup database.

Canonical location (migrated): src/texttospeech/phonetics/phonetic_word_manager.py
"""

import os
import json
import re
import tempfile
import time
from typing import Dict, Optional, List, Tuple
import azure.cognitiveservices.speech as speechsdk
import sounddevice as sd
import soundfile as sf
from datetime import datetime
import yaml

# Use overlay-capable lookup manager (general + personal)
from texttospeech.phonetics.manager import PhoneticLookupManager
# Use canonical AzureTTS for basic configuration (voice selection etc.)
from texttospeech.tts.azure import AzureTTS
 

class PhoneticEntry:
    """Represents a custom phonetic pronunciation entry."""
    
    def __init__(self, word: str, phonetic: str, source: str = "custom", 
                 confidence: float = 1.0, created_date: str = None):
        self.word = word.lower()
        self.phonetic = phonetic
        self.source = source  # "custom", "azure_recognition", "recorded", etc.
        self.confidence = confidence
        self.created_date = created_date or datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "word": self.word,
            "phonetic": self.phonetic,
            "source": self.source,
            "confidence": self.confidence,
            "created_date": self.created_date
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhoneticEntry':
        return cls(**data)


class AudioRecorder:
    """Handles audio recording for pronunciation samples."""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
    
    def record_word(self, duration: float = 3.0) -> Optional[str]:
        """
        Record audio and save to a temporary file.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Path to the recorded audio file, or None if failed
        """
        try:
            print(f"\n🎤 Recording for {duration} seconds...")
            print("   Get ready... Recording will start in:")
            for i in range(3, 0, -1):
                print(f"   {i}...")
                time.sleep(1)
            
            print("   🔴 RECORDING NOW - Speak clearly!")
            
            # Record audio
            audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='float32'
            )
            sd.wait()  # Wait until recording is finished
            
            print("   ✅ Recording complete!")
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(temp_file.name, audio_data, self.sample_rate)
            
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Error recording audio: {e}")
            return None


class PhoneticExtractor:
    """Extracts phonetic transcriptions from audio using Azure Speech Recognition."""
    
    def __init__(self, azure_api_key: str, azure_region: str):
        self.api_key = azure_api_key
        self.region = azure_region
    
    def extract_phonetics_from_audio(self, audio_file_path: str, 
                                   expected_word: str = None) -> Optional[Tuple[str, str]]:
        """
        Extract phonetic transcription from audio file.
        
        Args:
            audio_file_path: Path to the audio file
            expected_word: Expected word for validation
            
        Returns:
            Tuple of (recognized_text, phonetic_transcription) or None if failed
        """
        try:
            # Create speech config
            speech_config = speechsdk.SpeechConfig(
                subscription=self.api_key, 
                region=self.region
            )
            
            # Enable detailed recognition results to get phonetic info
            speech_config.request_word_level_timestamps()
            speech_config.output_format = speechsdk.OutputFormat.Detailed
            
            # Create audio config from file
            audio_config = speechsdk.audio.AudioConfig(filename=audio_file_path)
            
            # Create speech recognizer
            speech_recognizer = speechsdk.SpeechRecognizer(
                speech_config=speech_config, 
                audio_config=audio_config
            )
            
            print("🔍 Analyzing audio for phonetics...")
            
            # Perform recognition
            result = speech_recognizer.recognize_once()
            
            if result.reason == speechsdk.ResultReason.RecognizedSpeech:
                recognized_text = result.text.strip().lower().rstrip('.')
                
                # Generate phonetic approximation (placeholder heuristic)
                phonetic = self._text_to_ipa_approximation(recognized_text)
                
                print(f"✅ Recognized: '{recognized_text}'")
                
                # Validate against expected word if provided
                if expected_word and expected_word.lower() not in recognized_text:
                    print(f"⚠️  Warning: Expected '{expected_word}' but recognized '{recognized_text}'")
                
                return recognized_text, phonetic
                
            else:
                print(f"❌ Speech recognition failed: {result.reason}")
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.CancellationDetails(result)
                    print(f"   Error details: {cancellation_details.reason}")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting phonetics: {e}")
            return None
    
    def _text_to_ipa_approximation(self, text: str) -> str:
        """
        Convert text to approximate IPA notation.
        This is a simplified implementation - could be enhanced with a proper G2P system.
        """
        # Basic English phonetic mappings
        mappings = {
            # Vowels
            'a': 'æ', 'e': 'ɛ', 'i': 'ɪ', 'o': 'ɔ', 'u': 'ʊ',
            'ee': 'iː', 'oo': 'uː', 'ar': 'ɑr', 'er': 'ər', 'or': 'ɔr',
            'ay': 'eɪ', 'oy': 'ɔɪ', 'ow': 'aʊ',
            
            # Consonants
            'th': 'θ', 'sh': 'ʃ', 'ch': 'tʃ', 'ng': 'ŋ', 'ph': 'f',
            'ck': 'k', 'qu': 'kw',
            
            # Common endings
            'tion': 'ʃən', 'sion': 'ʃən', 'ing': 'ɪŋ', 'ed': 'd'
        }
        
        result = text.lower()
        
        # Apply mappings in order of length (longest first to avoid conflicts)
        for grapheme in sorted(mappings.keys(), key=len, reverse=True):
            result = result.replace(grapheme, mappings[grapheme])
        
        return result


class InteractivePhoneticManager:
    """Interactive manager for phonetic word recording and management."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        
        # Initialize Azure components
        azure_config = self.config.get("azure", {})
        self.azure_api_key = azure_config.get("api_key")
        self.azure_region = azure_config.get("region")
        
        if not self.azure_api_key or not self.azure_region:
            raise ValueError("Azure API key and region must be configured in config/config.yaml")
        
        # Initialize components
        self.recorder = AudioRecorder()
        self.extractor = PhoneticExtractor(self.azure_api_key, self.azure_region)
        # Overlay-aware manager (tracked general + personal override)
        self.lookup_manager = PhoneticLookupManager(
            general_path="data/phonetic_lookup.json",
            personal_path="data/phonetic_lookup.personal.json",
        )
        
        # Initialize TTS for phonetic playback (configures voice)
        self._init_tts()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return {}
    
    def _init_tts(self):
        """Initialize TTS client for phonetic playback."""
        try:
            azure_config = self.config.get("azure", {})
            voice_name = azure_config.get("voice_name", "en-US-JennyNeural")
            
            # Keep an AzureTTS instance primarily to honor configured voice
            self.tts_client = AzureTTS(
                api_key=self.azure_api_key,
                region=self.azure_region,
                voice_name=voice_name
            )
            
            print(f"🔊 TTS initialized with voice: {voice_name}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not initialize TTS for playback: {e}")
            self.tts_client = None
    
    def _play_phonetic_tts(self, word: str, phonetic: str) -> bool:
        """Play back the phonetic pronunciation using TTS with proper phonetic processing."""
        try:
            from .processing import process_phonetic_for_tts
            
            # Use the PhoneticProcessor to generate correct SSML/text
            voice_name = getattr(self.tts_client, "voice_name", None) or \
                         self.config.get("azure", {}).get("voice_name", "en-US-JennyNeural")
            
            method, content = process_phonetic_for_tts(
                word, 
                phonetic, 
                "azure"  # Backend type (removed extra voice_name parameter)
            )
            
            is_ssml = (method == "ssml")
            
            print(f"🎵 Generating TTS for '{word}' with phonetic: {phonetic}")
            print(f"   (Using {'SSML' if is_ssml else 'text'} synthesis)")
            
            # Create temp file for playback
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_path = temp_file.name
            
            # Generate TTS audio using the TTS client
            success = self.tts_client.text_to_speech(
                text=content,
                voice_name=voice_name,
                output_path=temp_path,
                is_ssml=is_ssml
            )
            
            if success:
                print("🔊 Playing back phonetic pronunciation...")
                
                # Load and play the audio
                data, sample_rate = sf.read(temp_path)
                sd.play(data, sample_rate)
                sd.wait()  # Wait until playback is finished
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                
                return True
            else:
                print(f"❌ TTS synthesis failed")
                return False
                
        except Exception as e:
            print(f"❌ Error playing phonetic TTS: {e}")
            return False

    def _play_phonetic_unified(self, word: str, phonetic: str) -> bool:
        """
        Play back phonetic pronunciation using the unified processing pipeline.
        This ensures consistency with LLM Coach and main TTS pipeline.
        """
        try:
            # Import the unified processing components
            from texttospeech.processing.modality_to_speech import ModalityToSpeech
            from texttospeech.phonetics.processing import PhoneticProcessor, PhoneticNotationValidator
            
            # Create phonetic processor
            voice_name = getattr(self.tts_client, "voice_name", None) or "en-US-JennyNeural"
            phonetic_processor = PhoneticProcessor(
                backend="azure",
                voice_name=voice_name,
                accepts_ssml=True
            )
            
            # Create modality processor with unified pipeline
            modality_processor = ModalityToSpeech(self.tts_client, phonetic_processor)
            
            # Extract phonetic content if it's already in markup format
            import re
            
            print(f"🔍 DEBUG: Raw phonetic input: '{phonetic}'")
            
            # Check if phonetic already contains markup tags
            ipa_match = re.match(r'\[ipa:([^\]]+)\]', phonetic)
            pron_match = re.match(r'\[pron:([^\]]+)\]', phonetic)
            ph_match = re.match(r'\[ph:([^\]]+)\]', phonetic)
            phonetic_match = re.match(r'\[phonetic:([^\]]+)\]', phonetic)
            
            if ipa_match:
                # Use original IPA markup directly without re-wrapping
                clean_phonetic = ipa_match.group(1)
                markdown_text = f"[ipa:{clean_phonetic}]"
                print(f"🔍 DEBUG: Detected IPA markup, using directly: '{markdown_text}'")
            elif pron_match:
                # Use original pron markup directly without re-wrapping
                clean_phonetic = pron_match.group(1)
                markdown_text = f"[pron:{clean_phonetic}]"
                print(f"🔍 DEBUG: Detected PRON markup, using directly: '{markdown_text}'")
            elif ph_match:
                # Convert ph to pron markup without re-wrapping
                clean_phonetic = ph_match.group(1)
                markdown_text = f"[pron:{clean_phonetic}]"
                print(f"🔍 DEBUG: Detected PH markup, converted to: '{markdown_text}'")
            elif phonetic_match:
                # Convert phonetic to pron markup without re-wrapping
                clean_phonetic = phonetic_match.group(1)
                markdown_text = f"[pron:{clean_phonetic}]"
                print(f"🔍 DEBUG: Detected PHONETIC markup, converted to: '{markdown_text}'")
            else:
                # No markup detected, classify and wrap appropriately
                notation_type = PhoneticNotationValidator.classify_notation(phonetic)
                print(f"🔍 DEBUG: No markup detected, classified as: {notation_type.value}")
                if notation_type.value == 'ipa':
                    markdown_text = f"[ipa:{phonetic}]{word}[/ipa]"
                elif notation_type.value == 'syllabic':
                    markdown_text = f"[pron:{phonetic}]{word}[/pron]"
                else:
                    # Default to pronunciation markup
                    markdown_text = f"[pron:{phonetic}]{word}[/pron]"
            
            print(f"🔍 DEBUG: Final markdown text: '{markdown_text}'")
            
            # Create temp file for playback
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                temp_path = temp_file.name
            
            print(f"🎵 Generating TTS for '{word}' with phonetic: {phonetic}")
            print(f"   Using unified processing pipeline with markup: {markdown_text}")
            
            # Use the same single-segment synthesis as LLM Coach
            success = modality_processor.synthesize_single_segment(
                text=markdown_text,
                voice_name=voice_name,
                output_path=temp_path,
                apply_phonetics=True
            )
            
            if success:
                print("🔊 Playing back phonetic pronunciation...")
                
                # Load and play the audio
                data, sample_rate = sf.read(temp_path)
                sd.play(data, sample_rate)
                sd.wait()  # Wait until playback is finished
                
                # Clean up temp file
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                
                return True
            else:
                print(f"❌ TTS synthesis failed")
                return False
                
        except Exception as e:
            print(f"❌ Error playing phonetic TTS via unified pipeline: {e}")
            return False
    
    def record_word_workflow(self, word: str) -> bool:
        """
        Complete workflow for recording a word and managing its phonetic entry.
        
        Args:
            word: The word to record
            
        Returns:
            True if the word was successfully processed and saved
        """
        word = word.strip().lower()
        
        if not word:
            print("❌ Invalid word")
            return False
        
        print(f"\n🎯 Processing word: '{word}'")
        
        # Step 2: Check if word exists in lookup list
        existing_entry = self.lookup_manager.get_pronunciation(word)
        if existing_entry:
            print(f"📝 Word '{word}' already exists with phonetic: {existing_entry.phonetic}")
            print(f"   Source: {existing_entry.source}, Created: {existing_entry.created_date}")
            
            # Ask if user wants to overwrite
            while True:
                response = input("   Do you want to overwrite this pronunciation? (y/n): ").strip().lower()
                if response in ['y', 'yes']:
                    break
                elif response in ['n', 'no']:
                    print("   Keeping existing pronunciation.")
                    return False
                else:
                    print("   Please enter 'y' or 'n'")
        
        # Step 4: Record audio pronunciation
        print(f"\n📼 Ready to record pronunciation for '{word}'")
        input("   Press Enter when ready to start recording...")
        
        audio_file = self.recorder.record_word(duration=3.0)
        if not audio_file:
            print("❌ Recording failed")
            return False
        
        try:
            # Step 5: Extract/generate phonetics
            result = self.extractor.extract_phonetics_from_audio(audio_file, word)
            if not result:
                print("❌ Could not extract phonetics from recording")
                return False
            
            recognized_text, phonetic = result
            
            # Step 6: Show phonetics to user
            print(f"\n📋 Generated phonetics:")
            print(f"   Recognized word: {recognized_text}")
            print(f"   Phonetic notation: {phonetic}")
            
            # Allow user to edit phonetics
            while True:
                edit_response = input("\n   Would you like to edit the phonetics? (y/n): ").strip().lower()
                if edit_response in ['y', 'yes']:
                    custom_phonetic = input(f"   Enter phonetic notation for '{word}': ").strip()
                    if custom_phonetic:
                        phonetic = custom_phonetic
                        print(f"   Updated phonetic: {phonetic}")
                    break
                elif edit_response in ['n', 'no']:
                    break
                else:
                    print("   Please enter 'y' or 'n'")
            
            # Step 7: Play back TTS using phonetics
            print(f"\n🎵 Testing phonetic pronunciation...")
            if self._play_phonetic_tts(word, phonetic):
                print("   Playback complete!")
            else:
                print("   Could not play back pronunciation")
            
            # Step 8: Ask if user wants to save to the list
            while True:
                save_response = input(f"\n   Save phonetic pronunciation for '{word}'? (y/n): ").strip().lower()
                if save_response in ['y', 'yes']:
                    self.lookup_manager.add_pronunciation(word, phonetic, "recorded")
                    print(f"✅ Saved pronunciation for '{word}': {phonetic}")
                    return True
                elif save_response in ['n', 'no']:
                    print("   Pronunciation not saved.")
                    return False
                else:
                    print("   Please enter 'y' or 'n'")
        
        finally:
            # Clean up audio file
            try:
                os.remove(audio_file)
            except Exception:
                pass
    
    def interactive_menu(self):
        """Main interactive menu for phonetic word management."""
        print("\n🎙️  Interactive Phonetic Word Manager")
        print("=" * 50)
        
        while True:
            print("\nOptions:")
            print("1. Record new word pronunciation")
            print("2. List existing pronunciations")
            print("3. Remove pronunciation")
            print("4. Test pronunciation playback")
            print("5. Exit")
            
            choice = input("\nSelect option (1-5): ").strip()
            
            if choice == '1':
                word = input("\nEnter the word to record: ").strip()
                if word:
                    self.record_word_workflow(word)
                else:
                    print("❌ Please enter a valid word")
            
            elif choice == '2':
                self.lookup_manager.list_pronunciations()
            
            elif choice == '3':
                word = input("\nEnter word to remove: ").strip()
                if word:
                    self.lookup_manager.remove_pronunciation(word)
                else:
                    print("❌ Please enter a valid word")
            
            elif choice == '4':
                word = input("\nEnter word to test: ").strip()
                if word:
                    entry = self.lookup_manager.get_pronunciation(word)
                    if entry:
                        print(f"Testing pronunciation for '{word}': {entry.phonetic}")
                        self._play_phonetic_tts(word, entry.phonetic)
                    else:
                        print(f"❌ No pronunciation found for '{word}'")
                else:
                    print("❌ Please enter a valid word")
            
            elif choice == '5':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1-5.")


def main():
    """Main function to run the interactive phonetic word manager."""
    try:
        manager = InteractivePhoneticManager()
        manager.interactive_menu()
    except Exception as e:
        print(f"❌ Error initializing phonetic manager: {e}")


if __name__ == "__main__":
    main()