"""
Markdown Parser Module

This module provides functionality to parse Markdown documents with alias and inline voice tags
for text-to-speech conversion.
"""

import re
from typing import List, Dict, Tuple, Optional

 
class VoiceSegment:
    """
    Represents a segment of text with a specific voice and optional scheduled start time (ms).
    """
    def __init__(self, voice: str, text: str, start_ms: Optional[int] = None):
        self.voice = voice  # Alias or direct voice name (resolved alias)
        self.text = text
        self.start_ms = start_ms  # Scheduled start in milliseconds, None = sequential append

    def __str__(self):
        start_str = f"@{self.start_ms}ms" if self.start_ms is not None else "@seq"
        return f"[{self.voice}{start_str}] {self.text[:40]}..."

 
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
        # Match timestamp start cues (e.g., [start:0:04], [start:1:05.250], [start:4.5s])
        self.start_tag_pattern = re.compile(
            r'\[start:(?:(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?|(\d+(?:\.\d+)?)s)\]'
        )
        # Match bare timestamp lines (e.g., "0:04", "1:05.250", "4.5s") used as cues
        self.bare_start_pattern = re.compile(
            r'^\s*(?:(\d{1,2}):\d{2}(?:\.(\d{1,3}))?|(?:\d+(?:\.\d+)?)s)\s*$',
            re.MULTILINE
        )
        # Match timeline reset tags
        self.reset_pattern = re.compile(r'\[timestamp_reset\]')

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

    def split_into_voice_segments(self, text: str, aliases: Dict[str, str], default_voice: Optional[str] = None) -> List[VoiceSegment]:
        """
        Split text into voice/timed segments based on [voice:...] and [start:...] tags.
        - Resolves aliases for voices.
        - Associates subsequent text with the most recently selected voice.
        - Optional default_voice is used when no [voice:...] tags appear.
        - [start:...] may appear on a line by itself or with same-line text.
        - [timestamp_reset] is recognized but does not alter parsed start_ms (scheduler handles resets).
        """
        segments: List[VoiceSegment] = []

        def parse_start_ms_from_line(line: str) -> Tuple[Optional[int], str]:
            """
            Parse [start:...] tag or bare timestamp line and return (start_ms, trailing_text_after_tag).
            Returns (None, line) if no start cue found.
            """
            # First, check for explicit [start:...] tag with optional same-line trailing text
            m = re.match(r'^\s*\[start:(?:(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?|(\d+(?:\.\d+)?)s)\]\s*(.*)$', line)
            if m:
                if m.group(4):  # seconds form
                    seconds = float(m.group(4))
                    return int(round(seconds * 1000)), m.group(5) or ""
                mm = int(m.group(1) or "0")
                ss = int(m.group(2) or "0")
                ms = int((m.group(3) or "0").ljust(3, "0")) if m.group(3) else 0
                return (mm * 60 + ss) * 1000 + ms, (m.group(5) or "")
            # Next, check for bare timestamp line (no trailing text; subsequent paragraph applies)
            m2 = re.match(r'^\s*(?:(\d{1,2}):(\d{2})(?:\.(\d{1,3}))?|(\d+(?:\.\d+)?)s)\s*$', line)
            if m2:
                if m2.group(4):  # seconds form
                    seconds = float(m2.group(4))
                    return int(round(seconds * 1000)), ""
                mm = int(m2.group(1) or "0")
                ss = int(m2.group(2) or "0")
                ms = int((m2.group(3) or "0").ljust(3, "0")) if m2.group(3) else 0
                return (mm * 60 + ss) * 1000 + ms, ""
            return None, line

        lines = text.splitlines()
        current_voice: Optional[str] = default_voice
        current_start_ms: Optional[int] = None
        current_text_lines: List[str] = []

        def finish_segment():
            nonlocal current_text_lines, current_start_ms, current_voice
            joined = "\n\n".join(current_text_lines).strip()
            if joined and current_voice:
                segments.append(VoiceSegment(current_voice, joined, current_start_ms))
            current_text_lines = []
            current_start_ms = None

        for raw_line in lines:
            line = raw_line.rstrip()

            # Voice switch tag
            if line.startswith("[voice:"):
                finish_segment()
                m = re.match(r"\[voice:([^\]]+)\]", line)
                if m:
                    alias_or_voice = m.group(1).strip()
                    current_voice = aliases.get(alias_or_voice, alias_or_voice)
                # continue to next line
                continue

            # Timestamp reset tag (scheduler will handle actual reset; parser just ends current segment)
            if self.reset_pattern.match(line.strip()):
                finish_segment()
                # Do not modify current_voice; allow continuous voice context
                # Reset is semantic for scheduler; no direct impact on start_ms here
                continue

            # Start cue tag (with optional same-line trailing content)
            start_ms, trailing = parse_start_ms_from_line(line)
            if start_ms is not None:
                # New start cue: finish previous segment and begin a new timed one
                finish_segment()
                current_start_ms = start_ms
                if trailing.strip():
                    current_text_lines.append(trailing.strip())
                continue

            # Content line
            if line.strip() == "":
                # preserve blank line separator if we already have content
                if len(current_text_lines) > 0:
                    current_text_lines.append("")
            else:
                # Only record text when a voice (or default voice) is set
                if current_voice:
                    current_text_lines.append(line.strip())

        # Flush last segment
        finish_segment()

        return segments

    def parse(self, markdown_text: str, default_voice: str = None) -> Tuple[Dict[str, str], List[MarkdownSection]]:
        """
        Parse the markdown document and extract alias definitions and sections with voice segments.
        
        Args:
            markdown_text (str): The markdown document text.
            default_voice (str, optional): Default voice to use when no voice tags are found.
            
        Returns:
            Tuple[Dict[str, str], List[MarkdownSection]]: (aliases, sections)
        """
        aliases = self.extract_aliases(markdown_text)
        sections = []
        for title, start, end in self.parse_sections(markdown_text):
            section_text = markdown_text[start:end].strip()
            
            # Check for voice or timestamp tags in the section
            has_voice_tags = self.voice_pattern.search(section_text)
            has_start_tags = self.start_tag_pattern.search(section_text) or self.bare_start_pattern.search(section_text)

            if has_voice_tags or has_start_tags:
                # Process sections with voice/timestamp tags (including bare timestamps)
                file_path = self.generate_filename_from_title(title)
                segments = self.split_into_voice_segments(section_text, aliases, default_voice)
                if segments:
                    sections.append(MarkdownSection(title, file_path, segments))
            elif default_voice and section_text.strip():
                # Use default voice for sections without tags
                file_path = self.generate_filename_from_title(title)
                segments = [VoiceSegment(default_voice, section_text, None)]
                sections.append(MarkdownSection(title, file_path, segments))
                
        return aliases, sections


def process_markdown(markdown_text: str, default_voice: str = None) -> Tuple[Dict[str, str], List[MarkdownSection]]:
    """
    Process a Markdown document and extract alias definitions and sections with voice segments.

    Args:
        markdown_text (str): The Markdown document text.
        default_voice (str, optional): Default voice to use when no voice tags are found.

    Returns:
        Tuple[Dict[str, str], List[MarkdownSection]]: (aliases, sections)
    """
    parser = MarkdownParser()
    return parser.parse(markdown_text, default_voice)
# -----------------------------------------------
# Chapter JSON converter aligned to UI model
# References:
# - UI parser: [ts.parseChapterMarkdown()](src/texttospeech/UI/src/lib/markdown-parser.ts:8)
# - UI types: [ts.types.ts](src/texttospeech/UI/src/lib/types.ts:1)
# - Mocking strategy: [ts.MOCKS.md](src/texttospeech/UI/MOCKS.md:1)
# -----------------------------------------------
import re
from typing import List
from texttospeech.api.models import ChapterResponse, Chapter, Paragraph, TextSection, VoiceAlias

def parse_chapter_markdown_to_response(markdown_text: str) -> ChapterResponse:
    """
    Convert markdown with [alias:] and [voice:] tags into ChapterResponse
    mirroring the UI structure exactly (section.voice holds the alias name).
    """
    lines = markdown_text.split("\n")

    chapter_id = 1
    chapter_title = ""
    aliases: List[VoiceAlias] = []
    paragraphs: List[Paragraph] = []

    current_paragraph_header = ""
    current_sections: List[TextSection] = []
    current_voice_alias = ""
    current_text_lines: List[str] = []
    paragraph_counter = 1

    def finish_section():
        nonlocal current_text_lines, current_sections, current_voice_alias
        if current_voice_alias and len(current_text_lines) > 0:
            # Preserve blank lines as paragraph separators like UI parser (join with \n\n)
            # Remove leading/trailing blanks
            # Keep empty strings to produce proper double-newline separation
            # Filter None just in case
            joined = "\n\n".join([s for s in current_text_lines])
            text = joined.strip()
            if text:
                current_sections.append(TextSection(voice=current_voice_alias, text=text))
        current_text_lines = []

    def finish_paragraph():
        nonlocal current_paragraph_header, current_sections, paragraph_counter, paragraphs, current_voice_alias
        finish_section()
        if current_paragraph_header and len(current_sections) > 0:
            pid = f"p{paragraph_counter}"
            paragraphs.append(Paragraph(id=pid, header=current_paragraph_header, sections=current_sections))
            paragraph_counter += 1
        current_paragraph_header = ""
        current_sections = []
        current_voice_alias = ""

    for line in lines:
        # Chapter title, e.g. "#Chapter 1"
        if line.startswith("#Chapter "):
            m = re.match(r"#Chapter\s+(\d+)", line)
            if m:
                try:
                    chapter_id = int(m.group(1))
                except Exception:
                    chapter_id = 1
            chapter_title = re.sub(r"^#+\s*", "", line).strip()
            continue

        # Alias definition: [alias:Name=Voice]
        if line.startswith("[alias:"):
            m = re.match(r"\[alias:([^=]+)=([^\]]+)\]", line)
            if m:
                aliases.append(VoiceAlias(name=m.group(1).strip(), voice=m.group(2).strip()))
            continue

        # Paragraph header: "##Paragraph N ..." (keep full text as header)
        if line.startswith("##"):
            finish_paragraph()
            current_paragraph_header = re.sub(r"^#+\s*", "", line).strip()
            continue

        # Voice tag: [voice:AliasName] (store alias name, do NOT resolve to actual voice)
        if line.startswith("[voice:"):
            finish_section()
            m = re.match(r"\[voice:([^\]]+)\]", line)
            if m:
                current_voice_alias = m.group(1).strip()
            continue

        # Content lines
        if line.strip() == "":
            # Preserve empty line separators between content chunks
            if len(current_text_lines) > 0:
                current_text_lines.append("")
        else:
            # Only record text when a voice alias is set (matches UI behavior)
            if current_voice_alias:
                current_text_lines.append(line.strip())

    # Finish trailing structures
    finish_paragraph()

    chapter = Chapter(id=chapter_id, title=chapter_title, aliases=aliases, paragraphs=paragraphs)
    return ChapterResponse(chapter=chapter)