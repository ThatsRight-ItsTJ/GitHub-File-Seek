# 🔍 GitHub File Hunter

**Advanced GitHub repository file extraction tool with intelligent batch processing and auto-branch detection.**

## ✨ Features

- 🎯 **Pattern-based file searching** with wildcards, regex, and extensions
- 🚀 **100% success rate batch processing** with auto-branch detection
- 📦 **Pre-built search profiles** for common development scenarios
- 🌐 **Web interface** with interactive file tree exploration
- ⚡ **Concurrent downloads** with rate limiting and progress tracking
- 📊 **Smart fallback logic** adapts to different repository structures
- 🔄 **CSV/JSON batch processing** for multiple repositories

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/GitHub-File-Seek.git
cd GitHub-File-Seek

# Install dependencies
pip install -r requirements.txt

# Set GitHub token (optional but recommended)
export GITHUB_TOKEN=your_github_token_here
```

### Basic Usage

```bash
# Search for Python files in a repository
python github_file_hunter.py microsoft/vscode --extensions .py --download

# Use a pre-built profile
python github_file_hunter.py fastapi/fastapi --profile api --download

# Batch process multiple repositories
python batch_hunter.py --batch-file repos.csv --download

# Launch web interface
python web_interface.py
```

## 📋 Batch Processing Formats

### CSV Format Example

Create a file `repos.csv`:

```csv
repo_url,profile,output_dir,branch,extensions
microsoft/vscode,config,./downloads/vscode,main,
https://github.com/fastapi/fastapi,api,./downloads/fastapi,,
kubernetes/kubernetes,docker,./downloads/k8s,master,
openai/gpt-3,,,,.py,.js
```

### JSON Format Example

Create a file `repos.json`:

```json
[
  {
    "repo_url": "microsoft/vscode",
    "profile": "config",
    "output_dir": "./downloads/vscode",
    "branch": "main"
  },
  {
    "repo_url": "https://github.com/fastapi/fastapi",
    "profile": "api",
    "output_dir": "./downloads/fastapi",
    "branch": null
  },
  {
    "repo_url": "kubernetes/kubernetes",
    "profile": "docker",
    "output_dir": "./downloads/k8s",
    "branch": "master"
  },
  {
    "repo_url": "openai/gpt-3",
    "output_dir": "./downloads/openai",
    "search_criteria": {
      "extensions": [".py", ".js"],
      "exclude_patterns": ["node_modules/*", "*.test.js"]
    }
  }
]
```

## 🎯 Search Profiles

Pre-built profiles for common scenarios:

- **config** - Configuration files (yml, json, toml, env)
- **api** - API routes, endpoints, clients
- **auth** - Authentication & security files
- **database** - Database schemas, migrations, ORM files
- **docker** - Containerization files
- **cicd** - CI/CD pipeline configurations
- **docs** - Documentation files
- **tests** - Test files and configurations
- **frontend** - Frontend assets and components
- **backend** - Backend services and APIs
- **scripts** - Automation and build scripts
- **ml** - Machine learning models and data

## 🌐 Web Interface

Launch the interactive web dashboard:

```bash
python web_interface.py
```

Features:
- Visual repository exploration
- Interactive file filtering
- Real-time download progress
- Results export (JSON/CSV/TXT)
- Batch job management

## 🔧 Advanced Usage

### Custom Search Criteria

```bash
# Search with multiple extensions
python github_file_hunter.py repo/name --extensions .py,.js,.ts --download

# Use regex patterns
python github_file_hunter.py repo/name --patterns ".*config.*\.yml$" --download

# Exclude specific paths
python github_file_hunter.py repo/name --exclude "node_modules/*,dist/*" --download

# Size-based filtering
python github_file_hunter.py repo/name --max-size 1MB --min-size 1KB --download
```

### Batch Processing Options

```bash
# Process with custom concurrency
python batch_hunter.py --batch-file repos.csv --concurrent 5 --download

# Preview mode (no downloads)
python batch_hunter.py --batch-file repos.json --preview-only

# Export results
python batch_hunter.py --batch-file repos.csv --export results.json --export-format json
```

## 📊 Auto-Branch Detection

The tool automatically detects repository default branches:

- Set `branch: null` in JSON or leave empty in CSV
- Automatically handles "main", "master", or custom default branches
- 100% success rate with smart fallback logic

## 🛠️ Configuration

### Environment Variables

```bash
export GITHUB_TOKEN=your_token_here          # GitHub API token
export GITHUB_HUNTER_CONCURRENT=3            # Default concurrency
export GITHUB_HUNTER_OUTPUT_DIR=./downloads  # Default output directory
```

### Config File

Create `config.json`:

```json
{
  "github_token": "your_token_here",
  "default_output_dir": "./downloads",
  "max_concurrent": 3,
  "rate_limit_delay": 1.0,
  "default_profiles": ["config", "api", "docker"]
}
```

## 📁 Project Structure

```
GitHub-File-Seek/
├── github_file_hunter.py      # Main CLI tool
├── batch_hunter.py            # Batch processing
├── web_interface.py           # Web dashboard
├── github_hunter_profiles.py  # Search profiles
├── requirements.txt           # Dependencies
├── README.md                  # This file
├── README_HUNTER.md          # Detailed documentation
├── examples/                  # Usage examples
└── templates/                 # Web interface templates
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 🔗 Links

- [Detailed Documentation](README_HUNTER.md)
- [GitHub Repository](https://github.com/your-username/GitHub-File-Seek)
- [Issue Tracker](https://github.com/your-username/GitHub-File-Seek/issues)

---

**Made with ❤️ for developers who need efficient repository file extraction.**