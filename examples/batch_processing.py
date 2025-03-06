#!/usr/bin/env python
"""Batch processing example using ChronoSynth."""

import os
import subprocess
import glob

# Ensure all required directories exist
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
BATCH_DIR = os.path.join(EXAMPLES_DIR, "batch")
OUTPUT_DIR = os.path.join(EXAMPLES_DIR, "outputs", "batch_outputs")
CONFIG_DIR = os.path.join(EXAMPLES_DIR, "configs")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Run batch processing using the machines.txt file
def run_batch_processing():
    """Run a batch processing job using the machines.txt configuration."""
    cmd = [
        "python", "-m", "chronosynth",
        "--batch-file", os.path.join(BATCH_DIR, "machines.txt"),
        "--output-dir", OUTPUT_DIR,
        "--config-file", os.path.join(CONFIG_DIR, "standard_fields.json"),
        "--minutes", "60",
        "--interval-seconds", "10",
        "--noise-scale", "0.5"
    ]
    
    print("Running batch processing command:")
    print(" ".join(cmd))
    
    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("\nBatch processing completed successfully!")
    else:
        print("\nBatch processing encountered an error:")
        print(result.stderr)
        return False
    
    return True

# Generate an HTML summary that loads all the batch files
def generate_summary():
    """Generate a summary HTML file that shows all batch outputs."""
    # Find all JSON files in the output directory
    json_files = glob.glob(os.path.join(OUTPUT_DIR, "*.json"))
    
    if not json_files:
        print("No output files found.")
        return
    
    print(f"Found {len(json_files)} output files.")
    
    # Try to generate a combined HTML viewer
    try:
        cmd = [
            "python", "-m", "chronosynth",
            "--generate-viewer",
            "--viewer-file", os.path.join(OUTPUT_DIR, "batch_viewer.html"),
            "--plot-label", "Server Monitoring Batch Results"
        ]
        
        print("\nGenerating combined HTML viewer:")
        print(" ".join(cmd))
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"HTML viewer generated at {os.path.join(OUTPUT_DIR, 'batch_viewer.html')}")
        else:
            print("Error generating HTML viewer:")
            print(result.stderr)
    
    except Exception as e:
        print(f"Exception while generating HTML viewer: {str(e)}")

if __name__ == "__main__":
    print("=== ChronoSynth Batch Processing Example ===")
    success = run_batch_processing()
    
    if success:
        generate_summary()
    
    print("\nExample complete. Output files are in:")
    print(OUTPUT_DIR)