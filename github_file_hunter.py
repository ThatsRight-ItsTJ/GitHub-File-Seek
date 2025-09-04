#!/usr/bin/env python3
"""
GitHub File Hunter

A powerful tool that combines repository exploration with selective file downloading.
Find and download specific files from GitHub repositories using patterns, extensions,
or custom filters without cloning the entire repository.

Features:
- Search files by name patterns, extensions, or regex
- Filter by directory paths
- Bulk download matching files
- Preview before download
- Maintain directory structure
- Rate limiting and error handling
"""

import asyncio
import aiohttp
import aiofiles
import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Callable, Set
from urllib.parse import urlparse
import fnmatch

@dataclass
class FileMatch:
    """Represents a file that matches search criteria."""
    path: str
    size: int
    download_url: str
    sha: str
    type: str = "blob"
    
    @property
    def filename(self) -> str:
        return os.path.basename(self.path)
    
    @property
    def directory(self) -> str:
        return os.path.dirname(self.path)
    
    @property
    def extension(self) -> str:
        return os.path.splitext(self.path)[1].lower()

@dataclass 
class SearchCriteria:
    """Search criteria for finding files."""
    name_patterns: List[str] = field(default_factory=list)
    extensions: List[str] = field(default_factory=list)
    path_patterns: List[str] = field(default_factory=list)
    exclude_patterns: List[str] = field(default_factory=list)
    min_size: int = 0
    max_size: int = float('inf')
    regex_pattern: Optional[str] = None
    case_sensitive: bool = False

class GitHubFileHunter:
    """Main class for GitHub file hunting and downloading."""
    
    def __init__(self, github_token: str = None, max_concurrent: int = 5):
        self.github_token = github_token
        self.max_concurrent = max_concurrent
        self.session = None
        self.downloaded_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        
    async def __aenter__(self):
        headers = {
            'User-Agent': 'GitHub-File-Hunter/1.0',
            'Accept': 'application/vnd.github.v3+json'
        }
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        self.session = aiohttp.ClientSession(
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def parse_github_url(self, url: str) -> tuple:
        """Parse GitHub URL to extract owner, repo, and branch."""
        if url.startswith('https://github.com/'):
            url = url.replace('https://github.com/', '')
        
        parts = url.strip('/').split('/')
        
        if len(parts) >= 2:
            owner, repo = parts[0], parts[1]
            repo = repo.replace('.git', '')  # Remove .git suffix
            
            # Extract branch if present
            branch = 'main'
            if len(parts) > 2 and parts[2] == 'tree':
                branch = parts[3] if len(parts) > 3 else 'main'
            
            return owner, repo, branch
        else:
            raise ValueError("Invalid GitHub URL format")

    async def get_repository_tree(self, owner: str, repo: str, branch: str = None) -> Dict:
        """Get complete repository tree using GitHub API."""
        if not branch:
            branch = await self.get_default_branch(owner, repo)
        
        # Get branch SHA
        ref_url = f"https://api.github.com/repos/{owner}/{repo}/git/refs/heads/{branch}"
        async with self.session.get(ref_url) as response:
            if response.status != 200:
                raise Exception(f"Could not find branch '{branch}'. Status: {response.status}")
            ref_data = await response.json()
            branch_sha = ref_data['object']['sha']
        
        # Get recursive tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch_sha}?recursive=1"
        async with self.session.get(tree_url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch tree. Status: {response.status}")

    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch of the repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}"
        async with self.session.get(url) as response:
            if response.status == 200:
                repo_info = await response.json()
                return repo_info.get('default_branch', 'main')
            else:
                return 'main'

    def search_files(self, tree_data: Dict, criteria: SearchCriteria, owner: str, repo: str, branch: str) -> List[FileMatch]:
        """Search for files matching the given criteria."""
        matches = []
        
        for item in tree_data.get('tree', []):
            if item['type'] != 'blob':  # Only process files, not directories
                continue
            
            file_path = item['path']
            file_size = item.get('size', 0)
            
            # Check if file matches criteria
            if self._matches_criteria(file_path, file_size, criteria):
                download_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
                
                match = FileMatch(
                    path=file_path,
                    size=file_size,
                    download_url=download_url,
                    sha=item['sha']
                )
                matches.append(match)
        
        return matches

    def _matches_criteria(self, file_path: str, file_size: int, criteria: SearchCriteria) -> bool:
        """Check if a file matches the search criteria."""
        filename = os.path.basename(file_path)
        file_ext = os.path.splitext(filename)[1].lower()
        
        # Size filter
        if file_size < criteria.min_size or file_size > criteria.max_size:
            return False
        
        # Exclude patterns
        for exclude_pattern in criteria.exclude_patterns:
            if self._matches_pattern(file_path, exclude_pattern, criteria.case_sensitive):
                return False
        
        # Name patterns
        if criteria.name_patterns:
            name_match = any(
                self._matches_pattern(filename, pattern, criteria.case_sensitive)
                for pattern in criteria.name_patterns
            )
            if not name_match:
                return False
        
        # Extension filter
        if criteria.extensions:
            ext_match = any(
                file_ext == ext.lower() if not criteria.case_sensitive else file_ext == ext
                for ext in criteria.extensions
            )
            if not ext_match:
                return False
        
        # Path patterns
        if criteria.path_patterns:
            path_match = any(
                self._matches_pattern(file_path, pattern, criteria.case_sensitive)
                for pattern in criteria.path_patterns
            )
            if not path_match:
                return False
        
        # Regex pattern
        if criteria.regex_pattern:
            flags = 0 if criteria.case_sensitive else re.IGNORECASE
            if not re.search(criteria.regex_pattern, file_path, flags):
                return False
        
        return True

    def _matches_pattern(self, text: str, pattern: str, case_sensitive: bool) -> bool:
        """Check if text matches a glob pattern."""
        if not case_sensitive:
            text = text.lower()
            pattern = pattern.lower()
        
        return fnmatch.fnmatch(text, pattern)

    async def download_file(self, file_match: FileMatch, base_output_dir: str = ".") -> bool:
        """Download a single file."""
        try:
            # Create directory structure
            full_output_path = os.path.join(base_output_dir, file_match.path)
            output_dir = os.path.dirname(full_output_path)
            
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            print(f"📥 Downloading: {file_match.path}")
            print(f"   Size: {self._format_size(file_match.size)}")
            
            async with self.session.get(file_match.download_url) as response:
                if response.status == 200:
                    content = await response.read()
                    
                    async with aiofiles.open(full_output_path, 'wb') as f:
                        await f.write(content)
                    
                    self.downloaded_count += 1
                    print(f"✅ Success: {file_match.path}")
                    return True
                else:
                    print(f"❌ HTTP {response.status}: {file_match.path}")
                    self.failed_count += 1
                    return False
        
        except Exception as e:
            print(f"❌ Error downloading {file_match.path}: {str(e)}")
            self.failed_count += 1
            return False

    async def download_files(self, matches: List[FileMatch], output_dir: str = ".") -> None:
        """Download multiple files with concurrency control."""
        if not matches:
            print("No files to download.")
            return
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def download_with_semaphore(file_match):
            async with semaphore:
                return await self.download_file(file_match, output_dir)
        
        print(f"🚀 Starting download of {len(matches)} files to '{output_dir}'...\n")
        
        tasks = [download_with_semaphore(match) for match in matches]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        print(f"\n📊 Download Summary:")
        print(f"   ✅ Successful: {self.downloaded_count}")
        print(f"   ❌ Failed: {self.failed_count}")
        print(f"   📁 Total: {len(matches)}")

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f}KB"
        else:
            return f"{size_bytes / (1024 * 1024):.1f}MB"

    def display_matches(self, matches: List[FileMatch], show_details: bool = False) -> None:
        """Display found matches in a formatted way."""
        if not matches:
            print("❌ No files found matching criteria.")
            return
        
        print(f"🔍 Found {len(matches)} matching files:\n")
        
        # Group by directory for better organization
        by_directory = {}
        for match in matches:
            dir_name = match.directory or "."
            if dir_name not in by_directory:
                by_directory[dir_name] = []
            by_directory[dir_name].append(match)
        
        total_size = 0
        for dir_name in sorted(by_directory.keys()):
            print(f"📁 {dir_name}/")
            
            for match in sorted(by_directory[dir_name], key=lambda x: x.filename):
                size_str = self._format_size(match.size)
                total_size += match.size
                
                if show_details:
                    print(f"   📄 {match.filename} ({size_str}) - {match.extension}")
                    if show_details:
                        print(f"      SHA: {match.sha[:8]}...")
                        print(f"      URL: {match.download_url}")
                else:
                    print(f"   📄 {match.filename} ({size_str})")
            print()
        
        print(f"📊 Total: {len(matches)} files, {self._format_size(total_size)}")

    def export_matches(self, matches: List[FileMatch], filename: str, format: str = "json") -> None:
        """Export matches to a file."""
        if format.lower() == "json":
            data = [
                {
                    "path": match.path,
                    "filename": match.filename,
                    "directory": match.directory,
                    "size": match.size,
                    "extension": match.extension,
                    "download_url": match.download_url,
                    "sha": match.sha
                }
                for match in matches
            ]
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
        
        elif format.lower() == "csv":
            import csv
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['path', 'filename', 'directory', 'size', 'extension', 'download_url', 'sha'])
                for match in matches:
                    writer.writerow([
                        match.path, match.filename, match.directory,
                        match.size, match.extension, match.download_url, match.sha
                    ])
        
        elif format.lower() == "txt":
            with open(filename, 'w') as f:
                for match in matches:
                    f.write(f"{match.path}\n")
        
        print(f"📝 Exported {len(matches)} matches to {filename}")

def create_search_criteria_from_args(args) -> SearchCriteria:
    """Create SearchCriteria object from command line arguments."""
    criteria = SearchCriteria()
    
    if args.name:
        criteria.name_patterns = args.name
    
    if args.ext:
        criteria.extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in args.ext]
    
    if args.path:
        criteria.path_patterns = args.path
    
    if args.exclude:
        criteria.exclude_patterns = args.exclude
    
    if args.min_size:
        criteria.min_size = args.min_size
    
    if args.max_size:
        criteria.max_size = args.max_size
    
    if args.regex:
        criteria.regex_pattern = args.regex
    
    criteria.case_sensitive = args.case_sensitive
    
    return criteria

async def main():
    parser = argparse.ArgumentParser(
        description='GitHub File Hunter - Find and download specific files from GitHub repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find all Python files
  python github_file_hunter.py owner/repo --ext py

  # Find specific config files
  python github_file_hunter.py https://github.com/owner/repo --name "*.yml" "config.*"

  # Find files in specific directories
  python github_file_hunter.py owner/repo --path "src/*" "tests/*" --ext py js

  # Find large files
  python github_file_hunter.py owner/repo --min-size 1000000

  # Preview without downloading
  python github_file_hunter.py owner/repo --ext py --preview-only

  # Download with custom output directory
  python github_file_hunter.py owner/repo --ext py --download --output-dir ./downloaded_files
        """
    )
    
    # Required arguments
    parser.add_argument('repo', help='GitHub repository (owner/repo or full URL)')
    
    # Search criteria
    parser.add_argument('--name', '-n', nargs='+', help='File name patterns (supports wildcards)')
    parser.add_argument('--ext', '-e', nargs='+', help='File extensions (e.g., py js md)')
    parser.add_argument('--path', '-p', nargs='+', help='Path patterns (supports wildcards)')
    parser.add_argument('--exclude', '-x', nargs='+', help='Exclude patterns')
    parser.add_argument('--regex', '-r', help='Regex pattern to match file paths')
    parser.add_argument('--min-size', type=int, help='Minimum file size in bytes')
    parser.add_argument('--max-size', type=int, help='Maximum file size in bytes')
    parser.add_argument('--case-sensitive', action='store_true', help='Case-sensitive matching')
    
    # Repository options
    parser.add_argument('--branch', '-b', help='Repository branch (default: repo default)')
    parser.add_argument('--token', '-t', help='GitHub personal access token',
                       default=os.getenv('GITHUB_TOKEN'))
    
    # Action options
    parser.add_argument('--preview-only', action='store_true', help='Only show matches, don\'t download')
    parser.add_argument('--download', '-d', action='store_true', help='Download matching files')
    parser.add_argument('--output-dir', '-o', default='.', help='Output directory for downloads')
    
    # Display options
    parser.add_argument('--details', action='store_true', help='Show detailed file information')
    parser.add_argument('--export', help='Export matches to file (JSON/CSV/TXT)')
    parser.add_argument('--export-format', choices=['json', 'csv', 'txt'], default='json',
                       help='Export file format')
    
    # Performance options
    parser.add_argument('--concurrent', '-c', type=int, default=5,
                       help='Maximum concurrent downloads')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not any([args.name, args.ext, args.path, args.regex]):
        print("❌ Error: Must specify at least one search criteria (--name, --ext, --path, or --regex)")
        return 1
    
    try:
        async with GitHubFileHunter(args.token, args.concurrent) as hunter:
            # Parse repository URL
            owner, repo, branch = hunter.parse_github_url(args.repo)
            if args.branch:
                branch = args.branch
            
            print(f"🔍 Searching {owner}/{repo} (branch: {branch})")
            if args.token:
                print("🔑 Using GitHub token")
            else:
                print("⚠️  No token - may hit rate limits")
            print()
            
            # Get repository tree
            print("📡 Fetching repository structure...")
            tree_data = await hunter.get_repository_tree(owner, repo, branch)
            total_files = len([item for item in tree_data.get('tree', []) if item['type'] == 'blob'])
            print(f"📊 Repository contains {total_files} files")
            
            # Create search criteria and find matches
            criteria = create_search_criteria_from_args(args)
            matches = hunter.search_files(tree_data, criteria, owner, repo, branch)
            
            # Display results
            hunter.display_matches(matches, args.details)
            
            # Export if requested
            if args.export:
                hunter.export_matches(matches, args.export, args.export_format)
            
            # Download if requested
            if args.download and matches and not args.preview_only:
                print()
                confirm = input(f"Download {len(matches)} files to '{args.output_dir}'? (y/N): ")
                if confirm.lower() in ['y', 'yes']:
                    await hunter.download_files(matches, args.output_dir)
                else:
                    print("Download cancelled.")
            elif args.preview_only:
                print("👁️  Preview mode - no files downloaded")
            elif not matches:
                print("💡 No files found. Try adjusting your search criteria.")
            elif not args.download:
                print("💡 Use --download to download these files")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))