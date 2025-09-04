#!/usr/bin/env python3
"""
GitHub File Hunter - Search Profiles

Pre-built search profiles for common development scenarios.
Makes it easy to find specific types of files without remembering complex patterns.
"""

import asyncio
import argparse
import os
from github_file_hunter import GitHubFileHunter, SearchCriteria

# Pre-defined search profiles
SEARCH_PROFILES = {
    "config": {
        "description": "Configuration files",
        "criteria": SearchCriteria(
            name_patterns=["*config*", "*.conf", "*.cfg", "*.ini", "settings.*"],
            extensions=[".yml", ".yaml", ".toml", ".json", ".env"],
            exclude_patterns=["node_modules/*", ".git/*", "*.min.*"]
        )
    },
    
    "api": {
        "description": "API-related files",
        "criteria": SearchCriteria(
            name_patterns=["*api*", "*client*", "*server*", "*route*", "*endpoint*"],
            path_patterns=["*api*", "*routes*", "*handlers*", "*controllers*"],
            extensions=[".py", ".js", ".ts", ".go", ".java", ".php", ".rb"],
            exclude_patterns=["test*", "*test*", "*.min.*"]
        )
    },
    
    "auth": {
        "description": "Authentication and security files",
        "criteria": SearchCriteria(
            name_patterns=["*auth*", "*login*", "*security*", "*token*", "*jwt*", "*oauth*"],
            path_patterns=["*auth*", "*security*", "*middleware*"],
            extensions=[".py", ".js", ".ts", ".go", ".java"],
            exclude_patterns=["test*", "*test*"]
        )
    },
    
    "database": {
        "description": "Database and ORM files",
        "criteria": SearchCriteria(
            name_patterns=["*db*", "*database*", "*model*", "*schema*", "*migration*", "*orm*"],
            path_patterns=["*models*", "*db*", "*database*", "*migrations*", "*schemas*"],
            extensions=[".py", ".js", ".ts", ".sql", ".go", ".java"],
            exclude_patterns=["test*", "*test*"]
        )
    },
    
    "docker": {
        "description": "Docker and containerization files",
        "criteria": SearchCriteria(
            name_patterns=["Dockerfile*", "docker-compose*", "*docker*", ".dockerignore"],
            extensions=[".yml", ".yaml"],
            path_patterns=["*docker*", "*containers*"]
        )
    },
    
    "ci": {
        "description": "CI/CD pipeline files",
        "criteria": SearchCriteria(
            name_patterns=["*.yml", "*.yaml", "Jenkinsfile", "*.sh"],
            path_patterns=[".github/*", ".gitlab-ci*", ".circleci/*", "ci/*", "scripts/*", ".jenkins/*"],
            exclude_patterns=["node_modules/*"]
        )
    },
    
    "docs": {
        "description": "Documentation files",
        "criteria": SearchCriteria(
            name_patterns=["README*", "CHANGELOG*", "LICENSE*", "*.md", "*.rst", "*.txt"],
            path_patterns=["docs/*", "documentation/*", "wiki/*"],
            extensions=[".md", ".rst", ".txt", ".adoc"]
        )
    },
    
    "tests": {
        "description": "Test files",
        "criteria": SearchCriteria(
            name_patterns=["*test*", "*spec*", "*_test.*", "test_*"],
            path_patterns=["test*", "*test*", "spec/*", "__tests__/*"],
            extensions=[".py", ".js", ".ts", ".go", ".java", ".rb", ".php"]
        )
    },
    
    "frontend": {
        "description": "Frontend/UI files",
        "criteria": SearchCriteria(
            extensions=[".js", ".ts", ".jsx", ".tsx", ".vue", ".svelte", ".html", ".css", ".scss", ".sass"],
            path_patterns=["src/*", "components/*", "views/*", "pages/*", "static/*", "assets/*"],
            exclude_patterns=["node_modules/*", "dist/*", "build/*", "*.min.*"]
        )
    },
    
    "backend": {
        "description": "Backend/Server files",
        "criteria": SearchCriteria(
            extensions=[".py", ".go", ".java", ".rb", ".php", ".cs", ".rs"],
            path_patterns=["src/*", "lib/*", "app/*", "server/*", "api/*"],
            exclude_patterns=["test*", "*test*", "vendor/*", "node_modules/*"]
        )
    },
    
    "scripts": {
        "description": "Scripts and automation",
        "criteria": SearchCriteria(
            extensions=[".sh", ".bash", ".py", ".ps1", ".bat", ".js"],
            path_patterns=["scripts/*", "bin/*", "tools/*", "automation/*"],
            name_patterns=["*.sh", "*.py", "*.js", "*script*", "*automation*"]
        )
    },
    
    "ml": {
        "description": "Machine Learning files",
        "criteria": SearchCriteria(
            name_patterns=["*model*", "*train*", "*predict*", "*ml*", "*ai*", "*neural*", "*deep*"],
            path_patterns=["models/*", "training/*", "ml/*", "ai/*", "notebooks/*"],
            extensions=[".py", ".ipynb", ".R", ".pkl", ".h5", ".pt", ".pth", ".onnx"]
        )
    },
    
    "security": {
        "description": "Security-related files",
        "criteria": SearchCriteria(
            name_patterns=["*security*", "*cert*", "*key*", "*ssl*", "*tls*", "*crypto*"],
            extensions=[".pem", ".crt", ".key", ".p12", ".jks"],
            exclude_patterns=["*.example", "*.sample", "test*"]
        )
    },
    
    "large": {
        "description": "Large files (>1MB)",
        "criteria": SearchCriteria(
            min_size=1024*1024,  # 1MB
            exclude_patterns=["node_modules/*", ".git/*", "*.log"]
        )
    }
}

class GitHubHunterProfiles:
    """GitHub File Hunter with pre-built search profiles."""
    
    def __init__(self, github_token: str = None):
        self.github_token = github_token
    
    def list_profiles(self):
        """List all available search profiles."""
        print("🎯 Available Search Profiles:")
        print("=" * 50)
        
        for name, profile in SEARCH_PROFILES.items():
            print(f"📋 {name:<12} - {profile['description']}")
        
        print(f"\n💡 Use: python {os.path.basename(__file__)} <repo> --profile <name>")
    
    def get_profile_details(self, profile_name: str):
        """Show details of a specific profile."""
        if profile_name not in SEARCH_PROFILES:
            print(f"❌ Profile '{profile_name}' not found")
            return
        
        profile = SEARCH_PROFILES[profile_name]
        criteria = profile['criteria']
        
        print(f"🎯 Profile: {profile_name}")
        print(f"📝 Description: {profile['description']}")
        print("=" * 50)
        
        if criteria.name_patterns:
            print(f"📄 Name patterns: {', '.join(criteria.name_patterns)}")
        
        if criteria.extensions:
            print(f"🔧 Extensions: {', '.join(criteria.extensions)}")
        
        if criteria.path_patterns:
            print(f"📁 Path patterns: {', '.join(criteria.path_patterns)}")
        
        if criteria.exclude_patterns:
            print(f"🚫 Exclude patterns: {', '.join(criteria.exclude_patterns)}")
        
        if criteria.min_size > 0:
            print(f"📏 Min size: {criteria.min_size} bytes")
        
        if criteria.max_size < float('inf'):
            print(f"📏 Max size: {criteria.max_size} bytes")
        
        if criteria.regex_pattern:
            print(f"🔍 Regex: {criteria.regex_pattern}")
    
    async def search_with_profile(self, repo_url: str, profile_name: str, 
                                 branch: str = None, download: bool = False, 
                                 output_dir: str = ".", preview_only: bool = False,
                                 show_details: bool = False, export_file: str = None,
                                 export_format: str = "json"):
        """Search using a pre-built profile."""
        
        if profile_name not in SEARCH_PROFILES:
            print(f"❌ Unknown profile: {profile_name}")
            print("Available profiles:")
            for name in SEARCH_PROFILES.keys():
                print(f"  - {name}")
            return
        
        profile = SEARCH_PROFILES[profile_name]
        criteria = profile['criteria']
        
        print(f"🎯 Using profile: {profile_name}")
        print(f"📝 {profile['description']}")
        print()
        
        async with GitHubFileHunter(self.github_token) as hunter:
            # Parse repository URL
            owner, repo, detected_branch = hunter.parse_github_url(repo_url)
            search_branch = branch or detected_branch
            
            print(f"🔍 Searching {owner}/{repo} (branch: {search_branch})")
            if self.github_token:
                print("🔑 Using GitHub token")
            else:
                print("⚠️  No token - may hit rate limits")
            print()
            
            # Get repository tree
            print("📡 Fetching repository structure...")
            tree_data = await hunter.get_repository_tree(owner, repo, search_branch)
            total_files = len([item for item in tree_data.get('tree', []) if item['type'] == 'blob'])
            print(f"📊 Repository contains {total_files} files")
            
            # Search with profile criteria
            matches = hunter.search_files(tree_data, criteria, owner, repo, search_branch)
            
            # Display results
            hunter.display_matches(matches, show_details)
            
            # Export if requested
            if export_file:
                hunter.export_matches(matches, export_file, export_format)
            
            # Download if requested
            if download and matches and not preview_only:
                print()
                confirm = input(f"Download {len(matches)} files to '{output_dir}'? (y/N): ")
                if confirm.lower() in ['y', 'yes']:
                    await hunter.download_files(matches, output_dir)
                else:
                    print("Download cancelled.")
            elif preview_only:
                print("👁️  Preview mode - no files downloaded")
            elif not matches:
                print("💡 No files found with this profile. Try a different profile or custom search.")
            elif not download:
                print("💡 Use --download to download these files")

async def main():
    parser = argparse.ArgumentParser(
        description='GitHub File Hunter - Search with pre-built profiles',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all available profiles
  python github_hunter_profiles.py --list

  # Show details of a specific profile
  python github_hunter_profiles.py --show config

  # Search for config files
  python github_hunter_profiles.py owner/repo --profile config

  # Search and download API files
  python github_hunter_profiles.py https://github.com/owner/repo --profile api --download

  # Preview Docker files without downloading
  python github_hunter_profiles.py owner/repo --profile docker --preview-only
        """
    )
    
    # Repository (optional for list/show operations)
    parser.add_argument('repo', nargs='?', help='GitHub repository (owner/repo or full URL)')
    
    # Profile operations
    parser.add_argument('--list', '-l', action='store_true', help='List all available profiles')
    parser.add_argument('--show', '-s', help='Show details of a specific profile')
    parser.add_argument('--profile', '-p', help='Search profile to use')
    
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
    parser.add_argument('--export', help='Export matches to file')
    parser.add_argument('--export-format', choices=['json', 'csv', 'txt'], default='json',
                       help='Export file format')
    
    args = parser.parse_args()
    
    hunter_profiles = GitHubHunterProfiles(args.token)
    
    # Handle list operation
    if args.list:
        hunter_profiles.list_profiles()
        return 0
    
    # Handle show operation
    if args.show:
        hunter_profiles.get_profile_details(args.show)
        return 0
    
    # Validate required arguments for search
    if not args.repo:
        print("❌ Error: Repository required for search operations")
        print("💡 Use --list to see available profiles or --help for usage")
        return 1
    
    if not args.profile:
        print("❌ Error: Profile required for search operations")
        print("💡 Use --list to see available profiles")
        return 1
    
    try:
        await hunter_profiles.search_with_profile(
            args.repo, args.profile, args.branch, args.download,
            args.output_dir, args.preview_only, args.details,
            args.export, args.export_format
        )
        
        return 0
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(asyncio.run(main()))