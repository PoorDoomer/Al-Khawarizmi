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
from typing import Dict, List

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress
from dotenv import load_dotenv

# ASCII Banner
ASCII_BANNER = """
|____ | | | | / / |     /   | |  | |          /  |              /  | 
    / / | | |/ /| |__  / /| | |  | | __ _ _ __`| | _____ __ ___ `| | 
    \ \ | |    \| '_ \/ /_| | |/\| |/ _` | '__|| ||_  / '_ ` _ \ | | 
.___/ / | | |\  \ | | \___  \  /\  / (_| | |  _| |_/ /| | | | | || |_
\____/|_| \_| \_/_| |_|   |_/\/  \/ \__,_|_|  \___/___|_| |_| |_\___/
"""

# Set up logging
logging.basicConfig(filename='compile_project.log', level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Lock for writing to the output file
write_lock = threading.Lock()

class ProjectTextCLI:
    def __init__(self):
        self.console = Console()
        self.agents_available = {
            "code_analyzer": {
                "name": "Code Analyzer",
                "description": "Analyzes code quality, patterns, and suggests improvements",
                "features": [
                    "Code smell detection",
                    "Complexity analysis",
                    "Best practices checking",
                    "Performance optimization suggestions"
                ]
            },
            "documentation_generator": {
                "name": "Documentation Generator",
                "description": "Generates comprehensive documentation from code",
                "features": [
                    "Function documentation",
                    "API documentation",
                    "Usage examples",
                    "README generation"
                ]
            },
            "security_scanner": {
                "name": "Security Scanner",
                "description": "Scans code for potential security vulnerabilities",
                "features": [
                    "Vulnerability detection",
                    "Security best practices",
                    "Dependency security check",
                    "OWASP compliance check"
                ]
            },
            "dependency_analyzer": {
                "name": "Dependency Analyzer",
                "description": "Analyzes project dependencies and suggests updates",
                "features": [
                    "Dependency graph generation",
                    "Version conflict detection",
                    "Update recommendations",
                    "Unused dependency detection"
                ]
            }
        }
        load_dotenv()

    def show_banner(self):
        """Display the ASCII banner and welcome message"""
        self.console.print(ASCII_BANNER, style="bold blue")
        self.console.print("\n[bold cyan]Welcome to Project2Text![/bold cyan]")
        self.console.print("Your one-stop solution for project documentation and analysis\n")

    def show_features(self):
        """Display main features in a table"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Feature", style="cyan")
        table.add_column("Description", style="green")

        features = [
            ("📁 Multi-threading", "Process files concurrently for better performance"),
            ("📝 Multiple Formats", "Output in Markdown, HTML, or JSON"),
            ("🔍 Smart Filtering", "Include/exclude files by extension or pattern"),
            ("📊 Progress Tracking", "Real-time progress bars and statistics"),
            ("🌳 Directory Tree", "Generate ASCII tree of project structure"),
            ("📏 Size Management", "Split output into multiple files if needed"),
            ("🤖 AI Agents", "Optional AI-powered code analysis and documentation"),
            ("🔒 Security", "Secure handling of sensitive files"),
            ("📈 Token Counter", "Track token usage for AI processing"),
        ]

        for feature, description in features:
            table.add_row(feature, description)

        self.console.print(table)

    def check_api_keys(self) -> bool:
        """Check if necessary API keys are present in .env"""
        required_keys = ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY']
        return any(os.getenv(key) for key in required_keys)

    def prompt_for_api_key(self):
        """Prompt user for API key if not found in .env"""
        self.console.print("\n[yellow]No API keys found in .env file[/yellow]")
        provider = Prompt.ask(
            "Which AI provider would you like to use?",
            choices=["openai", "anthropic", "skip"],
            default="openai"
        )

        if provider != "skip":
            api_key = Prompt.ask(f"Please enter your {provider.upper()} API key", password=True)
            # Temporarily set the API key for this session
            os.environ[f'{provider.upper()}_API_KEY'] = api_key
            self.console.print("[green]API key set successfully![/green]")

    def show_agent_options(self):
        """Display available AI agents and their capabilities"""
        self.console.print("\n[bold cyan]Available AI Agents[/bold cyan]")

        for agent_id, agent_info in self.agents_available.items():
            panel = Panel.fit(
                f"[cyan]{agent_info['description']}[/cyan]\n\n"
                "[yellow]Features:[/yellow]\n" +
                "\n".join(f"• {feature}" for feature in agent_info['features']),
                title=f"[bold]{agent_info['name']}[/bold]",
                border_style="blue"
            )
            self.console.print(panel)

    def run(self):
        """Main execution method"""
        self.show_banner()
        self.show_features()

        # Check for API keys
        if not self.check_api_keys():
            self.prompt_for_api_key()

        # Prompt user for inputs
        self.prompt_user_inputs()

        # Run the file compilation process
        self.compile_project_files()

    def prompt_user_inputs(self):
        """Prompt the user for necessary inputs"""
        self.console.print("\n[bold cyan]Setup Wizard[/bold cyan]")
        self.dir_path = Prompt.ask("Enter the directory to scan", default=os.getcwd())
        self.output_filename = Prompt.ask("Enter the output file name", default="project_files.md")
        self.output_format = Prompt.ask("Choose output file format", choices=["markdown", "html", "json"], default="markdown")
        
        include_extensions = Prompt.ask("File extensions to include (comma-separated, e.g., .py,.txt). Leave blank to include all.", default="")
        self.include_extensions = [ext.strip() for ext in include_extensions.split(",")] if include_extensions else []

        exclude_extensions = Prompt.ask("File extensions to exclude (comma-separated, e.g., .exe,.dll). Leave blank to exclude none.", default="")
        self.exclude_extensions = [ext.strip() for ext in exclude_extensions.split(",")] if exclude_extensions else []

        exclude_dirs = Prompt.ask("Directories to exclude (comma-separated, default: .git,__pycache__,node_modules)", default=".git,__pycache__,node_modules")
        self.exclude_dirs = [d.strip() for d in exclude_dirs.split(",")]

        exclude_files = Prompt.ask("Files to exclude (comma-separated). Leave blank to exclude none.", default="")
        self.exclude_files = [f.strip() for f in exclude_files.split(",")] if exclude_files else []

        pattern_include = Prompt.ask("Patterns to include (comma-separated, e.g., *.py,test_*.txt). Leave blank to include all.", default="")
        self.pattern_include = [p.strip() for p in pattern_include.split(",")] if pattern_include else []

        pattern_exclude = Prompt.ask("Patterns to exclude (comma-separated, e.g., *.log,temp_*). Leave blank to exclude none.", default="")
        self.pattern_exclude = [p.strip() for p in pattern_exclude.split(",")] if pattern_exclude else []

        ignore_patterns = Prompt.ask("Files or directories to ignore (supports glob patterns, e.g., folder/*,file.txt). Leave blank to ignore none.", default="")
        self.ignore_patterns = [p.strip() for p in ignore_patterns.split(",")] if ignore_patterns else []

        self.start_marker = Prompt.ask("Custom start marker for file content", default="=== Start of")
        self.end_marker = Prompt.ask("Custom end marker for file content", default="=== End of")

        self.no_metadata = Confirm.ask("Exclude file metadata from the output?", default=False)

        self.limit_size = Prompt.ask("Maximum size (in bytes) for each output file (0 for no limit)", default="0")
        self.limit_size = int(self.limit_size)

    def compile_project_files(self):
        """Compiles project files into a single text file based on provided arguments"""
        from file_processor import compile_project_files

        compile_project_files(
            dir_path=self.dir_path,
            output_filename=self.output_filename,
            output_format=self.output_format,
            include_extensions=self.include_extensions,
            exclude_extensions=self.exclude_extensions,
            exclude_dirs=self.exclude_dirs,
            exclude_files=self.exclude_files,
            pattern_include=self.pattern_include,
            pattern_exclude=self.pattern_exclude,
            ignore_patterns=self.ignore_patterns,
            start_marker=self.start_marker,
            end_marker=self.end_marker,
            no_metadata=self.no_metadata,
            limit_size=self.limit_size,
            console=self.console
        )
