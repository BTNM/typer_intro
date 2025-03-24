import os
import sys
import glob
import shutil
import json
import typer
from typing import Optional
from enum import Enum
import jsonlines

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typer_func import (
    find_jsonl_files,
    get_new_directory,
    translate_file_title,
    translate_safe_title,
)


app = typer.Typer()


# @app.command()
# def convert(
#     input_file: str,
#     output_format: FileFormat,
#     output_file: Optional[str] = None,
#     verbose: bool = False,
# ):
#     """
#     Convert files between different formats.
#     """
#     if verbose:
#         typer.echo(f"Converting {input_file} to {output_format}")

#     # Conversion logic would go here
#     typer.echo(f"Converted to {output_format}")


# @app.command()
# def process(
#     files: list[str],
#     debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
#     force: bool = typer.Option(False, "--force", "-f", help="Force processing"),
# ):
#     """
#     Process multiple files at once.
#     """
#     for file in files:
#         typer.echo(f"Processing {file}")
#         if debug:
#             typer.echo("Debug info...")


@app.command()
def list(
    directory: str = typer.Argument(
        "../storage",  # default value
        help="Storage directory to process",  # help text
        exists=True,  # verify directory exists
        file_okay=False,  # must be directory, not file
        dir_okay=True,  # allow directories)
    ),
    list_mode: bool = typer.Option(
        False, "--list", "-l", help="List files in more detail"
    ),
):
    """List all files in the given directory (defaults to 'storage')."""
    typer.echo(f"Listing files in {directory}...")
    jsonl_files = glob.glob(os.path.join(directory, "**", "*.jl"), recursive=True)
    for file in jsonl_files:
        if list_mode:
            file_stats = os.stat(file)
            typer.echo(f"{file} - Size: {file_stats.st_size / (1024 * 1024):.2f} MB")
        else:
            typer.echo(file)


# def unpack_jsonl(
#     filename: str = typer.Argument(
#         help="Input JSONL filename to unpack into text file",
#         exists=True,
#         file_okay=True,
#     ),
#     length: int = typer.Option(
#         10, "--length", "-l", help="chapter text length to unpack jsonl file into"
#     ),
# ):
#     """Unpack the JSONL file into a text file."""
#     typer.echo(f"Unpacking {filename} into text file with length {length}...")

#     with open(filename, "r", encoding="utf-8") as f:
#         for line in f:
#             data = json.loads(line)

#     pass


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
    # Create parent directory if it doesn't exist
    # os.makedirs(os.path.dirname(file_path), exist_ok=True)
    # opens the file for writing with utf-8 encoding and writes the chapter content to the file
    with open(file_path, "w", encoding="utf-8") as text_file:
        text_file.write(chapter_text)


def read_jsonl_file(
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
                typer.echo(f"Filename: {filename}")

                # Create the full output path by joining the output directory and filename
                file_path = os.path.join(output_text_directory, filename)
                output_text_to_file(file_path, main_text)
                # Clear main_text after writing to file
                main_text = ""


@app.command()
def unpack(
    directory: str = typer.Argument(
        default="storage_jl",
        help="Input directory storage for raw jsonl files",
        exists=True,
        file_okay=True,
    ),
    length: int = typer.Option(
        10, "--length", "-l", help="chapter text length to unpack jsonl file into"
    ),
):
    """Unpack the JSONL file into a text file."""
    home_user = os.path.expanduser("~")
    storage_directory_path = os.path.normpath(os.path.join(home_user, directory))
    typer.echo(f"Processing directory: {storage_directory_path}")

    if not os.path.exists(storage_directory_path):
        typer.echo(f"Directory not found at path: {storage_directory_path}")
        raise typer.Exit(1)

    jsonl_files = find_jsonl_files(storage_directory_path)

    # typer.echo(
    #     f"Unpacking jsonl files in {directory} into text file with chapter length {length}"
    # )
    if jsonl_files:  # Check if list is not empty
        file = jsonl_files[0]  # Get first file only
        directory_path = os.path.dirname(file)
        # typer.echo(f"directory_path: {directory_path}")
        typer.echo(f"Unpacking: {file}")
        read_jsonl_file(file, directory_path, length)


@app.command()
def rename(
    directory: str = typer.Argument(
        default="storage_jl",  # Remove default value to allow any path
        help="Input directory storage for raw jsonl files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    """Rename JSON files directly using translated novel titles."""
    home_user = os.path.expanduser("~")
    directory_path = os.path.normpath(os.path.join(home_user, directory))
    typer.echo(f"Processing directory: {directory_path}")

    if not os.path.exists(directory_path):
        typer.echo(f"Directory not found at path: {directory_path}")
        raise typer.Exit(1)

    # os.makedirs(directory_path, exist_ok=True)
    jsonl_files = find_jsonl_files(directory_path)

    for file in jsonl_files:
        file_dir = os.path.dirname(file)
        safe_title = translate_file_title(file)

        if safe_title and safe_title != "Translation error invalid source language":
            new_file = os.path.join(file_dir, f"{safe_title}.jl")
            if file != new_file:  # Only rename if name is different
                if not os.path.exists(new_file):
                    typer.echo(f"Renaming to: {new_file}")
                    # os.rename(file, new_file)
                else:
                    typer.echo(f"File exists, skipping: {new_file}")
        else:
            typer.echo(f"Translation failed for: {file}")


@app.command()
def copy_rename(
    directory: str = typer.Argument(
        "storage_jl",
        help="Input directory storage for raw jsonl files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    """Rename and translate Japanese novel titles and organize them in new directories."""
    typer.echo("Renaming files...")

    home_user = os.path.expanduser("~")
    directory_path = os.path.normpath(os.path.join(home_user, directory))
    typer.echo(f"Processing directory: {directory_path}")

    if not os.path.exists(directory_path):
        typer.echo(f"Directory not found at path: {directory_path}")
        raise typer.Exit(1)

    # Create base output directory with _txt suffix
    storage_directory_name = f"{directory}_txt"
    # os.makedirs(storage_directory_name, exist_ok=True)

    # Find all .jl files recursively
    jsonl_files = find_jsonl_files(directory_path)

    for file in jsonl_files:
        storage_directory_path = get_new_directory(
            file, home_user, directory_path, storage_directory_name
        )
        safe_title = translate_file_title(file)

        # Create output file path
        new_file = os.path.join(storage_directory_path, f"{safe_title}.jl")

        # Copy file if translation successful
        if safe_title and safe_title != "Translation error invalid source language":
            if not os.path.exists(new_file):
                typer.echo(f"Copying to: {new_file}")
                shutil.copy2(file, new_file)
            else:
                typer.echo(f"File exists, skipping: {new_file}")
        else:
            typer.echo(f"Translation failed for: {file}")


if __name__ == "__main__":
    app()
