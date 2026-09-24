import os
import requests
import argparse
import hashlib
from urllib.parse import urlparse

# Audio Asset Manager for NVGT Projects
# Finds and downloads audio assets robustly with verification and deduplication.

AUDIO_MAGIC_BYTES = {
    b'RIFF': 'wav',
    b'OggS': 'ogg',
    b'fLaC': 'flac',
    b'ID3': 'mp3',
    b'\xff\xfb': 'mp3',
}

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def verify_audio(filepath):
    with open(filepath, 'rb') as f:
        header = f.read(4)
        if any(header.startswith(magic) for magic in AUDIO_MAGIC_BYTES):
            return True
        f.seek(0)
        header2 = f.read(2)
        if header2 in [b'\xff\xfb', b'\xff\xf3', b'\xff\xf2']:
            return True
    return False

def download_file(url, target_folder):
    if not os.path.exists(target_folder):
        os.makedirs(target_folder)
        
    filename = os.path.basename(urlparse(url).path).split("?")[0]
    if not filename:
        filename = "downloaded_asset.wav"
        
    filepath = os.path.join(target_folder, filename)
    
    print(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url, stream=True, timeout=15)
        response.raise_for_status()
        
        if 'text/html' in response.headers.get('Content-Type', '').lower():
            print(f"Error: URL returned HTML, not audio: {url}")
            return False
            
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        if not verify_audio(filepath):
            print(f"Error: Not a valid audio file. Deleting: {filename}")
            os.remove(filepath)
            return False
            
        current_hash = get_file_hash(filepath)
        for other in os.listdir(target_folder):
            op = os.path.join(target_folder, other)
            if op != filepath and os.path.isfile(op) and get_file_hash(op) == current_hash:
                print(f"Warning: Duplicate of {other}. Deleting: {filename}")
                os.remove(filepath)
                return True
        
        print(f"Successfully downloaded and verified: {filename}")
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def search_advice():
    print("For better audio game assets, search for:")
    print("- 'SFX footstep grass wav'")
    print("- 'ambient forest loop wav'")
    print("- 'UI click mechanical wav'")
    print("Sites recommended: Freesound.org, OpenGameArt.org, Soniss GDC (for large packs)")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NVGT Asset Manager")
    parser.add_argument("--download", help="URL of the asset to download")
    parser.add_argument("--target", default="sounds", help="Target folder for assets")
    parser.add_argument("--advice", action="store_true", help="Get search advice")
    
    args = parser.parse_args()
    
    if args.advice:
        search_advice()
    
    if args.download:
        download_file(args.download, args.target)
