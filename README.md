# Project2Text

Project2Text is a versatile command-line tool that compiles all text-based files in a project directory into a single or multiple output files. It supports various output formats, handles large projects efficiently with multi-threading, and provides extensive customization options.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Command-Line Arguments](#command-line-arguments)
- [Examples](#examples)
- [Output Formats](#output-formats)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## Features
- **Multi-threading**: Processes files concurrently to improve performance on large projects
- **Customizable Output**: Supports Markdown, HTML, and JSON formats
- **File Inclusion/Exclusion**: Include or exclude files based on extensions, patterns, or specific names
- **Ignore Patterns**: Exclude files or directories using glob patterns
- **Size Limitation**: Split output into multiple files if a size limit is exceeded
- **Token Counting**: Counts the number of tokens (words) in the output files
- **Metadata Inclusion**: Optionally include file metadata such as size, last modified date, creation time, permissions, and owner
- **Custom Markers**: Customize start and end markers for file content
- **ASCII Tree Generation**: Generates an ASCII tree representation of the project directory
- **Progress Indicators**: Displays a progress bar during file processing

## Installation

### Prerequisites
- Python 3.6 or higher

### Install Required Libraries
Install the necessary Python libraries using pip:
```bash
pip install chardet tqdm
```

### Clone the Repository
```bash
git clone https://github.com/yourusername/Project2Text.git
cd Project2Text
```

## Usage
The script can be run directly from the command line:
```bash
python project2text.py [options]
```

## Command-Line Arguments
```plaintext
positional arguments:
  dir_path              The directory to scan.
                        Default is the current working directory.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output file name. Default is "project_files.md".
  --format {markdown,html,json}
                        Output file format. Choices are markdown, html, json.
                        Default is "markdown".
  --include [INCLUDE [INCLUDE ...]]
                        File extensions to include (e.g., .py .txt).
  --exclude [EXCLUDE [EXCLUDE ...]]
                        File extensions to exclude (e.g., .exe .dll).
  --exclude-dirs [EXCLUDE_DIRS [EXCLUDE_DIRS ...]]
                        Directories to exclude (default: .git, __pycache__,
                        node_modules).
  --exclude-files [EXCLUDE_FILES [EXCLUDE_FILES ...]]
                        Files to exclude (e.g., secrets.txt).
  --pattern-include [PATTERN_INCLUDE [PATTERN_INCLUDE ...]]
                        Patterns to include (e.g., *.py test_*.txt).
  --pattern-exclude [PATTERN_EXCLUDE [PATTERN_EXCLUDE ...]]
                        Patterns to exclude (e.g., *.log temp_*).
  --ignore [IGNORE [IGNORE ...]]
                        Files or directories to ignore (supports glob
                        patterns, e.g., folder/*, file.txt).
  --start-marker START_MARKER
                        Custom start marker for file content.
  --end-marker END_MARKER
                        Custom end marker for file content.
  --no-metadata         Exclude file metadata from the output.
  --limit LIMIT         Maximum size (in bytes) for each output file. If
                        exceeded, additional files are created.
```

## Examples

### Basic Usage
Compile all files in the current directory into project_files.md:
```bash
python project2text.py
```

### Specify Directory and Output Format
Compile files from a specific directory and output in HTML format:
```bash
python project2text.py "/path/to/project" --format html -o project_files.html
```

### Include Specific File Extensions
Include only .py and .txt files:
```bash
python project2text.py --include .py .txt
```

### Exclude Specific Directories and Files
Exclude .git directory and config.yaml file:
```bash
python project2text.py --exclude-dirs .git --exclude-files config.yaml
```

### Use Ignore Patterns
Ignore all files in logs/ directory and files ending with .log:
```bash
python project2text.py --ignore "logs/*" "*.log"
```

### Limit Output File Size
Set a maximum output file size of 1 MB (1,048,576 bytes):
```bash
python project2text.py --limit 1048576
```

## Output Formats

### Markdown (Default)
Outputs a .md file with:
- ASCII tree of the project directory
- Concatenated file contents with customizable markers
- Optional inclusion of file metadata

### HTML
Outputs a .html file with:
- Proper HTML structure and headings
- File contents displayed within `<pre>` tags
- ASCII tree and file metadata included

### JSON
Outputs a .json file with:
- JSON object containing the ASCII tree and file contents
- File metadata included in the JSON structure

## Limitations
- **Binary Files**: Binary files are automatically skipped to prevent unreadable content
- **Encoding**: The script attempts to read files using their detected encoding but may fail for files with unknown encodings
- **Permissions**: On some operating systems, file owner information may not be accurate
- **Token Counting**: Token counting is approximate, based on splitting text by whitespace

## Contributing
Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Commit your changes with descriptive messages
4. Open a pull request against the main branch

## License
This project is licensed under a license hhh

## Acknowledgments
- **chardet**: Universal encoding detector used for handling file encodings
- **tqdm**: Provides progress bars for long-running operations
- **Python Community**: For the extensive resources and support
