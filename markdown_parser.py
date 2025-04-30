"""
Markdown Parser Module

This module provides functionality to parse Markdown documents with custom file annotations
and process them for text-to-speech conversion.
"""

import os
import re
from typing import List, Dict, Tuple, Optional


class MarkdownSection:
    """
    Represents a section in a Markdown document.
    """
    
    def __init__(self, title: str, content: str, file_path: Optional[str] = None, voice_name: Optional[str] = None):
        """
        Initialize a Markdown section.
        
        Args:
            title (str): The title of the section.
            content (str): The content of the section.
            file_path (str, optional): The file path where the audio should be saved.
            voice_name (str, optional): The name of the voice to use for this section.
        """
        self.title = title
        self.content = content
        self.file_path = file_path
        self.voice_name = voice_name
    
    def __str__(self) -> str:
        """
        String representation of the section.
        """
        voice_info = f", Voice: {self.voice_name}" if self.voice_name else ""
        return f"Section: {self.title}\nFile: {self.file_path}{voice_info}\nContent: {self.content[:50]}..."


class MarkdownParser:
    """
    Parser for Markdown documents with custom file annotations.
    """
    
    def __init__(self):
        """
        Initialize the Markdown parser.
        """
        # Regex pattern to match headings with file and voice annotations
        # Examples: 
        # ## Section Title {file=output.mp3}
        # ## Section Title {file=output.mp3, voice=Aria}
        # ## Section Title {file=output.mp3 voice=Aria}
        self.heading_pattern = re.compile(r'^(#+)\s+(.*?)(?:\s+\{(.*?)\})?$', re.MULTILINE)
        
        # Regex patterns to extract parameters from the annotation
        self.file_pattern = re.compile(r'file=(.*?)(?:,|\s|$)')
        self.voice_pattern = re.compile(r'voice=(.*?)(?:,|\s|$)')
    
    def generate_filename_from_title(self, title: str) -> str:
        """
        Generate a filename from a section title by removing special characters and replacing spaces with underscores.
        
        Args:
            title (str): The section title.
            
        Returns:
            str: A sanitized filename.
        """
        # Remove special characters and replace spaces with underscores
        filename = re.sub(r'[^\w\s-]', '', title).strip().lower()
        filename = re.sub(r'[-\s]+', '_', filename)
        return filename + ".mp3"
    
    def parse(self, markdown_text: str) -> List[MarkdownSection]:
        """
        Parse a Markdown document and extract sections with file annotations.
        If no file annotation is provided, generate a filename from the section title.
        
        Args:
            markdown_text (str): The Markdown document text.
            
        Returns:
            List[MarkdownSection]: A list of parsed sections.
        """
        # Find all headings with their positions
        headings = []
        for match in self.heading_pattern.finditer(markdown_text):
            level = len(match.group(1))  # Number of # characters
            title = match.group(2).strip()
            annotation = match.group(3) if match.group(3) else None
            position = match.start()
            
            # Extract file path and voice name from the annotation
            file_path = None
            voice_name = None
            if annotation:
                file_match = self.file_pattern.search(annotation)
                if file_match:
                    file_path = file_match.group(1).strip()
                
                voice_match = self.voice_pattern.search(annotation)
                if voice_match:
                    voice_name = voice_match.group(1).strip()
            
            headings.append((level, title, file_path, voice_name, position))
        
        # Extract content between headings
        sections = []
        
        # Keep track of parent sections for nested headings
        section_hierarchy = {}  # level -> title
        
        for i, (level, title, file_path, voice_name, position) in enumerate(headings):
            # Get content until the next heading or end of text
            if i < len(headings) - 1:
                next_position = headings[i + 1][4]  # Position is now at index 4
                content = markdown_text[position:next_position]
            else:
                content = markdown_text[position:]
            
            # Remove the heading line itself from the content
            content = content.split('\n', 1)[1] if '\n' in content else ''
            
            # Update section hierarchy
            section_hierarchy[level] = title
            
            # Generate file path if not provided
            if not file_path:
                # Build the full section path based on hierarchy
                section_path = []
                for l in range(1, level + 1):
                    if l in section_hierarchy:
                        section_path.append(section_hierarchy[l])
                
                # Generate filename from the section path
                file_path = self.generate_filename_from_title("_".join(section_path))
            
            # Add the section
            sections.append(MarkdownSection(title, content.strip(), file_path, voice_name))
        
        return sections


def process_markdown(markdown_text: str) -> List[MarkdownSection]:
    """
    Process a Markdown document and extract sections with file annotations.
    
    Args:
        markdown_text (str): The Markdown document text.
        
    Returns:
        List[MarkdownSection]: A list of parsed sections.
    """
    parser = MarkdownParser()
    return parser.parse(markdown_text)
