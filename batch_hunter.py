#!/usr/bin/env python3
"""
GitHub File Hunter - Batch Mode

Process multiple repositories and file patterns from configuration files.
Supports CSV, JSON input formats for bulk operations.
"""

import asyncio
import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any
import argparse
from github_file_hunter import GitHubFileHunter, SearchCriteria, FileMatch

class BatchHunter:
    """Batch processing for multiple repositories."""
    
    def __init__(self, github_token: str = None, max_concurrent: int = 3):
        self.github_token = github_token
        self.max_concurrent = max_concurrent
        self.results = []
        
    async def process_batch_file(self, batch_file: str, output_dir: str = "./batch_downloads") -> None:
        """Process a batch configuration file."""
        
        if batch_file.endswith('.json'):
            batch_config = self._load_json_batch(batch_file)
        elif batch_file.endswith('.csv'):
            batch_config = self._load_csv_batch(batch_file)
        else:
            raise ValueError("Batch file must be JSON or CSV format")
        
        print(f"🚀 Processing {len(batch_config)} repositories...")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Process repositories with concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def process_repo_with_semaphore(repo_config):
            async with semaphore:
                return await self._process_single_repo(repo_config, output_dir)
        
        tasks = [process_repo_with_semaphore(config) for config in batch_config]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Compile results
        self._compile_batch_results(results, output_dir)
        
    def _load_json_batch(self, file_path: str) -> List[Dict]:
        """Load batch configuration from JSON file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Support both single config and array of configs
        if isinstance(data, dict):
            return [data]
        return data
    
    def _load_csv_batch(self, file_path: str) -> List[Dict]:
        """Load batch configuration from CSV file."""
        configs = []
        
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                config = {
                    'repo_url': row['repo_url'],
                    'search_criteria': {}
                }
                
                # Parse search criteria from CSV columns
                if 'extensions' in row and row['extensions']:
                    config['search_criteria']['extensions'] = row['extensions'].split(',')
                
                if 'name_patterns' in row and row['name_patterns']:
                    config['search_criteria']['name_patterns'] = row['name_patterns'].split(',')
                
                if 'path_patterns' in row and row['path_patterns']:
                    config['search_criteria']['path_patterns'] = row['path_patterns'].split(',')
                
                if 'exclude_patterns' in row and row['exclude_patterns']:
                    config['search_criteria']['exclude_patterns'] = row['exclude_patterns'].split(',')
                
                if 'min_size' in row and row['min_size']:
                    config['search_criteria']['min_size'] = int(row['min_size'])
                
                if 'max_size' in row and row['max_size']:
                    config['search_criteria']['max_size'] = int(row['max_size'])
                
                if 'regex_pattern' in row and row['regex_pattern']:
                    config['search_criteria']['regex_pattern'] = row['regex_pattern']
                
                # Optional fields
                config['branch'] = row.get('branch', None)
                config['output_subdir'] = row.get('output_subdir', None)
                
                configs.append(config)
        
        return configs
    
    async def _process_single_repo(self, repo_config: Dict, base_output_dir: str) -> Dict:
        """Process a single repository configuration."""
        repo_url = repo_config['repo_url']
        search_criteria_dict = repo_config.get('search_criteria', {})
        branch = repo_config.get('branch', None)
        output_subdir = repo_config.get('output_subdir', None)
        
        print(f"\n🔍 Processing: {repo_url}")
        
        try:
            async with GitHubFileHunter(self.github_token) as hunter:
                # Parse repository URL
                owner, repo, detected_branch = hunter.parse_github_url(repo_url)
                search_branch = branch or detected_branch
                
                # Create search criteria
                criteria = SearchCriteria()
                
                if 'name_patterns' in search_criteria_dict:
                    criteria.name_patterns = search_criteria_dict['name_patterns']
                if 'extensions' in search_criteria_dict:
                    criteria.extensions = search_criteria_dict['extensions']
                if 'path_patterns' in search_criteria_dict:
                    criteria.path_patterns = search_criteria_dict['path_patterns']
                if 'exclude_patterns' in search_criteria_dict:
                    criteria.exclude_patterns = search_criteria_dict['exclude_patterns']
                if 'min_size' in search_criteria_dict:
                    criteria.min_size = search_criteria_dict['min_size']
                if 'max_size' in search_criteria_dict:
                    criteria.max_size = search_criteria_dict['max_size']
                if 'regex_pattern' in search_criteria_dict:
                    criteria.regex_pattern = search_criteria_dict['regex_pattern']
                
                # Get repository tree
                tree_data = await hunter.get_repository_tree(owner, repo, search_branch)
                
                # Search for matches
                matches = hunter.search_files(tree_data, criteria, owner, repo, search_branch)
                
                # Determine output directory
                if output_subdir:
                    repo_output_dir = os.path.join(base_output_dir, output_subdir)
                else:
                    repo_output_dir = os.path.join(base_output_dir, f"{owner}_{repo}")
                
                # Download files
                if matches:
                    await hunter.download_files(matches, repo_output_dir)
                
                result = {
                    'repo_url': repo_url,
                    'owner': owner,
                    'repo': repo,
                    'branch': search_branch,
                    'status': 'success',
                    'files_found': len(matches),
                    'files_downloaded': hunter.downloaded_count,
                    'files_failed': hunter.failed_count,
                    'output_dir': repo_output_dir,
                    'matches': [
                        {
                            'path': match.path,
                            'size': match.size,
                            'download_url': match.download_url
                        }
                        for match in matches
                    ]
                }
                
                print(f"✅ {repo_url}: {len(matches)} files found, {hunter.downloaded_count} downloaded")
                return result
                
        except Exception as e:
            error_result = {
                'repo_url': repo_url,
                'status': 'error',
                'error': str(e),
                'files_found': 0,
                'files_downloaded': 0,
                'files_failed': 0
            }
            print(f"❌ {repo_url}: {str(e)}")
            return error_result
    
    def _compile_batch_results(self, results: List[Dict], output_dir: str) -> None:
        """Compile and save batch processing results."""
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, dict)]
        
        # Calculate summary statistics
        total_repos = len(valid_results)
        successful_repos = len([r for r in valid_results if r['status'] == 'success'])
        total_files_found = sum(r.get('files_found', 0) for r in valid_results)
        total_files_downloaded = sum(r.get('files_downloaded', 0) for r in valid_results)
        total_files_failed = sum(r.get('files_failed', 0) for r in valid_results)
        
        summary = {
            'batch_summary': {
                'total_repositories': total_repos,
                'successful_repositories': successful_repos,
                'failed_repositories': total_repos - successful_repos,
                'total_files_found': total_files_found,
                'total_files_downloaded': total_files_downloaded,
                'total_files_failed': total_files_failed,
                'success_rate': f"{(successful_repos / total_repos * 100):.1f}%" if total_repos > 0 else "0%"
            },
            'repository_results': valid_results
        }
        
        # Save detailed results
        results_file = os.path.join(output_dir, 'batch_results.json')
        with open(results_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Save summary CSV
        summary_file = os.path.join(output_dir, 'batch_summary.csv')
        with open(summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['repo_url', 'status', 'files_found', 'files_downloaded', 'files_failed', 'output_dir'])
            
            for result in valid_results:
                writer.writerow([
                    result.get('repo_url', ''),
                    result.get('status', ''),
                    result.get('files_found', 0),
                    result.get('files_downloaded', 0),
                    result.get('files_failed', 0),
                    result.get('output_dir', '')
                ])
        
        # Print summary
        print(f"\n📊 Batch Processing Summary:")
        print(f"   📁 Total repositories: {total_repos}")
        print(f"   ✅ Successful: {successful_repos}")
        print(f"   ❌ Failed: {total_repos - successful_repos}")
        print(f"   📄 Total files found: {total_files_found}")
        print(f"   📥 Total files downloaded: {total_files_downloaded}")
        print(f"   💾 Results saved to: {output_dir}")

async def main():
    parser = argparse.ArgumentParser(
        description='GitHub File Hunter - Batch processing mode',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process batch from JSON file
  python batch_hunter.py batch_config.json

  # Process batch from CSV file with custom output
  python batch_hunter.py repos.csv --output-dir ./batch_results

  # Generate example batch files
  python batch_hunter.py --generate-examples
        """
    )
    
    parser.add_argument('batch_file', nargs='?', help='Batch configuration file (JSON or CSV)')
    parser.add_argument('--output-dir', '-o', default='./batch_downloads', 
                       help='Output directory for batch downloads')
    parser.add_argument('--token', '-t', help='GitHub personal access token',
                       default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--concurrent', '-c', type=int, default=3,
                       help='Maximum concurrent repository processing')
    parser.add_argument('--generate-examples', action='store_true',
                       help='Generate example batch configuration files')
    
    args = parser.parse_args()
    
    if args.generate_examples:
        generate_example_files()
        return 0
    
    if not args.batch_file:
        print("❌ Error: Batch file required")
        print("💡 Use --generate-examples to create example files")
        return 1
    
    if not os.path.exists(args.batch_file):
        print(f"❌ Error: Batch file '{args.batch_file}' not found")
        return 1
    
    try:
        batch_hunter = BatchHunter(args.token, args.concurrent)
        await batch_hunter.process_batch_file(args.batch_file, args.output_dir)
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

def generate_example_files():
    """Generate example batch configuration files."""
    
    # JSON example
    json_example = [
        {
            "repo_url": "microsoft/vscode",
            "search_criteria": {
                "extensions": [".py", ".js", ".ts"],
                "path_patterns": ["src/*"],
                "exclude_patterns": ["node_modules/*", "test*"]
            },
            "branch": "main",
            "output_subdir": "vscode_source"
        },
        {
            "repo_url": "https://github.com/fastapi/fastapi",
            "search_criteria": {
                "name_patterns": ["*api*", "*route*"],
                "extensions": [".py"]
            },
            "output_subdir": "fastapi_files"
        }
    ]
    
    with open('batch_example.json', 'w') as f:
        json.dump(json_example, f, indent=2)
    
    # CSV example
    csv_example = [
        ['repo_url', 'extensions', 'name_patterns', 'path_patterns', 'exclude_patterns', 'branch', 'output_subdir'],
        ['microsoft/vscode', '.py,.js,.ts', '', 'src/*', 'node_modules/*,test*', 'main', 'vscode_source'],
        ['fastapi/fastapi', '.py', '*api*,*route*', '', '', '', 'fastapi_files'],
        ['django/django', '.py', '*model*,*view*', 'django/*', 'test*', 'main', 'django_core']
    ]
    
    with open('batch_example.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(csv_example)
    
    print("✅ Generated example files:")
    print("   📄 batch_example.json - JSON format example")
    print("   📄 batch_example.csv - CSV format example")
    print("\n💡 Edit these files and run:")
    print("   python batch_hunter.py batch_example.json")
    print("   python batch_hunter.py batch_example.csv")

if __name__ == "__main__":
    exit(asyncio.run(main()))