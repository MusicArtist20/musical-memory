import re
import sys

# NVGT BGT Porting Assistant v1.0
# Scans legacy BGT code and highlights mandatory NVGT-specific upgrades.

RULES = [
    (r"(sound|menu|file|network|socket|db_props|ini|sqlite|dict|dictionary)\s+([a-zA-Z0-9_]+)\s*;", 
     "LEGACY DECLARATION: Replace with handle '@' (e.g., sound@ s = sound();)"),
    (r"wait\(\s*([0-9.]+)\s*\);", 
     "TIMING FIX: Ensure wait() uses uint ms (e.g., wait(5) instead of wait(5.0))"),
    (r"\.draw\(\)", 
     "DEPRECATION: Graphical .draw() methods aren't supported in standard NVGT headless mode."),
    (r"get_last_key\(\)", 
     "MAPPING: Use key_pressed() or event loops for modern input handling."),
    (r"input_box\((.*?)\)", 
     "UI CHECK: Verify if you need to use the advanced 'audio_form' class for accessible inputs.")
]

def scan_file(filename):
    print(f"--- Scanning Legacy BGT File: {filename} ---")
    try:
        with open(filename, "r") as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                for pattern, msg in RULES:
                    if re.search(pattern, line):
                        print(f"[Line {i+1}] {line.strip()}")
                        print(f"    --> {msg}")
    except Exception as e:
        print(f"Error scanning {filename}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python bgt_porting_validator.py <filename.bgt>")
    else:
        scan_file(sys.argv[1])
