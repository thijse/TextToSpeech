"""
Phonetic Processing Module

Provides core phonetic processing capabilities for TTS applications:
- IPA and phonetic notation validation
- SSML generation for Azure TTS
- Text hint generation for ElevenLabs
- Custom markup parsing ([ipa:...], [phonetic:...], etc.)

This module is used by both the TTS client pipeline and the phonetics tooling.
"""

import re
import html
from typing import Tuple, List, Dict, Optional, NamedTuple
from dataclasses import dataclass
from enum import Enum


class PhoneticNotationType(Enum):
    """Types of phonetic notation supported."""
    IPA = "ipa"           # International Phonetic Alphabet: /həˈloʊ/
    SIMPLIFIED = "simplified"  # Simplified phonetics: huh-LOH
    SYLLABIC = "syllabic"     # Syllable-based: hel-LO
    TEXT = "text"             # Text pronunciation hints: "said like hello"
    UNKNOWN = "unknown"       # Could not determine type


@dataclass
class PhoneticSegment:
    """Represents a segment of text with optional phonetic information."""
    text: str                           # Original text
    phonetic: Optional[str] = None      # Phonetic notation if provided
    notation_type: PhoneticNotationType = PhoneticNotationType.UNKNOWN
    is_phonetic: bool = False           # True if this segment has phonetic data


class ValidationIssue(NamedTuple):
    """Represents an issue found during phonetic validation."""
    type: str           # Type of issue (invalid_char, malformed, etc.)
    message: str        # Human-readable message
    position: int = -1  # Character position if applicable


class PhoneticNotationValidator:
    """Validates phonetic notation and determines notation types."""
    
    # IPA character sets (simplified but comprehensive)
    IPA_VOWELS = set([
        'i', 'ɪ', 'e', 'ɛ', 'æ', 'ɑ', 'ɒ', 'ɔ', 'o', 'ʊ', 'u', 'ʌ', 'ə', 'ɜ', 'ɝ',
        'y', 'ʏ', 'ø', 'œ', 'ɶ', 'ɯ', 'ɨ', 'ɘ', 'ɵ', 'ɤ', 'ɐ', 'ɞ', 'ɱ',
        # Relaxed acceptance: plain 'a' frequently appears in diphthongs aɪ / aʊ
        'a'
    ])
    
    IPA_CONSONANTS = set([
        'p', 'b', 't', 'd', 'k', 'g', 'q', 'ɢ', 'ʔ', 'm', 'ɱ', 'n', 'ɳ', 'ɲ', 'ŋ', 'ɴ',
        'ʙ', 'r', 'ʀ', 'ɾ', 'ɽ', 'ɸ', 'β', 'f', 'v', 'θ', 'ð', 's', 'z', 'ʃ', 'ʒ', 'ʂ', 'ʐ',
        'ç', 'ʝ', 'x', 'ɣ', 'χ', 'ʁ', 'ħ', 'ʕ', 'h', 'ɦ', 'ɬ', 'ɮ', 'ʋ', 'ɹ', 'ɻ', 'j', 'ɰ',
        'l', 'ɭ', 'ʎ', 'ʟ', 'w', 'ɥ', 'ʜ', 'ʢ', 'ʡ', 'ɕ', 'ʑ', 'ɺ', 'ɧ', 'ɚ'
    ])
    
    IPA_SUPRASEGMENTALS = set([
        'ˈ', 'ˌ', 'ː', 'ˑ', '̆', '|', '‖', '.', '‿', '↗', '↘'
    ])
    
    IPA_DIACRITICS = set([
        '̥', '̬', 'ʰ', '̹', '̜', '̟', '̠', '̈', '̽', '̩', '̯', '˞', '̤', '̰', '̼', '̺', '̻', '̃', 
        'ⁿ', 'ˡ', '̚', '̪', '̬', '̊', '̃', '́', '̀', '̂', '̌', '̄', '̆', '̋', '̏'
    ])
    
    @classmethod
    def classify_notation(cls, phonetic: str) -> PhoneticNotationType:
        """Determine the type of phonetic notation."""
        if not phonetic or not phonetic.strip():
            return PhoneticNotationType.UNKNOWN
            
        # Clean the notation
        clean = phonetic.strip()
        
        # Remove common wrapper characters for analysis
        if clean.startswith('/') and clean.endswith('/'):
            clean = clean[1:-1]
        elif clean.startswith('[') and clean.endswith(']'):
            clean = clean[1:-1]
            
        # Check for syllable patterns FIRST (dashes + uppercase)
        if '-' in clean and any(c.isupper() for c in clean):
            return PhoneticNotationType.SYLLABIC
            
        # Count IPA characters
        ipa_chars = 0
        total_chars = 0
        
        for char in clean:
            if char.isalpha() or char in cls.IPA_VOWELS or char in cls.IPA_CONSONANTS or char in cls.IPA_SUPRASEGMENTALS:
                total_chars += 1
                if char in cls.IPA_VOWELS or char in cls.IPA_CONSONANTS or char in cls.IPA_SUPRASEGMENTALS:
                    ipa_chars += 1
        
        # If more than 80% IPA characters AND no obvious syllabic markers, consider it IPA
        # Raised threshold to avoid misclassifying syllabic notations
        if total_chars > 0 and (ipa_chars / total_chars) > 0.8 and '-' not in clean and not any(c.isupper() for c in clean):
            return PhoneticNotationType.IPA
            
        # Check for simplified patterns (mixed case, common letter combinations)
        if any(c.isupper() for c in clean) and any(c.islower() for c in clean):
            return PhoneticNotationType.SIMPLIFIED
            
        # If it's mostly text-like
        if ' ' in clean or len(clean.split()) > 1:
            return PhoneticNotationType.TEXT
            
        return PhoneticNotationType.UNKNOWN
    
    @classmethod
    def validate_ipa(cls, ipa_text: str) -> Tuple[bool, List[ValidationIssue]]:
        """Validate IPA notation and return issues found.

        Relaxations applied:
        - Plain Latin 'a' now accepted (common in diphthongs aɪ, aʊ)
        - Unknown ASCII letters are treated as SOFT issues (do not invalidate)
        - Syllable delimiter '.' and leading stress marks always accepted
        """
        issues: List[ValidationIssue] = []
        soft_issues: List[ValidationIssue] = []

        if not ipa_text:
            issues.append(ValidationIssue("empty", "IPA notation cannot be empty"))
            return False, issues

        clean = ipa_text.strip()
        if clean.startswith('/') and clean.endswith('/'):
            clean = clean[1:-1]
        elif clean.startswith('[') and clean.endswith(']'):
            clean = clean[1:-1]

        # Allowed base chars
        valid_chars = cls.IPA_VOWELS | cls.IPA_CONSONANTS | cls.IPA_SUPRASEGMENTALS | cls.IPA_DIACRITICS
        # Add common punctuation and delimiters
        valid_chars.update(' .,;:()[]/')

        for i, char in enumerate(clean):
            if char in valid_chars or char.isspace():
                continue
            # Soft-accept unknown ASCII letters (e.g., residual transliteration fragments)
            if 'a' <= char <= 'z' or 'A' <= char <= 'Z':
                soft_issues.append(ValidationIssue("soft_char", f"Non-IPA ASCII letter '{char}' (treated as soft)", i))
                continue
            issues.append(ValidationIssue("invalid_char", f"Invalid IPA character '{char}'", i))

        if len(clean.strip()) == 0:
            issues.append(ValidationIssue("empty_content", "No phonetic content found"))

        # If only soft issues, treat as valid
        if issues:
            return False, issues + soft_issues
        return True, soft_issues  # Return soft issues for visibility
    
    @classmethod
    def validate_notation(cls, phonetic: str) -> Tuple[PhoneticNotationType, bool, List[ValidationIssue]]:
        """Validate any phonetic notation and return type, validity, and issues."""
        notation_type = cls.classify_notation(phonetic)
        
        if notation_type == PhoneticNotationType.IPA:
            is_valid, issues = cls.validate_ipa(phonetic)
        elif notation_type == PhoneticNotationType.UNKNOWN:
            issues = [ValidationIssue("unknown_type", f"Could not determine phonetic notation type for: {phonetic}")]
            is_valid = False
        else:
            # For non-IPA types, do basic validation
            issues = []
            is_valid = bool(phonetic.strip())
            if not is_valid:
                issues.append(ValidationIssue("empty", "Phonetic notation cannot be empty"))
        
        return notation_type, is_valid, issues


class PhoneticSSMLGenerator:
    """Generates SSML or text for different TTS backends."""
    
    @staticmethod
    def generate_azure_ssml(text: str, phonetic: str, voice_name: str = "en-US-JennyNeural") -> str:
        """Generate Azure SSML with phoneme tags."""
        # Escape text for XML
        escaped_text = html.escape(text)
        
        # Clean phonetic notation (remove wrapper characters)
        clean_phonetic = phonetic.strip()
        if clean_phonetic.startswith('/') and clean_phonetic.endswith('/'):
            clean_phonetic = clean_phonetic[1:-1]
        elif clean_phonetic.startswith('[') and clean_phonetic.endswith(']'):
            clean_phonetic = clean_phonetic[1:-1]
            
        # Escape phonetic for XML
        escaped_phonetic = html.escape(clean_phonetic)
        
        # Generate SSML phoneme tag
        return f'<phoneme alphabet="ipa" ph="{escaped_phonetic}">{escaped_text}</phoneme>'
    
    @staticmethod
    def generate_azure_emphasis(text: str, level: str = "moderate") -> str:
        """Generate Azure SSML emphasis for simplified phonetics."""
        escaped_text = html.escape(text)
        return f'<emphasis level="{level}">{escaped_text}</emphasis>'
    
    @staticmethod
    def generate_elevenlabs_hint(text: str, phonetic: str) -> str:
        """Generate ElevenLabs text with pronunciation hint."""
        # For ElevenLabs, we provide hints in parentheses
        # Convert complex phonetics to simpler hints when possible
        simplified = PhoneticSSMLGenerator._simplify_for_elevenlabs(phonetic)
        return f"{text} ({simplified})"
    
    @staticmethod
    def _simplify_for_elevenlabs(phonetic: str) -> str:
        """Convert complex phonetics to simplified pronunciation hints."""
        # Remove IPA wrapper characters
        clean = phonetic.strip()
        if clean.startswith('/') and clean.endswith('/'):
            clean = clean[1:-1]
        elif clean.startswith('[') and clean.endswith(']'):
            clean = clean[1:-1]
            
        # Basic IPA to English mapping for common sounds
        mappings = {
            'ə': 'uh', 'ɪ': 'ih', 'ɛ': 'eh', 'æ': 'ah', 'ɑ': 'ah', 'ɔ': 'aw',
            'ʊ': 'oo', 'ʌ': 'uh', 'ɜ': 'er', 'θ': 'th', 'ð': 'th', 'ʃ': 'sh',
            'ʒ': 'zh', 'ʧ': 'ch', 'ʤ': 'j', 'ŋ': 'ng', 'ˈ': '', 'ˌ': ''
        }
        
        result = clean
        for ipa, simple in mappings.items():
            result = result.replace(ipa, simple)
            
        return result


class PhoneticMarkupParser:
    """Parses phonetic markup tags in text."""
    
    # Regex patterns for different phonetic markup tags
    PATTERNS = {
        'ipa': re.compile(r'\[ipa:(.*?)\](.*?)\[/ipa\]', re.IGNORECASE | re.DOTALL),
        'phonetic': re.compile(r'\[phonetic:(.*?)\](.*?)\[/phonetic\]', re.IGNORECASE | re.DOTALL),
        'ph': re.compile(r'\[ph:(.*?)\](.*?)\[/ph\]', re.IGNORECASE | re.DOTALL),
        'pron': re.compile(r'\[pron:(.*?)\](.*?)\[/pron\]', re.IGNORECASE | re.DOTALL),
    }
    
    # Standalone patterns for single-tag phonetic notations (LLM format)
    STANDALONE_PATTERNS = {
        'ipa': re.compile(r'\[ipa:(.*?)\]', re.IGNORECASE),
        'phonetic': re.compile(r'\[phonetic:(.*?)\]', re.IGNORECASE),
        'ph': re.compile(r'\[ph:(.*?)\]', re.IGNORECASE),
        'pron': re.compile(r'\[pron:(.*?)\]', re.IGNORECASE),
    }
    
    @classmethod
    def parse_text(cls, text: str) -> List[PhoneticSegment]:
        """Parse text and return list of segments with phonetic information."""
        segments = []
        remaining_text = text
        
        while remaining_text:
            # Find the earliest phonetic tag (paired tags first, then standalone)
            earliest_match = None
            earliest_pos = len(remaining_text)
            earliest_tag = None
            is_standalone = False
            
            # Check paired patterns first
            for tag_name, pattern in cls.PATTERNS.items():
                match = pattern.search(remaining_text)
                if match and match.start() < earliest_pos:
                    earliest_match = match
                    earliest_pos = match.start()
                    earliest_tag = tag_name
                    is_standalone = False
            
            # If no paired tags found, check standalone patterns
            if not earliest_match:
                for tag_name, pattern in cls.STANDALONE_PATTERNS.items():
                    match = pattern.search(remaining_text)
                    if match and match.start() < earliest_pos:
                        earliest_match = match
                        earliest_pos = match.start()
                        earliest_tag = tag_name
                        is_standalone = True
            
            if earliest_match:
                # Add text before the tag as a regular segment
                if earliest_pos > 0:
                    plain_text = remaining_text[:earliest_pos]
                    segments.append(PhoneticSegment(
                        text=plain_text,
                        is_phonetic=False
                    ))
                
                # Handle the phonetic segment
                phonetic_notation = earliest_match.group(1).strip()
                
                if is_standalone:
                    # For standalone tags, the phonetic notation IS the text to be spoken
                    text_content = phonetic_notation  # Use the phonetic as the text content
                else:
                    # For paired tags, use the text between tags
                    text_content = earliest_match.group(2).strip()
                
                # Determine notation type
                notation_type = PhoneticNotationValidator.classify_notation(phonetic_notation)
                
                segments.append(PhoneticSegment(
                    text=text_content,
                    phonetic=phonetic_notation,
                    notation_type=notation_type,
                    is_phonetic=True
                ))
                
                # Continue with remaining text
                remaining_text = remaining_text[earliest_match.end():]
            else:
                # No more phonetic tags, add remaining text as plain segment
                if remaining_text.strip():
                    segments.append(PhoneticSegment(
                        text=remaining_text,
                        is_phonetic=False
                    ))
                break
        
        return segments


class PhoneticProcessor:
    """Main phonetic processor that orchestrates parsing, validation, and generation."""
    
    def __init__(self, backend: str = "azure", voice_name: str = "en-US-JennyNeural", accepts_ssml: bool = True):
        """
        Initialize the phonetic processor.
        
        Args:
            backend: TTS backend ("azure" or "elevenlabs")
            voice_name: Voice name for SSML generation
            accepts_ssml: Whether the backend accepts SSML
        """
        self.backend = backend.lower()
        self.voice_name = voice_name
        self.accepts_ssml = accepts_ssml
        self.parser = PhoneticMarkupParser()
        self.validator = PhoneticNotationValidator()
        self.ssml_generator = PhoneticSSMLGenerator()
    
    def preprocess_text(self, text: str) -> Tuple[bool, str]:
        """
        Process text with phonetic markup and return appropriate format for TTS backend.
        
        Args:
            text: Input text potentially containing phonetic markup
            
        Returns:
            (is_ssml, processed_text): Whether output is SSML and the processed text
        """
        print(f"🔍 PHONETIC PROCESSOR DEBUG: Input text: '{text}'")
        
        if not text or not text.strip():
            return False, text
            
        # Parse the text for phonetic segments
        segments = self.parser.parse_text(text)
        print(f"🔍 PHONETIC PROCESSOR DEBUG: Parsed {len(segments)} segments")
        for i, seg in enumerate(segments):
            print(f"   Segment {i}: text='{seg.text}', phonetic='{seg.phonetic}', is_phonetic={seg.is_phonetic}")
        
        # Check if any segments have phonetic information
        has_phonetics = any(seg.is_phonetic for seg in segments)
        
        if not has_phonetics:
            # No phonetic markup found, return original text
            return False, text
        
        # Process segments based on backend
        if self.backend == "azure" and self.accepts_ssml:
            return self._generate_azure_ssml(segments)
        elif self.backend == "elevenlabs":
            return self._generate_elevenlabs_text(segments)
        else:
            # Fallback: return text with phonetic hints stripped
            return False, self._generate_fallback_text(segments)
    
    def _generate_azure_ssml(self, segments: List[PhoneticSegment]) -> Tuple[bool, str]:
        """Generate Azure SSML from phonetic segments."""
        print(f"🔍 SSML GENERATOR DEBUG: Processing {len(segments)} segments for Azure")
        ssml_parts = []
        
        for segment in segments:
            print(f"🔍 SSML GENERATOR DEBUG: Processing segment - text='{segment.text}', phonetic='{segment.phonetic}', is_phonetic={segment.is_phonetic}")
            if segment.is_phonetic and segment.phonetic:
                # Validate the phonetic notation
                notation_type, is_valid, issues = self.validator.validate_notation(segment.phonetic)
                print(f"🔍 SSML GENERATOR DEBUG: Validation - type={notation_type.value}, valid={is_valid}, issues={len(issues)}")
                
                if is_valid and notation_type == PhoneticNotationType.IPA:
                    # Use phoneme tag for IPA
                    ssml_part = self.ssml_generator.generate_azure_ssml(
                        segment.text, segment.phonetic, self.voice_name
                    )
                    print(f"🔍 SSML GENERATOR DEBUG: Generated IPA SSML: '{ssml_part}'")
                elif is_valid and notation_type in [PhoneticNotationType.SIMPLIFIED, PhoneticNotationType.SYLLABIC]:
                    # Use emphasis for simplified phonetics
                    ssml_part = self.ssml_generator.generate_azure_emphasis(segment.text)
                else:
                    # Invalid or unknown notation, use plain text
                    ssml_part = html.escape(segment.text)
                
                ssml_parts.append(ssml_part)
            else:
                # Plain text segment
                ssml_parts.append(html.escape(segment.text))
        
        # Wrap in proper SSML structure with voice tag as required by Azure
        content = ''.join(ssml_parts)
        ssml = f'<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US"><voice name="{self.voice_name}">{content}</voice></speak>'
        return True, ssml
    
    def _generate_elevenlabs_text(self, segments: List[PhoneticSegment]) -> Tuple[bool, str]:
        """Generate ElevenLabs text with pronunciation hints."""
        text_parts = []
        
        for segment in segments:
            if segment.is_phonetic and segment.phonetic:
                # Add pronunciation hint
                text_part = self.ssml_generator.generate_elevenlabs_hint(
                    segment.text, segment.phonetic
                )
                text_parts.append(text_part)
            else:
                # Plain text segment
                text_parts.append(segment.text)
        
        return False, ''.join(text_parts)
    
    def _generate_fallback_text(self, segments: List[PhoneticSegment]) -> str:
        """Generate plain text by stripping phonetic markup."""
        text_parts = []
        
        for segment in segments:
            text_parts.append(segment.text)
        
        return ''.join(text_parts)


# Convenience functions for direct use
def validate_phonetic_notation(phonetic: str) -> Tuple[PhoneticNotationType, bool, List[ValidationIssue]]:
    """Validate phonetic notation. Returns (type, is_valid, issues)."""
    return PhoneticNotationValidator.validate_notation(phonetic)


def process_phonetic_for_tts(text: str, phonetic: str, backend: str = "azure") -> Tuple[str, str]:
    """
    Process a single phonetic for TTS backend.
    
    Returns:
        (method, content): Method type ("ssml" or "text") and the content
    """
    processor = PhoneticProcessor(backend=backend)
    
    # Create a simple phonetic markup for processing
    markup = f"[ipa:{phonetic}]{text}[/ipa]"
    is_ssml, processed = processor.preprocess_text(markup)
    
    return ("ssml" if is_ssml else "text", processed)


# Export main classes and functions
__all__ = [
    "PhoneticProcessor",
    "PhoneticNotationType", 
    "PhoneticSegment",
    "ValidationIssue",
    "PhoneticNotationValidator",
    "PhoneticSSMLGenerator", 
    "PhoneticMarkupParser",
    "validate_phonetic_notation",
    "process_phonetic_for_tts"
]
 