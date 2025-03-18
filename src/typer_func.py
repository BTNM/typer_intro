from googletrans import Translator
import asyncio


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


if __name__ == "__main__":
    asyncio.run(test_translate())
