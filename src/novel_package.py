import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class NovelPackage:
    file: str
    directory_path: str
    output_chapter_range: int
    start_chapter: Optional[int] = None
    start_range_modulo: int = 1
    end_range_modulo: int = 0
    main_text: str = ""
    novel_title: str = ""
    novel_description: str = ""
    chapters: List[dict] = field(default_factory=list)
    current_chapter_number: int = 0

    def add_chapter_content(self, chapter: dict) -> None:
        """Add chapter content to main text"""
        if chapter.get("volume_title"):
            self.main_text += chapter.get("volume_title") + "\n"

        self.main_text += chapter.get("chapter_title", "") + "\n"
        if chapter.get("chapter_foreword"):
            self.main_text += chapter.get("chapter_foreword") + "\n"
        self.main_text += chapter.get("chapter_text", "") + "\n"
        if chapter.get("chapter_afterword"):
            self.main_text += chapter.get("chapter_afterword") + "\n"

    def should_write_chunk(self, chapter_number: int, last_chapter: int) -> bool:
        """Check if current chunk should be written to file"""
        return (
            int(chapter_number) % self.output_chapter_range == self.end_range_modulo
            or chapter_number == last_chapter
        )

    def write_chunk_to_file(self, text_content: str, range_text: str) -> None:
        """Write a chunk of text to file with appropriate naming and directory structure

        Args:
            text_content (str): The processed text content to write
            range_text (str): Chapter range text for filename
        """
        # Get the base directory name and add _text suffix
        base_dir = os.path.basename(os.path.dirname(self.file))
        output_text_directory = os.path.join(
            os.path.dirname(os.path.dirname(self.file)), f"{base_dir}_text"
        )

        # Create output directory if needed
        os.makedirs(output_text_directory, exist_ok=True)

        # Create filename with chapter range and truncated novel title
        filename = f"{range_text} {self.novel_title[:30]}.txt"

        # Create full output path
        file_path = os.path.join(output_text_directory, filename)

        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
