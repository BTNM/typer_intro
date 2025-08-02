import os
import jsonlines
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple
from utils_translate import translate_title


@dataclass
class Chapter:
    """Represents a single chapter of a novel with optimized storage."""

    number: int
    title: str = ""
    volume: str = ""
    foreword: str = ""
    content: str = ""
    afterword: str = ""
    is_skipped: bool = False

    def __post_init__(self):
        """Check if chapter should be skipped based on title patterns."""
        skip_patterns = ["人物紹介", "登場人物"]
        self.is_skipped = any(p in self.title for p in skip_patterns)

    def formatted_content(self) -> str:
        """Returns formatted chapter content with all sections."""
        parts = []
        if self.volume:
            parts.append(self.volume)
        if self.title:
            parts.append(self.title)
        if self.foreword:
            parts.append(self.foreword)
        parts.append(self.content)
        if self.afterword:
            parts.append(self.afterword)
        return "\n".join(parts)


@dataclass
class Novel:
    """Represents a novel with optimized chunk processing."""

    title: str = ""
    description: str = ""
    source_path: str = ""
    output_dir: str = ""
    chunk_size: int = 10
    chapters: List[Chapter] = field(default_factory=list)
    current_chunk: List[Chapter] = field(default_factory=list)

    def add_chapter(self, chapter: Chapter) -> None:
        """Add chapter to novel, handling skip logic."""
        if not chapter.is_skipped:
            self.chapters.append(chapter)
            self.current_chunk.append(chapter)

    def should_flush_chunk(self) -> bool:
        """Check if current chunk should be written to file."""
        return len(self.current_chunk) >= self.chunk_size

    def flush_chunk(self) -> None:
        """Write current chunk to file and reset buffer."""
        if not self.current_chunk:
            return

        start = self.current_chunk[0].number
        end = self.current_chunk[-1].number
        content = self._build_chunk_content(start, end)
        self._write_chunk_file(start, end, content)
        self.current_chunk = []

    def _build_chunk_content(self, start: int, end: int) -> str:
        """Combine chapters into formatted chunk content."""
        header = (
            f"{start}-{end} {self.title}\n{self.description}\n"
            if start == 1
            else f"{start}-{end} "
        )
        content = "".join(ch.formatted_content() for ch in self.current_chunk)
        return header + content

    def _write_chunk_file(self, start: int, end: int, content: str) -> None:
        """Write chunk content to appropriately named file."""
        # Use the provided output directory directly
        output_dir = self.output_dir

        # Create filename with chapter range and title
        safe_title = translate_title(self.title)
        if "error" in safe_title.lower() or not safe_title.strip():
            safe_title = self.title if self.title.strip() else "untitled_novel"

        filename = f"{start}-{end} {safe_title[:30]}.txt"
        filepath = os.path.join(output_dir, safe_title, filename)

        # Ensure novel-specific directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


def process_jsonl_file3(filepath: str, output_dir: str, chunk_size: int = 10) -> None:
    """Optimized JSONL processor using new Novel and Chapter classes."""
    # Initialize novel object
    novel = Novel(
        source_path=filepath,
        output_dir=output_dir,
        chunk_size=chunk_size,
    )

    with jsonlines.open(filepath) as reader:
        for data in reader:
            # Extract novel title and description from the first entry
            if not novel.title:
                novel.title = data.get("novel_title", "")
                novel.description = data.get("novel_description", "")

            chapter = Chapter(
                number=int(data["chapter_number"]),
                title=data.get("chapter_title", ""),
                volume=data.get("volume_title", ""),
                foreword=data.get("chapter_foreword", ""),
                content=data.get("chapter_text", ""),
                afterword=data.get("chapter_afterword", ""),
            )

            novel.add_chapter(chapter)

            if novel.should_flush_chunk():
                novel.flush_chunk()

    # Flush any remaining chapters
    novel.flush_chunk()
