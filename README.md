# Web Novel Processing Tool

A command-line tool for crawling, processing, and organizing Japanese web novels (particularly from Syosetu and Nocturne), with features for translation and text file generation.

## Features

- **Web Crawling**: Crawl novels from Syosetu (ncode.syosetu.com) and Nocturne (novel18.syosetu.com)
- **JSONL Processing**: Process crawled data stored in JSONL format
- **Text Unpacking**: Convert JSONL files into organized text files with translated novel titles with configurable chapter grouping
- **File Organization**: Automatically organize processed novels into structured directories

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/BTNM/typer_intro.git
   cd typer_intro
   ```

2. Install dependencies (choose one method):

   **Using pip:**
   ```bash
   pip install -r requirements.txt
   ```

   **Using uv (recommended for faster installation):**
   ```bash
   # Install uv if you haven't already
   pip install uv

   # Install dependencies using uv
   uv pip install -r requirements.txt
   ```

## Usage

All commands should be run from the `src/` directory:

```bash
cd src/
```

### Available Commands

#### 1. List Files
List all JSONL files in a directory.

```bash
# List files in default 'storage_jl' directory
typer main.py run list

# List files with detailed information
typer main.py run list --list

# List files in a specific directory
typer main.py run list /path/to/directory
```

#### 2. Crawl Novels

##### Syosetu Spider
Crawl novels from Syosetu (ncode.syosetu.com).

```bash
# Crawl a novel with default URL
typer main.py run syosetu-spider

# Crawl a specific novel
typer main.py run syosetu-spider https://ncode.syosetu.com/n8356ga/

# Crawl starting from a specific chapter
typer main.py run syosetu-spider https://ncode.syosetu.com/n8356ga/ --start-chapter 201
typer main.py run syosetu-spider https://ncode.syosetu.com/n8356ga/ -sc 201
```

##### Nocturne Spider
Crawl novels from Nocturne (novel18.syosetu.com).

```bash
# Crawl a novel with default URL
typer main.py run nocturne-spider

# Crawl a specific novel
typer main.py run nocturne-spider https://novel18.syosetu.com/n0153ce/

# Crawl starting from a specific chapter
typer main.py run nocturne-spider https://novel18.syosetu.com/n0153ce/ --start-chapter 50
typer main.py run nocturne-spider https://novel18.syosetu.com/n0153ce/ -sc 50
```


#### 3. File Management

##### Rename
Rename JSONL files using translated novel titles.

```bash
# Rename files in default 'storage_jl' directory
typer main.py run rename

# Rename files in a specific directory
typer main.py run rename /path/to/directory
```

##### Copy and Rename
Copy files to a new directory structure with translated titles.

```bash
# Copy and rename files in default 'storage_jl' directory
typer main.py run copy-rename

# Copy and rename files in a specific directory
typer main.py run copy-rename /path/to/directory
```

#### 4. Process JSONL Files

##### Unpack (Latest)
Process JSONL files into text files with optimized processing.

```bash
# Process files in default 'storage_jl' directory with default chapter length (10)
typer main.py run unpack

# Process files in a specific directory
typer main.py run unpack /path/to/directory

# Process with custom chapter length
typer main.py run unpack --length 20
typer main.py run unpack -l 20
```

##### Unpack3 (Optimized)
Process JSONL files using the optimized v2 processing logic.

```bash
# Process files with optimized logic
typer main.py run unpack3

# Process with custom chapter length
typer main.py run unpack3 --length 15
typer main.py run unpack3 -l 15
```

## How It Works

1. **Crawling**: The spiders crawl web novels and save data in JSONL format
2. **Processing**: JSONL files are processed to extract chapter content
3. **Translation**: Japanese titles are translated to English for filenames
4. **Organization**: Chapters are grouped into text files (default 10 chapters per file)
5. **Output**: Text files are organized in directories by novel title

## Configuration

- Default storage directory: `storage_jl`
- Default output directory: `storage_jl_text`
- Default chapter grouping: 10 chapters per text file
