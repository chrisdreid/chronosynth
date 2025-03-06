#!/usr/bin/env python
"""
Example demonstrating how to use the ChronoSynth viewer server from Python.
"""

import os
import sys
import time
from pathlib import Path

# Add the parent directory to the path so we can import the viewer server
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from chronosynth import TimeSeriesGenerator
from chronosynth.examples.viewer_server import run_server, ViewerAPI

# Ensure outputs directory exists
EXAMPLE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(EXAMPLE_DIR, "outputs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_sample_datasets():
    """Generate some sample datasets to view."""
    generator = TimeSeriesGenerator()
    
    # Configure fields
    config_file = os.path.join(EXAMPLE_DIR, "configs/standard_fields.json")
    with open(config_file, 'r') as f:
        import json
        config = json.load(f)
    generator.configure_fields(config)
    
    # Generate three different datasets
    datasets = [
        {
            "name": "dataset1",
            "description": "High CPU Load",
            "keyframes": [
                "c~", "g~", "m~",
                "@0s;c20;g10;m5000",
                "@1m;c80;g20;m8000",
                "@2m;c90;g30;m10000",
                "@3m;c70;g40;m12000",
                "@4m;c50;g30;m10000",
                "@5m;c20;g10;m8000"
            ]
        },
        {
            "name": "dataset2",
            "description": "High GPU Load",
            "keyframes": [
                "c~", "g~", "m~",
                "@0s;c10;g20;m5000",
                "@1m;c20;g70;m8000",
                "@2m;c30;g90;m10000",
                "@3m;c40;g80;m12000",
                "@4m;c30;g60;m10000",
                "@5m;c10;g30;m8000"
            ]
        },
        {
            "name": "dataset3",
            "description": "High Memory Load",
            "keyframes": [
                "c~", "g~", "m~",
                "@0s;c10;g10;m8000",
                "@1m;c20;g20;m16000",
                "@2m;c30;g30;m24000",
                "@3m;c40;g40;m28000",
                "@4m;c30;g30;m20000",
                "@5m;c10;g10;m10000"
            ]
        }
    ]
    
    file_paths = []
    
    for dataset in datasets:
        # Generate data
        data = generator.generate(
            minutes=5,
            interval_seconds=10,
            keyframes=dataset["keyframes"]
        )
        
        # Save as JSON
        output_path = os.path.join(OUTPUT_DIR, f"{dataset['name']}.json")
        generator.save(data, output_path, format="structured")
        file_paths.append(output_path)
        print(f"Generated dataset: {output_path}")
        
        # Save as PKL
        pkl_path = os.path.join(OUTPUT_DIR, f"{dataset['name']}.pkl")
        generator.save(data, pkl_path, format="structured", output_format="pkl")
        
    return file_paths

def main():
    """Run the viewer example."""
    # Generate sample datasets
    file_paths = generate_sample_datasets()
    
    # Start the viewer server
    port = run_server(open_browser=False, directory=parent_dir)
    
    # Create API client
    api = ViewerAPI(port=port)
    if not api.wait_for_connection():
        print("Failed to connect to viewer server")
        return
    
    # Load multiple files and set view mode to multi
    print(f"Loading {len(file_paths)} files into viewer...")
    api.load_multiple_files(file_paths)
    api.set_view_mode("multi")
    
    print(f"\nViewer server running at http://localhost:{port}")
    print("Press Ctrl+C to exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

if __name__ == "__main__":
    main()