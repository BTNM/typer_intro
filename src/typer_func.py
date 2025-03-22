import os
import asyncio
import glob
import json
from googletrans import Translator


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


def translate_file_title(file: str):
    """Translate the title of the novel from Japanese to English."""
    # Read and translate title
    with open(file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        data = json.loads(first_line)
        novel_title = data.get("novel_title", "")

    translated_title = asyncio.run(translate_to_eng(novel_title, "ja"))
    # typer.echo(f"Translating: {novel_title} -> {translated_title}")

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


if __name__ == "__main__":
    asyncio.run(test_translate())
