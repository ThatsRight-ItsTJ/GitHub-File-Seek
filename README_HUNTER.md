# GitHub File Hunter - Complete User Guide 📚

**Comprehensive documentation for smart GitHub file discovery and downloads**

This guide covers all features, use cases, and advanced configurations for the GitHub File Hunter tool with centralized download management.

## 📋 Table of Contents

1. [Installation & Setup](#installation--setup)
2. [Basic Usage](#basic-usage)
3. [Advanced Search Patterns](#advanced-search-patterns)
4. [Batch Processing](#batch-processing)
5. [Repository Analysis](#repository-analysis)
6. [Web Interface](#web-interface)
7. [Download Management](#download-management)
8. [Configuration Examples](#configuration-examples)
9. [Troubleshooting](#troubleshooting)
10. [API Reference](#api-reference)

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- Git
- GitHub account (recommended for token)

### Installation Steps

```bash
# Clone the repository
git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
cd GitHub-File-Seek

# Install dependencies
pip install -r requirements.txt

# Set up GitHub token (recommended)
export GITHUB_TOKEN="ghp_your_token_here"
```

### GitHub Token Setup

1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Set as environment variable or use `--token` flag

## 🎯 Basic Usage

### Individual File Downloads

```bash
# Download specific files
python github_file_hunter.py microsoft/vscode README.md package.json

# Download from specific branch
python github_file_hunter.py owner/repo file.txt --branch develop

# Download to custom directory
python github_file_hunter.py owner/repo file.txt --output-dir ./my_downloads
```

**Note**: All downloads go to `resulting_downloads/` folder by default, organized by repository.

### Pattern-Based Search

```bash
# Search by file extensions
python github_file_hunter.py fastapi/fastapi --extensions .py .md

# Search by filename patterns
python github_file_hunter.py django/django --name-patterns "*test*" "*config*"

# Search by path patterns
python github_file_hunter.py owner/repo --path-patterns "src/*" "docs/*"

# Exclude patterns
python github_file_hunter.py owner/repo --extensions .py --exclude-patterns "*test*" "__pycache__/*"
```

### List Without Downloading

```bash
# Preview matches
python github_file_hunter.py owner/repo --extensions .py --list-only

# Count files by type
python github_file_hunter.py owner/repo --structure-only
```

## 🔍 Advanced Search Patterns

### Glob Patterns

```bash
# Wildcard matching
--name-patterns "*.config.js" "test_*.py"

# Directory patterns
--path-patterns "src/**/*.ts" "docs/*.md"

# Character classes
--name-patterns "[Tt]est*" "config.[jt]s"
```

### Regular Expressions

```bash
# Regex patterns
--regex ".*\.(js|ts)$"

# Complex patterns
--regex "^(src|lib)/.*\.(py|js)$"

# Case-insensitive matching (default)
--regex "readme.*\.md"
```

### Size Filtering

```bash
# File size constraints
--min-size 1024 --max-size 1048576

# Human-readable sizes (in configuration files)
"min_size": "1KB"
"max_size": "1MB"
```

## 📦 Batch Processing

### Creating Batch Configurations

```bash
# Create sample JSON configuration
python batch_hunter.py --create-sample json --sample-file my_batch.json

# Create sample CSV configuration
python batch_hunter.py --create-sample csv --sample-file my_batch.csv
```

### JSON Configuration Format

```json
[
  {
    "repo_url": "microsoft/vscode",
    "output_dir": "./resulting_downloads/vscode",
    "branch": "main",
    "search_criteria": {
      "extensions": [".json", ".md", ".yml"],
      "exclude_patterns": ["node_modules/*", "out/*", "*.min.*"]
    }
  },
  {
    "repo_url": "fastapi/fastapi",
    "profile": "api",
    "output_dir": "./resulting_downloads/fastapi",
    "search_criteria": {
      "patterns": ["*api*", "*route*", "*endpoint*"],
      "extensions": [".py"],
      "exclude_patterns": ["*test*", "__pycache__/*"]
    }
  },
  {
    "repo_url": "django/django",
    "output_dir": "./resulting_downloads/django",
    "search_criteria": {
      "path_patterns": ["django/core/*", "django/contrib/*"],
      "extensions": [".py"],
      "max_size": "500KB"
    }
  }
]
```

### CSV Configuration Format

```csv
repo_url,profile,output_dir,branch,extensions,patterns,exclude_patterns,max_size,min_size
microsoft/vscode,config,./resulting_downloads/vscode,main,"",""node_modules/*,""
fastapi/fastapi,api,./resulting_downloads/fastapi,"",".py","*api*,*route*","*test*",""
kubernetes/kubernetes,docker,./resulting_downloads/k8s,master,".yml,.yaml","*docker*,*k8s*","vendor/*",1MB,""
```

### Running Batch Operations

```bash
# Preview matches
python batch_hunter.py -f my_batch.json

# Download all files
python batch_hunter.py -f my_batch.json --download

# Concurrent processing
python batch_hunter.py -f my_batch.json --download --concurrent 5

# Export results
python batch_hunter.py -f my_batch.json --download --export results.json
```

## 🌳 Repository Analysis

### Structure Analysis

```bash
# Analyze repository structure
python github_file_hunter.py microsoft/vscode --structure-only

# Custom output directory
python github_file_hunter.py owner/repo --structure-only --output-dir ./analysis
```

### Analysis Output

The structure analysis creates a JSON file with:

```json
{
  "summary": {
    "total_files": 1250,
    "total_directories": 85,
    "total_size_mb": 15.7,
    "average_file_size": 12800
  },
  "file_types": {
    ".ts": 450,
    ".js": 320,
    ".json": 180,
    ".md": 45,
    ".yml": 25
  },
  "largest_files": [...],
  "top_directories": [...],
  "all_files": [...]
}
```

## 🌐 Web Interface

### Launching the Web Interface

```bash
# Start web server
python web_interface.py

# Access at http://localhost:5000
```

### Web Interface Features

- **Repository Search**: Enter GitHub URLs and search criteria
- **Real-time Preview**: See matching files before downloading
- **Batch Upload**: Upload CSV/JSON batch configurations
- **Download Management**: Monitor download progress
- **Result Export**: Download results as JSON/CSV
- **Token Management**: Secure token storage

### Web Interface Usage

1. **Single Repository**:
   - Enter repository URL
   - Set search criteria (extensions, patterns, etc.)
   - Preview matches
   - Download files

2. **Batch Processing**:
   - Upload batch configuration file
   - Review repositories and criteria
   - Start batch processing
   - Monitor progress

3. **Results Management**:
   - View download statistics
   - Export results
   - Access downloaded files

## 📁 Download Management

### Centralized Downloads

All downloads are organized in the `resulting_downloads/` folder:

```
resulting_downloads/
├── microsoft_vscode/
│   ├── src/
│   │   ├── main.ts
│   │   └── utils.ts
│   ├── package.json
│   └── README.md
├── fastapi_fastapi/
│   ├── fastapi/
│   │   ├── main.py
│   │   └── routing.py
│   └── docs/
├── analysis/
│   ├── microsoft_vscode_structure.json
│   └── fastapi_fastapi_structure.json
└── batch_results/
    └── batch_20231201_results.json
```

### Download Behavior

- **Automatic Organization**: Files maintain their repository structure
- **Conflict Resolution**: Repository names are sanitized for filesystem compatibility
- **Progress Tracking**: Real-time download progress with success/failure counts
- **Error Handling**: Failed downloads are logged and retried
- **Git Integration**: `resulting_downloads/` is automatically ignored by Git

### Custom Output Directories

```bash
# Custom directory (still goes to resulting_downloads/)
python github_file_hunter.py owner/repo file.txt --output-dir custom_folder

# Results in: resulting_downloads/custom_folder/file.txt
```

## 🔧 Configuration Examples

### AI/ML Repository Analysis

```json
[
  {
    "repo_url": "huggingface/transformers",
    "output_dir": "./resulting_downloads/transformers",
    "search_criteria": {
      "extensions": [".py"],
      "patterns": ["*model*", "*transformer*", "*attention*"],
      "exclude_patterns": ["*test*", "__pycache__/*", "examples/*"]
    }
  },
  {
    "repo_url": "tensorflow/tensorflow",
    "output_dir": "./resulting_downloads/tensorflow",
    "search_criteria": {
      "path_patterns": ["tensorflow/python/keras/*", "tensorflow/core/*"],
      "extensions": [".py", ".cc", ".h"],
      "max_size": "1MB"
    }
  }
]
```

### Web Development Stack

```json
[
  {
    "repo_url": "facebook/react",
    "profile": "frontend",
    "output_dir": "./resulting_downloads/react",
    "search_criteria": {
      "extensions": [".js", ".ts"],
      "exclude_patterns": ["*test*", "node_modules/*", "build/*"]
    }
  },
  {
    "repo_url": "expressjs/express",
    "profile": "backend",
    "output_dir": "./resulting_downloads/express",
    "search_criteria": {
      "extensions": [".js"],
      "patterns": ["lib/*", "*.js"],
      "exclude_patterns": ["test/*", "examples/*"]
    }
  }
]
```

### DevOps Configuration

```json
[
  {
    "repo_url": "kubernetes/kubernetes",
    "profile": "docker",
    "output_dir": "./resulting_downloads/k8s",
    "search_criteria": {
      "extensions": [".yaml", ".yml"],
      "patterns": ["*deploy*", "*service*", "*config*"],
      "exclude_patterns": ["vendor/*", "hack/*"]
    }
  },
  {
    "repo_url": "hashicorp/terraform",
    "output_dir": "./resulting_downloads/terraform",
    "search_criteria": {
      "extensions": [".tf", ".hcl"],
      "exclude_patterns": ["*test*", ".terraform/*"]
    }
  }
]
```

## 🐛 Troubleshooting

### Common Issues

#### Rate Limiting
```bash
# Error: API rate limit exceeded
# Solution: Use GitHub token
export GITHUB_TOKEN="your_token"
python github_file_hunter.py owner/repo --token $GITHUB_TOKEN
```

#### Repository Not Found
```bash
# Error: Repository owner/repo not found
# Solutions:
# 1. Check repository name spelling
# 2. Ensure repository is public or token has access
# 3. Verify token permissions
```

#### Pattern Matching Issues
```bash
# Error: No files found matching criteria
# Solutions:
# 1. Use --list-only to see all files first
# 2. Check pattern syntax (glob vs regex)
# 3. Use --structure-only to analyze repository
```

#### Download Failures
```bash
# Error: Failed to download files
# Solutions:
# 1. Check network connectivity
# 2. Verify file permissions in output directory
# 3. Reduce concurrent downloads: --concurrent 1
```

### Debug Mode

```bash
# Enable verbose output
python batch_hunter.py -f batch.json --download --verbose

# Test token detection
python test_token_detection.py
```

### Performance Optimization

```bash
# Optimize for large repositories
python batch_hunter.py -f batch.json --download --concurrent 10

# Limit file sizes
python github_file_hunter.py owner/repo --extensions .py --max-size 100000

# Use specific patterns to reduce search space
python github_file_hunter.py owner/repo --path-patterns "src/*" --extensions .py
```

## 📚 API Reference

### Search Profiles

| Profile | Extensions | Patterns | Use Case |
|---------|------------|----------|----------|
| `config` | .yml, .yaml, .json, .toml, .env | *config*, *settings*, *.env* | Configuration files |
| `api` | .py, .js, .ts, .go, .java | *api*, *route*, *endpoint* | API implementations |
| `auth` | .py, .js, .ts, .go, .java | *auth*, *login*, *jwt*, *oauth* | Authentication code |
| `database` | .sql, .py, .js, .go | *model*, *schema*, *migration* | Database code |
| `docker` | .yml, .yaml, .sh | Dockerfile*, *docker*, *compose* | Containerization |
| `cicd` | .yml, .yaml, .json, .sh | .github/*, *ci*, *pipeline* | CI/CD workflows |
| `docs` | .md, .rst, .txt | README*, docs/*, *.md | Documentation |
| `tests` | .py, .js, .ts, .go | *test*, *spec*, test/* | Test files |
| `frontend` | .js, .ts, .jsx, .tsx, .vue | src/*, components/* | Frontend code |
| `backend` | .py, .js, .go, .java, .php | server/*, api/*, services/* | Backend services |
| `scripts` | .sh, .py, .js, .ps1 | scripts/*, bin/*, tools/* | Build scripts |
| `ml` | .py, .ipynb, .pkl, .h5 | *model*, *train*, notebooks/* | ML/AI code |

### Command Line Arguments

#### github_file_hunter.py

| Argument | Short | Type | Description |
|----------|-------|------|-------------|
| `--extensions` | `-e` | list | File extensions to search |
| `--name-patterns` | `-n` | list | Filename patterns |
| `--path-patterns` | `-p` | list | Path patterns |
| `--exclude-patterns` | `-x` | list | Exclusion patterns |
| `--regex` | `-r` | string | Regular expression |
| `--min-size` | | int | Minimum file size (bytes) |
| `--max-size` | | int | Maximum file size (bytes) |
| `--branch` | `-b` | string | Git branch |
| `--output-dir` | `-o` | string | Output directory |
| `--token` | `-t` | string | GitHub token |
| `--list-only` | `-l` | flag | List without downloading |
| `--structure-only` | `-s` | flag | Structure analysis only |

#### batch_hunter.py

| Argument | Short | Type | Description |
|----------|-------|------|-------------|
| `--batch-file` | `-f` | string | Batch configuration file |
| `--create-sample` | | choice | Create sample (csv/json) |
| `--sample-file` | | string | Sample filename |
| `--download` | `-d` | flag | Download files |
| `--preview-only` | | flag | Preview matches only |
| `--concurrent` | `-c` | int | Max concurrent jobs |
| `--token` | `-t` | string | GitHub token |
| `--export` | | string | Export results file |
| `--export-format` | | choice | Export format (json/csv) |
| `--verbose` | `-v` | flag | Verbose output |
| `--quiet` | `-q` | flag | Quiet mode |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Network error |
| 4 | Authentication error |
| 5 | File system error |

## 🎯 Best Practices

### Performance

1. **Use GitHub Tokens**: Avoid rate limiting
2. **Optimize Patterns**: Use specific patterns to reduce search space
3. **Limit Concurrent Jobs**: Start with 3-5 concurrent downloads
4. **Filter by Size**: Exclude large files if not needed
5. **Use Profiles**: Leverage built-in search profiles

### Organization

1. **Centralized Downloads**: Let the tool manage `resulting_downloads/`
2. **Meaningful Names**: Use descriptive output directory names
3. **Batch Configurations**: Save and version your batch files
4. **Regular Cleanup**: Periodically clean up downloaded files

### Security

1. **Token Security**: Use environment variables for tokens
2. **Repository Access**: Verify repository permissions
3. **File Validation**: Review downloaded files before use
4. **Network Security**: Use HTTPS for all connections

---

**Happy hunting! 🎯 For more examples and updates, visit the [GitHub repository](https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek).**