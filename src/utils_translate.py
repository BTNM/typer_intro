import asyncio
import json
from googletrans import Translator
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


def translate_title(title: str):
    """Translate the title of the novel from Japanese to English."""
    translated_title = asyncio.run(translate_to_eng(title, "ja"))
    # typer.echo(f"Translating: {title} -> {translated_title}")

    return translated_title


def translate_file_title(file: str):
    """Translate the title of the novel from Japanese to English."""
    # Read and translate title
    with open(file, "r", encoding="utf-8") as f:
        first_line = f.readline()
        data = json.loads(first_line)
        novel_title = data.get("novel_title", "")

    return translate_safe_title(novel_title)
