"""
TTS Interface Module

This module defines the interface that all Text-to-Speech implementations must follow.
"""

from typing import Dict, Optional, Any


class TTSInterface:
    """
    Interface for Text-to-Speech services.
    All TTS implementations must implement these methods.
    """
    
    def get_voices(self):
        """
        Fetch all available voices from the TTS service.

        Returns:
            object: A response object containing the voices.
        """
        raise NotImplementedError("Subclasses must implement get_voices()")

    def get_voice_details(self, voice_id):
        """
        Fetch details for a specific voice.

        Args:
            voice_id (str): The ID of the voice to fetch.

        Returns:
            object: The voice details.
        """
        raise NotImplementedError("Subclasses must implement get_voice_details()")
            
    def find_voice_by_name(self, voice_name):
        """
        Find a voice by its name.
        
        Args:
            voice_name (str): The name of the voice to find.
            
        Returns:
            str: The voice ID if found, None otherwise.
        """
        raise NotImplementedError("Subclasses must implement find_voice_by_name()")
            
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
        raise NotImplementedError("Subclasses must implement text_to_speech()")
