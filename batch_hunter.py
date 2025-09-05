#!/usr/bin/env python3
"""
Enhanced GitHub File Hunter - Batch Processing with Structure Analysis
Supports individual file downloads, pattern matching, and repository structure analysis.
"""

import json
import os
import sys
import argparse
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
import shutil
import tempfile

# Import the main hunter class
from github_file_hunter import GitHubFileHunter, analyze_repository_structure

class BatchGitHubHunter:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.temp_structure_dir = None
        self.structure_cache = {}
        
    async def analyze_repositories_first(self, repositories: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        First analyze all repositories to get their structure and avoid branch/file issues.
        
        Args:
            repositories: List of repository configurations
            
        Returns:
            Dictionary mapping repo keys to their structure data
        """
        print("🔍 Phase 1: Analyzing repository structures to prevent branch/file issues...")
        
        structure_results = {}
        
        for repo_config in repositories:
            owner = repo_config.get('owner')
            repo = repo_config.get('repo')
            branch = repo_config.get('branch')
            
            if not owner or not repo:
                continue
                
            repo_key = f"{owner}/{repo}"
            
            # Skip if already analyzed
            if repo_key in structure_results:
                continue
                
            print(f"  📊 Analyzing {repo_key}...")
            
            try:
                repo_url = f"https://github.com/{owner}/{repo}"
                structure_data = await analyze_repository_structure(
                    repo_url=repo_url,
                    branch=branch,
                    github_token=self.token,
                    output_dir=self.temp_structure_dir
                )
                
                if structure_data:
                    structure_results[repo_key] = structure_data
                    print(f"    ✅ {structure_data.get('summary', {}).get('total_files', 0)} files found")
                else:
                    print(f"    ❌ Failed to analyze structure")
                    
            except Exception as e:
                print(f"    ❌ Error: {e}")
                
        print(f"📊 Structure analysis complete: {len(structure_results)} repositories analyzed\n")
        return structure_results
        
    def validate_and_fix_config(self, repo_config: Dict[str, Any], structure_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and fix repository configuration using structure data.
        
        Args:
            repo_config: Original repository configuration
            structure_data: Repository structure analysis data
            
        Returns:
            Fixed repository configuration
        """
        fixed_config = repo_config.copy()
        
        # Fix branch name using actual repository info
        repo_info = structure_data.get('repository_info', {})
        actual_branch = repo_info.get('branch')
        if actual_branch and actual_branch != repo_config.get('branch'):
            print(f"    🔧 Fixed branch: {repo_config.get('branch', 'None')} → {actual_branch}")
            fixed_config['branch'] = actual_branch
            
        # Validate individual files exist
        all_files = structure_data.get('all_files', [])
        file_paths = [f['path'] for f in all_files]
        
        individual_files = repo_config.get('individual_files', [])
        if individual_files:
            valid_files = []
            for file_path in individual_files:
                if file_path in file_paths:
                    valid_files.append(file_path)
                else:
                    # Try to find similar files
                    similar_files = [f for f in file_paths if os.path.basename(f) == os.path.basename(file_path)]
                    if similar_files:
                        print(f"    🔧 File not found: {file_path}, using similar: {similar_files[0]}")
                        valid_files.append(similar_files[0])
                    else:
                        print(f"    ❌ File not found and no alternatives: {file_path}")
                        
            fixed_config['individual_files'] = valid_files
            
        # Validate patterns match actual files
        patterns = repo_config.get('patterns', [])
        if patterns:
            import fnmatch
            valid_patterns = []
            for pattern in patterns:
                matching_files = [f for f in file_paths if fnmatch.fnmatch(f, pattern)]
                if matching_files:
                    valid_patterns.append(pattern)
                    print(f"    ✅ Pattern '{pattern}' matches {len(matching_files)} files")
                else:
                    print(f"    ❌ Pattern '{pattern}' matches no files")
                    
            fixed_config['patterns'] = valid_patterns
            
        return fixed_config
        
    async def process_batch_config(self, config_file: str, structure_only: bool = False) -> Dict[str, Any]:
        """
        Process a batch configuration file for multiple repositories.
        
        Args:
            config_file: Path to JSON configuration file
            structure_only: If True, only analyze structure without downloading files
            
        Returns:
            Dictionary with processing results
        """
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"❌ Error reading config file: {e}")
            return {"success": False, "error": str(e)}
            
        repositories = config.get('repositories', [])
        output_dir = config.get('output_dir', './downloads')
        create_repo_folders = config.get('create_repo_folders', True)
        
        if not repositories:
            print("❌ No repositories found in config")
            return {"success": False, "error": "No repositories in config"}
            
        # Create temporary directory for structure files
        self.temp_structure_dir = tempfile.mkdtemp(prefix="github_structures_")
        print(f"📁 Created temporary structure directory: {self.temp_structure_dir}")
        
        # Phase 1: Analyze all repositories first
        structure_results = await self.analyze_repositories_first(repositories)
        
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "repositories": {},
            "structure_dir": self.temp_structure_dir if structure_only else None,
            "structure_analysis": structure_results
        }
        
        if structure_only:
            # If structure-only mode, just return the analysis
            for repo_key, structure_data in structure_results.items():
                results["repositories"][repo_key] = {
                    "success": True,
                    "total_files": structure_data.get("summary", {}).get("total_files", 0)
                }
                results["processed"] += 1
            return results
        
        # Phase 2: Process downloads using structure-validated configurations
        print("🔍 Phase 2: Processing downloads using validated configurations...")
        
        for repo_config in repositories:
            try:
                owner = repo_config.get('owner')
                repo = repo_config.get('repo')
                
                if not owner or not repo:
                    print(f"❌ Missing owner or repo in config: {repo_config}")
                    results["failed"] += 1
                    continue
                
                repo_key = f"{owner}/{repo}"
                print(f"\n🔍 Processing {repo_key}")
                
                # Check if we have structure data for this repo
                if repo_key not in structure_results:
                    print(f"❌ No structure data available for {repo_key}")
                    results["repositories"][repo_key] = {
                        "success": False,
                        "error": "No structure data available"
                    }
                    results["failed"] += 1
                    continue
                
                # Validate and fix configuration using structure data
                structure_data = structure_results[repo_key]
                fixed_config = self.validate_and_fix_config(repo_config, structure_data)
                
                # Get fixed values
                branch = fixed_config.get('branch')
                individual_files = fixed_config.get('individual_files', [])
                patterns = fixed_config.get('patterns', [])
                exclude_patterns = fixed_config.get('exclude_patterns', [])
                max_files = fixed_config.get('max_files', 100)
                output_subdir = fixed_config.get('output_subdir', '')
                
                # Determine output directory
                if output_subdir:
                    final_output_dir = os.path.join(output_dir, output_subdir)
                elif create_repo_folders:
                    final_output_dir = os.path.join(output_dir, f"{owner}_{repo}")
                else:
                    final_output_dir = output_dir
                
                # Initialize hunter for this repository
                hunter = GitHubFileHunter(github_token=self.token)
                
                # Download files using the existing hunter functionality
                async with hunter:
                    # Get repository tree
                    tree_data = await hunter.get_repository_tree(owner, repo, branch)
                    
                    # Create search criteria
                    from github_file_hunter import SearchCriteria
                    criteria = SearchCriteria()
                    criteria.specific_files = individual_files
                    criteria.path_patterns = patterns
                    criteria.exclude_patterns = exclude_patterns
                    
                    # Search for matches
                    matches = hunter.search_files(tree_data, criteria, owner, repo, branch or tree_data.get('sha', 'main'))
                    
                    # Limit matches if specified
                    if max_files and len(matches) > max_files:
                        matches = matches[:max_files]
                    
                    if matches:
                        await hunter.download_files(matches, final_output_dir)
                        results["repositories"][repo_key] = {
                            "success": True,
                            "downloaded": len(matches),
                            "output_dir": final_output_dir
                        }
                        print(f"✅ {repo_key}: {len(matches)} files downloaded")
                    else:
                        results["repositories"][repo_key] = {
                            "success": False,
                            "error": "No matching files found"
                        }
                        print(f"❌ {repo_key}: No matching files found")
                        results["failed"] += 1
                        continue
                
                results["processed"] += 1
                
            except Exception as e:
                print(f"❌ Error processing {owner}/{repo}: {e}")
                results["repositories"][f"{owner}/{repo}"] = {
                    "success": False,
                    "error": str(e)
                }
                results["failed"] += 1
        
        # Clean up temporary structure directory if downloads were successful
        if results["failed"] == 0 and self.temp_structure_dir:
            try:
                shutil.rmtree(self.temp_structure_dir)
                print(f"🧹 Cleaned up temporary structure directory")
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up temporary directory: {e}")
        
        return results

async def main():
    parser = argparse.ArgumentParser(description='Batch GitHub File Hunter')
    parser.add_argument('config', help='JSON configuration file')
    parser.add_argument('--token', help='GitHub personal access token')
    parser.add_argument('--structure-only', action='store_true', 
                       help='Only analyze repository structures without downloading files')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.config):
        print(f"❌ Config file not found: {args.config}")
        sys.exit(1)
    
    hunter = BatchGitHubHunter(token=args.token)
    
    print(f"🚀 Starting batch processing with config: {args.config}")
    if args.structure_only:
        print("📊 Structure analysis mode - no files will be downloaded")
    
    results = await hunter.process_batch_config(args.config, structure_only=args.structure_only)
    
    print(f"\n📊 Batch processing complete!")
    print(f"✅ Processed: {results['processed']}")
    print(f"❌ Failed: {results['failed']}")
    
    if args.structure_only and results.get("structure_dir"):
        print(f"📁 Structure files saved to: {results['structure_dir']}")
    
    # Print summary
    for repo, result in results.get("repositories", {}).items():
        if result["success"]:
            if args.structure_only:
                print(f"  ✅ {repo}: {result.get('total_files', 0)} files analyzed")
            else:
                print(f"  ✅ {repo}: {result.get('downloaded', 0)} files downloaded")
        else:
            print(f"  ❌ {repo}: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(main())