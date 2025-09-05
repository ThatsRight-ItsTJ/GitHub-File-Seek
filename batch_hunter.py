#!/usr/bin/env python3
"""
Batch GitHub File Hunter - Process multiple repositories efficiently
"""

import asyncio
import json
import csv
import os
import argparse
from typing import List, Dict, Any
from github_file_hunter import GitHubFileHunter, SearchCriteria
from repo_structure_analyzer import RepoStructureAnalyzer

class BatchHunter:
    """Batch processing for multiple repositories."""
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.results = {}
        
    async def process_repositories(self, config: Dict[str, Any], structure_only: bool = False) -> Dict[str, Any]:
        """Process multiple repositories based on configuration."""
        
        repositories = config.get('repositories', [])
        output_dir = config.get('output_dir', './batch_downloads')
        create_repo_folders = config.get('create_repo_folders', True)
        
        print(f"🚀 Processing {len(repositories)} repositories...")
        if structure_only:
            print("📋 Structure analysis mode - no files will be downloaded")
        
        results = {
            'total_repositories': len(repositories),
            'successful': 0,
            'failed': 0,
            'repositories': {}
        }
        
        for repo_config in repositories:
            repo_key = f"{repo_config['owner']}/{repo_config['repo']}"
            
            try:
                if structure_only:
                    # Structure analysis only
                    result = await self._analyze_repository_structure(repo_config)
                else:
                    # Full file hunting and download
                    result = await self._process_single_repository(repo_config, output_dir, create_repo_folders)
                
                results['repositories'][repo_key] = result
                results['successful'] += 1
                
            except Exception as e:
                print(f"❌ {repo_key}: {str(e)}")
                results['repositories'][repo_key] = {
                    'error': str(e),
                    'status': 'failed'
                }
                results['failed'] += 1
        
        return results
    
    async def _analyze_repository_structure(self, repo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze repository structure without downloading files."""
        
        owner = repo_config['owner']
        repo = repo_config['repo']
        branch = repo_config.get('branch')
        
        repo_url = f"https://github.com/{owner}/{repo}"
        
        analyzer = RepoStructureAnalyzer(self.github_token)
        analysis = await analyzer.analyze_repository(repo_url, branch)
        
        print(f"📊 {owner}/{repo}: {analysis['summary']['total_files']} files, {analysis['summary']['total_size_mb']} MB")
        
        return {
            'status': 'success',
            'structure_analysis': analysis,
            'files_found': analysis['summary']['total_files'],
            'total_size_mb': analysis['summary']['total_size_mb']
        }
    
    async def _process_single_repository(self, repo_config: Dict[str, Any], 
                                       base_output_dir: str, create_repo_folders: bool) -> Dict[str, Any]:
        """Process a single repository configuration."""
        
        owner = repo_config['owner']
        repo = repo_config['repo']
        branch = repo_config.get('branch')
        individual_files = repo_config.get('individual_files', [])
        patterns = repo_config.get('patterns', [])
        exclude_patterns = repo_config.get('exclude_patterns', [])
        max_files = repo_config.get('max_files', 100)
        max_size_mb = repo_config.get('max_size_mb', 10)
        
        print(f"🔍 Processing {owner}/{repo}...")
        
        # Determine output directory
        if create_repo_folders:
            output_dir = os.path.join(base_output_dir, f"{owner}_{repo}")
        else:
            output_dir = base_output_dir
        
        async with GitHubFileHunter(self.github_token) as hunter:
            # Get repository tree
            tree_data = await hunter.get_repository_tree(owner, repo, branch)
            
            # Create search criteria
            criteria = SearchCriteria()
            criteria.specific_files = individual_files
            criteria.exclude_patterns = exclude_patterns
            criteria.max_size = max_size_mb * 1024 * 1024 if max_size_mb else None
            
            # Add patterns if provided
            if patterns:
                for pattern in patterns:
                    if pattern.startswith('*.'):
                        # Extension pattern
                        criteria.extensions.append(pattern[1:])
                    elif '/' in pattern:
                        # Path pattern
                        criteria.path_patterns.append(pattern)
                    else:
                        # Name pattern
                        criteria.name_patterns.append(pattern)
            
            # Search for matches
            matches = hunter.search_files(tree_data, criteria, owner, repo, branch or 'main')
            
            # Limit results
            if max_files and len(matches) > max_files:
                matches = matches[:max_files]
                print(f"⚠️  Limited to {max_files} files (from {len(matches)} found)")
            
            if matches:
                # Download files
                await hunter.download_files(matches, output_dir)
                
                downloaded_files = [
                    {
                        'path': match.path,
                        'size': match.size,
                        'download_url': match.download_url
                    }
                    for match in matches
                ]
                
                total_size = sum(match.size for match in matches)
                
                print(f"✅ {owner}/{repo}: {len(matches)} files downloaded ({total_size / 1024 / 1024:.2f} MB)")
                
                return {
                    'status': 'success',
                    'files_downloaded': len(matches),
                    'total_size_bytes': total_size,
                    'total_size_mb': round(total_size / 1024 / 1024, 2),
                    'output_directory': output_dir,
                    'downloaded_files': downloaded_files
                }
            else:
                print(f"⚠️  {owner}/{repo}: No files found matching criteria")
                return {
                    'status': 'no_files',
                    'files_downloaded': 0,
                    'message': 'No files found matching criteria'
                }
    
    def load_config_from_json(self, config_file: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def load_config_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """Load configuration from CSV file."""
        repositories = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                repo_config = {
                    'owner': row['owner'],
                    'repo': row['repo']
                }
                
                # Parse individual files (semicolon separated)
                if row.get('individual_files'):
                    repo_config['individual_files'] = [
                        f.strip() for f in row['individual_files'].split(';') if f.strip()
                    ]
                
                # Parse patterns (semicolon separated)
                if row.get('patterns'):
                    repo_config['patterns'] = [
                        p.strip() for p in row['patterns'].split(';') if p.strip()
                    ]
                
                # Parse other fields
                if row.get('max_files'):
                    repo_config['max_files'] = int(row['max_files'])
                
                if row.get('max_size_mb'):
                    repo_config['max_size_mb'] = float(row['max_size_mb'])
                
                if row.get('branch'):
                    repo_config['branch'] = row['branch']
                
                repositories.append(repo_config)
        
        return {
            'repositories': repositories,
            'output_dir': './batch_downloads',
            'create_repo_folders': True
        }
    
    def save_results(self, results: Dict[str, Any], output_dir: str):
        """Save batch processing results."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save detailed results as JSON
        results_file = os.path.join(output_dir, 'batch_results.json')
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Create summary CSV
        summary_file = os.path.join(output_dir, 'batch_summary.csv')
        with open(summary_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Repository', 'Status', 'Files Downloaded', 'Total Size (MB)', 'Output Directory'
            ])
            
            for repo_key, repo_result in results['repositories'].items():
                if repo_result.get('status') == 'success':
                    writer.writerow([
                        repo_key,
                        repo_result['status'],
                        repo_result.get('files_downloaded', 0),
                        repo_result.get('total_size_mb', 0),
                        repo_result.get('output_directory', 'N/A')
                    ])
                else:
                    writer.writerow([
                        repo_key,
                        repo_result.get('status', 'error'),
                        0,
                        0,
                        repo_result.get('error', 'Unknown error')
                    ])
        
        print(f"\n📊 Results saved:")
        print(f"   📄 Detailed: {results_file}")
        print(f"   📊 Summary: {summary_file}")
    
    def generate_example_configs(self):
        """Generate example configuration files."""
        
        # JSON example
        json_example = {
            "repositories": [
                {
                    "owner": "microsoft",
                    "repo": "vscode",
                    "individual_files": ["README.md", "package.json", "src/main.ts"],
                    "patterns": ["*.py", "*.json"],
                    "exclude_patterns": ["node_modules/*", "*.min.js"],
                    "max_files": 50,
                    "max_size_mb": 10
                },
                {
                    "owner": "facebook",
                    "repo": "react",
                    "individual_files": ["README.md", "LICENSE"],
                    "patterns": ["packages/*/package.json", "scripts/*.js"],
                    "max_files": 25
                }
            ],
            "output_dir": "./batch_downloads",
            "create_repo_folders": True
        }
        
        with open('batch_example.json', 'w') as f:
            json.dump(json_example, f, indent=2)
        
        # CSV example
        csv_example = [
            ['owner', 'repo', 'individual_files', 'patterns', 'max_files', 'max_size_mb'],
            ['microsoft', 'vscode', 'README.md;package.json;src/main.ts', '*.py;*.json', '50', '10'],
            ['facebook', 'react', 'README.md;LICENSE', 'packages/*/package.json;scripts/*.js', '25', '5'],
            ['nodejs', 'node', 'package.json;.gitignore', 'src/*.js;test/*.js', '30', '8']
        ]
        
        with open('batch_example.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(csv_example)
        
        print("📝 Example configuration files generated:")
        print("   📄 batch_example.json")
        print("   📊 batch_example.csv")

async def main():
    parser = argparse.ArgumentParser(description='Batch GitHub File Hunter')
    parser.add_argument('--config', '-c', help='JSON configuration file')
    parser.add_argument('--csv', help='CSV configuration file')
    parser.add_argument('--structure-only', '-s', action='store_true', 
                       help='Only analyze repository structures without downloading files')
    parser.add_argument('--token', '-t', help='GitHub token', default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--output-dir', '-o', default='./batch_downloads', help='Output directory')
    parser.add_argument('--generate-examples', '-g', action='store_true', 
                       help='Generate example configuration files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.generate_examples:
        hunter = BatchHunter()
        hunter.generate_example_configs()
        return
    
    if not args.config and not args.csv:
        print("❌ Error: Please provide either --config or --csv configuration file")
        print("Use --generate-examples to create example configuration files")
        return 1
    
    try:
        hunter = BatchHunter(args.token)
        
        # Load configuration
        if args.config:
            config = hunter.load_config_from_json(args.config)
        else:
            config = hunter.load_config_from_csv(args.csv)
        
        # Override output directory if specified
        if args.output_dir != './batch_downloads':
            config['output_dir'] = args.output_dir
        
        # Process repositories
        results = await hunter.process_repositories(config, args.structure_only)
        
        # Save results
        output_dir = config.get('output_dir', './batch_downloads')
        if args.structure_only:
            output_dir = './structure_analysis'
        
        hunter.save_results(results, output_dir)
        
        # Print summary
        print(f"\n🎉 Batch processing complete!")
        print(f"   ✅ Successful: {results['successful']}")
        print(f"   ❌ Failed: {results['failed']}")
        
        if args.structure_only:
            total_files = sum(
                repo.get('structure_analysis', {}).get('summary', {}).get('total_files', 0)
                for repo in results['repositories'].values()
                if 'structure_analysis' in repo
            )
            print(f"   📊 Total files analyzed: {total_files}")
        else:
            total_downloaded = sum(
                repo.get('files_downloaded', 0) 
                for repo in results['repositories'].values()
            )
            print(f"   📥 Total files downloaded: {total_downloaded}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))