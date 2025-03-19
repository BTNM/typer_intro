import typer
from typing import Optional
from enum import Enum
import os
import sys
import glob
import shutil
import json
import asyncio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from typer_func import translate_to_eng


app = typer.Typer()


class FileFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    JSONLINES = "jsonl"


@app.command()
def convert(
    input_file: str,
    output_format: FileFormat,
    output_file: Optional[str] = None,
    verbose: bool = False,
):
    """
    Convert files between different formats.
    """
    if verbose:
        typer.echo(f"Converting {input_file} to {output_format}")

    # Conversion logic would go here
    typer.echo(f"Converted to {output_format}")


@app.command()
def process(
    files: list[str],
    debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug mode"),
    force: bool = typer.Option(False, "--force", "-f", help="Force processing"),
):
    """
    Process multiple files at once.
    """
    for file in files:
        typer.echo(f"Processing {file}")
        if debug:
            typer.echo("Debug info...")


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


# @app.command()
# def rename(
#     input_directory: str = typer.Argument(
#         "../storage",
#         help="Input directory storage for raw jsonl files",
#         exists=True,
#         file_okay=False,
#         dir_okay=True,
#     ),
#     # output_directory: str = typer.Argument(
#     #     "../storage_txt",
#     #     help="Output directory Storage for renamed txt files",
#     #     exists=True,
#     #     file_okay=False,
#     #     dir_okay=True,
#     # ),
# ):
#     typer.echo("Renaming files...")
#     jsonl_files = glob.glob(os.path.join(input_directory, "**", "*.jl"), recursive=True)
#     for file in jsonl_files:
#         # Read the first line of the JSONL file to get the novel title
#         with open(file, "r", encoding="utf-8") as f:
#             first_line = f.readline()
#             data = json.loads(first_line)
#             novel_title = data.get("novel_title", "")

#         # Translate the title to English using asyncio
#         translated_title = asyncio.run(translate_to_eng(novel_title, "ja"))
#         print(f"translated_title: {translated_title}")

#         # Create a valid filename from the translated title
#         safe_title = (
#             "".join(
#                 word
#                 for word in translated_title
#                 if word.isalnum() or word in (" ", "-", "_")
#             )
#             .strip()
#             .replace(" ", "_")
#         )
#         print(f"safe_title: {safe_title}")

#         # # Only proceed if translation was successful
#         # if safe_title and safe_title != "Translation error invalid source language":
#         #     # Create the new file path with .txt extension in output_directory
#         #     new_file = os.path.join(output_directory, f"{safe_title}.txt")

#         #     # Copy the file to the new location with new name
#         #     if not os.path.exists(new_file):
#         #         typer.echo(f"Copying {file} to {new_file}")
#         #         shutil.copy2(file, new_file)
#         #     else:
#         #         typer.echo(f"File {new_file} already exists, skipping...")
#         # else:
#         #     typer.echo(f"Skipping {file} due to translation error")


def find_jsonl_files(directory: str):
    """Find all .jl files recursively in the given directory."""
    return glob.glob(os.path.join(directory, "**", "*.jl"), recursive=True)


def get_new_directory(file, directory: str, name: str) -> str:
    """Create a new directory with _txt suffix."""
    # Get relative path to maintain directory structure
    file_relative_path: str = os.path.relpath(file, directory)
    # typer.echo(f"file relative path: {file_relative_path}")
    # scrapyd_webnovel_jsonl/syosetu_spider/960159f6ff8611ef85850242ac110002.jl
    directory_path = os.path.dirname(file_relative_path)
    # typer.echo(f"Directory path: {directory_path}")
    # scrapyd_webnovel_jsonl/syosetu_spider

    # Create corresponding output directory
    storage_directory = os.path.join(name, directory_path)
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


@app.command()
def rename(
    directory: str = typer.Argument(
        "storage",
        help="Input directory storage for raw jsonl files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    """Rename JSON files directly using translated novel titles."""
    typer.echo("Renaming files...")

    os.makedirs(directory, exist_ok=True)
    jsonl_files = find_jsonl_files(directory)

    for file in jsonl_files:
        file_dir = os.path.dirname(file)
        safe_title = translate_file_title(file)

        if safe_title and safe_title != "Translation error invalid source language":
            new_file = os.path.join(file_dir, f"{safe_title}.jl")
            if file != new_file:  # Only rename if name is different
                if not os.path.exists(new_file):
                    typer.echo(f"Renaming to: {new_file}")
                    os.rename(file, new_file)
                else:
                    typer.echo(f"File exists, skipping: {new_file}")
        else:
            typer.echo(f"Translation failed for: {file}")


@app.command()
def copy_rename(
    directory: str = typer.Argument(
        "storage",
        help="Input directory storage for raw jsonl files",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
):
    """Rename and translate Japanese novel titles and organize them in new directories."""
    typer.echo("Renaming files...")

    # Create base output directory with _txt suffix
    storage_directory_name = f"{directory}_txt"
    os.makedirs(storage_directory_name, exist_ok=True)

    # Find all .jl files recursively
    jsonl_files = find_jsonl_files(directory)

    for file in jsonl_files:
        storage_directory_path = get_new_directory(
            file, directory, storage_directory_name
        )
        safe_title = translate_file_title(file)

        # Create output file path
        new_file = os.path.join(storage_directory_path, f"{safe_title}.txt")

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
