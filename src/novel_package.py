import os
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from utils_translate import translate_safe_title, translate_title

# Chapter skipping constants
SKIP_TITLE_PATTERNS = ["人物紹介", "登場人物"]


@dataclass
class Chapter:
    chapter_number: int
    volume_title: Optional[str] = None
    chapter_title: Optional[str] = None
    chapter_foreword: Optional[str] = None
    chapter_text: Optional[str] = None
    chapter_afterword: Optional[str] = None

    def get_chapter_text(self) -> str:
        """Combine all chapter content into a single string."""
        chapter_parts = [
            self.volume_title,
            self.chapter_title,
            self.chapter_foreword,
            self.chapter_text,
            self.chapter_afterword,
        ]
        return "\n".join(text_part for text_part in chapter_parts if text_part)

    def check_skip_chapter(self) -> bool:
        """Check if chapter should be skipped based on its title."""
        return any(pattern in self.chapter_title for pattern in SKIP_TITLE_PATTERNS)


@dataclass
class NovelPackage:
    filepath_jl: str
    directory_path: str
    novel_title: str = ""
    novel_description: str = ""
    output_chapter_length: int = 10
    start_at_chapter: Optional[int] = None
    lastest_chapter: int = 0
    current_chapter_number: int = 0
    chapters: List[Chapter] = field(default_factory=list)
    chunk_start_chapter: int = 1
    chunk_end_chapter: int = 0

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the novel."""
        self.chapters.append(chapter)

    def get_novel_text(self) -> str:
        """Combine all chapters into a single string."""
        novel_text = "".join(chapter.get_chapter_text() for chapter in self.chapters)
        return novel_text

    def check_reset_chunk_positions(self):
        """Reset chunk position counters if they reach output chapter length."""
        if self.chunk_start_chapter == self.output_chapter_length:
            self.chunk_start_chapter = 0
        if self.chunk_end_chapter == self.output_chapter_length:
            self.chunk_end_chapter = 0

    def process_chunk_position(self, chapter_number: int):
        """
        Process chapter chunk position and handle increment to increase start chapter position
        """
        # Check if chapter number matches the starting position in chunk pattern
        increase_chunk_chapter_position = (
            int(chapter_number) % self.output_chapter_length == self.chunk_start_chapter
        )

        if increase_chunk_chapter_position:
            # Increment chunk values to increase start chapter position
            self.chunk_start_chapter += 1
            self.chunk_end_chapter += 1

            self.check_reset_chunk_positions()

    def check_start_new_chunk(self, chapter_number: int) -> None:
        """Start a new chunk if the chapter number matches the chunk start chapter."""
        if int(chapter_number) % self.output_chapter_length == self.chunk_start_chapter:
            self.current_chapter_number = chapter_number

    def should_write_chunk(self, chapter_number: int) -> bool:
        """Check if current chunk should be written to file."""
        return (
            int(chapter_number) % self.output_chapter_length == self.chunk_end_chapter
            or chapter_number == self.lastest_chapter
        )

    def add_chapter_prefix_start_end(self, start: int, end: int) -> Tuple[str, str]:
        """Process a range of chapters and return filename components"""
        chapter_start_end = f"{start}-{end}"
        if int(start) <= self.output_chapter_length:
            prefix = (
                f"{chapter_start_end} {self.novel_title}\n{self.novel_description}\n"
            )
        else:
            prefix = f"{chapter_start_end} "
        return chapter_start_end, prefix

    def write_chunk_to_file(self, text_content: str, chapter_start_end: str) -> None:
        """Write a chunk of text to file with appropriate naming and directory structure.

        Args:
            text_content (str): The processed text content to write
            chapter_start_end (str): Chapter range text for filename
        """
        # Get the base directory name and add _text suffix
        base_dir = os.path.basename(os.path.dirname(self.filepath_jl))
        output_text_directory = os.path.join(
            os.path.dirname(os.path.dirname(self.filepath_jl)), f"{base_dir}_text"
        )

        # Create output directory if needed
        os.makedirs(output_text_directory, exist_ok=True)

        english_title = translate_title(self.novel_title)
        # Create a novel-specific directory using the novel title
        novel_directory = os.path.join(output_text_directory, english_title)
        os.makedirs(novel_directory, exist_ok=True)

        # Create filename with chapter range and truncated novel title
        filename = f"{chapter_start_end} {self.novel_title[:30]}.txt"

        # Create full output path
        file_path = os.path.join(novel_directory, filename)

        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
