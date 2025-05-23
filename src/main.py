import os
import sys
import glob
import shutil
import json
import typer
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils_translate import translate_file_title
from typer_func import (
    get_new_directory,
    find_jsonl_files,
    process_jsonl_file,
)

HOME_USER = os.path.expanduser("~")

app = typer.Typer()


@app.command()
def list(
    directory: str = typer.Argument(
        "storage_jl",  # default value
        help="Storage directory to process",  # help text
        exists=True,  # verify directory exists
        file_okay=False,  # must be directory, not file
        dir_okay=True,  # allow directories)
    ),
    list_mode: bool = typer.Option(
        False, "--list", "-l", help="List files in more detail"
    ),
):
    """List all files in the home user given directory (defaults to 'storage_jl')."""
    storage_directory_path = os.path.normpath(os.path.join(HOME_USER, directory))

    typer.echo(f"Listing files in {storage_directory_path}...")
    jsonl_files = glob.glob(
        os.path.join(storage_directory_path, "**", "*.jl"), recursive=True
    )
    for file in jsonl_files:
        if list_mode:
            file_stats = os.stat(file)
            typer.echo(f"{file} - Size: {file_stats.st_size / (1024 * 1024):.2f} MB")
        else:
            typer.echo(file)


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
    storage_directory_path = os.path.normpath(os.path.join(HOME_USER, directory))
    typer.echo(f"Processing directory: {storage_directory_path}")

    if not os.path.exists(storage_directory_path):
        typer.echo(f"Directory not found at path: {storage_directory_path}")
        raise typer.Exit(1)

    jsonl_files = find_jsonl_files(storage_directory_path)

    # typer.echo(
    #     f"Unpacking jsonl files in {directory} into text file with chapter length {length}"
    # )
    if jsonl_files:  # Check if list is not empty
        # file = jsonl_files[0]  # Get first file only
        for file in jsonl_files:
            # for file in jsonl_files:
            file_directory_path = os.path.dirname(file)
            # typer.echo(f"directory_path: {file_directory_path}")
            typer.echo(f"Unpacking file: {file}")
            # process_jsonl_file_old(file, directory_path, length)
            process_jsonl_file(file, file_directory_path, length)


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
    storage_directory_path = os.path.normpath(os.path.join(HOME_USER, directory))
    typer.echo(f"Processing directory: {storage_directory_path}")

    if not os.path.exists(storage_directory_path):
        typer.echo(f"Directory not found at path: {storage_directory_path}")
        raise typer.Exit(1)

    # os.makedirs(directory_path, exist_ok=True)
    jsonl_files = find_jsonl_files(storage_directory_path)

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

    directory_path = os.path.normpath(os.path.join(HOME_USER, directory))
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
            file, HOME_USER, directory_path, storage_directory_name
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
