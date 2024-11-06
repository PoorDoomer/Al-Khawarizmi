import os
import sys
import json
import ast
import threading
import argparse
import logging
from typing import Dict, List, Tuple, Set
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

class DependencyAnalyzer:
    """Analyzes Python files for imports and dependencies"""
    
    def __init__(self):
        self.import_graph: Dict[str, Set[str]] = {}
        self.class_definitions: Dict[str, List[str]] = {}
        self.function_definitions: Dict[str, List[str]] = {}
        
    def analyze_file(self, file_path: str) -> Tuple[Set[str], List[str], List[str]]:
        """Analyze a single Python file for imports, classes, and functions"""
        imports = set()
        classes = []
        functions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=file_path)
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    for name in node.names:
                        imports.add(f"{module}.{name.name}")
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
                    
            return imports, classes, functions
        except Exception as e:
            logging.error(f"Error analyzing file {file_path}: {str(e)}")
            return set(), [], []

class SmartFileProcessor:
    def __init__(self, llm_name: str, codebase_path: str, output_dir: str):
        load_dotenv()
        self.llm_name = llm_name.lower()
        self.codebase_path = Path(codebase_path)
        self.output_dir = Path(output_dir)
        self.token_limit = self.get_token_limit()
        self.chunks: List[List[Tuple[str, str]]] = []
        self.dependency_analyzer = DependencyAnalyzer()
        self.file_metadata: Dict[str, dict] = {}
        
        # Create output directory immediately upon initialization
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('smart_processor.log'),
                logging.StreamHandler()
            ]
        )
    def get_token_limit(self) -> int:
        """Get token limit from environment variables"""
        token_limit_env_var = f"LLM_TOKEN_LIMIT_{self.llm_name.upper()}"
        token_limit = int(os.getenv(token_limit_env_var, 4000))
        logging.info(f"Using token limit: {token_limit} for {self.llm_name}")
        return token_limit
    
    def analyze_codebase(self):
        """Analyze the codebase structure and dependencies"""
        logging.info("Starting codebase analysis...")
        
        def process_file(file_path: Path) -> Tuple[Path, dict]:
            relative_path = file_path.relative_to(self.codebase_path)
            file_size = file_path.stat().st_size
            
            metadata = {
                'size': file_size,
                'relative_path': str(relative_path),
                'extension': file_path.suffix,
                'imports': [],
                'classes': [],
                'functions': []
            }
            
            if file_path.suffix == '.py':
                imports, classes, functions = self.dependency_analyzer.analyze_file(str(file_path))
                metadata.update({
                    'imports': list(imports),
                    'classes': classes,
                    'functions': functions
                })
            
            return file_path, metadata
        
        # Collect all files recursively
        files = []
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.css', '.html', '.md']:
            files.extend(self.codebase_path.rglob(f"*{ext}"))
        
        # Process files in parallel
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(lambda f: process_file(f), files))
        
        # Store results
        for file_path, metadata in results:
            self.file_metadata[str(file_path)] = metadata
        
        # Generate summary
        self.generate_analysis_summary()
    
    def generate_analysis_summary(self):
        """Generate a summary of the codebase analysis"""
        logging.info("Generating analysis summary...")
        summary = {
            'total_files': len(self.file_metadata),
            'file_types': {},
            'total_size': 0,
            'python_stats': {
                'total_classes': 0,
                'total_functions': 0,
                'total_imports': 0
            }
        }
        
        for metadata in self.file_metadata.values():
            ext = metadata['extension']
            summary['file_types'][ext] = summary['file_types'].get(ext, 0) + 1
            summary['total_size'] += metadata['size']
            
            if ext == '.py':
                summary['python_stats']['total_classes'] += len(metadata['classes'])
                summary['python_stats']['total_functions'] += len(metadata['functions'])
                summary['python_stats']['total_imports'] += len(metadata['imports'])
        
        try:
            # Ensure output directory exists before writing summary
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save summary to JSON
            summary_path = self.output_dir / 'analysis_summary.json'
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2)
            
            logging.info(f"Analysis summary saved to {summary_path}")
            
        except Exception as e:
            logging.error(f"Error saving analysis summary: {str(e)}")
            raise

    
    def estimate_tokens(self, content: str) -> int:
        """Estimate number of tokens in content"""
        # More accurate token estimation based on common tokenizer rules
        # This is a simplified version - production should use actual tokenizer
        words = content.split()
        special_chars = sum(1 for c in content if not c.isalnum() and not c.isspace())
        return len(words) + (special_chars // 2)
    
    def split_into_chunks(self):
        """Split files into chunks based on token limit"""
        logging.info("Splitting files into chunks...")
        
        current_chunk = []
        current_tokens = 0
        
        # Sort files by size to optimize chunking
        sorted_files = sorted(
            self.file_metadata.items(),
            key=lambda x: x[1]['size']
        )
        
        for file_path, metadata in sorted_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tokens = self.estimate_tokens(content)
            
            # If single file exceeds token limit, split it
            if tokens > self.token_limit:
                logging.warning(f"File {file_path} exceeds token limit, splitting...")
                # Split into smaller chunks (implement based on specific needs)
                continue
            
            if current_tokens + tokens > self.token_limit:
                self.chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            current_chunk.append((str(metadata['relative_path']), content))
            current_tokens += tokens
        
        if current_chunk:
            self.chunks.append(current_chunk)
        
        logging.info(f"Created {len(self.chunks)} chunks")
    

    def generate_output_files(self):
        """Generate output files with metadata and content"""
        logging.info("Generating output files...")
        
        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            for i, chunk in enumerate(self.chunks):
                chunk_file = self.output_dir / f'chunk_{i+1}.md'
                
                with open(chunk_file, 'w', encoding='utf-8') as f:
                    f.write(f"# Code Chunk {i+1}\n\n")
                    
                    for relative_path, content in chunk:
                        f.write(f"## File: {relative_path}\n\n")
                        
                        # Add metadata if available
                        full_path = str(self.codebase_path / relative_path)
                        if full_path in self.file_metadata:
                            metadata = self.file_metadata[full_path]
                            if metadata['extension'] == '.py':
                                f.write("### Metadata\n")
                                f.write(f"- Classes: {', '.join(metadata['classes'])}\n")
                                f.write(f"- Functions: {', '.join(metadata['functions'])}\n")
                                f.write(f"- Imports: {', '.join(metadata['imports'])}\n\n")
                        
                        f.write("### Content\n")
                        f.write("```" + (metadata['extension'][1:] if metadata['extension'] else '') + "\n")
                        f.write(content)
                        f.write("\n```\n\n")
                
                logging.info(f"Generated {chunk_file}")
                
        except Exception as e:
            logging.error(f"Error generating output files: {str(e)}")
            raise
    
    def process(self):
        """Main processing method"""
        try:
            self.analyze_codebase()
            self.split_into_chunks()
            self.generate_output_files()
            logging.info("Processing completed successfully")
        except Exception as e:
            logging.error(f"Error during processing: {str(e)}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Smart File Processor for LLMs')
    parser.add_argument('--llm', required=True, help='Target LLM name (e.g., gpt3, gpt4, claude)')
    parser.add_argument('--codebase', required=True, help='Path to the codebase directory')
    parser.add_argument('--output_dir', required=True, help='Directory to save the output files')
    
    args = parser.parse_args()
    
    processor = SmartFileProcessor(args.llm, args.codebase, args.output_dir)
    processor.process()

if __name__ == "__main__":
    main()