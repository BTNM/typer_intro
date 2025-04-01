import os
from dataclasses import dataclass, field
from typing import Optional, List, Tuple
from utils_translate import translate_safe_title, translate_title


SKIP_TITLES_LIST = ["人物紹介", "登場人物"]


@dataclass
class Chapter:
    chapter_number: int
    volume_title: Optional[str] = None
    chapter_title: Optional[str] = None
    chapter_foreword: Optional[str] = None
    chapter_text: Optional[str] = None
    chapter_afterword: Optional[str] = None
    skip_title_list: list[str] = field(default_factory=lambda: SKIP_TITLES_LIST)

    def get_chapter_text(self) -> str:
        """Combine all chapter content into a single string."""
        text = ""
        if self.volume_title:
            text += self.volume_title + "\n"
        if self.chapter_title:
            text += self.chapter_title + "\n"
        if self.chapter_foreword:
            text += self.chapter_foreword + "\n"
        if self.chapter_text:
            text += self.chapter_text + "\n"
        if self.chapter_afterword:
            text += self.chapter_afterword + "\n"
        return text

    def check_skip_chapter(self) -> bool:
        """Check if the chapter should be skipped based on its title."""
        for title in self.skip_title_list:
            if title == self.chapter_title:
                return True
        return False


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
    start_range_modulo: int = 1
    end_range_modulo: int = 0

    def add_chapter(self, chapter: Chapter) -> None:
        """Add a chapter to the novel."""
        self.chapters.append(chapter)

    def get_novel_text(self) -> str:
        """Combine all chapters into a single string."""
        novel_text = "".join(chapter.get_chapter_text() for chapter in self.chapters)
        return novel_text

    def check_start_new_chunk(self, chapter_number: int) -> None:
        """Start a new chunk if the chapter number matches the start range modulo."""
        if int(chapter_number) % self.output_chapter_length == self.start_range_modulo:
            self.current_chapter_number = chapter_number

    def should_write_chunk(self, chapter_number: int) -> bool:
        """Check if current chunk should be written to file."""
        return (
            int(chapter_number) % self.output_chapter_length == self.end_range_modulo
            or chapter_number == self.lastest_chapter
        )

    def add_chapter_prefix_range_text(self, start: int, end: int) -> Tuple[str, str]:
        """Process a range of chapters and return filename components"""
        chapter_range_text = f"{start}-{end}"
        if int(start) <= self.output_chapter_length:
            prefix = (
                f"{chapter_range_text} {self.novel_title}\n{self.novel_description}\n"
            )
        else:
            prefix = f"{chapter_range_text} "
        return chapter_range_text, prefix

    def write_chunk_to_file(self, text_content: str, range_text: str) -> None:
        """Write a chunk of text to file with appropriate naming and directory structure.

        Args:
            text_content (str): The processed text content to write
            range_text (str): Chapter range text for filename
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
        filename = f"{range_text} {self.novel_title[:30]}.txt"

        # Create full output path
        file_path = os.path.join(novel_directory, filename)

        # Write content to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text_content)
