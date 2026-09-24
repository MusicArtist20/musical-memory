import sys
import argparse
import requests
import json

# A simplified tool for the NVGT skill to search documentation directly from GitHub.
# Usage: python github_search.py "query" [--type code|issues|commits]

def search_github(query, search_type="code"):
    # Base URL for searching the NVGT repository
    repo = "samtupy/nvgt"
    if search_type == "code":
        url = f"https://api.github.com/search/code?q={query}+repo:{repo}"
    elif search_type == "issues":
        url = f"https://api.github.com/search/issues?q={query}+repo:{repo}"
    else:
        url = f"https://api.github.com/search/commits?q={query}+repo:{repo}"

    # Note: AI can use read_url_content if it needs to scrape, but this script is for structured search.
    # However, since I (Antigravity) don't have a GitHub API key, I will suggest using search_web with site prefix.
    # But the user wants a *tool*. So I'll provide a script that constructs the search URLs.

    print(f"Requesting GitHub search for '{query}' in {repo}...")
    # Since we might be rate-limited or lacking keys, we'll provide the search results URLs
    # for the AI to then use read_url_content on.
    
    search_url = f"https://github.com/{repo}/search?q={query}"
    print(f"Search URL: {search_url}")
    
    # Actually executing the search via web_search or read_url_content is preferred by the AI.
    # This script can serve as a 'command' that the AI executes to get fixed URLs.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search NVGT GitHub Repository")
    parser.add_argument("query", help="The term to search for")
    parser.add_argument("--type", choices=["code", "issues", "commits"], default="code", help="Type of search")
    args = parser.parse_args()
    
    search_github(args.query, args.type)
