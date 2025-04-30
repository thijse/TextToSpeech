"""
Azure TTS Implementation Module

This module provides an implementation of the TTSInterface for the Azure Speech Service.
"""

import os
import tempfile
from typing import Dict, Optional, Any, List
import azure.cognitiveservices.speech as speechsdk
from tts_interface import TTSInterface


class AzureVoice:
    """
    A simple class to represent an Azure voice.
    """
    def __init__(self, voice_id, name, locale, gender, style_list=None):
        self.voice_id = voice_id  # Using name as ID for compatibility
        self.name = name
        self.locale = locale
        self.gender = gender
        self.style_list = style_list or []
        
        # Add additional attributes for compatibility with ElevenLabs
        self.category = "azure"
        self.description = f"{locale} {gender} voice"
        self.labels = {
            "locale": locale,
            "gender": gender
        }


class AzureVoicesResponse:
    """
    A simple class to mimic the ElevenLabs voices response structure.
    """
    def __init__(self, voices):
        self.voices = voices


class AzureTTS(TTSInterface):
    """
    Azure implementation of the TTS interface.
    """

    def __init__(self, api_key, region, voice_name="en-US-JennyNeural"):
        """
        Initialize the Azure Speech Service client with the provided API key and region.

        Args:
            api_key (str): The Azure Speech Service API key.
            region (str): The Azure region (e.g., "westus", "eastus").
            voice_name (str, optional): The default voice name to use. Defaults to "en-US-JennyNeural".
        """
        self.api_key = api_key
        self.region = region
        self.default_voice_name = voice_name
        
        # Create a speech config
        self.speech_config = speechsdk.SpeechConfig(subscription=api_key, region=region)
        
        # Cache for voices
        self._voices_cache = None

    def get_voices(self):
        """
        Fetch all available voices from the Azure Speech Service.

        Returns:
            object: A response object containing the voices.
        """
        try:
            # If we have a cached list of voices, return it
            if self._voices_cache:
                return self._voices_cache
                
            # Create a speech synthesizer
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config)
            
            # Get the list of voices
            result = synthesizer.get_voices_async().get()
            
            if result.reason == speechsdk.ResultReason.VoicesListRetrieved:
                # Convert to our format
                voices = []
                for voice in result.voices:
                    voice_id = voice.short_name
                    name = voice.short_name
                    locale = voice.locale
                    gender = voice.gender.name
                    style_list = voice.style_list if hasattr(voice, 'style_list') else []
                    
                    voices.append(AzureVoice(voice_id, name, locale, gender, style_list))
                
                # Cache the result
                self._voices_cache = AzureVoicesResponse(voices)
                return self._voices_cache
            else:
                print(f"Error fetching voices: {result.reason}")
                return None
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return None

    def get_voice_details(self, voice_id):
        """
        Fetch details for a specific voice.

        Args:
            voice_id (str): The ID (name) of the voice to fetch.

        Returns:
            object: The voice details.
        """
        try:
            # Get all voices
            response = self.get_voices()
            if not response or not hasattr(response, 'voices'):
                return None
                
            # Find the voice with the matching ID
            for voice in response.voices:
                if voice.voice_id == voice_id:
                    return voice
                    
            return None
        except Exception as e:
            print(f"Error fetching voice details: {e}")
            return None
            
    def find_voice_by_name(self, voice_name):
        """
        Find a voice by its name.
        
        Args:
            voice_name (str): The name of the voice to find.
            
        Returns:
            str: The voice ID if found, None otherwise.
        """
        try:
            # Get all voices
            response = self.get_voices()
            if not response or not hasattr(response, 'voices'):
                return None
                
            # Find the voice with the matching name
            for voice in response.voices:
                if voice.name.lower() == voice_name.lower():
                    return voice.voice_id
                    
            return None
        except Exception as e:
            print(f"Error finding voice by name: {e}")
            return None
            
    def text_to_speech(self, text, voice_name, output_path, output_format="mp3"):
        """
        Generate speech from text using the specified voice and save it to the specified path.
        
        Args:
            text (str): The text to convert to speech.
            voice_name (str): The name of the voice to use.
            output_path (str): The path where the audio file will be saved.
            output_format (str, optional): The audio format to use. 
                                          Azure supports: "raw-8khz-16bit-mono-pcm", 
                                          "raw-16khz-16bit-mono-pcm", "riff-8khz-16bit-mono-pcm",
                                          "riff-16khz-16bit-mono-pcm", "audio-16khz-128kbitrate-mono-mp3",
                                          "audio-16khz-64kbitrate-mono-mp3", "audio-16khz-32kbitrate-mono-mp3",
                                          "raw-24khz-16bit-mono-pcm", "riff-24khz-16bit-mono-pcm",
                                          "audio-24khz-160kbitrate-mono-mp3", "audio-24khz-96kbitrate-mono-mp3",
                                          "audio-24khz-48kbitrate-mono-mp3"
                                          Defaults to "mp3".
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Map the output format to Azure's format
            if output_format == "mp3" or output_format.startswith("mp3_"):
                # Default to high quality MP3
                azure_format = speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3
            else:
                # Try to map other formats
                format_map = {
                    "wav": speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
                    "ogg": speechsdk.SpeechSynthesisOutputFormat.Ogg24Khz16BitMonoOpus,
                    "webm": speechsdk.SpeechSynthesisOutputFormat.Webm24Khz16BitMonoOpus
                }
                azure_format = format_map.get(output_format, speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3)
            
            # Set the voice name
            self.speech_config.speech_synthesis_voice_name = voice_name
            
            # Set the output format
            self.speech_config.set_speech_synthesis_output_format(azure_format)
            
            # Create a speech synthesizer
            # For file output, we need to use the AudioConfig
            audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
            synthesizer = speechsdk.SpeechSynthesizer(speech_config=self.speech_config, audio_config=audio_config)
            
            # Generate speech
            print(f"Generating speech using voice '{voice_name}'...")
            result = synthesizer.speak_text_async(text).get()
            
            # Check the result
            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                print(f"Speech generated and saved to '{output_path}'.")
                return True
            else:
                print(f"Error generating speech: {result.reason}")
                if result.reason == speechsdk.ResultReason.Canceled:
                    cancellation_details = speechsdk.SpeechSynthesisCancellationDetails(result)
                    print(f"Error details: {cancellation_details.reason}, {cancellation_details.error_details}")
                return False
        except Exception as e:
            print(f"Error generating speech: {e}")
            return False
