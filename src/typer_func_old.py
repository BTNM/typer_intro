import os
import jsonlines
from typing import Optional


def check_title_text_skip(chapter: dict):
    """
    Check if the chapter title includes specific words that indicate it should be skipped.
    Args:
        chapter (dict): A dictionary containing the chapter data, including the chapter title and number.

    Returns:
        bool: True if the chapter title includes specific words that indicate it should be skipped, False otherwise.
    """
    skip_content_titles = ["人物紹介", "登場人物"]
    # iterates through each title to check if it is present in the chapter title
    for title_check in skip_content_titles:
        if title_check in chapter.get("chapter_title"):
            return True  # returns True, and start end num rest if the chapter should be skipped
    return False  # returns False and start end num rest if the chapter should not be skipped


def increase_chapter_modulo_rest_check(
    chapter_start_modulo_rest: int,
    chapter_end_modulo_rest: int,
    output_chapter_range: int,
):
    """
    Increase chapter modulo rest check variable, if rest is equal to output_chapter_range then reset back to 0 to get correct numbering
    """
    chapter_start_modulo_rest += 1
    chapter_end_modulo_rest += 1
    #
    if chapter_start_modulo_rest == output_chapter_range:
        chapter_start_modulo_rest = 0
    if chapter_end_modulo_rest == output_chapter_range:
        chapter_end_modulo_rest = 0

    return chapter_start_modulo_rest, chapter_end_modulo_rest


def modulo_increase_on_title_skip(chapter, output_chapter_range):
    title_skip = check_title_text_skip(chapter)
    if title_skip:
        # Increase chapter modulo check when skip chapter, if equal to output range reset to avoid start number on skipped chapters
        # chapter_num = 14 , output_chapter_range 10
        if (
            int(chapter.get("chapter_number")) % output_chapter_range
            == chapter_start_modulo_rest
        ):
            chapter_start_modulo_rest, chapter_end_modulo_rest = (
                increase_chapter_modulo_rest_check(
                    chapter_start_modulo_rest,
                    chapter_end_modulo_rest,
                    output_chapter_range,
                )
            )
        # continue to next loop on if
        return True
    return False


def add_main_text_content(chapter, main_text):
    """Add the main text content of a chapter to the main output text.
    Args:
        chapter (dict): A dictionary containing the chapter information,
            including the title, foreword, main text, and afterword.
        main_text (str): The main output text that the chapter content will be added to.

    Returns:
        str: The updated main output text.
    """
    # Add the chapter title to the main output text and foreword and afterword if they exist.
    main_text += chapter.get("chapter_title") + "\n"
    if chapter.get("chapter_foreword"):
        main_text += chapter.get("chapter_foreword") + "\n"
    # add main chapter content
    main_text += chapter.get("chapter_text") + "\n"
    if chapter.get("chapter_afterword"):
        main_text += chapter.get("chapter_afterword") + "\n"

    return main_text


def output_text_to_file(file_path: str, chapter_text: str):
    """
    Save the content of chapter range to a text file in the specified directory path.
    Args:
        file_path (str): The path where where the directory, novel name and filename into a path
        chapter_text (str): The content of the chapter to be saved.
    """
    # opens the file for writing with utf-8 encoding and writes the chapter content to the file
    with open(file_path, "w", encoding="utf-8") as text_file:
        text_file.write(chapter_text)


def process_jsonl_file_old(
    file: str,
    directory_path: str,
    output_chapter_range: int = 10,
    start_chapter: Optional[int] = None,
):
    """
    Read a JSON lines file containing a novel content, split into sized chapters, then write each
    group of chapters to a separate text file.

    Args:
        file (str): Path to the JSON lines file.
        length (int): The maximum length of each chapter text. Defaults to 10.
    """
    main_text = ""
    chapter_start_modulo_rest = 1
    chapter_end_modulo_rest = 0
    output_chapter_range = int(output_chapter_range)

    start_chapter_numbering = start_chapter if start_chapter else 1

    with jsonlines.open(file, "r") as jsonlinesReader:
        for chapter in jsonlinesReader.iter(type=dict, skip_invalid=True):
            chapter_number = chapter.get("chapter_number")
            # Skip chapter content if chapter title in the skip list
            title_skip = check_title_text_skip(chapter)

            if modulo_increase_on_title_skip(chapter, output_chapter_range):
                # continue to next loop on if
                continue

            # save start and end chapter num to add to file text name
            if int(chapter_number) % output_chapter_range == chapter_start_modulo_rest:
                if chapter.get("volume_title"):
                    main_text += chapter.get("volume_title") + "\n"
                start_chapter_numbering = chapter_number

            # add chapter title to main output text and foreword and afterword if exist
            main_text = add_main_text_content(chapter, main_text)

            # get last novel chapter number from the start, end list
            chapter_last_num = chapter.get("chapter_start_end").split("/")[1]
            # Every output_chapter_range chapter section and save novel title, last chapter number to the text file output
            if (
                int(chapter_number) % output_chapter_range == chapter_end_modulo_rest
                or chapter_number == chapter_last_num
            ):
                novel_title = chapter.get("novel_title")
                # novel_title = translate_safe_title(chapter.get("novel_title"))
                novel_description = chapter.get("novel_description")
                start_end_chapter_number = f"{start_chapter_numbering}-{chapter_number}"
                # add start and end chapter prefix to main text, novel title and description if first txt output
                if int(start_chapter_numbering) <= output_chapter_range:
                    main_text = f"{start_end_chapter_number} {novel_title}\n{novel_description}\n{main_text}"
                else:
                    main_text = f"{start_end_chapter_number} {main_text}"

                # Get the base directory name and add _text suffix
                base_dir = os.path.basename(os.path.dirname(file))
                output_text_directory = os.path.join(
                    os.path.dirname(os.path.dirname(file)), f"{base_dir}_text"
                )
                # typer.echo(f"Output directory: {output_text_directory}")
                # /home/btnm/storage_jl/scrapyd_webnovel_jsonl/syosetu_spider_text

                # Create output directory if it doesn't exist
                os.makedirs(output_text_directory, exist_ok=True)

                filename = f"{start_end_chapter_number} {novel_title[:30]}.txt"
                # typer.echo(f"Filename: {filename}")

                # Create the full output path by joining the output directory and filename
                file_path = os.path.join(output_text_directory, filename)
                output_text_to_file(file_path, main_text)
                # Clear main_text after writing to file
                main_text = ""
