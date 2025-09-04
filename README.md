# GitHub File Hunter 🔍

An enhanced version of DownGit that intelligently finds and downloads specific files from GitHub repositories without cloning the entire repository.

## Features

- **Smart File Discovery**: Use GitHub API to traverse repository trees and find files matching your criteria
- **Pattern-Based Searching**: Support for wildcards, regex patterns, file extensions, and custom filters
- **Pre-built Profiles**: 14 ready-to-use search profiles for common development scenarios
- **Batch Processing**: Process multiple repositories from configuration files
- **Concurrent Downloads**: Fast, rate-limited downloads with progress tracking
- **Multiple Export Formats**: Save results as JSON, CSV, or TXT
- **Web Interface**: User-friendly Flask dashboard for non-technical users
- **Flexible Output**: Preview-only mode or direct downloads to organized folders

## Installation

```bash
# Clone the repository
git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
cd GitHub-File-Seek

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Basic Usage

```bash
# Find all Python files in a repository
python github_file_hunter.py microsoft/vscode --ext py --preview-only

# Download configuration files using a pre-built profile
python github_file_hunter.py facebook/react --profile config --download

# Search for files matching a pattern
python github_file_hunter.py google/tensorflow --pattern "*.dockerfile" --download
```

### Using Pre-built Profiles

```bash
# Available profiles: config, api, auth, database, docker, ci, docs, tests, frontend, backend, scripts, ml, security, large

# Find all configuration files
python github_file_hunter.py owner/repo --profile config --preview-only

# Download API-related files
python github_file_hunter.py owner/repo --profile api --download

# Find documentation files
python github_file_hunter.py owner/repo --profile docs --preview-only
```

## Batch Processing 📦

The batch processing feature allows you to process multiple repositories at once using configuration files. This is perfect for:
- Analyzing multiple projects simultaneously
- Collecting files from related repositories
- Automated file gathering workflows
- Research and comparison tasks

### Creating Batch Configuration Files

#### CSV Format

Create a CSV file with repository information:

```csv
repository,profile,extensions,patterns,max_files,output_folder
microsoft/vscode,config,,*.json;*.yml,50,vscode_configs
facebook/react,frontend,js;jsx;ts;tsx,,100,react_frontend
google/tensorflow,ml,py,,200,tensorflow_ml
docker/compose,docker,,docker*;*.dockerfile,30,docker_files
```

**CSV Columns:**
- `repository`: GitHub repository in format `owner/repo`
- `profile`: Pre-built profile name (optional)
- `extensions`: Comma-separated file extensions (optional)
- `patterns`: Semicolon-separated file patterns (optional)
- `max_files`: Maximum files to download per repository (optional)
- `output_folder`: Custom output folder name (optional)

#### JSON Format

Create a JSON file with detailed configuration:

```json
{
  "repositories": [
    {
      "repository": "microsoft/vscode",
      "profile": "config",
      "patterns": ["*.json", "*.yml", "*.yaml"],
      "max_files": 50,
      "output_folder": "vscode_configs"
    },
    {
      "repository": "facebook/react",
      "extensions": ["js", "jsx", "ts", "tsx"],
      "exclude_patterns": ["*.test.*", "*.spec.*"],
      "max_files": 100,
      "output_folder": "react_source"
    },
    {
      "repository": "google/tensorflow",
      "profile": "ml",
      "custom_filters": {
        "min_size": 1024,
        "max_size": 1048576
      },
      "output_folder": "tensorflow_ml"
    }
  ],
  "global_settings": {
    "download": true,
    "export_format": "json",
    "concurrent_limit": 5,
    "rate_limit_delay": 0.1
  }
}
```

### Running Batch Processing

```bash
# Process repositories from CSV file
python batch_hunter.py --config repositories.csv

# Process repositories from JSON file
python batch_hunter.py --config batch_config.json

# Preview mode (don't download, just show what would be found)
python batch_hunter.py --config repositories.csv --preview-only

# Custom output directory
python batch_hunter.py --config batch_config.json --output-dir /path/to/output

# Export results to specific format
python batch_hunter.py --config repositories.csv --export-format csv
```

### Batch Processing Options

```bash
python batch_hunter.py [OPTIONS]

Options:
  --config PATH              Configuration file (CSV or JSON) [required]
  --output-dir PATH          Base output directory [default: ./batch_downloads]
  --preview-only            Show what would be downloaded without downloading
  --export-format FORMAT    Export format: json, csv, txt [default: json]
  --concurrent-limit INT     Max concurrent downloads [default: 5]
  --rate-limit FLOAT        Delay between requests in seconds [default: 0.1]
  --verbose                 Enable verbose logging
  --help                    Show help message
```

### Example Batch Workflows

#### 1. Configuration Analysis Across Projects

```csv
repository,profile,max_files,output_folder
kubernetes/kubernetes,config,100,k8s_configs
docker/docker,config,50,docker_configs
hashicorp/terraform,config,75,terraform_configs
ansible/ansible,config,60,ansible_configs
```

```bash
python batch_hunter.py --config config_analysis.csv --export-format json
```

#### 2. Frontend Framework Comparison

```json
{
  "repositories": [
    {
      "repository": "facebook/react",
      "extensions": ["js", "jsx", "ts", "tsx"],
      "max_files": 200,
      "output_folder": "react_source"
    },
    {
      "repository": "vuejs/vue",
      "extensions": ["js", "ts", "vue"],
      "max_files": 200,
      "output_folder": "vue_source"
    },
    {
      "repository": "angular/angular",
      "extensions": ["ts", "js"],
      "max_files": 200,
      "output_folder": "angular_source"
    }
  ],
  "global_settings": {
    "download": true,
    "export_format": "csv"
  }
}
```

#### 3. Security Analysis

```csv
repository,profile,patterns,max_files,output_folder
owasp/owasp-top-ten,security,*.md;*.yml;*.json,50,owasp_security
securecodewarrior/secure-code-review,security,,100,secure_review
microsoft/security-devops-action,security,*.yml;*.yaml;*.json,75,ms_security
```

### Batch Processing Output

The batch processor creates:
- **Individual repository folders**: Each repository gets its own subfolder
- **Consolidated reports**: Summary files with all findings
- **Export files**: Results in your chosen format (JSON/CSV/TXT)
- **Progress logs**: Detailed processing information

Example output structure:
```
batch_downloads/
├── microsoft_vscode/          # Repository-specific downloads
│   ├── package.json
│   ├── tsconfig.json
│   └── ...
├── facebook_react/
│   ├── package.json
│   ├── babel.config.js
│   └── ...
├── batch_results.json         # Consolidated results
├── batch_summary.csv          # Processing summary
└── batch_log.txt             # Detailed processing log
```

## Command Line Options

### github_file_hunter.py

```bash
python github_file_hunter.py REPOSITORY [OPTIONS]

Arguments:
  REPOSITORY                GitHub repository (owner/repo format)

Options:
  --profile PROFILE         Use pre-built search profile
  --ext EXTENSIONS          File extensions (comma-separated)
  --pattern PATTERNS        File patterns (supports wildcards)
  --regex PATTERN           Regular expression pattern
  --exclude PATTERNS        Exclude patterns
  --max-files INT           Maximum files to process [default: 100]
  --download                Download files (default: preview only)
  --output-dir PATH         Output directory [default: ./downloads]
  --export-format FORMAT    Export format: json, csv, txt [default: json]
  --concurrent-limit INT    Max concurrent downloads [default: 10]
  --rate-limit FLOAT        Delay between requests [default: 0.1]
  --github-token TOKEN      GitHub API token
  --verbose                 Enable verbose logging
  --help                    Show help message
```

## Pre-built Profiles

| Profile | Description | File Types |
|---------|-------------|------------|
| `config` | Configuration files | .json, .yml, .yaml, .toml, .ini, .cfg, .conf |
| `api` | API-related files | OpenAPI specs, API docs, endpoint definitions |
| `auth` | Authentication files | Auth configs, JWT, OAuth, security policies |
| `database` | Database files | SQL, migrations, database configs |
| `docker` | Docker files | Dockerfiles, docker-compose, container configs |
| `ci` | CI/CD files | GitHub Actions, Jenkins, Travis, CircleCI |
| `docs` | Documentation | README, docs, guides, wikis |
| `tests` | Test files | Unit tests, integration tests, test configs |
| `frontend` | Frontend files | HTML, CSS, JS, React, Vue, Angular |
| `backend` | Backend files | Server code, APIs, microservices |
| `scripts` | Scripts | Shell, Python, automation scripts |
| `ml` | Machine Learning | Models, datasets, ML configs, notebooks |
| `security` | Security files | Security configs, policies, certificates |
| `large` | Large files | Files over 1MB, binaries, assets |

## Web Interface

Launch the web dashboard for a user-friendly experience:

```bash
python web_interface.py
```

Then open http://localhost:5000 in your browser.

Features:
- Repository browsing with real-time file tree
- Interactive file filtering and selection
- Drag-and-drop batch configuration upload
- Progress tracking for downloads
- Export results in multiple formats

## Advanced Usage

### Custom Filters

```bash
# Find Python files larger than 10KB
python github_file_hunter.py owner/repo --ext py --min-size 10240

# Find recently modified files (last 30 days)
python github_file_hunter.py owner/repo --modified-since 30

# Exclude test files
python github_file_hunter.py owner/repo --ext js --exclude "*.test.*,*.spec.*"
```

### Using GitHub Token

For better rate limits and private repository access:

```bash
export GITHUB_TOKEN="your_token_here"
python github_file_hunter.py owner/private-repo --download
```

### Export Formats

```bash
# Export as CSV
python github_file_hunter.py owner/repo --export-format csv

# Export as plain text
python github_file_hunter.py owner/repo --export-format txt

# Export as JSON (default)
python github_file_hunter.py owner/repo --export-format json
```

## Examples

### Find Configuration Files
```bash
python github_file_hunter.py kubernetes/kubernetes --profile config --max-files 50 --download
```

### Download Frontend Assets
```bash
python github_file_hunter.py facebook/react --profile frontend --exclude "*.test.*" --download
```

### Security Audit
```bash
python github_file_hunter.py owner/repo --profile security --export-format csv --preview-only
```

### Custom Pattern Search
```bash
python github_file_hunter.py owner/repo --pattern "*.dockerfile,docker-compose*" --download
```

## Troubleshooting

### Rate Limiting
If you encounter rate limiting:
- Use a GitHub token: `export GITHUB_TOKEN="your_token"`
- Increase rate limit delay: `--rate-limit 0.5`
- Reduce concurrent downloads: `--concurrent-limit 3`

### Large Repositories
For large repositories:
- Use `--max-files` to limit results
- Use specific patterns to narrow search
- Use `--preview-only` first to estimate size

### Memory Issues
If processing very large files:
- Reduce `--concurrent-limit`
- Use smaller `--max-files` values
- Process in smaller batches

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built upon the DownGit concept
- Uses GitHub API for repository traversal
- Inspired by the need for selective file downloading from repositories