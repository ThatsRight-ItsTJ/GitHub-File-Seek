# GitHub File Hunter - Complete Usage Guide

A powerful tool for finding and downloading specific files from GitHub repositories without cloning the entire repo.

## 🚀 Quick Start

### Installation
```bash
# Install dependencies
pip install aiohttp aiofiles

# Make scripts executable
chmod +x github_file_hunter.py
chmod +x github_hunter_profiles.py
```

### Basic Usage
```bash
# Find all Python files
python github_file_hunter.py microsoft/vscode --ext py

# Use pre-built profile for config files
python github_hunter_profiles.py microsoft/vscode --profile config

# Download all API-related files
python github_hunter_profiles.py fastapi/fastapi --profile api --download
```

## 🎯 Search Profiles (Easy Mode)

### Available Profiles
```bash
# List all available profiles
python github_hunter_profiles.py --list
```

**Built-in Profiles:**
- `config` - Configuration files (yml, json, toml, etc.)
- `api` - API-related files (routes, endpoints, clients)
- `auth` - Authentication and security files
- `database` - Database models, schemas, migrations
- `docker` - Docker and containerization files
- `ci` - CI/CD pipeline files
- `docs` - Documentation files
- `tests` - Test files and specs
- `frontend` - Frontend/UI files (js, css, html)
- `backend` - Backend/server files
- `scripts` - Scripts and automation
- `ml` - Machine Learning files
- `security` - Security-related files
- `large` - Large files (>1MB)

### Profile Examples
```bash
# Find config files and preview
python github_hunter_profiles.py kubernetes/kubernetes --profile config --preview-only

# Download Docker files
python github_hunter_profiles.py docker/compose --profile docker --download --output-dir ./docker_files

# Combine multiple profiles
python github_hunter_profiles.py fastapi/fastapi --profile "api,auth,docs" --download

# Show profile details
python github_hunter_profiles.py --show api
```

## 🔍 Advanced Search (Custom Mode)

### Search by File Extensions
```bash
# Find specific file types
python github_file_hunter.py owner/repo --ext py js ts

# Multiple extensions with size limit
python github_file_hunter.py owner/repo --ext py --min-size 1000 --max-size 100000
```

### Search by Name Patterns
```bash
# Find files with specific names (supports wildcards)
python github_file_hunter.py owner/repo --name "config.*" "*settings*" "*.yml"

# Case-sensitive search
python github_file_hunter.py owner/repo --name "README*" --case-sensitive
```

### Search by Path Patterns
```bash
# Find files in specific directories
python github_file_hunter.py owner/repo --path "src/*" "api/*" --ext py

# Exclude certain patterns
python github_file_hunter.py owner/repo --ext js --exclude "node_modules/*" "dist/*" "*.min.*"
```

### Search with Regex
```bash
# Use regex for complex patterns
python github_file_hunter.py owner/repo --regex ".*test.*\.py$"

# Find API endpoints
python github_file_hunter.py owner/repo --regex ".*(api|route|endpoint).*\.(py|js|ts)$"
```

### Size-based Search
```bash
# Find large files
python github_file_hunter.py owner/repo --min-size 1048576  # Files > 1MB

# Find small config files
python github_file_hunter.py owner/repo --ext yml json --max-size 10240  # Files < 10KB
```

## 📁 Output and Export Options

### Download Options
```bash
# Download to specific directory
python github_file_hunter.py owner/repo --ext py --download --output-dir ./python_files

# Preview before downloading
python github_file_hunter.py owner/repo --ext py --preview-only

# Control download concurrency
python github_file_hunter.py owner/repo --ext py --download --concurrent 10
```

### Export Results
```bash
# Export to JSON
python github_file_hunter.py owner/repo --ext py --export results.json

# Export to CSV
python github_file_hunter.py owner/repo --ext py --export results.csv --export-format csv

# Export to simple text list
python github_file_hunter.py owner/repo --ext py --export files.txt --export-format txt
```

### Display Options
```bash
# Show detailed information
python github_file_hunter.py owner/repo --ext py --details

# Quiet mode (minimal output)
python github_file_hunter.py owner/repo --ext py --quiet
```

## 🔑 Authentication

### GitHub Token Setup
```bash
# Set environment variable (recommended)
export GITHUB_TOKEN="ghp_your_token_here"

# Or pass directly
python github_file_hunter.py owner/repo --token ghp_your_token_here --ext py
```

**Why use a token?**
- Increased rate limits (5,000 vs 60 requests/hour)
- Access to private repositories
- Better reliability for large repositories

## 🎯 Real-World Examples

### 1. Audit Configuration Files
```bash
# Find all config files in a project
python github_hunter_profiles.py kubernetes/kubernetes --profile config --export k8s_configs.json

# Look for sensitive config patterns
python github_file_hunter.py owner/repo --name "*secret*" "*key*" "*password*" --ext yml json
```

### 2. Extract API Documentation
```bash
# Get API-related files and docs
python github_hunter_profiles.py fastapi/fastapi --profile "api,docs" --download --output-dir ./fastapi_study

# Find OpenAPI/Swagger specs
python github_file_hunter.py owner/repo --name "*swagger*" "*openapi*" "*.api" --ext yml json
```

### 3. Security Analysis
```bash
# Find security-related files
python github_hunter_profiles.py owner/repo --profile security --preview-only

# Look for potential secrets
python github_file_hunter.py owner/repo --name "*.pem" "*.key" "*secret*" "*token*"
```

### 4. Code Architecture Study
```bash
# Get backend structure
python github_hunter_profiles.py django/django --profile backend --path "django/*" --download

# Extract test patterns
python github_hunter_profiles.py pytest-dev/pytest --profile tests --download --output-dir ./test_patterns
```

### 5. DevOps Automation
```bash
# Collect CI/CD configurations
python github_hunter_profiles.py kubernetes/kubernetes --profile ci --download --output-dir ./k8s_ci

# Find deployment scripts
python github_file_hunter.py owner/repo --name "*deploy*" "*build*" --ext sh yml
```

### 6. Machine Learning Projects
```bash
# Extract ML models and notebooks
python github_hunter_profiles.py tensorflow/tensorflow --profile ml --download

# Find training scripts
python github_file_hunter.py owner/repo --name "*train*" "*model*" --ext py ipynb
```

## 🛠️ Custom Profiles

### Create Custom Profile
```bash
# Create a profile for React components
python github_hunter_profiles.py --create-profile react-components \
  --profile-description "React component files" \
  --profile-extensions jsx tsx \
  --profile-paths "src/components/*" "components/*" \
  --profile-names "*Component*" "*component*"
```

### Save and Reuse
```bash
# The custom profile is now available
python github_hunter_profiles.py facebook/react --profile react-components --download
```

## 📊 Performance Tips

### For Large Repositories
```bash
# Use specific paths to limit scope
python github_file_hunter.py kubernetes/kubernetes --path "cmd/*" "pkg/*" --ext go

# Limit file size to avoid huge downloads
python github_file_hunter.py owner/repo --ext py --max-size 1048576  # Max 1MB files

# Reduce concurrency for stability
python github_file_hunter.py owner/repo --ext py --download --concurrent 3
```

### Rate Limiting
```bash
# Use GitHub token to avoid rate limits
export GITHUB_TOKEN="your_token"

# For very large repos, consider using specific branches
python github_file_hunter.py owner/repo --branch main --ext py
```

## 🚨 Common Use Cases

### 1. Learning from Open Source
```bash
# Study FastAPI's architecture
python github_hunter_profiles.py tiangolo/fastapi --profile "api,auth" --download --output-dir ./fastapi_study

# Examine Django's models
python github_file_hunter.py django/django --name "*model*" --path "django/*" --ext py --download
```

### 2. Security Auditing
```bash
# Find configuration files that might contain secrets
python github_hunter_profiles.py owner/repo --profile config --name "*prod*" "*secret*"

# Look for hardcoded keys
python github_file_hunter.py owner/repo --regex ".*[kK]ey.*=.*" --ext py js
```

### 3. Documentation Gathering
```bash
# Collect all docs for offline reading
python github_hunter_profiles.py microsoft/vscode --profile docs --download --output-dir ./vscode_docs

# Find README files in subdirectories
python github_file_hunter.py owner/repo --name "README*" --path "*/*"
```

### 4. Code Migration Assistance
```bash
# Extract specific technology stack files
python github_file_hunter.py owner/repo --ext py --path "src/*" --exclude "*test*" --download

# Find database migrations
python github_file_hunter.py owner/repo --name "*migration*" "*migrate*" --ext py sql
```

## 🔧 Troubleshooting

### Common Issues
```bash
# Rate limited? Use a token
export GITHUB_TOKEN="your_token"

# Repository not found? Check URL format
python github_file_hunter.py owner/repo  # ✅ Good
python github_file_hunter.py https://github.com/owner/repo  # ✅ Also good

# No files found? Check your patterns
python github_file_hunter.py owner/repo --ext py --preview-only  # Test first

# Download failed? Check permissions and disk space
python github_file_hunter.py owner/repo --ext py --download --output-dir ./downloads
```

### Debug Mode
```bash
# Enable verbose output
python github_file_hunter.py owner/repo --ext py --details --preview-only
```

## 🎉 Pro Tips

1. **Start with `--preview-only`** to see what you'll get before downloading
2. **Use profiles** for common searches - they're faster and more reliable
3. **Set GitHub token** as environment variable for seamless authentication
4. **Combine multiple profiles** for comprehensive searches
5. **Export results** to analyze patterns before downloading
6. **Use size limits** to avoid downloading huge files accidentally
7. **Exclude common directories** like `node_modules`, `.git`, `dist` to focus on source code

---

Happy hunting! 🎯
