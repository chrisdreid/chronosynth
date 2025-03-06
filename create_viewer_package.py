#!/usr/bin/env python3
"""
Script to create a self-contained web viewer package that can be distributed

This script creates a complete package containing:
1. A self-contained viewer HTML file with embedded JavaScript libraries
2. An index.html file for navigation
3. Optional sample data files for demonstration

The resulting package can be shared with users who want to view time series data
without installing ChronoSynth.
"""

import os
import sys
import shutil
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from chronosynth.visualization.html_plotter import HTMLPlotter
    from chronosynth.core.generator import TimeSeriesGenerator
    from chronosynth.setup_viewer_libs import setup_libs
except ImportError:
    from visualization.html_plotter import HTMLPlotter
    from core.generator import TimeSeriesGenerator
    from setup_viewer_libs import setup_libs


def create_viewer_package(output_dir, generate_sample_data=True):
    """
    Creates a self-contained web viewer package with all necessary files.
    
    Args:
        output_dir: Directory to create the package in
        generate_sample_data: Whether to generate sample data files
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating self-contained viewer package in: {output_dir}")
    
    # Make sure JS libraries are available
    setup_libs()
    
    # Generate the viewer HTML with embedded libraries
    viewer_file = os.path.join(output_dir, "viewer.html")
    HTMLPlotter.generate_viewer(viewer_file)
    print(f"Created viewer: {viewer_file}")
    
    # Generate sample data if requested
    sample_files = []
    if generate_sample_data:
        sample_files = create_sample_data(output_dir)
    
    # Create an index.html file
    index_file = os.path.join(output_dir, "index.html")
    create_index_html(index_file, sample_files)
    print(f"Created index page: {index_file}")
    
    print(f"\nViewer package created successfully in {output_dir}")
    print(f"To use the viewer, open {os.path.join(output_dir, 'index.html')} in a web browser.")


def create_index_html(file_path, sample_files=None):
    """
    Create an index.html file that links to the viewer and sample files.
    
    Args:
        file_path: Path to write the index.html file
        sample_files: List of sample data files to link to
    """
    # Create links to sample files if provided
    file_links = ""
    if sample_files:
        for file_path in sample_files:
            basename = os.path.basename(file_path)
            description = "Sample data"
            
            if "sine" in basename.lower():
                description = "Sample sine wave data"
            elif "random" in basename.lower():
                description = "Sample random walk data"
            elif "multi" in basename.lower():
                description = "Multiple time series in one file"
            
            file_links += f"""        <li>
            <a href="viewer.html?filepath={basename}">{basename}</a> - {description}
        </li>\n"""
    else:
        # Default sample file links in case no sample files were provided
        file_links = """        <li>
            <a href="viewer.html?filepath=sine_wave.pkl">Sine Wave (PKL)</a> - Sample sine wave data
        </li>
        <li>
            <a href="viewer.html?filepath=random_walk.pkl">Random Walk (PKL)</a> - Sample random walk data
        </li>
        <li>
            <a href="viewer.html?filepath=multi_series.pkl">Multiple Series (PKL)</a> - Multiple time series in one file
        </li>"""
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>ChronoSynth Data Viewer</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }}
        .file-list {{
            margin: 20px 0;
            padding: 0;
            list-style: none;
        }}
        .file-list li {{
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }}
        .file-list a {{
            color: #0066cc;
            text-decoration: none;
            font-weight: bold;
        }}
        .file-list a:hover {{
            text-decoration: underline;
        }}
        .note {{
            background-color: #fff8dc;
            padding: 15px;
            border-left: 5px solid #ffeb3b;
            margin: 20px 0;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <h1>ChronoSynth Data Viewer</h1>
    <p>This is a self-contained web viewer for ChronoSynth time series data. It has all JavaScript libraries embedded
    in the HTML file, so you don't need an internet connection to use it.</p>
    
    <div class="note">
        <strong>Note:</strong> Make sure JavaScript is enabled in your browser. If viewing locally,
        some browsers may have security restrictions that prevent loading data files from the filesystem.
        If you encounter issues, try using a simple web server or a different browser.
    </div>
    
    <h2>Available Data Files</h2>
    <ul class="file-list">
{file_links}
    </ul>
    
    <h2>Standalone Viewer</h2>
    <p>You can also <a href="viewer.html">open the viewer directly</a> and load files manually.</p>
    
    <h2>Using this Viewer</h2>
    <p>You can:</p>
    <ul>
        <li>Click on one of the sample data files above to view it</li>
        <li>Open the viewer directly and drag-and-drop data files onto it</li>
        <li>Use the file selector in the viewer to load .pkl, .npy or .json files</li>
    </ul>
    
    <hr>
    <p><small>Generated by ChronoSynth</small></p>
</body>
</html>"""
    
    with open(file_path, "w") as f:
        f.write(html_content)


def create_sample_data(output_dir):
    """
    Generate sample data files
    
    Args:
        output_dir: Directory to save sample data files
        
    Returns:
        List of paths to the generated files
    """
    print("Generating sample data files...")
    
    file_paths = []
    
    # Create generator
    generator = TimeSeriesGenerator()
    
    # Generate sine wave data
    start_time = datetime.now() - timedelta(hours=1)
    sine_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        keyframes=["value:0:20", "value:0.5:80", "value:1:20"],
        start_time=start_time
    )
    sine_pkl = os.path.join(output_dir, "sine_wave.pkl")
    sine_npy = os.path.join(output_dir, "sine_wave.npy")
    generator.save(sine_data, sine_pkl, "structured", "pkl")
    generator.save(sine_data, sine_npy, "structured", "npy")
    file_paths.extend([sine_pkl, sine_npy])
    print("  Created sine wave data: sine_wave.pkl, sine_wave.npy")
    
    # Generate random walk data
    random_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        load="high",
        noise_scale=2.0,
        start_time=start_time
    )
    random_pkl = os.path.join(output_dir, "random_walk.pkl")
    random_npy = os.path.join(output_dir, "random_walk.npy")
    generator.save(random_data, random_pkl, "structured", "pkl")
    generator.save(random_data, random_npy, "structured", "npy")
    file_paths.extend([random_pkl, random_npy])
    print("  Created random walk data: random_walk.pkl, random_walk.npy")
    
    # Generate multi-series data
    multi_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        keyframes=[
            "cpu:0:10", "cpu:0.25:90", "cpu:0.5:20", "cpu:0.75:75", "cpu:1:30",
            "mem:0:20", "mem:0.25:40", "mem:0.5:80", "mem:0.75:60", "mem:1:30",
            "disk:0:5", "disk:0.25:25", "disk:0.5:95", "disk:0.75:45", "disk:1:15"
        ],
        start_time=start_time
    )
    multi_pkl = os.path.join(output_dir, "multi_series.pkl")
    generator.save(multi_data, multi_pkl, "structured", "pkl")
    file_paths.append(multi_pkl)
    print("  Created multi-series data: multi_series.pkl")
    
    return file_paths


def main():
    parser = argparse.ArgumentParser(description="Create a self-contained web viewer package")
    parser.add_argument("--output-dir", "-o", type=str, default="viewer_package",
                      help="Directory to create the package in")
    parser.add_argument("--no-samples", action="store_true",
                      help="Don't generate sample data files")
    
    args = parser.parse_args()
    
    create_viewer_package(args.output_dir, not args.no_samples)


if __name__ == "__main__":
    main()