import os
import glob
import jsonlines
from typing import Optional
from novel_package import NovelPackage, Chapter


def find_jsonl_files(directory: str):
    """Find all jl files recursively in the given directory.
    Args:
        directory (str): The directory to search for JSONL files.
    Returns:
        list: A list of paths to JSONL files.
    """
    return glob.glob(os.path.join(directory, "**", "*.jl"), recursive=True)


def get_new_directory(file, home_user: str, directory: str, name: str) -> str:
    """Create a new directory with _txt suffix."""
    # Get relative path to maintain directory structure
    file_relative_path: str = os.path.relpath(file, directory)
    # typer.echo(f"file relative path: {file_relative_path}")
    # scrapyd_webnovel_jsonl/syosetu_spider/960159f6ff8611ef85850242ac110002.jl
    directory_path = os.path.dirname(file_relative_path)
    # typer.echo(f"Directory path: {directory_path}")
    # scrapyd_webnovel_jsonl/syosetu_spider

    # Create corresponding output directory
    storage_directory = os.path.join(home_user, name, directory_path)
    os.makedirs(storage_directory, exist_ok=True)
    # typer.echo(f"Output directory: {storage_directory}")
    # storage_txt/scrapyd_webnovel_jsonl/syosetu_spider

    return storage_directory


def process_jsonl_file(
    filepath_jl: str,
    directory_path: str,
    output_chapter_length: int = 10,
    start_at_chapter: Optional[int] = None,
):
    """Process JSONL file and write chapter chunks."""
    novel = NovelPackage(
        filepath_jl=filepath_jl,
        directory_path=directory_path,
        output_chapter_length=output_chapter_length,
        start_at_chapter=start_at_chapter,
    )

    # Get novel title and last chapter from the first chapter
    with jsonlines.open(filepath_jl, "r") as reader:
        for chapter_data in reader.iter(type=dict):
            chapter = Chapter(
                chapter_number=int(chapter_data.get("chapter_number")),
                volume_title=chapter_data.get("volume_title"),
                chapter_title=chapter_data.get("chapter_title"),
                chapter_foreword=chapter_data.get("chapter_foreword"),
                chapter_text=chapter_data.get("chapter_text"),
                chapter_afterword=chapter_data.get("chapter_afterword"),
            )

            # Handle chapter skipping with new logic
            if chapter.check_skip_chapter():
                novel.process_chunk_position(chapter.chapter_number)
                continue

            _update_novel_metadata(novel, chapter_data, chapter)
            _process_novel_chunk(novel, chapter.chapter_number)


def _update_novel_metadata(novel: NovelPackage, chapter_data: dict, chapter: Chapter):
    """Update novel metadata from chapter data."""
    novel.lastest_chapter = int(chapter_data.get("chapter_start_end").split("/")[1])
    novel.novel_title = chapter_data.get("novel_title", "")
    novel.novel_description = chapter_data.get("novel_description", "")
    novel.add_chapter(chapter)


def _process_novel_chunk(novel: NovelPackage, chapter_number: int):
    """Process novel chunk and write to file if needed."""
    # Check if start new chunk
    novel.check_start_new_chunk(chapter_number)

    # Write chunk if needed
    if novel.should_write_chunk(chapter_number):
        chapter_start_end, prefix = novel.add_chapter_prefix_start_end(
            novel.current_chapter_number, chapter_number
        )
        novel.write_chunk_to_file(
            text_content=prefix + novel.get_novel_text(),
            chapter_start_end=chapter_start_end,
        )
        novel.chapters.clear()
