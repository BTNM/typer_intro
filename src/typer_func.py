import os
import asyncio
import glob
import json
import jsonlines
from googletrans import Translator
from typing import Optional, List
from novel_package import NovelPackage
from processor import ChapterProcessor


async def translate_to_eng(text: str, lang: str = "ja"):
    """
    Translate Japanese text to English using Google Translate.

    Args:
        text: Text or sentence to translate
        lang: Source language code ('ja' for Japanese)
    Returns:
        str: Translated text or error message
    """
    translator = Translator()
    try:
        result = await translator.translate(text, src=lang, dest="en")
        return result.text
    except Exception as e:
        return f"Translation error: {str(e)}"


async def test_translate():
    print(await translate_to_eng("こんにちは、世界！"))
    print(await translate_to_eng("おはようございます", "ja"))
    print(await translate_to_eng("Good morning", "en"))


def find_jsonl_files(directory: str):
    """Find all .jl files recursively in the given directory."""
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


def translate_safe_title(title: str):
    """Translate the title of the novel from Japanese to English."""
    translated_title = asyncio.run(translate_to_eng(title, "ja"))
    # typer.echo(f"Translating: {title} -> {translated_title}")

    # Create safe filename
    safe_title = (
        "".join(
            word
            for word in translated_title
            if word.isalnum() or word in (" ", "-", "_")
        )
        .strip()
        .replace(" ", "_")
    )

    return safe_title


def translate_file_title(file: str):
    """Translate the title of the novel from Japanese to English."""
    # Read and translate title
    with open(file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        data = json.loads(first_line)
        novel_title = data.get("novel_title", "")

    return translate_safe_title(novel_title)


def read_jsonl_file_test(
    file: str,
    directory_path: str,
    output_chapter_range: int = 10,
    start_chapter: Optional[int] = None,
):
    """Process JSONL file and write chapter chunks"""
    novel = NovelPackage(
        file=file,
        directory_path=directory_path,
        output_chapter_range=output_chapter_range,
        start_chapter=start_chapter,
    )

    processor = ChapterProcessor()

    with jsonlines.open(file, "r") as reader:
        for chapter in reader.iter(type=dict, skip_invalid=True):
            if processor.check_skip_chapter(chapter):
                continue

            chapter_num = chapter.get("chapter_number")

            # Start new chunk
            if (
                int(chapter_num) % novel.output_chapter_range
                == novel.start_range_modulo
            ):
                novel.current_chapter_number = chapter_num

            novel.add_chapter_content(chapter)

            # Write chunk if needed
            last_chapter = chapter.get("chapter_start_end").split("/")[1]
            if novel.should_write_chunk(chapter_num, last_chapter):
                range_text, prefix = processor.process_chapter_range(
                    novel.current_chapter_number, chapter_num, novel
                )

                write_chunk_to_file(novel, prefix + novel.main_text, range_text)
                novel.main_text = ""


if __name__ == "__main__":
    asyncio.run(test_translate())
