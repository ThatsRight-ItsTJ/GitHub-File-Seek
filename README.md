# GitHub File Hunter 🔍

**Smart file discovery and download tool for GitHub repositories**

Intelligently finds and downloads specific files from GitHub repositories without cloning the entire repository. Supports individual files, patterns, batch operations, and repository structure analysis with centralized download management.

## ✨ Features

- 🎯 **Individual File Downloads**: Download specific files by name or path
- 🔍 **Pattern-Based Search**: Use glob patterns, regex, or file extensions
- 📦 **Batch Processing**: Process multiple repositories from CSV/JSON configurations
- 🌳 **Repository Structure Analysis**: Analyze and export repository file structures
- 🚀 **High Performance**: Async downloads with concurrent processing
- 📁 **Centralized Downloads**: All files organized in `resulting_downloads/` folder
- 🔑 **GitHub Token Support**: Avoid rate limits with personal access tokens
- 🌐 **Web Interface**: User-friendly Flask dashboard for GUI operations

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
cd GitHub-File-Seek
pip install -r requirements.txt
```

### Basic Usage

```bash
# Download specific files
python github_file_hunter.py microsoft/vscode README.md package.json

# Search by file extensions
python github_file_hunter.py fastapi/fastapi --extensions .py --list-only

# Search with patterns
python github_file_hunter.py django/django --path-patterns "django/core/*" --extensions .py

# Analyze repository structure
python github_file_hunter.py microsoft/vscode --structure-only
```

### Batch Processing

```bash
# Create sample configuration
python batch_hunter.py --create-sample json --sample-file my_batch.json

# Preview matches without downloading
python batch_hunter.py -f my_batch.json

# Download all matching files
python batch_hunter.py -f my_batch.json --download
```

## 📁 Download Organization

All downloaded files are automatically organized in the `resulting_downloads/` folder:

```
resulting_downloads/
├── repo1_owner_repo1_name/
│   ├── src/
│   │   └── main.py
│   └── README.md
├── repo2_owner_repo2_name/
│   ├── config/
│   │   └── settings.json
│   └── docs/
└── structure_analysis/
    └── repo_structure.json
```

## 🔧 Configuration

### Environment Variables

```bash
export GITHUB_TOKEN="your_github_token_here"
```

### Batch Configuration (JSON)

```json
[
  {
    "repo_url": "microsoft/vscode",
    "output_dir": "./resulting_downloads/vscode",
    "search_criteria": {
      "extensions": [".json", ".md"],
      "exclude_patterns": ["node_modules/*", "out/*"]
    }
  },
  {
    "repo_url": "fastapi/fastapi",
    "profile": "api",
    "output_dir": "./resulting_downloads/fastapi",
    "branch": "main"
  }
]
```

### Search Profiles

Built-in profiles for common use cases:

- `config` - Configuration files (.yml, .json, .env, etc.)
- `api` - API-related files (routes, endpoints, controllers)
- `auth` - Authentication and security files
- `database` - Database models, schemas, migrations
- `docker` - Docker and containerization files
- `cicd` - CI/CD workflows and pipelines
- `docs` - Documentation files
- `tests` - Test files and specs
- `frontend` - Frontend code (JS, TS, Vue, React)
- `backend` - Backend services and APIs
- `scripts` - Build scripts and utilities
- `ml` - Machine learning models and notebooks

## 📊 Advanced Features

### Repository Structure Analysis

```bash
# Analyze repository structure
python github_file_hunter.py owner/repo --structure-only

# Output includes:
# - File type distribution
# - Directory structure
# - Size statistics
# - Largest files
```

### Web Interface

```bash
# Launch web dashboard
python web_interface.py

# Access at http://localhost:5000
```

### Concurrent Processing

```bash
# Process multiple repositories concurrently
python batch_hunter.py -f batch.json --download --concurrent 5
```

## 🛠️ Command Line Options

### github_file_hunter.py

```bash
python github_file_hunter.py [repo_url] [files...] [options]

Options:
  --extensions, -e      File extensions (.py, .js, etc.)
  --name-patterns, -n   Filename patterns (*test*, config*)
  --path-patterns, -p   Path patterns (src/*, docs/*)
  --exclude-patterns, -x Exclude patterns (node_modules/*)
  --regex, -r           Regular expression pattern
  --min-size           Minimum file size in bytes
  --max-size           Maximum file size in bytes
  --branch, -b         Specific branch to search
  --output-dir, -o     Output directory (default: ./resulting_downloads)
  --token, -t          GitHub personal access token
  --list-only, -l      List files without downloading
  --structure-only, -s  Analyze structure only
```

### batch_hunter.py

```bash
python batch_hunter.py [options]

Options:
  --batch-file, -f     CSV or JSON batch configuration file
  --create-sample      Create sample batch file (csv/json)
  --download, -d       Download matching files
  --preview-only       Show matches without downloading
  --concurrent, -c     Max concurrent processing (default: 3)
  --token, -t          GitHub personal access token
  --export             Export results to file
  --export-format      Export format (json/csv)
```

## 📈 Performance & Limits

- **Rate Limits**: Use GitHub token to avoid API limits
- **Concurrent Downloads**: Configurable concurrent processing
- **File Size Limits**: Filter by min/max file sizes
- **Pattern Optimization**: Smart glob/regex pattern detection
- **Error Recovery**: Automatic fallback for failed patterns

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Links

- **Repository**: https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek
- **Issues**: https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek/issues
- **Documentation**: See README_HUNTER.md for detailed usage examples

## 🙏 Acknowledgments

- Built with Python asyncio for high performance
- Uses GitHub API v3 for repository access
- Supports both glob and regex pattern matching
- Centralized download management for better organization

---

**Happy file hunting! 🎯**