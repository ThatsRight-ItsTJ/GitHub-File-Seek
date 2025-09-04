#!/usr/bin/env python3
"""
GitHub File Hunter - Web Interface

A Flask-based web interface for the GitHub File Hunter tool.
Provides an easy-to-use GUI for repository exploration and file downloading.
"""

import os
import asyncio
import json
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
import tempfile
import zipfile
from pathlib import Path
from github_file_hunter import GitHubFileHunter, SearchCriteria
from github_hunter_profiles import SEARCH_PROFILES

app = Flask(__name__)
CORS(app)

# Global configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file upload

@app.route('/')
def index():
    """Main interface page."""
    return render_template('index.html', profiles=list(SEARCH_PROFILES.keys()))

@app.route('/api/repository/tree', methods=['POST'])
def get_repository_tree():
    """Get repository file tree."""
    data = request.get_json()
    repo_url = data.get('repo_url')
    branch = data.get('branch')
    token = data.get('token')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    async def fetch_tree():
        try:
            async with GitHubFileHunter(token) as hunter:
                owner, repo, detected_branch = hunter.parse_github_url(repo_url)
                search_branch = branch or detected_branch
                
                tree_data = await hunter.get_repository_tree(owner, repo, search_branch)
                
                return {
                    'success': True,
                    'owner': owner,
                    'repo': repo,
                    'branch': search_branch,
                    'total_files': len([item for item in tree_data.get('tree', []) if item['type'] == 'blob']),
                    'tree': tree_data.get('tree', [])
                }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    result = asyncio.run(fetch_tree())
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/search', methods=['POST'])
def search_files():
    """Search for files in repository."""
    data = request.get_json()
    
    repo_url = data.get('repo_url')
    search_criteria = data.get('search_criteria', {})
    profile = data.get('profile')
    branch = data.get('branch')
    token = data.get('token')
    
    if not repo_url:
        return jsonify({'error': 'Repository URL is required'}), 400
    
    async def perform_search():
        try:
            async with GitHubFileHunter(token) as hunter:
                owner, repo, detected_branch = hunter.parse_github_url(repo_url)
                search_branch = branch or detected_branch
                
                # Get repository tree
                tree_data = await hunter.get_repository_tree(owner, repo, search_branch)
                
                # Create search criteria
                if profile and profile in SEARCH_PROFILES:
                    criteria = SEARCH_PROFILES[profile]['criteria']
                else:
                    criteria = SearchCriteria()
                    
                    if 'name_patterns' in search_criteria:
                        criteria.name_patterns = search_criteria['name_patterns']
                    if 'extensions' in search_criteria:
                        criteria.extensions = search_criteria['extensions']
                    if 'path_patterns' in search_criteria:
                        criteria.path_patterns = search_criteria['path_patterns']
                    if 'exclude_patterns' in search_criteria:
                        criteria.exclude_patterns = search_criteria['exclude_patterns']
                    if 'min_size' in search_criteria:
                        criteria.min_size = search_criteria['min_size']
                    if 'max_size' in search_criteria:
                        criteria.max_size = search_criteria['max_size']
                    if 'regex_pattern' in search_criteria:
                        criteria.regex_pattern = search_criteria['regex_pattern']
                
                # Search for matches
                matches = hunter.search_files(tree_data, criteria, owner, repo, search_branch)
                
                # Convert matches to JSON-serializable format
                results = []
                total_size = 0
                
                for match in matches:
                    match_data = {
                        'path': match.path,
                        'filename': match.filename,
                        'directory': match.directory,
                        'size': match.size,
                        'extension': match.extension,
                        'download_url': match.download_url,
                        'sha': match.sha
                    }
                    results.append(match_data)
                    total_size += match.size
                
                return {
                    'success': True,
                    'matches': results,
                    'total_files': len(results),
                    'total_size': total_size,
                    'profile_used': profile if profile else 'custom'
                }
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    result = asyncio.run(perform_search())
    
    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/api/download', methods=['POST'])
def download_files():
    """Download selected files as a ZIP archive."""
    data = request.get_json()
    
    files_to_download = data.get('files', [])
    repo_info = data.get('repo_info', {})
    token = data.get('token')
    
    if not files_to_download:
        return jsonify({'error': 'No files selected for download'}), 400
    
    async def download_and_zip():
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, 'github_files.zip')
                
                async with GitHubFileHunter(token) as hunter:
                    # Download files to temp directory
                    download_dir = os.path.join(temp_dir, 'downloads')
                    os.makedirs(download_dir, exist_ok=True)
                    
                    # Create FileMatch objects from the data
                    from github_file_hunter import FileMatch
                    matches = []
                    
                    for file_data in files_to_download:
                        match = FileMatch(
                            path=file_data['path'],
                            size=file_data['size'],
                            download_url=file_data['download_url'],
                            sha=file_data['sha']
                        )
                        matches.append(match)
                    
                    # Download files
                    await hunter.download_files(matches, download_dir)
                    
                    # Create ZIP file
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(download_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, download_dir)
                                zipf.write(file_path, arcname)
                    
                    # Read ZIP file content
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()
                    
                    return {
                        'success': True,
                        'zip_content': zip_content,
                        'filename': f"{repo_info.get('owner', 'repo')}_{repo_info.get('repo', 'files')}.zip"
                    }
                    
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    result = asyncio.run(download_and_zip())
    
    if result['success']:
        # Save ZIP to temporary file and return download link
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        temp_file.write(result['zip_content'])
        temp_file.close()
        
        # Store file info in session or cache for download
        return jsonify({
            'success': True,
            'download_url': f'/download/{os.path.basename(temp_file.name)}',
            'filename': result['filename']
        })
    else:
        return jsonify(result), 400

@app.route('/download/<filename>')
def serve_download(filename):
    """Serve downloaded ZIP file."""
    temp_path = os.path.join(tempfile.gettempdir(), filename)
    
    if os.path.exists(temp_path):
        return send_file(temp_path, as_attachment=True, download_name=filename)
    else:
        return "File not found", 404

@app.route('/api/profiles')
def get_profiles():
    """Get available search profiles."""
    profiles_data = {}
    
    for name, profile in SEARCH_PROFILES.items():
        criteria = profile['criteria']
        profiles_data[name] = {
            'description': profile['description'],
            'name_patterns': criteria.name_patterns,
            'extensions': criteria.extensions,
            'path_patterns': criteria.path_patterns,
            'exclude_patterns': criteria.exclude_patterns,
            'min_size': criteria.min_size if criteria.min_size > 0 else None,
            'max_size': criteria.max_size if criteria.max_size < float('inf') else None,
            'regex_pattern': criteria.regex_pattern
        }
    
    return jsonify(profiles_data)

# Create templates directory and basic HTML template
def create_templates():
    """Create the templates directory and basic HTML template."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>GitHub File Hunter</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f7fa; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #2c3e50; margin-bottom: 10px; }
        .card { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; color: #34495e; }
        .form-control { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; }
        .btn { padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; margin-right: 10px; }
        .btn-primary { background: #3498db; color: white; }
        .btn-success { background: #27ae60; color: white; }
        .btn-warning { background: #f39c12; color: white; }
        .btn:hover { opacity: 0.9; }
        .results { margin-top: 20px; }
        .file-item { padding: 10px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }
        .file-item:hover { background: #f8f9fa; }
        .file-info { flex: 1; }
        .file-path { font-weight: bold; color: #2c3e50; }
        .file-meta { font-size: 12px; color: #7f8c8d; }
        .loading { text-align: center; padding: 20px; }
        .error { color: #e74c3c; background: #fdf2f2; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .success { color: #27ae60; background: #f2fdf2; padding: 10px; border-radius: 4px; margin: 10px 0; }
        .profiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 15px 0; }
        .profile-btn { padding: 8px 12px; background: #ecf0f1; border: 1px solid #bdc3c7; border-radius: 4px; cursor: pointer; text-align: center; }
        .profile-btn:hover { background: #d5dbdb; }
        .profile-btn.active { background: #3498db; color: white; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 GitHub File Hunter</h1>
            <p>Find and download specific files from GitHub repositories</p>
        </div>

        <div class="card">
            <h3>Repository Information</h3>
            <div class="form-group">
                <label for="repo-url">Repository URL or owner/repo:</label>
                <input type="text" id="repo-url" class="form-control" placeholder="e.g., microsoft/vscode or https://github.com/microsoft/vscode">
            </div>
            <div class="form-group">
                <label for="branch">Branch (optional):</label>
                <input type="text" id="branch" class="form-control" placeholder="main, master, develop...">
            </div>
            <div class="form-group">
                <label for="token">GitHub Token (optional but recommended):</label>
                <input type="password" id="token" class="form-control" placeholder="ghp_...">
            </div>
            <button class="btn btn-primary" onclick="loadRepository()">Load Repository</button>
        </div>

        <div class="card" id="search-section" style="display: none;">
            <h3>Search Options</h3>
            
            <div class="form-group">
                <label>Quick Profiles:</label>
                <div class="profiles" id="profiles-grid"></div>
            </div>

            <div class="form-group">
                <label for="extensions">File Extensions (comma-separated):</label>
                <input type="text" id="extensions" class="form-control" placeholder="py, js, md, yml">
            </div>
            <div class="form-group">
                <label for="name-patterns">Name Patterns (comma-separated):</label>
                <input type="text" id="name-patterns" class="form-control" placeholder="*config*, README*, *.test.*">
            </div>
            <div class="form-group">
                <label for="path-patterns">Path Patterns (comma-separated):</label>
                <input type="text" id="path-patterns" class="form-control" placeholder="src/*, docs/*, api/*">
            </div>
            <div class="form-group">
                <label for="exclude-patterns">Exclude Patterns (comma-separated):</label>
                <input type="text" id="exclude-patterns" class="form-control" placeholder="node_modules/*, *.min.*, test/*">
            </div>
            
            <button class="btn btn-success" onclick="searchFiles()">Search Files</button>
            <button class="btn btn-warning" onclick="clearSearch()">Clear</button>
        </div>

        <div class="card" id="results-section" style="display: none;">
            <h3>Search Results</h3>
            <div id="results-summary"></div>
            <div id="results-list"></div>
            <div id="download-section" style="margin-top: 20px; display: none;">
                <button class="btn btn-success" onclick="downloadSelected()">Download Selected Files</button>
                <button class="btn btn-primary" onclick="selectAll()">Select All</button>
                <button class="btn btn-warning" onclick="selectNone()">Select None</button>
            </div>
        </div>

        <div id="loading" class="loading" style="display: none;">
            <p>⏳ Loading...</p>
        </div>

        <div id="messages"></div>
    </div>

    <script>
        let currentRepo = null;
        let searchResults = [];
        let selectedProfile = null;

        // Load available profiles
        fetch('/api/profiles')
            .then(response => response.json())
            .then(profiles => {
                const grid = document.getElementById('profiles-grid');
                for (const [name, profile] of Object.entries(profiles)) {
                    const btn = document.createElement('div');
                    btn.className = 'profile-btn';
                    btn.textContent = name;
                    btn.title = profile.description;
                    btn.onclick = () => selectProfile(name, profile);
                    grid.appendChild(btn);
                }
            });

        function selectProfile(name, profile) {
            // Clear previous selection
            document.querySelectorAll('.profile-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            selectedProfile = name;
            
            // Fill form fields with profile data
            document.getElementById('extensions').value = profile.extensions ? profile.extensions.join(', ') : '';
            document.getElementById('name-patterns').value = profile.name_patterns ? profile.name_patterns.join(', ') : '';
            document.getElementById('path-patterns').value = profile.path_patterns ? profile.path_patterns.join(', ') : '';
            document.getElementById('exclude-patterns').value = profile.exclude_patterns ? profile.exclude_patterns.join(', ') : '';
        }

        function showLoading(show) {
            document.getElementById('loading').style.display = show ? 'block' : 'none';
        }

        function showMessage(message, type = 'error') {
            const div = document.createElement('div');
            div.className = type;
            div.textContent = message;
            document.getElementById('messages').appendChild(div);
            setTimeout(() => div.remove(), 5000);
        }

        function loadRepository() {
            const repoUrl = document.getElementById('repo-url').value.trim();
            const branch = document.getElementById('branch').value.trim();
            const token = document.getElementById('token').value.trim();

            if (!repoUrl) {
                showMessage('Please enter a repository URL');
                return;
            }

            showLoading(true);

            fetch('/api/repository/tree', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ repo_url: repoUrl, branch, token })
            })
            .then(response => response.json())
            .then(data => {
                showLoading(false);
                if (data.success) {
                    currentRepo = data;
                    document.getElementById('search-section').style.display = 'block';
                    showMessage(`Repository loaded: ${data.owner}/${data.repo} (${data.total_files} files)`, 'success');
                } else {
                    showMessage('Error loading repository: ' + data.error);
                }
            })
            .catch(error => {
                showLoading(false);
                showMessage('Network error: ' + error.message);
            });
        }

        function searchFiles() {
            if (!currentRepo) {
                showMessage('Please load a repository first');
                return;
            }

            const searchCriteria = {
                name_patterns: document.getElementById('name-patterns').value.split(',').map(s => s.trim()).filter(s => s),
                extensions: document.getElementById('extensions').value.split(',').map(s => s.trim()).filter(s => s),
                path_patterns: document.getElementById('path-patterns').value.split(',').map(s => s.trim()).filter(s => s),
                exclude_patterns: document.getElementById('exclude-patterns').value.split(',').map(s => s.trim()).filter(s => s)
            };

            showLoading(true);

            fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    repo_url: document.getElementById('repo-url').value.trim(),
                    branch: document.getElementById('branch').value.trim(),
                    token: document.getElementById('token').value.trim(),
                    search_criteria: searchCriteria,
                    profile: selectedProfile
                })
            })
            .then(response => response.json())
            .then(data => {
                showLoading(false);
                if (data.success) {
                    searchResults = data.matches;
                    displayResults(data);
                } else {
                    showMessage('Search error: ' + data.error);
                }
            })
            .catch(error => {
                showLoading(false);
                showMessage('Network error: ' + error.message);
            });
        }

        function displayResults(data) {
            const resultsSection = document.getElementById('results-section');
            const summary = document.getElementById('results-summary');
            const resultsList = document.getElementById('results-list');

            resultsSection.style.display = 'block';

            // Summary
            const totalSizeMB = (data.total_size / (1024 * 1024)).toFixed(2);
            summary.innerHTML = `
                <p><strong>${data.total_files}</strong> files found (${totalSizeMB} MB total)</p>
                <p>Profile used: <strong>${data.profile_used}</strong></p>
            `;

            // Results list
            resultsList.innerHTML = '';
            data.matches.forEach((file, index) => {
                const div = document.createElement('div');
                div.className = 'file-item';
                div.innerHTML = `
                    <div class="file-info">
                        <div class="file-path">${file.path}</div>
                        <div class="file-meta">${formatFileSize(file.size)} • ${file.extension || 'no ext'}</div>
                    </div>
                    <input type="checkbox" id="file-${index}" data-index="${index}">
                `;
                resultsList.appendChild(div);
            });

            document.getElementById('download-section').style.display = 'block';
        }

        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        function selectAll() {
            document.querySelectorAll('#results-list input[type="checkbox"]').forEach(cb => cb.checked = true);
        }

        function selectNone() {
            document.querySelectorAll('#results-list input[type="checkbox"]').forEach(cb => cb.checked = false);
        }

        function downloadSelected() {
            const selected = [];
            document.querySelectorAll('#results-list input[type="checkbox"]:checked').forEach(cb => {
                const index = parseInt(cb.dataset.index);
                selected.push(searchResults[index]);
            });

            if (selected.length === 0) {
                showMessage('Please select files to download');
                return;
            }

            showLoading(true);

            fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    files: selected,
                    repo_info: currentRepo,
                    token: document.getElementById('token').value.trim()
                })
            })
            .then(response => response.json())
            .then(data => {
                showLoading(false);
                if (data.success) {
                    // Create download link
                    const a = document.createElement('a');
                    a.href = data.download_url;
                    a.download = data.filename;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    
                    showMessage(`Download started: ${data.filename}`, 'success');
                } else {
                    showMessage('Download error: ' + data.error);
                }
            })
            .catch(error => {
                showLoading(false);
                showMessage('Network error: ' + error.message);
            });
        }

        function clearSearch() {
            document.getElementById('extensions').value = '';
            document.getElementById('name-patterns').value = '';
            document.getElementById('path-patterns').value = '';
            document.getElementById('exclude-patterns').value = '';
            document.querySelectorAll('.profile-btn').forEach(btn => btn.classList.remove('active'));
            selectedProfile = null;
        }
    </script>
</body>
</html>'''
    
    with open(os.path.join(templates_dir, 'index.html'), 'w') as f:
        f.write(html_content)

def main():
    """Run the web interface."""
    create_templates()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting GitHub File Hunter Web Interface...")
    print(f"📱 Access at: http://localhost:{port}")
    print(f"🔧 Debug mode: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == "__main__":
    main()