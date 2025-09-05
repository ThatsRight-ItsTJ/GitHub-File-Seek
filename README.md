# GitHub File Hunter 🔍

A powerful Python tool for hunting and downloading specific files from GitHub repositories with advanced search capabilities, batch processing, and individual file downloads.

## 🚀 Features

- **Individual File Downloads**: Download specific files by exact path from any repository
- **Pattern-Based Search**: Hunt files using wildcards, extensions, and custom patterns
- **Batch Processing**: Process multiple repositories and files in one operation
- **Pre-built Profiles**: 14 ready-to-use search profiles for common file types
- **Web Interface**: User-friendly Flask dashboard for easy interaction
- **Flexible Configuration**: JSON and CSV configuration support
- **Smart Filtering**: Advanced filtering by file size, type, and content
- **Rate Limiting**: Built-in GitHub API rate limit handling

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/ThatsRight-ItsTJ/GitHub-File-Seek.git
cd GitHub-File-Seek

# Install dependencies
pip install -r requirements.txt

# Set up your GitHub token (optional but recommended)
export GITHUB_TOKEN="your_github_token_here"
```

## 🎯 Individual File Downloads

### Basic Syntax
Download specific files by providing their exact paths:

```bash
python github_file_hunter.py <owner/repo> <file1> [file2] [file3] ...
```

### Examples

**Download a single file:**
```bash
python github_file_hunter.py microsoft/vscode README.md
```

**Download multiple specific files:**
```bash
python github_file_hunter.py microsoft/vscode README.md package.json src/main.ts
```

**Download files from different directories:**
```bash
python github_file_hunter.py facebook/react README.md packages/react/package.json scripts/build.js
```

**Download configuration files:**
```bash
python github_file_hunter.py nodejs/node package.json .gitignore Dockerfile
```

### Individual File Download Features

- ✅ **Exact Path Matching**: Specify the complete file path
- ✅ **Multiple Files**: Download several files in one command
- ✅ **Cross-Directory**: Files from any directory structure
- ✅ **Error Handling**: Clear feedback for missing or inaccessible files
- ✅ **Progress Tracking**: Real-time download progress

## 🔍 Pattern-Based Search

Hunt files using patterns and wildcards:

```bash
# Find all Python files
python github_file_hunter.py microsoft/vscode "*.py"

# Find configuration files
python github_file_hunter.py facebook/react "*.json" "*.yml"

# Find files in specific directories
python github_file_hunter.py nodejs/node "src/*.js" "test/*.js"
```

## 📊 Batch Processing

### Including Individual Files in Batch Operations

You can combine individual file downloads with pattern matching in batch configurations.

#### JSON Configuration Format

```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "individual_files": ["README.md", "package.json", "src/main.ts"],
      "patterns": ["*.py", "*.json"],
      "max_files": 50
    },
    {
      "owner": "facebook", 
      "repo": "react",
      "individual_files": ["README.md", "LICENSE"],
      "patterns": ["packages/*/package.json"]
    }
  ],
  "output_dir": "downloads",
  "create_repo_folders": true
}
```

#### CSV Configuration Format

```csv
owner,repo,individual_files,patterns,max_files
microsoft,vscode,"README.md;package.json;src/main.ts","*.py;*.json",50
facebook,react,"README.md;LICENSE","packages/*/package.json",25
nodejs,node,"package.json;.gitignore","src/*.js;test/*.js",30
```

### Running Batch Operations

```bash
# Using JSON configuration
python batch_hunter.py --config batch_config.json

# Using CSV configuration  
python batch_hunter.py --csv repositories.csv

# Generate example configurations
python batch_hunter.py --generate-examples
```

### Advanced Batch Configuration

```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode", 
      "individual_files": [
        "README.md",
        "package.json", 
        "src/main.ts",
        "build/gulpfile.js"
      ],
      "patterns": [
        "*.py",
        "src/**/*.ts", 
        "extensions/*/package.json"
      ],
      "exclude_patterns": ["node_modules/*", "*.min.js"],
      "max_files": 100,
      "max_size_mb": 10
    }
  ],
  "output_dir": "batch_downloads",
  "create_repo_folders": true,
  "github_token": "optional_token_here"
}
```

## 🎨 Pre-built Profiles

Use ready-made search profiles for common scenarios:

```bash
# Web development files
python github_file_hunter.py microsoft/vscode --profile web_dev

# Python project files  
python github_file_hunter.py python/cpython --profile python_dev

# Configuration files
python github_file_hunter.py kubernetes/kubernetes --profile config_files

# Documentation files
python github_file_hunter.py facebook/react --profile docs
```

### Available Profiles

1. **web_dev** - HTML, CSS, JS, TS files
2. **python_dev** - Python source and config files
3. **config_files** - Configuration and settings files
4. **docs** - Documentation and README files
5. **docker_files** - Docker and containerization files
6. **ci_cd** - CI/CD pipeline files
7. **mobile_dev** - Mobile development files
8. **data_science** - Data science and ML files
9. **security** - Security and authentication files
10. **api_files** - API and service files
11. **test_files** - Testing and QA files
12. **build_files** - Build and deployment files
13. **license_legal** - License and legal files
14. **readme_docs** - README and documentation files

## 🌐 Web Interface

Launch the web dashboard for easy file hunting:

```bash
python web_interface.py
```

Then open http://localhost:5000 in your browser for a user-friendly interface.

## 📋 Command Line Options

### Individual File Downloads
```bash
python github_file_hunter.py <owner/repo> <file1> [file2] [file3] ...
  --token TOKEN          GitHub personal access token
  --output-dir DIR       Output directory (default: downloads)
  --create-folders       Create repository folders
  --verbose              Verbose output
```

### Pattern-Based Search
```bash
python github_file_hunter.py <owner/repo> <pattern1> [pattern2] ...
  --profile PROFILE      Use pre-built search profile
  --max-files N          Maximum files to download (default: 100)
  --max-size-mb N        Maximum file size in MB (default: 10)
  --exclude PATTERN      Exclude files matching pattern
  --token TOKEN          GitHub personal access token
  --output-dir DIR       Output directory
  --create-folders       Create repository folders
  --list-only            List files without downloading
  --verbose              Verbose output
```

### Batch Processing
```bash
python batch_hunter.py
  --config FILE          JSON configuration file
  --csv FILE            CSV configuration file  
  --generate-examples    Generate example configuration files
  --verbose             Verbose output
```

## 🔧 Configuration Examples

### Simple Individual Files Config
```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "individual_files": ["README.md", "package.json"]
    }
  ]
}
```

### Mixed Individual Files and Patterns
```json
{
  "repositories": [
    {
      "owner": "facebook", 
      "repo": "react",
      "individual_files": ["README.md", "LICENSE", "CHANGELOG.md"],
      "patterns": ["packages/*/package.json", "scripts/*.js"],
      "max_files": 25
    }
  ]
}
```

### Complex Multi-Repository Config
```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "individual_files": ["README.md", "package.json", "src/main.ts"],
      "patterns": ["*.py", "src/**/*.ts"],
      "exclude_patterns": ["node_modules/*"],
      "max_files": 50
    },
    {
      "owner": "facebook",
      "repo": "react", 
      "individual_files": ["README.md", "LICENSE"],
      "patterns": ["packages/*/package.json"]
    },
    {
      "owner": "nodejs",
      "repo": "node",
      "individual_files": ["package.json", ".gitignore", "Dockerfile"],
      "patterns": ["src/*.js", "test/*.js"],
      "max_files": 30
    }
  ],
  "output_dir": "multi_repo_downloads",
  "create_repo_folders": true
}
```

## 📈 Usage Examples

### Download Specific Files from Popular Repositories

```bash
# Get core files from VS Code
python github_file_hunter.py microsoft/vscode README.md package.json src/main.ts

# Get React's main files  
python github_file_hunter.py facebook/react README.md LICENSE packages/react/package.json

# Get Node.js configuration
python github_file_hunter.py nodejs/node package.json .gitignore Dockerfile

# Get Kubernetes manifests
python github_file_hunter.py kubernetes/kubernetes README.md Dockerfile build/build-image/Dockerfile
```

### Batch Download with Individual Files

Create `my_config.json`:
```json
{
  "repositories": [
    {
      "owner": "microsoft",
      "repo": "vscode",
      "individual_files": ["README.md", "package.json", "gulpfile.js"],
      "patterns": ["src/**/*.ts", "extensions/*/package.json"]
    },
    {
      "owner": "facebook", 
      "repo": "react",
      "individual_files": ["README.md", "LICENSE", "CHANGELOG.md"],
      "patterns": ["packages/*/package.json"]
    }
  ],
  "output_dir": "my_downloads"
}
```

Run the batch operation:
```bash
python batch_hunter.py --config my_config.json
```

## 🛠️ Advanced Features

### Error Handling
- Graceful handling of missing files
- Clear error messages for inaccessible repositories
- Automatic retry for rate-limited requests

### Performance Optimization
- Concurrent downloads for faster processing
- Smart caching to avoid duplicate requests
- Progress bars for long-running operations

### Security
- Secure token handling
- Validation of file paths and patterns
- Protection against directory traversal

## 📝 Output Structure

```
downloads/
├── microsoft_vscode/
│   ├── README.md
│   ├── package.json
│   └── src/
│       └── main.ts
├── facebook_react/
│   ├── README.md
│   ├── LICENSE
│   └── packages/
│       └── react/
│           └── package.json
└── batch_results.json
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Provide detailed information for better assistance

## 🔗 Related Projects

- [GitHub CLI](https://cli.github.com/) - Official GitHub command line tool
- [PyGithub](https://github.com/PyGithub/PyGithub) - Python GitHub API library
- [GitPython](https://github.com/gitpython-developers/GitPython) - Git repository interaction

---

**Happy File Hunting! 🎯**