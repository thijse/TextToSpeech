"""
Markdown Parser Module

This module provides functionality to parse Markdown documents with alias and inline voice tags
for text-to-speech conversion.
"""

import re
from typing import List, Dict, Tuple, Optional


class VoiceSegment:
    """
    Represents a segment of text with a specific voice.
    """
    def __init__(self, voice: str, text: str):
        self.voice = voice  # Alias or direct voice name
        self.text = text

    def __str__(self):
        return f"[{self.voice}] {self.text[:40]}..."


class MarkdownSection:
    """
    Represents a section in a Markdown document.
    """
    def __init__(self, title: str, file_path: str, segments: List[VoiceSegment]):
        self.title = title
        self.file_path = file_path
        self.segments = segments  # List[VoiceSegment]

    def __str__(self):
        segs = "\n".join(str(s) for s in self.segments)
        return f"Section: {self.title}\nFile: {self.file_path}\nSegments:\n{segs}"


class MarkdownParser:
    """
    Parser for Markdown documents with alias and inline voice tags.
    """
    def __init__(self):
        # Match headers (e.g., ## Slide 1)
        self.heading_pattern = re.compile(r'^(#+)\s+(.*)$', re.MULTILINE)
        # Match alias definitions (e.g., [alias:John=Aria])
        self.alias_pattern = re.compile(r'\[alias:([A-Za-z0-9_]+)=([A-Za-z0-9_\-]+)\]')
        # Match voice switches (e.g., [voice:John] or [voice:Aria])
        self.voice_pattern = re.compile(r'\[voice:([A-Za-z0-9_\\-]+)\]')

    def generate_filename_from_title(self, title: str) -> str:
        filename = re.sub(r'[^\w\s-]', '', title).strip().lower()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename + ".mp3"

    def extract_aliases(self, markdown_text: str) -> Dict[str, str]:
        """
        Extract alias definitions from the markdown text before the first section header (## or higher).
        """
        aliases = {}
        # Only look before the first section header (## or higher)
        # We need to skip the title (# Title) and look for section headers (## Section)
        section_header_pattern = re.compile(r'^(#{2,})\s+(.*)$', re.MULTILINE)
        first_section = section_header_pattern.search(markdown_text)
        
        # If there's no section header, search the entire document
        search_text = markdown_text[:first_section.start()] if first_section else markdown_text
        
        for match in self.alias_pattern.finditer(search_text):
            alias, voice = match.group(1), match.group(2)
            aliases[alias] = voice
        
        return aliases

    def parse_sections(self, markdown_text: str) -> List[Tuple[str, int, int]]:
        """
        Find all section headers and their positions.
        Returns a list of (title, start_pos, end_pos).
        """
        matches = list(self.heading_pattern.finditer(markdown_text))
        sections = []
        for i, match in enumerate(matches):
            title = match.group(2).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(markdown_text)
            sections.append((title, start, end))
        return sections

    def split_into_voice_segments(self, text: str, aliases: Dict[str, str]) -> List[VoiceSegment]:
        """
        Split text into segments based on [voice:...] tags.
        Each segment is assigned the corresponding voice (alias resolved if needed).
        """
        segments = []
        pos = 0
        current_voice = None
        for match in self.voice_pattern.finditer(text):
            voice = match.group(1)
            # Add previous segment if any
            if pos < match.start():
                if current_voice is not None:
                    segment_text = text[pos:match.start()].strip()
                    if segment_text:
                        segments.append(VoiceSegment(current_voice, segment_text))
            # Update current voice (resolve alias if present)
            current_voice = aliases.get(voice, voice)
            pos = match.end()
        # Add the last segment
        if current_voice is not None and pos < len(text):
            segment_text = text[pos:].strip()
            if segment_text:
                segments.append(VoiceSegment(current_voice, segment_text))
        return segments

    def parse(self, markdown_text: str) -> Tuple[Dict[str, str], List[MarkdownSection]]:
        """
        Parse the markdown document and extract alias definitions and sections with voice segments.
        Returns (aliases, sections).
        """
        aliases = self.extract_aliases(markdown_text)
        sections = []
        for title, start, end in self.parse_sections(markdown_text):
            section_text = markdown_text[start:end].strip()
            # Only process if there is at least one [voice:...] tag in the section
            if not self.voice_pattern.search(section_text):
                continue
            # Generate file path from title
            file_path = self.generate_filename_from_title(title)
            # Split into voice segments
            segments = self.split_into_voice_segments(section_text, aliases)
            if segments:
                sections.append(MarkdownSection(title, file_path, segments))
        return aliases, sections


def process_markdown(markdown_text: str) -> Tuple[Dict[str, str], List[MarkdownSection]]:
    """
    Process a Markdown document and extract alias definitions and sections with voice segments.

    Args:
        markdown_text (str): The Markdown document text.

    Returns:
        Tuple[Dict[str, str], List[MarkdownSection]]: (aliases, sections)
    """
    parser = MarkdownParser()
    return parser.parse(markdown_text)
