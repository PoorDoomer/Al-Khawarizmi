import os
import sys
import logging
import threading
import argparse
from typing import Dict, List, Optional
from pathlib import Path

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.logging import RichHandler
from dotenv import load_dotenv

from file_processor import compile_project_files
from smart_processor import SmartFileProcessor

# ASCII Banner
ASCII_BANNER = r"""
|____ | |   | | / / |     /   | |  | |          /  |              /  | 
    / / |   | |/ /| |__  / /| | |  | | __ _ _ __`| | _____ __ ___ `| | 
    \ \ |   |    \| '_ \/ /_| | |/\| |/ _` | '__|| ||_  / '_ ` _ \ | | 
.___/ / |     | |\  \ | | \___  \  /\  / (_| | |  _| |_/ /| | | | | || |_
\____/|_|   \_| \_/_| |_|   |_/\/  \/ \__,_|_|  \___/___|_| |_| |_\___/
"""

class Project2TextCLI:
    def __init__(self):
        self.console = Console()
        self.setup_logging()
        load_dotenv()
        
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
        
        # Initialize configuration
        self.config = self.initialize_config()
    
    def setup_logging(self):
        """Set up logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[
                RichHandler(console=self.console, rich_tracebacks=True),
                logging.FileHandler("project2text.log")
            ]
        )
        self.logger = logging.getLogger("project2text")

    def initialize_config(self) -> dict:
        """Initialize default configuration"""
        return {
            "dir_path": os.getcwd(),
            "output_filename": "project_files.md",
            "output_format": "markdown",
            "include_extensions": [],
            "exclude_extensions": [],
            "exclude_dirs": [".git", "__pycache__", "node_modules"],
            "exclude_files": [],
            "pattern_include": [],
            "pattern_exclude": [],
            "ignore_patterns": [],
            "start_marker": "=== Start of",
            "end_marker": "=== End of",
            "no_metadata": False,
            "limit_size": 0,
            "smart_processing": False,
            "llm_choice": "gpt3"
        }

    def show_banner(self):
        """Display the ASCII banner and welcome message"""
        self.console.print(ASCII_BANNER, style="bold blue")
        self.console.print("\n[bold cyan]Welcome to El Khawarizmi![/bold cyan]")
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
            ("🧠 Smart Processing", "Advanced code analysis and chunking for LLMs")
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

    def prompt_smart_processing(self):
        """Prompt for smart processing options"""
        self.config["smart_processing"] = Confirm.ask(
            "\n[cyan]Would you like to enable smart processing?[/cyan] (Recommended for large codebases)",
            default=False
        )

        if self.config["smart_processing"]:
            self.config["llm_choice"] = Prompt.ask(
                "Choose LLM model",
                choices=["gpt3", "gpt4", "claude"],
                default="gpt3"
            )
            
            # Show additional smart processing options
            self.console.print("\n[bold cyan]Smart Processing Configuration[/bold cyan]")
            self.console.print("This will analyze your codebase and prepare it for LLM processing")
            
            if Confirm.ask("Would you like to see detailed analysis options?", default=False):
                self.show_agent_options()

    def prompt_user_inputs(self):
        """Prompt the user for necessary inputs"""
        self.console.print("\n[bold cyan]Setup Wizard[/bold cyan]")
        
        # Basic configuration
        self.config["dir_path"] = Prompt.ask(
            "Enter the directory to scan",
            default=self.config["dir_path"]
        )
        
        self.config["output_filename"] = Prompt.ask(
            "Enter the output file name",
            default=self.config["output_filename"]
        )
        
        self.config["output_format"] = Prompt.ask(
            "Choose output file format",
            choices=["markdown", "html", "json"],
            default=self.config["output_format"]
        )

        # Advanced configuration
        if Confirm.ask("Would you like to configure advanced options?", default=False):
            self._prompt_advanced_options()

        # Smart processing configuration
        self.prompt_smart_processing()

    def _prompt_advanced_options(self):
        """Prompt for advanced configuration options"""
        # File extensions
        include_extensions = Prompt.ask(
            "File extensions to include (comma-separated, e.g., .py,.txt). Leave blank to include all.",
            default=""
        )
        self.config["include_extensions"] = [ext.strip() for ext in include_extensions.split(",")] if include_extensions else []

        exclude_extensions = Prompt.ask(
            "File extensions to exclude (comma-separated, e.g., .exe,.dll). Leave blank to exclude none.",
            default=""
        )
        self.config["exclude_extensions"] = [ext.strip() for ext in exclude_extensions.split(",")] if exclude_extensions else []

        # Directories and files
        exclude_dirs = Prompt.ask(
            "Directories to exclude (comma-separated)",
            default=",".join(self.config["exclude_dirs"])
        )
        self.config["exclude_dirs"] = [d.strip() for d in exclude_dirs.split(",")]

        exclude_files = Prompt.ask(
            "Files to exclude (comma-separated). Leave blank to exclude none.",
            default=""
        )
        self.config["exclude_files"] = [f.strip() for f in exclude_files.split(",")] if exclude_files else []

        # Patterns
        pattern_include = Prompt.ask(
            "Patterns to include (comma-separated, e.g., *.py,test_*.txt). Leave blank to include all.",
            default=""
        )
        self.config["pattern_include"] = [p.strip() for p in pattern_include.split(",")] if pattern_include else []

        pattern_exclude = Prompt.ask(
            "Patterns to exclude (comma-separated, e.g., *.log,temp_*). Leave blank to exclude none.",
            default=""
        )
        self.config["pattern_exclude"] = [p.strip() for p in pattern_exclude.split(",")] if pattern_exclude else []

        # Other options
        self.config["no_metadata"] = Confirm.ask(
            "Exclude file metadata from the output?",
            default=self.config["no_metadata"]
        )

        self.config["limit_size"] = int(Prompt.ask(
            "Maximum size (in bytes) for each output file (0 for no limit)",
            default=str(self.config["limit_size"])
        ))

    def process_files(self):
        """Process files according to configuration"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            # Regular processing
            task_id = progress.add_task("Processing files...", total=100)
            
            compile_project_files(
                dir_path=self.config["dir_path"],
                output_filename=self.config["output_filename"],
                output_format=self.config["output_format"],
                include_extensions=self.config["include_extensions"],
                exclude_extensions=self.config["exclude_extensions"],
                exclude_dirs=self.config["exclude_dirs"],
                exclude_files=self.config["exclude_files"],
                pattern_include=self.config["pattern_include"],
                pattern_exclude=self.config["pattern_exclude"],
                ignore_patterns=self.config["ignore_patterns"],
                start_marker=self.config["start_marker"],
                end_marker=self.config["end_marker"],
                no_metadata=self.config["no_metadata"],
                limit_size=self.config["limit_size"],
                console=self.console,
                progress=progress,
                task_id=task_id
            )

            # Smart processing if enabled
            if self.config["smart_processing"]:
                smart_task_id = progress.add_task("Running smart processing...", total=100)
                
                smart_output_dir = Path(self.config["output_filename"]).parent / "smart_processed"
                processor = SmartFileProcessor(
                    llm_name=self.config["llm_choice"],
                    codebase_path=self.config["dir_path"],
                    output_dir=str(smart_output_dir)
                )
                
                try:
                    processor.process()
                    progress.update(smart_task_id, completed=100)
                    self.logger.info(f"Smart processing complete. Output saved to: {smart_output_dir}")
                except Exception as e:
                    self.logger.error(f"Error during smart processing: {str(e)}")
                    progress.update(smart_task_id, completed=100, description="[red]Smart processing failed")

    def run(self):
        """Main execution method"""
        try:
            self.show_banner()
            self.show_features()

            # Parse command line arguments
            parser = argparse.ArgumentParser(description="Project2Text - Code Analysis and Documentation Tool")
            parser.add_argument("-s", "--smart", action="store_true", help="Enable smart processing")
            parser.add_argument("-l", "--llm", choices=["gpt3", "gpt4", "claude"], help="Choose LLM model for smart processing")
            parser.add_argument("-d", "--dir", help="Directory to scan")
            parser.add_argument("-o", "--output", help="Output file name")
            parser.add_argument("-f", "--format", choices=["markdown", "html", "json"], help="Output format")
            parser.add_argument("--skip-wizard", action="store_true", help="Skip the setup wizard")
            
            args = parser.parse_args()

            # Update config from command line arguments
            if args.smart:
                self.config["smart_processing"] = True
            if args.llm:
                self.config["llm_choice"] = args.llm
            if args.dir:
                self.config["dir_path"] = args.dir
            if args.output:
                self.config["output_filename"] = args.output
            if args.format:
                self.config["output_format"] = args.format

            # Check for API keys if smart processing is enabled
            if self.config["smart_processing"] and not self.check_api_keys():
                self.prompt_for_api_key()

            # Run setup wizard if not skipped
            if not args.skip_wizard:
                self.prompt_user_inputs()

            # Process files
            self.process_files()

            self.console.print("\n[bold green]Processing complete![/bold green]")
            self.console.print(f"Output saved to: {self.config['output_filename']}")
            
        except KeyboardInterrupt:
                    self.console.print("\n[yellow]Process interrupted by user[/yellow]")
                    sys.exit(1)
                    
        except Exception as e:
            self.logger.error(f"An error occurred: {str(e)}", exc_info=True)
            self.console.print(f"\n[red]Error: {str(e)}[/red]")
            self.console.print("[yellow]Check project2text.log for details[/yellow]")
            sys.exit(1)
                    
        finally:
           
            self.cleanup()

    def cleanup(self):
        """Clean up temporary files and resources"""
        try:
            # Add any cleanup operations here
            pass
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")

def main():
    """Entry point for the CLI"""
    cli = Project2TextCLI()
    cli.run()

if __name__ == "__main__":
    main()