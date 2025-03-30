from dataclasses import dataclass, field
from doctest import SKIP
from typing import List, Tuple

from novel_package import NovelPackage, Chapter

SKIP_TITLES_LIST = ["人物紹介", "登場人物"]


@dataclass
class ChapterProcessor:
    skip_titles: List[str] = field(default_factory=lambda: SKIP_TITLES_LIST)

    def check_skip_chapter(self, chapter_data: dict) -> bool:
        """Check if chapter should be skipped based on title."""
        for title in self.skip_titles:
            if title in chapter_data.get("chapter_title", ""):
                return True
        return False

    def add_chapter_prefix_range_text(
        self, start: int, end: int, novel_package: NovelPackage
    ) -> Tuple[str, str]:
        """Process a range of chapters and return filename components"""
        chapter_range_text = f"{start}-{end}"
        if int(start) <= novel_package.output_chapter_range:
            prefix = f"{chapter_range_text} {novel_package.novel_title}\n{novel_package.novel_description}\n"
        else:
            prefix = f"{chapter_range_text} "
        return chapter_range_text, prefix
