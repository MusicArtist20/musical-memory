import sys
import requests
import argparse
import re
import json

# NVGT Universal Truth Engine v3.0
# Fetches raw code, documentation, and GitHub issues directly from the source.

BASE_RAW_URL = "https://raw.githubusercontent.com/samtupy/nvgt/main/"
API_ISSUES_URL = "https://api.github.com/repos/samtupy/nvgt/issues"

def fetch_content(path):
    url = BASE_RAW_URL + path
    print(f"--- Fetching Content: {url} ---")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {path}: {e}")
        return None

def fetch_github_issues(state="open", labels=None):
    params = {"state": state}
    if labels:
        params["labels"] = labels
        
    print(f"--- Fetching GitHub Issues (state={state}) ---")
    try:
        response = requests.get(API_ISSUES_URL, params=params, timeout=10)
        response.raise_for_status()
        issues = response.json()
        for i in issues:
            print(f"[#{i['number']}] {i['title']} - {i['html_url']}")
            # Optional: print summary of body
            # print(f"    {i['body'][:100]}...")
        return issues
    except Exception as e:
        print(f"Error fetching issues: {e}")
        return None

def extract_class_info(content, class_name):
    # Regex for AngelScript/NVGT class extraction
    pattern = rf"class\s+{class_name}\s*[^{{]*\{{(.*?)\}}"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"--- Class {class_name} Found ---")
        methods = re.findall(r"(\w+\s+\w+\(.*?\);)", match.group(1))
        for m in methods:
            print(f"    {m.strip()}")
        return match.group(0)
    else:
        print(f"Class {class_name} not found.")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NVGT Universal Truth Engine")
    parser.add_argument("--source", help="Header filename in release/include/ (e.g., 'menu.nvgt')")
    parser.add_argument("--doc", help="Documentation filename (e.g., 'README.md' or 'docs/api.md')")
    parser.add_argument("--issues", action="store_true", help="Fetch open GitHub issues for troubleshooting")
    parser.add_argument("--class_name", help="Extract specific class from source")
    
    args = parser.parse_args()
    
    if args.source:
        path = f"release/include/{args.source}"
        if not path.endswith(".nvgt"): path += ".nvgt"
        content = fetch_content(path)
        if content:
            if args.class_name:
                extract_class_info(content, args.class_name)
            else:
                classes = re.findall(r"class\s+(\w+)", content)
                print(f"Classes found in {args.source}: {', '.join(classes)}")
                
    elif args.doc:
        content = fetch_content(args.doc)
        if content:
            print(content)
            
    elif args.issues:
        fetch_github_issues()
    else:
        parser.print_help()
