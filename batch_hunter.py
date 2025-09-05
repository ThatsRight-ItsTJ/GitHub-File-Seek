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
from github_file_hunter import GitHubFileHunter

class BatchGitHubHunter:
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.temp_structure_dir = None
        
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
        
        results = {
            "success": True,
            "processed": 0,
            "failed": 0,
            "repositories": {},
            "structure_dir": self.temp_structure_dir if structure_only else None
        }
        
        for repo_config in repositories:
            try:
                owner = repo_config.get('owner')
                repo = repo_config.get('repo')
                branch = repo_config.get('branch')
                individual_files = repo_config.get('individual_files', [])
                patterns = repo_config.get('patterns', [])
                exclude_patterns = repo_config.get('exclude_patterns', [])
                max_files = repo_config.get('max_files', 100)
                output_subdir = repo_config.get('output_subdir', '')
                
                if not owner or not repo:
                    print(f"❌ Missing owner or repo in config: {repo_config}")
                    results["failed"] += 1
                    continue
                
                repo_key = f"{owner}/{repo}"
                print(f"\n🔍 Processing {repo_key}")
                
                # Determine output directory
                if output_subdir:
                    final_output_dir = os.path.join(output_dir, output_subdir)
                elif create_repo_folders:
                    final_output_dir = os.path.join(output_dir, f"{owner}_{repo}")
                else:
                    final_output_dir = output_dir
                
                # Initialize hunter for this repository - fix the constructor call
                hunter = GitHubFileHunter(github_token=self.token)
                
                if structure_only:
                    # Only analyze structure
                    repo_url = f"https://github.com/{owner}/{repo}"
                    structure_data = await analyze_repository_structure(
                        repo_url=repo_url,
                        branch=branch,
                        github_token=self.token,
                        output_dir=self.temp_structure_dir
                    )
                    
                    if structure_data:
                        results["repositories"][repo_key] = {
                            "success": True,
                            "structure_file": os.path.join(self.temp_structure_dir, f"{owner}_{repo}_structure.json"),
                            "total_files": structure_data.get("summary", {}).get("total_files", 0)
                        }
                        print(f"✅ {repo_key}: Structure analyzed ({structure_data.get('summary', {}).get('total_files', 0)} files)")
                    else:
                        results["repositories"][repo_key] = {
                            "success": False,
                            "error": "Failed to analyze structure"
                        }
                        print(f"❌ {repo_key}: Structure analysis failed")
                        results["failed"] += 1
                        continue
                else:
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
        if not structure_only and results["failed"] == 0 and self.temp_structure_dir:
            try:
                shutil.rmtree(self.temp_structure_dir)
                print(f"🧹 Cleaned up temporary structure directory")
            except Exception as e:
                print(f"⚠️ Warning: Could not clean up temporary directory: {e}")
        
        return results

# Import the analyze function from github_file_hunter
from github_file_hunter import analyze_repository_structure

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