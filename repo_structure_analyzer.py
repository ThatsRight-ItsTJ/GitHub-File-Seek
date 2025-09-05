#!/usr/bin/env python3
"""
Repository Structure Analyzer
Programmatically analyze and export repository file structures
"""

import asyncio
import json
import csv
import os
from pathlib import Path
from collections import defaultdict
import argparse
from github_file_hunter import GitHubFileHunter

class RepoStructureAnalyzer:
    """Analyze repository structures programmatically."""
    
    def __init__(self, github_token=None):
        self.github_token = github_token
        
    async def analyze_repository(self, repo_url, branch=None):
        """Get complete structure analysis of a repository."""
        
        async with GitHubFileHunter(self.github_token) as hunter:
            owner, repo, detected_branch = hunter.parse_github_url(repo_url)
            use_branch = branch or detected_branch
            
            print(f"🔍 Analyzing {owner}/{repo} (branch: {use_branch})")
            
            # Get repository tree
            tree_data = await hunter.get_repository_tree(owner, repo, use_branch)
            
            # Analyze structure
            analysis = self._analyze_tree_structure(tree_data, owner, repo, use_branch)
            analysis['repository_info'] = {
                'owner': owner,
                'repo': repo,
                'branch': use_branch,
                'repo_url': repo_url
            }
            
            return analysis
    
    def _analyze_tree_structure(self, tree_data, owner, repo, branch):
        """Analyze the tree data and extract insights."""
        
        files = []
        directories = set()
        file_types = defaultdict(int)
        file_sizes = defaultdict(list)
        directory_stats = defaultdict(lambda: {'count': 0, 'total_size': 0})
        
        for item in tree_data.get('tree', []):
            if item['type'] == 'blob':  # File
                file_info = {
                    'path': item['path'],
                    'size': item['size'],
                    'sha': item['sha'],
                    'download_url': f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{item['path']}"
                }
                
                files.append(file_info)
                
                # Extract file extension
                ext = Path(item['path']).suffix.lower()
                if ext:
                    file_types[ext] += 1
                    file_sizes[ext].append(item['size'])
                else:
                    file_types['[no extension]'] += 1
                    file_sizes['[no extension]'].append(item['size'])
                
                # Directory statistics
                dir_path = str(Path(item['path']).parent)
                if dir_path != '.':
                    directories.add(dir_path)
                    directory_stats[dir_path]['count'] += 1
                    directory_stats[dir_path]['total_size'] += item['size']
            
            elif item['type'] == 'tree':  # Directory
                directories.add(item['path'])
        
        # Calculate statistics
        total_files = len(files)
        total_size = sum(f['size'] for f in files)
        avg_file_size = total_size / total_files if total_files > 0 else 0
        
        # Top file types
        top_file_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Largest files
        largest_files = sorted(files, key=lambda x: x['size'], reverse=True)[:10]
        
        # Directory statistics
        dir_stats = []
        for dir_path, stats in directory_stats.items():
            dir_stats.append({
                'path': dir_path,
                'file_count': stats['count'],
                'total_size': stats['total_size'],
                'avg_size': stats['total_size'] / stats['count'] if stats['count'] > 0 else 0
            })
        
        # Sort by file count
        top_directories = sorted(dir_stats, key=lambda x: x['file_count'], reverse=True)[:10]
        
        return {
            'summary': {
                'total_files': total_files,
                'total_directories': len(directories),
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'average_file_size': round(avg_file_size, 2)
            },
            'file_types': dict(top_file_types),
            'largest_files': largest_files,
            'top_directories': top_directories,
            'all_files': files,
            'all_directories': sorted(list(directories))
        }
    
    async def analyze_multiple_repos(self, repo_urls, output_dir="./structure_analysis"):
        """Analyze multiple repositories."""
        
        os.makedirs(output_dir, exist_ok=True)
        
        results = {}
        
        for repo_url in repo_urls:
            try:
                analysis = await self.analyze_repository(repo_url)
                results[repo_url] = analysis
                
                # Save individual analysis
                repo_name = repo_url.replace('https://github.com/', '').replace('/', '_')
                individual_file = os.path.join(output_dir, f"{repo_name}_structure.json")
                
                with open(individual_file, 'w') as f:
                    json.dump(analysis, f, indent=2)
                
                print(f"✅ {repo_url}: {analysis['summary']['total_files']} files analyzed")
                
            except Exception as e:
                print(f"❌ {repo_url}: Error - {str(e)}")
                results[repo_url] = {'error': str(e)}
        
        # Save combined results
        combined_file = os.path.join(output_dir, "combined_analysis.json")
        with open(combined_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Create summary CSV
        self._create_summary_csv(results, output_dir)
        
        return results
    
    def _create_summary_csv(self, results, output_dir):
        """Create a CSV summary of all analyzed repositories."""
        
        csv_file = os.path.join(output_dir, "repository_summary.csv")
        
        with open(csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Repository', 'Total Files', 'Total Directories', 
                'Total Size (MB)', 'Average File Size (bytes)', 
                'Top File Type', 'Top File Type Count'
            ])
            
            for repo_url, analysis in results.items():
                if 'error' not in analysis:
                    summary = analysis['summary']
                    file_types = analysis['file_types']
                    top_type = list(file_types.keys())[0] if file_types else 'N/A'
                    top_count = list(file_types.values())[0] if file_types else 0
                    
                    writer.writerow([
                        repo_url,
                        summary['total_files'],
                        summary['total_directories'],
                        summary['total_size_mb'],
                        summary['average_file_size'],
                        top_type,
                        top_count
                    ])
                else:
                    writer.writerow([repo_url, 'ERROR', '', '', '', '', ''])

async def main():
    parser = argparse.ArgumentParser(description='Repository Structure Analyzer')
    parser.add_argument('repositories', nargs='+', help='Repository URLs to analyze')
    parser.add_argument('--token', '-t', help='GitHub token', default=os.getenv('GITHUB_TOKEN'))
    parser.add_argument('--output-dir', '-o', default='./structure_analysis', help='Output directory')
    parser.add_argument('--branch', '-b', help='Specific branch to analyze')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both', 
                       help='Output format')
    
    args = parser.parse_args()
    
    analyzer = RepoStructureAnalyzer(args.token)
    
    if len(args.repositories) == 1:
        # Single repository analysis
        analysis = await analyzer.analyze_repository(args.repositories[0], args.branch)
        
        # Print summary
        summary = analysis['summary']
        print(f"\n📊 Repository Analysis Summary:")
        print(f"   📁 Total files: {summary['total_files']}")
        print(f"   📂 Total directories: {summary['total_directories']}")
        print(f"   💾 Total size: {summary['total_size_mb']} MB")
        print(f"   📈 Average file size: {summary['average_file_size']} bytes")
        
        print(f"\n🏆 Top file types:")
        for ext, count in list(analysis['file_types'].items())[:5]:
            print(f"   {ext}: {count} files")
        
        # Save results
        os.makedirs(args.output_dir, exist_ok=True)
        output_file = os.path.join(args.output_dir, "structure_analysis.json")
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n💾 Results saved to: {args.output_dir}")
        
    else:
        # Multiple repositories
        results = await analyzer.analyze_multiple_repos(args.repositories, args.output_dir)
        
        print(f"\n📊 Analyzed {len(args.repositories)} repositories")
        print(f"💾 Results saved to: {args.output_dir}")

if __name__ == "__main__":
    asyncio.run(main())