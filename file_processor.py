import os
import sys
import chardet
import logging
import threading
import time
import stat
import json
import html
import fnmatch
from concurrent.futures import ThreadPoolExecutor

from rich.console import Console
from rich.progress import Progress

# Lock for writing to the output file
write_lock = threading.Lock()
def compile_project_files(
        dir_path,
        output_filename,
        output_format,
        include_extensions,
        exclude_extensions,
        exclude_dirs,
        exclude_files,
        pattern_include,
        pattern_exclude,
        ignore_patterns,
        start_marker,
        end_marker,
        no_metadata,
        limit_size,
        progress,
        console: Console,
        task_id=None  # Added task_id parameter with default None
    ):
    """Compiles project files into a single text file based on provided arguments"""

    # Check if the provided directory exists
    if not os.path.isdir(dir_path):
        console.print(f"[red]The directory '{dir_path}' does not exist.[/red]")
        sys.exit(1)
        
    # Validate and adjust file extension based on format
    extension_map = {
        'markdown': '.md',
        'html': '.html',
        'json': '.json'
    }
    markers = {
        'start': start_marker,
        'end': end_marker
    }
    base_name = os.path.splitext(output_filename)[0]
    correct_extension = extension_map.get(output_format)
    
    if correct_extension:
        output_filename = f"{base_name}{correct_extension}"
        console.print(f"Output will be saved as: {output_filename}")

    metadata_options = {
        'File Size': not no_metadata,
        'Last Modified': not no_metadata,
        'Creation Time': not no_metadata,
        'Permissions': not no_metadata,
        'Owner': not no_metadata
    }

    try:
        # Generate the ASCII tree
        tree = generate_tree(dir_path, ignore_patterns=ignore_patterns)

        # Initialize file counter and state
        file_counter = {'count': 1, 'first_file': True, 'tree': tree}

        # Collect all files to process
        file_list = []
        for root, dirs, files in os.walk(dir_path):
            # Apply ignore patterns to directories
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(os.path.join(root, d), pattern) for pattern in ignore_patterns)]
            # Exclude specific directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            # Apply ignore patterns to files
            files = [f for f in files if not any(fnmatch.fnmatch(os.path.join(root, f), pattern) for pattern in ignore_patterns)]
            for file in files:
                if file in exclude_files:
                    continue
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, dir_path)

                # Skip files based on extensions
                if include_extensions and not any(file.endswith(ext) for ext in include_extensions):
                    continue
                if exclude_extensions and any(file.endswith(ext) for ext in exclude_extensions):
                    continue

                # Skip files based on patterns
                if pattern_include and not any(fnmatch.fnmatch(file, pat) for pat in pattern_include):
                    continue
                if pattern_exclude and any(fnmatch.fnmatch(file, pat) for pat in pattern_exclude):
                    continue

                # Skip binary files
                if is_binary(file_path):
                    continue

                file_list.append((file_path, relative_path, output_format, markers, metadata_options, output_filename, limit_size, file_counter))

        # Initialize counters for progress tracking
        total_files = len(file_list)
        files_processed = 0  # Added initialization of files_processed

        # Process files with multi-threading and a progress bar
        with ThreadPoolExecutor() as executor:
            for _ in executor.map(process_file_wrapper, file_list):
                files_processed += 1
                if task_id is not None:
                    # Update progress based on percentage of files processed
                    progress.update(task_id, completed=(files_processed / total_files) * 100)

        # Get the list of output files generated
        output_files = [f"{os.path.splitext(output_filename)[0]}_{i}{os.path.splitext(output_filename)[1]}" for i in range(1, file_counter['count'] + 1)]

        # Calculate the total size and tokens
        total_size = 0
        total_tokens = 0
        for output_file in output_files:
            if os.path.exists(output_file):
                size = os.path.getsize(output_file)
                tokens = count_tokens_in_file(output_file)
                total_size += size
                total_tokens += tokens
                console.print(f"Generated '{output_file}' - Size: {size} bytes, Tokens: {tokens}")

        console.print(f"Total output size: {total_size} bytes")
        console.print(f"Total number of tokens in output files: {total_tokens}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        console.print("[red]An error occurred during processing. Please check the log file for details.[/red]")

def generate_tree(dir_path, ignore_patterns=None):
    """Generates an ASCII tree representation of the directory structure."""
    ignore_patterns = ignore_patterns or []
    tree_lines = []
    for root, dirs, files in os.walk(dir_path):
        # Apply ignore patterns to directories
        dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(os.path.join(root, d), pattern) for pattern in ignore_patterns)]
        level = root.replace(dir_path, '').count(os.sep)
        indent = '    ' * level
        sub_indent = '    ' * (level + 1)
        tree_lines.append(f'{indent}{os.path.basename(root)}/')
        # Apply ignore patterns to files
        files = [f for f in files if not any(fnmatch.fnmatch(os.path.join(root, f), pattern) for pattern in ignore_patterns)]
        for f in files:
            tree_lines.append(f'{sub_indent}{f}')
    return tree_lines

def is_binary(file_path):
    """Determines if a file is binary."""
    try:
        with open(file_path, 'rb') as f:
            initial_bytes = f.read(1024)
        result = chardet.detect(initial_bytes)
        return result['encoding'] is None
    except Exception as e:
        logging.error(f'Error detecting if file is binary {file_path}: {e}')
        return True

def read_file_content(file_path):
    """Reads the content of a file, handling encoding issues."""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            encoding = result['encoding'] or 'utf-8'
            content = raw_data.decode(encoding, errors='replace')
            return content
    except Exception as e:
        logging.error(f'Error reading {file_path}: {e}')
        return f'Could not read file: {e}'

def process_file_wrapper(args):
    """Wrapper function for processing files in the thread pool"""
    process_file(*args)

def process_file(file_path, relative_path, output_format, markers, metadata_options,
                 output_file_path, limit_size, file_counter):
    """Processes a single file and writes its content to the output."""
    content = read_file_content(file_path)

    # Get file metadata
    stats = os.stat(file_path)
    size = stats.st_size
    mtime = time.ctime(stats.st_mtime)
    ctime = time.ctime(stats.st_ctime)
    permissions = stat.filemode(stats.st_mode)
    owner = stats.st_uid  # Note: On Windows, this may not be accurate

    metadata = {
        'File Size': f'{size} bytes',
        'Last Modified': mtime,
        'Creation Time': ctime,
        'Permissions': permissions,
        'Owner': owner
    }

    # Filter metadata based on options
    metadata_str = '\n'.join([f'{key}: {value}' for key, value in metadata.items() if metadata_options.get(key, True)])

    # Prepare content based on output format
    if output_format == 'markdown':
        file_content = f'\n{markers["start"]} {relative_path} {markers["start"]}\n{metadata_str}\n\n{content}\n{markers["end"]} {relative_path} {markers["end"]}\n'
    elif output_format == 'html':
        safe_content = html.escape(content)
        file_content = f'<h2>{relative_path}</h2>\n<pre>\n{safe_content}\n</pre>\n'
    elif output_format == 'json':
        file_content = json.dumps({
            'file': relative_path,
            'metadata': metadata,
            'content': content
        }, ensure_ascii=False) + '\n'
    else:
        file_content = f'\n{markers["start"]} {relative_path} {markers["start"]}\n{metadata_str}\n\n{content}\n{markers["end"]} {relative_path} {markers["end"]}\n'

    # Write to the output file with thread safety
    with write_lock:
        while True:
            current_output_file = f"{os.path.splitext(output_file_path)[0]}_{file_counter['count']}{os.path.splitext(output_file_path)[1]}"
            try:
                if not os.path.exists(current_output_file):
                    # If file doesn't exist, write the explanation and tree
                    write_explanation(current_output_file, output_format=output_format, markers=markers)
                    if file_counter['first_file']:
                        # Only write the tree to the first file
                        write_tree_to_output(current_output_file, file_counter['tree'], output_format)
                        file_counter['first_file'] = False
                current_size = os.path.getsize(current_output_file)
            except FileNotFoundError:
                current_size = 0

            # Check if adding the new content exceeds the limit
            if limit_size and (current_size + len(file_content.encode('utf-8')) > limit_size):
                # Move to the next file
                file_counter['count'] += 1
                continue  # Re-check with the new file
            else:
                with open(current_output_file, 'a', encoding='utf-8') as output_file:
                    output_file.write(file_content)
                break  # Content written, exit the loop

def write_tree_to_output(output_file_path, tree, output_format):
    """Writes the ASCII tree to the output file."""
    if output_format == 'markdown':
        with open(output_file_path, 'a', encoding='utf-8') as output_file:
            output_file.write('## ASCII Tree of the Project Directory\n\n')
            output_file.write('```\n')
            output_file.write('\n'.join(tree))
            output_file.write('\n```\n\n')
    elif output_format == 'html':
        with open(output_file_path, 'a', encoding='utf-8') as output_file:
            output_file.write('<h2>ASCII Tree of the Project Directory</h2>\n<pre>\n')
            output_file.write(html.escape('\n'.join(tree)))
            output_file.write('\n</pre>\n')
    elif output_format == 'json':
        try:
            with open(output_file_path, 'r+', encoding='utf-8') as output_file:
                data = json.load(output_file)
                data['ascii_tree'] = tree
                output_file.seek(0)
                json.dump(data, output_file, ensure_ascii=False, indent=4)
        except json.JSONDecodeError:
            with open(output_file_path, 'w', encoding='utf-8') as output_file:
                data = {'ascii_tree': tree}
                json.dump(data, output_file, ensure_ascii=False, indent=4)

def write_explanation(output_file_path, output_format='markdown', markers=None):
    """Writes an explanation of the file structure at the beginning of the output file."""
    start_marker = markers.get('start', '=== Start of')
    end_marker = markers.get('end', '=== End of')

    if output_format == 'markdown':
        explanation = f"""
# Project Files Compilation

This document contains the concatenated contents of project files.

## Structure Explanation

- **File Contents**: Each file's content is enclosed between markers indicating the start and end of the file.

Markers:
- `{start_marker} relative/path/to/file {start_marker}`: Indicates the beginning of a file's content.
- `{end_marker} relative/path/to/file {end_marker}`: Indicates the end of a file's content.

Additional Information:
- **File Size**: The size of the file in bytes.
- **Last Modified**: The last modification timestamp of the file.
- **Creation Time**: The creation timestamp of the file.
- **Permissions**: The file permissions.
- **Owner**: The owner of the file.

---

"""
    elif output_format == 'html':
        explanation = f"""
<html>
<head>
    <title>Project Files Compilation</title>
</head>
<body>
<h1>Project Files Compilation</h1>
<p>This document contains the concatenated contents of project files.</p>

<h2>Structure Explanation</h2>
<ul>
    <li><strong>File Contents</strong>: Each file's content is displayed below its heading.</li>
</ul>

<p>Markers:</p>
<ul>
    <li><code>{start_marker} relative/path/to/file {start_marker}</code>: Indicates the beginning of a file's content.</li>
    <li><code>{end_marker} relative/path/to/file {end_marker}</code>: Indicates the end of a file's content.</li>
</ul>

<p>Additional Information:</p>
<ul>
    <li><strong>File Size</strong>: The size of the file in bytes.</li>
    <li><strong>Last Modified</strong>: The last modification timestamp of the file.</li>
    <li><strong>Creation Time</strong>: The creation timestamp of the file.</li>
    <li><strong>Permissions</strong>: The file permissions.</li>
    <li><strong>Owner</strong>: The owner of the file.</li>
</ul>

<hr>
"""
    elif output_format == 'json':
        explanation = {
            'description': 'Project Files Compilation',
            'details': 'This document contains the concatenated contents of project files.',
            'structure_explanation': {
                'Markers': [
                    f'{start_marker} relative/path/to/file {start_marker}: Indicates the beginning of a file\'s content.',
                    f'{end_marker} relative/path/to/file {end_marker}: Indicates the end of a file\'s content.'
                ],
                'Additional Information': [
                    'File Size: The size of the file in bytes.',
                    'Last Modified: The last modification timestamp of the file.',
                    'Creation Time: The creation timestamp of the file.',
                    'Permissions: The file permissions.',
                    'Owner: The owner of the file.'
                ]
            }
        }
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            json.dump(explanation, output_file, ensure_ascii=False, indent=4)
        return
    else:
        explanation = ""

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(explanation)

def count_tokens_in_file(file_path):
    """Counts the number of tokens in the given file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tokens = content.split()
        return len(tokens)
    except Exception as e:
        logging.error(f'Error counting tokens in {file_path}: {e}')
        return 0
