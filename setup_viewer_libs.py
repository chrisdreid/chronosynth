#!/usr/bin/env python3
"""
Script to set up JavaScript libraries required for the ChronoSynth viewer.

This script will:
1. Create the necessary lib directory
2. Download required JavaScript libraries from CDNs
3. Place them in the lib directory for the viewer to access

This ensures that all required libraries are available locally for:
- Embedding in the self-contained viewer HTML
- Offline use in air-gapped environments 
- Testing and development

Required libraries:
- pickletojson.js - For parsing pickle files
- numjs.min.js - For parsing NumPy arrays and .npy files
- plotly.min.js - For interactive visualization
- dayjs.min.js - For date/time handling
"""

import os
import sys
import urllib.request
import shutil
from pathlib import Path

# Define library sources
LIBRARIES = {
    # Libraries embedded in the HTML
    "pickletojson.js": "https://unpkg.com/pickleparser@0.2.1/dist/index.js",
    "numjs.min.js": "https://cdnjs.cloudflare.com/ajax/libs/numjs/0.16.1/numjs.min.js",
    
    # External libraries loaded via CDN in the HTML but we'll download them for offline use
    "plotly.min.js": "https://cdn.plot.ly/plotly-2.35.2.min.js",
    "dayjs.min.js": "https://cdn.jsdelivr.net/npm/dayjs@1.10.4/dayjs.min.js"
}

def setup_libs(target_dir=None, force=False):
    """
    Set up the JavaScript libraries in the specified directory.
    
    Args:
        target_dir: The directory to place the libraries in (default: chronosynth/lib)
        force: Whether to force download even if the files already exist
    """
    # Determine the target directory
    if target_dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        target_dir = os.path.join(script_dir, "lib")
    
    # Create the directory if it doesn't exist
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"Setting up JavaScript libraries in: {target_dir}")
    
    # Download each library
    for lib_name, lib_url in LIBRARIES.items():
        lib_path = os.path.join(target_dir, lib_name)
        
        # Check if the file already exists
        if os.path.exists(lib_path) and not force:
            print(f"  {lib_name} already exists, skipping...")
            continue
        
        try:
            print(f"  Downloading {lib_name} from {lib_url}...")
            urllib.request.urlretrieve(lib_url, lib_path)
            print(f"  Successfully downloaded {lib_name}")
        except Exception as e:
            print(f"  Error downloading {lib_name}: {e}")
            
            # If download fails, create an empty file with warning comment
            with open(lib_path, 'w') as f:
                f.write(f"// Failed to download {lib_name} from {lib_url}\n")
                f.write(f"// Error: {e}\n")
                f.write("// Please download the file manually or run setup_viewer_libs.py again\n")
    
    # We don't need to copy these files anywhere else
    # since they're only used at generation time to be embedded into HTML
    
    print("Library setup complete!")

def main():
    """Command-line interface for the library setup script."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up JavaScript libraries for ChronoSynth viewer")
    parser.add_argument("--dir", "-d", type=str, help="Target directory for the libraries")
    parser.add_argument("--force", "-f", action="store_true", help="Force download even if files exist")
    
    args = parser.parse_args()
    
    setup_libs(args.dir, args.force)

if __name__ == "__main__":
    main()