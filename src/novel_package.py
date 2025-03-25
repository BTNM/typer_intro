from dataclasses import dataclass
from typing import Optional


@dataclass
class NovelPackage:
    file: str
    directory_path: str
    output_chapter_range: int
    start_chapter: Optional[int]
    start_range_modulo: int = 1
    end_range_modulo: int = 0
    main_text: str
    # novel_start: int = 1
    # novel_end: int
