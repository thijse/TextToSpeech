"""
ElevenLabs TTS Implementation Module

This module provides an implementation of the TTSInterface for the ElevenLabs API.
"""

import os
from typing import Dict, Optional, Any
from elevenlabs import ElevenLabs, Voice
from tts_interface import TTSInterface


class ElevenLabsTTS(TTSInterface):
    """
    ElevenLabs implementation of the TTS interface.
    """

    def __init__(self, api_key, model_id="eleven_monolingual_v1"):
        """
        Initialize the ElevenLabs client with the provided API key and model ID.

        Args:
            api_key (str): The ElevenLabs API key.
            model_id (str, optional): The model ID to use for speech generation.
                                     Options: eleven_monolingual_v1, eleven_multilingual_v1,
                                     eleven_multilingual_v2, eleven_turbo_v2.
                                     Defaults to "eleven_monolingual_v1".
        """
        self.client = ElevenLabs(api_key=api_key)
        self.model_id = model_id

    def get_voices(self):
        """
        Fetch all available voices from the ElevenLabs API.

        Returns:
            object: A response object containing the voices.
        """
        try:
            response = self.client.voices.get_all()
            return response
        except Exception as e:
            print(f"Error fetching voices: {e}")
            return None

    def get_voice_details(self, voice_id):
        """
        Fetch details for a specific voice.

        Args:
            voice_id (str): The ID of the voice to fetch.

        Returns:
            object: The voice details.
        """
        try:
            voice = self.client.voices.get(voice_id=voice_id)
            return voice
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
            response = self.get_voices()
            if not response or not hasattr(response, 'voices'):
                return None
                
            for voice in response.voices:
                if voice.name.lower() == voice_name.lower():
                    return voice.voice_id
                    
            return None
        except Exception as e:
            print(f"Error finding voice by name: {e}")
            return None
            
    def text_to_speech(self, text, voice_name, output_path, output_format="mp3_44100_128"):
        """
        Generate speech from text using the specified voice and save it to the specified path.
        
        Args:
            text (str): The text to convert to speech.
            voice_name (str): The name of the voice to use.
            output_path (str): The path where the audio file will be saved.
            output_format (str, optional): The audio format to use. 
                                          Valid formats include: mp3_44100_128, mp3_44100_64, etc.
                                          Defaults to "mp3_44100_128".
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Find the voice ID by name
            voice_id = self.find_voice_by_name(voice_name)
            if not voice_id:
                print(f"Voice '{voice_name}' not found.")
                return False
                
            # Generate speech
            print(f"Generating speech using voice '{voice_name}' with model '{self.model_id}'...")
            audio_stream = self.client.generate(
                text=text,
                voice=Voice(voice_id=voice_id),
                model=self.model_id,
                output_format=output_format
            )
            
            # Convert the generator to bytes
            audio_bytes = b''
            for chunk in audio_stream:
                audio_bytes += chunk
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Save the audio to the specified path
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
                
            print(f"Speech generated and saved to '{output_path}'.")
            return True
        except Exception as e:
            print(f"Error generating speech: {e}")
            return False
