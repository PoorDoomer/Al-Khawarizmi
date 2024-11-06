```text
|____ | | | | / / |     /   | |  | |          /  |              /  | 
    / / | | |/ /| |__  / /| | |  | | __ _ _ __`| | _____ __ ___ `| | 
    \ \ | |    \| '_ \/ /_| | |/\| |/ _` | '__|| ||_  / '_ ` _ \ | | 
.___/ / | | |\  \ | | \___  \  /\  / (_| | |  _| |_/ /| | | | | || |_
\____/|_| \_| \_/_| |_|   |_/\/  \/ \__,_|_|  \___/___|_| |_| |_\___/

# Al Khawarizmi

> A powerful CLI tool for compiling and analyzing project files with AI-powered insights

[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

## 🌟 Features

### Core Features
- 🚀 **Wizard-style CLI**: Interactive setup process for ease of use
- 🧵 **Multi-threading**: Concurrent file processing for optimal performance
- 📝 **Multiple Output Formats**: Support for Markdown, HTML, and JSON
- 🎯 **Smart Filtering**: Flexible file inclusion/exclusion patterns
- 📊 **Progress Tracking**: Real-time progress indicators
- 🌳 **Directory Visualization**: ASCII tree representation of project structure
- 📏 **Size Management**: Automatic file splitting based on size limits

### AI-Powered Features (Coming Soon)
- 🤖 **Code Analysis**: Detect code smells and suggest improvements
- 📚 **Documentation Generation**: Auto-generate comprehensive documentation
- 🔒 **Security Scanning**: Identify potential security vulnerabilities
- 📦 **Dependency Analysis**: Analyze and optimize project dependencies

## 🚀 Quick Start

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/Al-Khawarizmi.git
cd Al-Khawarizmi
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Basic Usage

Run the CLI wizard:
```bash
python main.py
```

## 🎯 Examples

### Basic File Compilation
```python
from cli import ProjectTextCLI

if __name__ == '__main__':
    cli = ProjectTextCLI()
    cli.run()
```

### Custom Configuration
```python
# Initialize with specific settings
cli = ProjectTextCLI()
cli.dir_path = "/path/to/project"
cli.output_format = "markdown"
cli.run()
```

## 🛠️ Configuration Options

### File Filtering
- **Extensions**: Include/exclude specific file types
- **Directories**: Exclude specific directories
- **Patterns**: Use glob patterns for precise filtering
- **Ignore Rules**: Define comprehensive ignore patterns

### Output Customization
- **Format Selection**: Choose between Markdown, HTML, or JSON
- **Custom Markers**: Define custom start/end markers
- **Metadata Control**: Include/exclude file metadata
- **Size Limits**: Set maximum output file sizes

## 🤖 AI Agents (Coming Soon)

### Available Agents
1. **Code Analyzer**
   - Code smell detection
   - Complexity analysis
   - Best practices checking
   - Performance optimization suggestions

2. **Documentation Generator**
   - Function documentation
   - API documentation
   - Usage examples
   - README generation

3. **Security Scanner**
   - Vulnerability detection
   - Security best practices
   - Dependency security check
   - OWASP compliance check

4. **Dependency Analyzer**
   - Dependency graph generation
   - Version conflict detection
   - Update recommendations
   - Unused dependency detection

## 📝 Output Formats

### Markdown (Default)
```markdown
=== Start of example.py ===
File content here...
=== End of example.py ===
```

### HTML
```html
<h2>example.py</h2>
<pre>
File content here...
</pre>
```

### JSON
```json
{
  "file": "example.py",
  "content": "File content here...",
  "metadata": {
    "size": "1024 bytes",
    "modified": "2024-11-06 10:00:00"
  }
}
```

## 🚧 Limitations

- Binary files are automatically skipped
- File encoding detection may vary
- OS-specific file owner information
- Approximate token counting
- AI features currently in development

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Rich](https://github.com/Textualize/rich) - Beautiful terminal formatting
- [Chardet](https://github.com/chardet/chardet) - Character encoding detection
- Python Community - Continuous support and inspiration

## 📞 Support

- 📧 Email: support@alkhawarizmi.dev
- 💬 Discord: [Join our community](https://discord.gg/alkhawarizmi)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/Al-Khawarizmi/issues)

---

Made with ❤️ by wa7d Bnadm/PoorDoomer
