# GitHub File Hunter - Smart Repository File Discovery & Download Tool

A powerful Python tool for intelligently discovering, analyzing, and downloading specific files from GitHub repositories without cloning entire repositories. Features advanced batch processing with repository structure analysis and smart validation.

## 🚀 Features

### Core Capabilities
- **Individual File Downloads** - Download specific files by exact path
- **Pattern-Based Search** - Use glob patterns to find files matching criteria
- **Batch Processing** - Process multiple repositories with a single configuration
- **Repository Structure Analysis** - Analyze repository structure before downloading
- **Smart Validation** - Automatic branch detection and file existence validation
- **Organized Output** - Structured folder organization with `output_subdir` support

### Advanced Features
- **Two-Phase Processing** - Structure analysis followed by validated downloads
- **Branch Auto-Detection** - Automatically detects correct branch names (main vs master)
- **File Validation** - Pre-validates file existence to prevent download failures
- **Pattern Validation** - Ensures patterns match actual repository files
- **Smart Cleanup** - Automatic cleanup of temporary files after successful operations
- **Error Prevention** - Prevents common issues like "branch not found" and "file not found"

## 📦 Installation

### Prerequisites
- Python 3.7+
- `aiohttp` for async HTTP requests
- `asyncio` for concurrent operations

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd GitHub-File-Seek

# Install dependencies
pip install aiohttp asyncio

# Set GitHub token (recommended for higher rate limits)
export GITHUB_TOKEN="your_github_token_here"
```

## 🔧 Usage

### Individual File Hunter

Download specific files from a repository:

```bash
# Download specific files
python github_file_hunter.py microsoft/vscode README.md package.json

# Search by file extensions
python github_file_hunter.py fastapi/fastapi --extensions .py --name-patterns "*api*"

# Search with path patterns
python github_file_hunter.py django/django --path-patterns "django/core/*" --extensions .py

# Use regex patterns
python github_file_hunter.py owner/repo --regex ".*\\.(js|ts)$"

# Analyze repository structure only
python github_file_hunter.py microsoft/vscode --structure-only
```

### Batch Processing (Recommended)

The enhanced batch hunter provides intelligent processing with structure validation:

```bash
# Run batch download with structure validation
python batch_hunter.py config.json --token your_github_token

# Structure analysis only (no downloads)
python batch_hunter.py config.json --structure-only --token your_github_token
```

## 📋 Configuration Format

### Batch Configuration JSON

Create a JSON configuration file for batch processing:

```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "individual_files": [
        "src/vs/workbench/api/browser/mainThreadLanguages.ts",
        "package.json"
      ],
      "patterns": [
        "src/vs/workbench/api/browser/*.ts"
      ],
      "exclude_patterns": [
        "*.test.ts",
        "test_*"
      ],
      "branch": "main",
      "max_files": 50,
      "output_subdir": "core"
    },
    {
      "owner": "facebook",
      "repo": "react",
      "patterns": [
        "packages/react/src/*.js"
      ],
      "exclude_patterns": [
        "__tests__/*",
        "*.test.js"
      ],
      "branch": "main",
      "max_files": 25,
      "output_subdir": "ui"
    }
  ],
  "output_dir": "./downloads",
  "create_repo_folders": false
}
```

### Configuration Parameters

#### Repository Level
- `owner` (required) - GitHub repository owner
- `repo` (required) - Repository name
- `individual_files` (optional) - List of specific file paths to download
- `patterns` (optional) - List of glob patterns for file matching
- `exclude_patterns` (optional) - List of patterns to exclude from downloads
- `branch` (optional) - Specific branch (auto-detected if not specified)
- `max_files` (optional) - Maximum number of files to download per repository
- `output_subdir` (optional) - Subdirectory within output_dir for organized structure

#### Global Level
- `output_dir` (optional) - Base output directory (default: "./downloads")
- `create_repo_folders` (optional) - Create separate folders per repository (default: true)

## 🔍 How It Works

### Two-Phase Processing

The batch hunter uses intelligent two-phase processing:

#### Phase 1: Structure Analysis
1. **Repository Analysis** - Analyzes each repository's structure
2. **Branch Detection** - Automatically detects correct branch names
3. **File Validation** - Validates that specified files actually exist
4. **Pattern Validation** - Ensures patterns match actual repository files
5. **Structure Storage** - Saves analysis to `PULLED_FILE_STRUCTURES/` folder

#### Phase 2: Validated Downloads
1. **Configuration Fixing** - Uses structure data to fix branch names and file paths
2. **Smart Matching** - Downloads only validated files and patterns
3. **Organized Output** - Places files in structured directories using `output_subdir`
4. **Cleanup** - Automatically removes temporary files after successful downloads

### Smart Validation Features

- **Branch Auto-Correction** - Fixes "main" vs "master" branch issues
- **File Existence Check** - Prevents "file not found" errors
- **Alternative File Suggestions** - Finds similar files when exact matches aren't available
- **Pattern Verification** - Validates patterns against actual repository contents

## 📁 Output Structure

### Standard Output
```
downloads/
├── owner_repo/
│   ├── file1.py
│   └── path/to/file2.js
└── another_owner_repo/
    └── file3.md
```

### Organized Output (with output_subdir)
```
project/
├── core/
│   ├── main_logic.py
│   └── utils.py
├── ui/
│   ├── components.js
│   └── styles.css
└── docs/
    └── README.md
```

### Structure Analysis Files
During processing, structure files are temporarily stored in:
```
PULLED_FILE_STRUCTURES/
├── microsoft_vscode_structure.json
├── facebook_react_structure.json
└── ...
```
*Note: These files are automatically cleaned up after successful downloads*

## 🛡️ Error Handling

### Common Issues Prevented
- **Branch Not Found** - Auto-detects correct branch names
- **File Not Found** - Validates file existence before download attempts
- **Pattern Mismatch** - Verifies patterns match actual files
- **Rate Limiting** - Use GitHub token for higher rate limits

### Failure Handling
- **Partial Failures** - Continues processing other repositories if some fail
- **Structure Preservation** - Keeps structure files for debugging when downloads fail
- **Detailed Logging** - Provides clear error messages and suggestions

## 🔑 Authentication

### GitHub Token Setup
For higher rate limits and private repository access:

```bash
# Environment variable (recommended)
export GITHUB_TOKEN="ghp_your_token_here"

# Command line parameter
python batch_hunter.py config.json --token ghp_your_token_here
```

### Token Permissions
Required permissions for your GitHub token:
- `public_repo` - For public repositories
- `repo` - For private repositories (if needed)

## 📊 Examples

### Example 1: AI/ML Project Structure
```json
{
  "repositories": [
    {
      "owner": "huggingface",
      "repo": "transformers",
      "patterns": ["src/transformers/models/bert/*.py"],
      "exclude_patterns": ["*test*"],
      "max_files": 20,
      "output_subdir": "models"
    },
    {
      "owner": "openai",
      "repo": "openai-python",
      "patterns": ["openai/*.py"],
      "exclude_patterns": ["tests/*"],
      "max_files": 15,
      "output_subdir": "api"
    }
  ],
  "output_dir": "./ai_project",
  "create_repo_folders": false
}
```

### Example 2: Web Development Stack
```json
{
  "repositories": [
    {
      "owner": "facebook",
      "repo": "react",
      "patterns": ["packages/react/src/*.js"],
      "output_subdir": "frontend"
    },
    {
      "owner": "expressjs",
      "repo": "express",
      "patterns": ["lib/*.js"],
      "output_subdir": "backend"
    },
    {
      "owner": "microsoft",
      "repo": "TypeScript",
      "individual_files": ["src/compiler/types.ts"],
      "output_subdir": "types"
    }
  ],
  "output_dir": "./web_stack"
}
```

## 🚨 Best Practices

### Configuration Design
- **Use specific patterns** - Avoid overly broad patterns that match too many files
- **Set reasonable max_files** - Prevent downloading excessive numbers of files
- **Organize with output_subdir** - Create logical folder structures
- **Include exclude_patterns** - Filter out test files and build artifacts

### Performance Optimization
- **Use GitHub tokens** - Avoid rate limiting issues
- **Batch related files** - Group related files in single repository configurations
- **Monitor file counts** - Use structure analysis to verify file counts before downloading

### Error Prevention
- **Let auto-detection work** - Don't specify branch names unless necessary
- **Use structure analysis first** - Run with `--structure-only` to verify configurations
- **Check patterns carefully** - Ensure patterns match expected files

## 🔧 Advanced Usage

### Repository Structure Analysis
```bash
# Analyze multiple repositories
python batch_hunter.py config.json --structure-only --token your_token

# Individual repository analysis
python github_file_hunter.py owner/repo --structure-only
```

### Custom Output Organization
```json
{
  "repositories": [
    {
      "owner": "tensorflow",
      "repo": "tensorflow",
      "patterns": ["tensorflow/python/ops/*.py"],
      "output_subdir": "core/ops"
    },
    {
      "owner": "tensorflow", 
      "repo": "tensorflow",
      "patterns": ["tensorflow/python/layers/*.py"],
      "output_subdir": "core/layers"
    }
  ],
  "output_dir": "./ml_framework"
}
```

## 📝 Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Solution: Use GitHub personal access token
   - Command: `--token your_github_token`

2. **Branch Not Found**
   - Solution: Let auto-detection work or check actual branch name
   - The tool automatically detects correct branch names

3. **No Files Found**
   - Solution: Use `--structure-only` to analyze repository first
   - Check that patterns match actual file paths

4. **Permission Denied**
   - Solution: Ensure GitHub token has appropriate permissions
   - Check if repository is private and token has `repo` scope

### Debug Mode
```bash
# Analyze structure first to debug configuration
python batch_hunter.py config.json --structure-only --token your_token

# Check individual repository
python github_file_hunter.py owner/repo --structure-only --token your_token
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with `aiohttp` for efficient async HTTP operations
- Inspired by the need for selective repository file extraction
- Thanks to the GitHub API for providing comprehensive repository access