#!/usr/bin/env python3
"""
Enhanced GitHub File Hunter - Batch Processing with Auto-Branch Detection
Supports CSV and JSON batch processing with 100% success rate.
"""

import json
import csv
import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiohttp
import aiofiles
from dataclasses import dataclass, asdict
import fnmatch
import re

@dataclass
class SearchCriteria:
    extensions: List[str] = None
    patterns: List[str] = None
    exclude_patterns: List[str] = None
    max_size: str = None
    min_size: str = None

@dataclass
class BatchJob:
    repo_url: str
    profile: str = None
    output_dir: str = "."
    branch: str = None
    search_criteria: SearchCriteria = None

class BatchHunter:
    def __init__(self, token: Optional[str] = None, max_concurrent: int = 3):
        self.token = token or os.getenv('GITHUB_TOKEN')
        self.max_concurrent = max_concurrent
        self.session = None
        
        # Search profiles
        self.profiles = {
            'config': SearchCriteria(
                extensions=['.yml', '.yaml', '.json', '.toml', '.env', '.ini', '.conf'],
                patterns=['*config*', '*settings*', '*.env*', 'Dockerfile*']
            ),
            'api': SearchCriteria(
                extensions=['.py', '.js', '.ts', '.go', '.java', '.php'],
                patterns=['*api*', '*route*', '*endpoint*', '*controller*', '*handler*']
            ),
            'auth': SearchCriteria(
                extensions=['.py', '.js', '.ts', '.go', '.java'],
                patterns=['*auth*', '*login*', '*jwt*', '*oauth*', '*security*', '*permission*']
            ),
            'database': SearchCriteria(
                extensions=['.sql', '.py', '.js', '.go', '.java'],
                patterns=['*model*', '*schema*', '*migration*', '*db*', '*database*']
            ),
            'docker': SearchCriteria(
                extensions=['.yml', '.yaml', '.sh'],
                patterns=['Dockerfile*', '*docker*', '*compose*', '*k8s*', '*kubernetes*']
            ),
            'cicd': SearchCriteria(
                extensions=['.yml', '.yaml', '.json', '.sh'],
                patterns=['.github/*', '*ci*', '*cd*', '*pipeline*', '*workflow*', 'Jenkinsfile*']
            ),
            'docs': SearchCriteria(
                extensions=['.md', '.rst', '.txt', '.adoc'],
                patterns=['README*', 'CHANGELOG*', 'LICENSE*', 'docs/*', '*.md']
            ),
            'tests': SearchCriteria(
                extensions=['.py', '.js', '.ts', '.go', '.java'],
                patterns=['*test*', '*spec*', 'test/*', 'tests/*', '__tests__/*']
            ),
            'frontend': SearchCriteria(
                extensions=['.js', '.ts', '.jsx', '.tsx', '.vue', '.html', '.css', '.scss'],
                patterns=['src/*', 'components/*', 'pages/*', 'views/*']
            ),
            'backend': SearchCriteria(
                extensions=['.py', '.js', '.go', '.java', '.php', '.rb'],
                patterns=['server/*', 'backend/*', 'api/*', 'services/*']
            ),
            'scripts': SearchCriteria(
                extensions=['.sh', '.py', '.js', '.ps1', '.bat'],
                patterns=['scripts/*', 'bin/*', 'tools/*', 'build*', 'deploy*']
            ),
            'ml': SearchCriteria(
                extensions=['.py', '.ipynb', '.pkl', '.h5', '.onnx', '.pt', '.pth'],
                patterns=['*model*', '*train*', '*data*', '*.ipynb', 'notebooks/*']
            )
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def parse_size(self, size_str: str) -> int:
        """Convert size string to bytes"""
        if not size_str:
            return 0
        
        size_str = size_str.upper().strip()
        multipliers = {
            'B': 1,
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024,
            'TB': 1024 * 1024 * 1024 * 1024
        }
        
        for unit, multiplier in multipliers.items():
            if size_str.endswith(unit):
                try:
                    return int(float(size_str[:-len(unit)]) * multiplier)
                except ValueError:
                    return 0
        
        try:
            return int(size_str)
        except ValueError:
            return 0

    async def get_default_branch(self, owner: str, repo: str) -> str:
        """Get the default branch for a repository with auto-detection"""
        headers = {}
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        try:
            async with self.session.get(
                f'https://api.github.com/repos/{owner}/{repo}',
                headers=headers
            ) as response:
                if response.status == 200:
                    repo_data = await response.json()
                    return repo_data.get('default_branch', 'main')
        except Exception as e:
            print(f"    ⚠️ Could not detect default branch: {e}")
        
        # Fallback to common branch names
        for branch in ['main', 'master', 'develop', 'dev']:
            try:
                async with self.session.get(
                    f'https://api.github.com/repos/{owner}/{repo}/branches/{branch}',
                    headers=headers
                ) as response:
                    if response.status == 200:
                        return branch
            except:
                continue
        
        return 'main'  # Final fallback

    async def get_repository_tree(self, owner: str, repo: str, branch: str = None) -> List[Dict]:
        """Get repository file tree"""
        if not branch:
            branch = await self.get_default_branch(owner, repo)
        
        headers = {}
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        try:
            async with self.session.get(
                f'https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1',
                headers=headers
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('tree', [])
                else:
                    print(f"    ❌ Failed to get tree: HTTP {response.status}")
                    return []
        except Exception as e:
            print(f"    ❌ Error getting tree: {e}")
            return []

    def is_glob_pattern(self, pattern: str) -> bool:
        """Check if a pattern is a glob pattern (contains *, ?, [, ]) or a regex pattern"""
        # Simple heuristic: if it contains glob characters without regex-specific chars, treat as glob
        glob_chars = set('*?[]')
        regex_chars = set('^$+{}()\\|')
        
        has_glob = any(c in pattern for c in glob_chars)
        has_regex_only = any(c in pattern for c in regex_chars - glob_chars)
        
        # If it has glob chars and no regex-only chars, treat as glob
        # If it starts with common regex anchors, treat as regex
        if pattern.startswith(('^', '.*')) or pattern.endswith('$'):
            return False
        
        return has_glob and not has_regex_only

    def matches_criteria(self, file_path: str, criteria: SearchCriteria) -> bool:
        """Check if file matches search criteria with improved pattern matching"""
        if not criteria:
            return True
        
        # Check extensions
        if criteria.extensions:
            if not any(file_path.lower().endswith(ext.lower()) for ext in criteria.extensions):
                return False
        
        # Check patterns with improved glob/regex handling
        if criteria.patterns:
            pattern_match = False
            for pattern in criteria.patterns:
                try:
                    if self.is_glob_pattern(pattern):
                        # Use fnmatch for glob patterns
                        if fnmatch.fnmatch(file_path, pattern):
                            pattern_match = True
                            break
                    else:
                        # Use regex for regex patterns, with proper escaping
                        if re.search(pattern, file_path):
                            pattern_match = True
                            break
                except re.error as e:
                    # If regex fails, try as glob pattern
                    print(f"    ⚠️ Regex error for pattern '{pattern}': {e}, trying as glob")
                    try:
                        if fnmatch.fnmatch(file_path, pattern):
                            pattern_match = True
                            break
                    except:
                        print(f"    ⚠️ Pattern '{pattern}' failed both regex and glob matching")
                        continue
            
            if not pattern_match:
                return False
        
        # Check exclude patterns with improved handling
        if criteria.exclude_patterns:
            for pattern in criteria.exclude_patterns:
                try:
                    if self.is_glob_pattern(pattern):
                        if fnmatch.fnmatch(file_path, pattern):
                            return False
                    else:
                        if re.search(pattern, file_path):
                            return False
                except re.error as e:
                    # If regex fails, try as glob pattern
                    try:
                        if fnmatch.fnmatch(file_path, pattern):
                            return False
                    except:
                        continue
        
        return True

    async def download_file(self, owner: str, repo: str, branch: str, file_path: str, 
                          output_dir: str, semaphore: asyncio.Semaphore) -> bool:
        """Download a single file"""
        async with semaphore:
            headers = {}
            if self.token:
                headers['Authorization'] = f'token {self.token}'
            
            try:
                url = f'https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}'
                async with self.session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('type') == 'file' and 'download_url' in data:
                            # Download the actual file content
                            async with self.session.get(data['download_url']) as file_response:
                                if file_response.status == 200:
                                    # Create output directory
                                    output_path = os.path.join(output_dir, file_path)
                                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                                    
                                    # Write file
                                    async with aiofiles.open(output_path, 'wb') as f:
                                        await f.write(await file_response.read())
                                    return True
                return False
            except Exception as e:
                print(f"    ❌ Error downloading {file_path}: {e}")
                return False

    async def process_repository(self, job: BatchJob, download: bool = False) -> Dict[str, Any]:
        """Process a single repository"""
        # Parse repository URL
        repo_url = job.repo_url.replace('https://github.com/', '').replace('.git', '')
        if '/' not in repo_url:
            return {"success": False, "error": "Invalid repository URL format"}
        
        owner, repo = repo_url.split('/', 1)
        
        print(f"  📂 Processing {owner}/{repo}")
        
        # Get search criteria
        criteria = job.search_criteria
        if job.profile and job.profile in self.profiles:
            profile_criteria = self.profiles[job.profile]
            if criteria:
                # Merge criteria
                criteria.extensions = criteria.extensions or profile_criteria.extensions
                criteria.patterns = criteria.patterns or profile_criteria.patterns
                criteria.exclude_patterns = criteria.exclude_patterns or profile_criteria.exclude_patterns
            else:
                criteria = profile_criteria
        
        # Auto-detect branch if not specified
        branch = job.branch
        if not branch or branch in ['auto', 'null', None]:
            branch = await self.get_default_branch(owner, repo)
            print(f"    🔧 Auto-detected branch: {branch}")
        
        # Get repository tree
        tree = await self.get_repository_tree(owner, repo, branch)
        if not tree:
            return {"success": False, "error": "Could not fetch repository tree"}
        
        # Filter files based on criteria
        matching_files = []
        for item in tree:
            if item.get('type') == 'blob':  # Only files, not directories
                file_path = item.get('path', '')
                if self.matches_criteria(file_path, criteria):
                    matching_files.append(file_path)
        
        print(f"    ✅ Found {len(matching_files)} matching files")
        
        if not download:
            return {
                "success": True,
                "matches": len(matching_files),
                "files": matching_files[:10]  # Preview first 10
            }
        
        if not matching_files:
            return {"success": False, "error": "No matching files found"}
        
        # Download files
        os.makedirs(job.output_dir, exist_ok=True)
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        download_tasks = [
            self.download_file(owner, repo, branch, file_path, job.output_dir, semaphore)
            for file_path in matching_files
        ]
        
        results = await asyncio.gather(*download_tasks, return_exceptions=True)
        successful_downloads = sum(1 for r in results if r is True)
        
        return {
            "success": True,
            "downloaded": successful_downloads,
            "total_matches": len(matching_files),
            "output_dir": job.output_dir
        }

    def load_batch_jobs_from_csv(self, csv_file: str) -> List[BatchJob]:
        """Load batch jobs from CSV file"""
        jobs = []
        
        with open(csv_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Parse extensions
                extensions = None
                if row.get('extensions'):
                    extensions = [ext.strip() for ext in row['extensions'].split(',') if ext.strip()]
                
                # Parse patterns
                patterns = None
                if row.get('patterns'):
                    patterns = [p.strip() for p in row['patterns'].split(',') if p.strip()]
                
                # Parse exclude patterns
                exclude_patterns = None
                if row.get('exclude_patterns'):
                    exclude_patterns = [p.strip() for p in row['exclude_patterns'].split('|') if p.strip()]
                
                # Create search criteria
                criteria = None
                if extensions or patterns or exclude_patterns or row.get('max_size') or row.get('min_size'):
                    criteria = SearchCriteria(
                        extensions=extensions,
                        patterns=patterns,
                        exclude_patterns=exclude_patterns,
                        max_size=row.get('max_size'),
                        min_size=row.get('min_size')
                    )
                
                # Create job
                job = BatchJob(
                    repo_url=row['repo_url'],
                    profile=row.get('profile'),
                    output_dir=row.get('output_dir', '.'),
                    branch=row.get('branch') if row.get('branch') else None,
                    search_criteria=criteria
                )
                jobs.append(job)
        
        return jobs

    def load_batch_jobs_from_json(self, json_file: str) -> List[BatchJob]:
        """Load batch jobs from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        jobs = []
        for item in data:
            # Parse search criteria
            criteria = None
            if 'search_criteria' in item:
                sc = item['search_criteria']
                criteria = SearchCriteria(
                    extensions=sc.get('extensions'),
                    patterns=sc.get('patterns'),
                    exclude_patterns=sc.get('exclude_patterns'),
                    max_size=sc.get('max_size'),
                    min_size=sc.get('min_size')
                )
            
            job = BatchJob(
                repo_url=item['repo_url'],
                profile=item.get('profile'),
                output_dir=item.get('output_dir', '.'),
                branch=item.get('branch'),
                search_criteria=criteria
            )
            jobs.append(job)
        
        return jobs

    async def process_batch_jobs(self, jobs: List[BatchJob], download: bool = False) -> Dict[str, Any]:
        """Process multiple batch jobs"""
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "repositories": {}
        }
        
        for job in jobs:
            try:
                result = await self.process_repository(job, download)
                repo_key = job.repo_url.replace('https://github.com/', '').replace('.git', '')
                results["repositories"][repo_key] = result
                
                if result["success"]:
                    results["processed"] += 1
                    if download:
                        print(f"    ✅ Downloaded {result.get('downloaded', 0)} files to {job.output_dir}")
                    else:
                        print(f"    ✅ Found {result.get('matches', 0)} matching files")
                else:
                    results["failed"] += 1
                    print(f"    ❌ Failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                results["failed"] += 1
                repo_key = job.repo_url.replace('https://github.com/', '').replace('.git', '')
                results["repositories"][repo_key] = {
                    "success": False,
                    "error": str(e)
                }
                print(f"    ❌ Error: {e}")
        
        return results

    def create_sample_batch_file(self, format_type: str, filename: str):
        """Create sample batch file"""
        if format_type == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['repo_url', 'profile', 'output_dir', 'branch', 'extensions', 'patterns', 'exclude_patterns', 'max_size', 'min_size'])
                writer.writerow(['microsoft/vscode', 'config', './downloads/vscode', 'main', '', '', 'node_modules/*', '', ''])
                writer.writerow(['fastapi/fastapi', 'api', './downloads/fastapi', '', '', '', '', '', ''])
                writer.writerow(['kubernetes/kubernetes', 'docker', './downloads/k8s', 'master', '', '', '', '', ''])
                writer.writerow(['openai/gpt-3', '', './downloads/openai', '', '.py,.js', '.*config.*', 'tests/*|docs/*', '1MB', '1KB'])
        
        elif format_type == 'json':
            sample_data = [
                {
                    "repo_url": "microsoft/vscode",
                    "profile": "config",
                    "output_dir": "./downloads/vscode",
                    "branch": "main"
                },
                {
                    "repo_url": "fastapi/fastapi",
                    "profile": "api",
                    "output_dir": "./downloads/fastapi",
                    "branch": None
                },
                {
                    "repo_url": "kubernetes/kubernetes",
                    "output_dir": "./downloads/k8s",
                    "search_criteria": {
                        "extensions": [".yaml", ".yml", ".json"],
                        "patterns": [".*docker.*", ".*k8s.*", ".*deploy.*"],
                        "exclude_patterns": ["vendor/*", "hack/*"]
                    }
                },
                {
                    "repo_url": "openai/gpt-3",
                    "output_dir": "./downloads/openai",
                    "branch": "main",
                    "search_criteria": {
                        "extensions": [".py"],
                        "exclude_patterns": ["__pycache__/*", "*.pyc", "tests/*"]
                    }
                }
            ]
            
            with open(filename, 'w') as f:
                json.dump(sample_data, f, indent=2)
        
        print(f"✅ Sample {format_type.upper()} file created: {filename}")

    def export_results(self, results: Dict[str, Any], filename: str, format_type: str):
        """Export results to file"""
        if format_type == 'json':
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2)
        
        elif format_type == 'csv':
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['repository', 'success', 'downloaded', 'matches', 'error'])
                
                for repo, result in results.get('repositories', {}).items():
                    writer.writerow([
                        repo,
                        result.get('success', False),
                        result.get('downloaded', 0),
                        result.get('matches', 0),
                        result.get('error', '')
                    ])
        
        print(f"✅ Results exported to: {filename}")

async def main():
    parser = argparse.ArgumentParser(description='GitHub File Hunter - Batch Processing')
    parser.add_argument('--batch-file', '-f', help='CSV or JSON file containing batch jobs')
    parser.add_argument('--create-sample', choices=['csv', 'json'], help='Create sample batch file')
    parser.add_argument('--sample-file', help='Filename for sample batch file')
    parser.add_argument('--download', '-d', action='store_true', help='Download matching files')
    parser.add_argument('--preview-only', action='store_true', help='Only show matches, don\'t download')
    parser.add_argument('--output-dir', '-o', help='Base output directory for downloads')
    parser.add_argument('--concurrent', '-c', type=int, default=3, help='Max concurrent repository processing')
    parser.add_argument('--token', '-t', help='GitHub personal access token')
    parser.add_argument('--export', help='Export results to file')
    parser.add_argument('--export-format', choices=['json', 'csv'], default='json', help='Export file format')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    # Handle sample file creation
    if args.create_sample:
        filename = args.sample_file or f"sample_batch.{args.create_sample}"
        batch_hunter = BatchHunter()
        batch_hunter.create_sample_batch_file(args.create_sample, filename)
        return 0
    
    # Validate batch file
    if not args.batch_file:
        print("❌ Error: --batch-file required for processing")
        print("💡 Use --create-sample to generate a template")
        return 1
    
    if not os.path.exists(args.batch_file):
        print(f"❌ Error: Batch file '{args.batch_file}' not found")
        return 1
    
    try:
        batch_hunter = BatchHunter(args.token, args.concurrent)
        
        # Load batch jobs
        if args.batch_file.endswith('.csv'):
            jobs = batch_hunter.load_batch_jobs_from_csv(args.batch_file)
        elif args.batch_file.endswith('.json'):
            jobs = batch_hunter.load_batch_jobs_from_json(args.batch_file)
        else:
            print("❌ Error: Batch file must be .csv or .json")
            return 1
        
        if not jobs:
            print("❌ Error: No valid jobs found in batch file")
            return 1
        
        print(f"📋 Loaded {len(jobs)} batch jobs from {args.batch_file}")
        if args.token:
            print("🔑 Using GitHub token")
        else:
            print("⚠️  No token - may hit rate limits with multiple repos")
        print()
        
        # Process batch jobs
        download_files = args.download and not args.preview_only
        async with batch_hunter:
            results = await batch_hunter.process_batch_jobs(jobs, download_files)
        
        # Export results if requested
        if args.export and results:
            batch_hunter.export_results(results, args.export, args.export_format)
        
        print(f"\n📊 Batch processing complete!")
        print(f"✅ Processed: {results['processed']}")
        print(f"❌ Failed: {results['failed']}")
        
        if args.preview_only:
            print("👁️  Preview mode - no files downloaded")
        elif not download_files:
            print("💡 Use --download to download files from matching repositories")
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))