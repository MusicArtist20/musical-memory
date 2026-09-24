import os
import sys

# NVGT Asset Orchestrator v1.0
# Organizes audio assets and generates the sound_pool initialization code.

def orchestrate(asset_dir):
    print(f"--- Orchestrating Assets: {asset_dir} ---")
    if not os.path.exists(asset_dir):
        print(f"Error: Directory {asset_dir} does not exist.")
        return
        
    boilerplate = "// --- Automatically Generated Sound Pool Initialization ---\n"
    boilerplate += "void init_sounds(sound_pool@ p) {\n"
    
    for root, dirs, files in os.walk(asset_dir):
        for file in files:
            if file.endswith((".wav", ".mp3", ".ogg", ".flac")):
                relative_path = os.path.relpath(os.path.join(root, file), asset_dir)
                # Sanitize for AS string
                safe_path = relative_path.replace("\\", "/")
                var_name = file.rsplit(".", 1)[0].replace(" ", "_")
                
                boilerplate += f"    // p.play_stationary(\"{safe_path}\", false); // Example for {var_name}\n"
                
    boilerplate += "}\n"
    
    print("--- Generated Boilerplate ---")
    print(boilerplate)
    
    with open("audio_boilerplate.nvgt", "w") as f:
        f.write(boilerplate)
        print("Written to audio_boilerplate.nvgt")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python asset_orchestrator.py <asset_directory>")
    else:
        orchestrate(sys.argv[1])
