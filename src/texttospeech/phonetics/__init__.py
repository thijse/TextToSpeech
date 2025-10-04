"""
Phonetics module for TextToSpeech package.

Provides phonetic processing, validation, markup parsing, and TTS integration.
"""

from .processing import (
    PhoneticProcessor,
    PhoneticNotationType,
    PhoneticSegment,
    ValidationIssue,
    PhoneticNotationValidator,
    PhoneticSSMLGenerator,
    PhoneticMarkupParser,
    validate_phonetic_notation,
    process_phonetic_for_tts
)

from .manager import (
    PhoneticEntry,
    PhoneticLookupManager
)

__all__ = [
    # Core processing
    "PhoneticProcessor",
    "PhoneticNotationType", 
    "PhoneticSegment",
    "ValidationIssue",
    "PhoneticNotationValidator",
    "PhoneticSSMLGenerator", 
    "PhoneticMarkupParser",
    "validate_phonetic_notation",
    "process_phonetic_for_tts",
    
    # Database management
    "PhoneticEntry",
    "PhoneticLookupManager"
]