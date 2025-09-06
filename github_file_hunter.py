#!/usr/bin/env python3
"""
GitHub File Hunter - Smart file discovery and download tool

Intelligently finds and downloads specific files from GitHub repositories
without cloning the entire repository. Supports individual files, patterns,
batch operations, and repository structure analysis.
"""

import asyncio
import aiohttp
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urlparse
import argparse
import sys

@dataclass
class SearchCriteria:
    """Criteria for searching files in repositories."""
    name_patterns: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    path_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    regex_pattern: Optional[str] = None
    specific_files: List[str] = field(default_factory=list)  # New: for individual file downloads

@dataclass
class FileMatch:
    """Represents a matched file."""
    path: str
    size: int
    download_url: str
    sha: str
    repo_owner: str
    repo_name: str
    branch: str

class GitHubFileHunter:
    """Main class for hunting files in GitHub repositories."""
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.session = None
        self.downloaded_count = 0
        self.failed_count = 0
        self.base_url = "https://api.github.com"
        
    async def __aenter__(self):
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'GitHub-File-Hunter/1.0'
        }
        
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def parse_github_url(self, url: str) -> tuple[str, str, Optional[str]]:
        """Parse GitHub URL to extract owner, repo, and branch."""
        
        # Remove .git suffix if present
        if url.endswith('.git'):
            url = url[:-4]
        
        # Handle different URL formats
        if url.startswith('https://github.com/'):
            path = url.replace('https://github.com/', '')
        elif url.startswith('git@github.com:'):
            path = url.replace('git@github.com:', '')
        else:
            # Assume it's in format "owner/repo"
            path = url
        
        # Split path and handle branch
        parts = path.split('/')
        if len(parts) >= 2:
            owner = parts[0]
            repo = parts[1]
            
            # Check for branch in URL (e.g., owner/repo/tree/branch)
            branch = None
            if len(parts) >= 4 and parts[2] == 'tree':
                branch = '/'.join(parts[3:])  # Support branch names with slashes
            
            return owner, repo, branch
        else:
            raise ValueError(f"Invalid GitHub URL format: {url}")
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get basic repository information."""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        async with self.session.get(url) as response:
            if response.status == 404:
                raise ValueError(f"Repository {owner}/{repo} not found or not accessible")
            elif response.status != 200:
                raise ValueError(f"Failed to access repository: HTTP {response.status}")
            
            return await response.json()
    
    async def get_repository_tree(self, owner: str, repo: str, branch: str = None) -> Dict[str, Any]:
        """Get the complete file tree of a repository."""
        
        # Get repository info to determine default branch if not specified
        if not branch:
            repo_info = await self.get_repository_info(owner, repo)
            branch = repo_info['default_branch']
        
        # Get the tree recursively
        url = f"{self.base_url}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        
        async with self.session.get(url) as response:
            if response.status == 404:
                raise ValueError(f"Branch '{branch}' not found in {owner}/{repo}")
            elif response.status != 200:
                raise ValueError(f"Failed to get repository tree: HTTP {response.status}")
            
            return await response.json()
    
    async def get_specific_file(self, owner: str, repo: str, file_path: str, branch: str = None) -> Optional[FileMatch]:
        """Get information about a specific file."""
        
        if not branch:
            repo_info = await self.get_repository_info(owner, repo)
            branch = repo_info['default_branch']
        
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
        
        async with self.session.get(url) as response:
            if response.status == 404:
                return None
            elif response.status != 200:
                raise ValueError(f"Failed to get file info: HTTP {response.status}")
            
            file_data = await response.json()
            
            # Handle if it's a directory
            if isinstance(file_data, list):
                return None
            
            if file_data.get('type') != 'file':
                return None
            
            return FileMatch(
                path=file_data['path'],
                size=file_data['size'],
                download_url=file_data['download_url'],
                sha=file_data['sha'],
                repo_owner=owner,
                repo_name=repo,
                branch=branch
            )
    
    def search_files(self, tree_data: Dict[str, Any], criteria: SearchCriteria, 
                    owner: str, repo: str, branch: str) -> List[FileMatch]:
        """Search for files matching the given criteria."""
        
        matches = []
        
        for item in tree_data.get('tree', []):
            if item['type'] != 'blob':  # Only process files, not directories
                continue
            
            file_path = item['path']
            file_size = item.get('size', 0)
            
            # Check specific files first (highest priority)
            if criteria.specific_files:
                if any(self._matches_specific_file(file_path, specific) for specific in criteria.specific_files):
                    matches.append(self._create_file_match(item, owner, repo, branch))
                    continue
            
            # Skip if no other criteria specified and specific files were requested
            if criteria.specific_files and not any([
                criteria.name_patterns, criteria.extensions, criteria.path_patterns, criteria.regex_pattern
            ]):
                continue
            
            # Check exclude patterns first
            if criteria.exclude_patterns:
                if any(self._matches_pattern(file_path, pattern) for pattern in criteria.exclude_patterns):
                    continue
            
            # Check file size constraints
            if criteria.min_size is not None and file_size < criteria.min_size:
                continue
            if criteria.max_size is not None and file_size > criteria.max_size:
                continue
            
            # Check name patterns
            if criteria.name_patterns:
                filename = os.path.basename(file_path)
                if not any(self._matches_pattern(filename, pattern) for pattern in criteria.name_patterns):
                    continue
            
            # Check extensions
            if criteria.extensions:
                file_ext = os.path.splitext(file_path)[1].lower()
                if not any(file_ext == ext.lower() for ext in criteria.extensions):
                    continue
            
            # Check path patterns
            if criteria.path_patterns:
                if not any(self._matches_pattern(file_path, pattern) for pattern in criteria.path_patterns):
                    continue
            
            # Check regex pattern
            if criteria.regex_pattern:
                if not re.search(criteria.regex_pattern, file_path, re.IGNORECASE):
                    continue
            
            # If we get here, the file matches all criteria
            matches.append(self._create_file_match(item, owner, repo, branch))
        
        return matches
    
    def _matches_specific_file(self, file_path: str, specific_file: str) -> bool:
        """Check if file path matches a specific file pattern."""
        # Exact match
        if file_path == specific_file:
            return True
        
        # Wildcard matching
        if '*' in specific_file or '?' in specific_file:
            return self._matches_pattern(file_path, specific_file)
        
        # Basename matching (for convenience)
        if os.path.basename(file_path) == specific_file:
            return True
        
        return False
    
    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches a glob-style pattern."""
        # Convert glob pattern to regex
        regex_pattern = pattern.replace('*', '.*').replace('?', '.')
        return re.match(f'^{regex_pattern}$', text, re.IGNORECASE) is not None
    
    def _create_file_match(self, item: Dict[str, Any], owner: str, repo: str, branch: str) -> FileMatch:
        """Create a FileMatch object from tree item."""
        download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
        
        return FileMatch(
            path=item['path'],
            size=item.get('size', 0),
            download_url=download_url,
            sha=item['sha'],
            repo_owner=owner,
            repo_name=repo,
            branch=branch
        )
    
    async def download_files(self, matches: List[FileMatch], output_dir: str) -> None:
        """Download all matched files to the specified directory."""
        
        if not matches:
            print("No files to download.")
            return
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"📥 Downloading {len(matches)} files to {output_dir}...")
        
        # Reset counters
        self.downloaded_count = 0
        self.failed_count = 0
        
        # Download files with progress
        semaphore = asyncio.Semaphore(5)  # Limit concurrent downloads
        
        async def download_single_file(match: FileMatch):
            async with semaphore:
                await self._download_file(match, output_dir)
        
        tasks = [download_single_file(match) for match in matches]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n✅ Download complete: {self.downloaded_count} successful, {self.failed_count} failed")
    
    async def _download_file(self, match: FileMatch, output_dir: str) -> None:
        """Download a single file."""
        
        try:
            # Create full output path
            output_path = os.path.join(output_dir, match.path)
            
            # Create directory structure
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download file
            async with self.session.get(match.download_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    with open(output_path, 'wb') as f:
                        f.write(content)
                    
                    self.downloaded_count += 1
                    print(f"✓ {match.path} ({match.size} bytes)")
                else:
                    self.failed_count += 1
                    print(f"✗ {match.path} (HTTP {response.status})")
        
        except Exception as e:
            self.failed_count += 1
            print(f"✗ {match.path} (Error: {e})")

async def download_individual_files(repo_url: str, file_paths: List[str], 
                                  output_dir: str = "./resulting_downloads", 
                                  github_token: str = None,
                                  branch: str = None) -> None:
    """Download specific individual files from a repository."""
    
    async with GitHubFileHunter(github_token) as hunter:
        # Parse repository URL
        owner, repo, detected_branch = hunter.parse_github_url(repo_url)
        search_branch = branch or detected_branch
        
        print(f"🎯 Downloading {len(file_paths)} specific files from {owner}/{repo}")
        if search_branch:
            print(f"📋 Branch: {search_branch}")
        
        matches = []
        
        # Get each specific file
        for file_path in file_paths:
            print(f"🔍 Looking for: {file_path}")
            
            try:
                file_match = await hunter.get_specific_file(owner, repo, file_path, search_branch)
                if file_match:
                    matches.append(file_match)
                    print(f"✅ Found: {file_path}")
                else:
                    print(f"❌ Not found: {file_path}")
            except Exception as e:
                print(f"❌ Error getting {file_path}: {e}")
        
        # Download found files
        if matches:
            await hunter.download_files(matches, output_dir)
        else:
            print("❌ No files found to download")

async def analyze_repository_structure(repo_url: str, branch: str = None, 
                                     github_token: str = None, 
                                     output_dir: str = "./resulting_downloads") -> Dict[str, Any]:
    """Analyze repository structure and return file mapping."""
    
    from repo_structure_analyzer import RepoStructureAnalyzer
    
    analyzer = RepoStructureAnalyzer(github_token)
    analysis = await analyzer.analyze_repository(repo_url, branch)
    
    # Save analysis to file
    os.makedirs(output_dir, exist_ok=True)
    repo_name = repo_url.replace('https://github.com/', '').replace('/', '_')
    output_file = os.path.join(output_dir, f"{repo_name}_structure.json")
    
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"📊 Structure analysis saved to: {output_file}")
    
    return analysis

async def main():
    parser = argparse.ArgumentParser(
        description='GitHub File Hunter - Smart file discovery and download',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download specific files
  python github_file_hunter.py microsoft/vscode README.md package.json

  # Search by patterns
  python github_file_hunter.py fastapi/fastapi --extensions .py --name-patterns "*api*"

  # Search with path patterns
  python github_file_hunter.py django/django --path-patterns "django/core/*" --extensions .py

  # Download from specific branch
  python github_file_hunter.py owner/repo file.txt --branch develop

  # Use regex pattern
  python github_file_hunter.py owner/repo --regex ".*\\.(js|ts)$"
  
  # Analyze repository structure only
  python github_file_hunter.py microsoft/vscode --structure-only
        """
    )
    
    parser.add_argument('repo_url', help='GitHub repository URL or owner/repo')
    parser.add_argument('files', nargs='*', help='Specific files to download (optional)')
    
    parser.add_argument('--extensions', '-e', nargs='+', 
                       help='File extensions to search for (e.g., .py .js)')
    parser.add_argument('--name-patterns', '-n', nargs='+',
                       help='Filename patterns to match (e.g., "*test*" "config*")')
    parser.add_argument('--path-patterns', '-p', nargs='+',
                       help='Path patterns to match (e.g., "src/*" "docs/*")')
    parser.add_argument('--exclude-patterns', '-x', nargs='+',
                       help='Patterns to exclude (e.g., "node_modules/*" "*.min.js")')
    parser.add_argument('--regex', '-r', 
                       help='Regular expression pattern for file paths')
    parser.add_argument('--min-size', type=int,
                       help='Minimum file size in bytes')
    parser.add_argument('--max-size', type=int,
                       help='Maximum file size in bytes')
    
    parser.add_argument('--branch', '-b', 
                       help='Specific branch to search (default: repository default)')
    parser.add_argument('--output-dir', '-o', default='./resulting_downloads',
                       help='Output directory for downloads')
    parser.add_argument('--token', '-t', 
                       help='GitHub personal access token',
                       default=os.getenv('GITHUB_TOKEN'))
    
    parser.add_argument('--list-only', '-l', action='store_true',
                       help='List matching files without downloading')
    parser.add_argument('--structure-only', '-s', action='store_true',
                       help='Only analyze repository structure without downloading files')
    
    args = parser.parse_args()
    
    try:
        # If structure-only mode, analyze repository structure
        if args.structure_only:
            analysis = await analyze_repository_structure(
                repo_url=args.repo_url,
                branch=args.branch,
                github_token=args.token,
                output_dir=args.output_dir
            )
            
            # Print summary
            summary = analysis['summary']
            print(f"\n📊 Repository Structure Summary:")
            print(f"   📁 Total files: {summary['total_files']}")
            print(f"   📂 Total directories: {summary['total_directories']}")
            print(f"   💾 Total size: {summary['total_size_mb']} MB")
            print(f"   📈 Average file size: {summary['average_file_size']} bytes")
            
            print(f"\n🏆 Top file types:")
            for ext, count in list(analysis['file_types'].items())[:5]:
                print(f"   {ext}: {count} files")
            
            return 0
        
        # If specific files are provided, download them individually
        if args.files:
            await download_individual_files(
                repo_url=args.repo_url,
                file_paths=args.files,
                output_dir=args.output_dir,
                github_token=args.token,
                branch=args.branch
            )
            return 0
        
        # Otherwise, search by patterns
        async with GitHubFileHunter(args.token) as hunter:
            # Parse repository URL
            owner, repo, detected_branch = hunter.parse_github_url(args.repo_url)
            search_branch = args.branch or detected_branch
            
            print(f"🔍 Searching repository: {owner}/{repo}")
            if search_branch:
                print(f"📋 Branch: {search_branch}")
            
            # Create search criteria
            criteria = SearchCriteria()
            
            if args.extensions:
                criteria.extensions = args.extensions
            if args.name_patterns:
                criteria.name_patterns = args.name_patterns
            if args.path_patterns:
                criteria.path_patterns = args.path_patterns
            if args.exclude_patterns:
                criteria.exclude_patterns = args.exclude_patterns
            if args.regex:
                criteria.regex_pattern = args.regex
            if args.min_size:
                criteria.min_size = args.min_size
            if args.max_size:
                criteria.max_size = args.max_size
            
            # Check if any search criteria provided
            if not any([criteria.extensions, criteria.name_patterns, criteria.path_patterns, 
                       criteria.regex_pattern, criteria.min_size, criteria.max_size]):
                print("❌ Error: No search criteria provided. Use --help for examples.")
                return 1
            
            # Get repository tree
            tree_data = await hunter.get_repository_tree(owner, repo, search_branch)
            
            # Search for matches
            matches = hunter.search_files(tree_data, criteria, owner, repo, search_branch)
            
            if not matches:
                print("❌ No files found matching the criteria.")
                return 1
            
            print(f"\n📄 Found {len(matches)} matching files:")
            for match in matches:
                size_str = f"({match.size} bytes)" if match.size else ""
                print(f"  📄 {match.path} {size_str}")
            
            if args.list_only:
                print(f"\n📋 Listed {len(matches)} files (use without --list-only to download)")
                return 0
            
            # Download files
            await hunter.download_files(matches, args.output_dir)
            return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))