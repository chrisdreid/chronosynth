#!/usr/bin/env python3
"""
Script to create a self-contained web viewer package
"""

import os
import sys
import shutil
import argparse
from datetime import datetime, timedelta

# Add the parent directory to the path so we can import local modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from chronosynth.visualization.html_plotter import HTMLPlotter
    from chronosynth.core.generator import TimeSeriesGenerator
except ImportError:
    from visualization.html_plotter import HTMLPlotter
    from core.generator import TimeSeriesGenerator


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
    
    # Generate the viewer HTML with embedded libraries
    viewer_file = os.path.join(output_dir, "viewer.html")
    HTMLPlotter.generate_viewer(viewer_file)
    print(f"Created viewer: {viewer_file}")
    
    # Create an index.html file
    index_file = os.path.join(output_dir, "index.html")
    create_index_html(index_file)
    print(f"Created index page: {index_file}")
    
    # Generate sample data if requested
    if generate_sample_data:
        create_sample_data(output_dir)
        
    print(f"\nViewer package created successfully in {output_dir}")
    print(f"To use the viewer, open {os.path.join(output_dir, 'index.html')} in a web browser.")


def create_index_html(file_path):
    """Create an index.html file that links to the viewer"""
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>ChronoSynth Data Viewer</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 10px;
        }
        .file-list {
            margin: 20px 0;
            padding: 0;
            list-style: none;
        }
        .file-list li {
            margin: 10px 0;
            padding: 10px;
            background: #f5f5f5;
            border-radius: 4px;
        }
        .file-list a {
            color: #0066cc;
            text-decoration: none;
            font-weight: bold;
        }
        .file-list a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <h1>ChronoSynth Data Viewer</h1>
    <p>This page allows you to view time series data generated with ChronoSynth.</p>
    
    <h2>Available Data Files</h2>
    <ul class="file-list">
        <li>
            <a href="viewer.html?filepath=sine_wave.pkl">Sine Wave (PKL)</a> - Sample sine wave data
        </li>
        <li>
            <a href="viewer.html?filepath=random_walk.pkl">Random Walk (PKL)</a> - Sample random walk data
        </li>
        <li>
            <a href="viewer.html?filepath=multi_series.pkl">Multiple Series (PKL)</a> - Multiple time series in one file
        </li>
    </ul>
    
    <h2>Standalone Viewer</h2>
    <p>You can also <a href="viewer.html">open the viewer directly</a> and load files manually.</p>
    
    <h2>Using this Viewer</h2>
    <p>This is a self-contained web viewer for ChronoSynth time series data. It has all the JavaScript libraries embedded
    in the HTML file, so you don't need an internet connection to use it.</p>
    
    <p>You can:</p>
    <ul>
        <li>Click on one of the sample data files above to view it</li>
        <li>Open the viewer directly and drag-and-drop data files onto it</li>
        <li>Use the file selector in the viewer to load .pkl, .npy or .json files</li>
    </ul>
</body>
</html>"""
    
    with open(file_path, "w") as f:
        f.write(html_content)


def create_sample_data(output_dir):
    """Generate sample data files"""
    print("Generating sample data files...")
    
    # Create generator
    generator = TimeSeriesGenerator()
    
    # Generate sine wave data
    start_time = datetime.now() - timedelta(hours=1)
    sine_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        keyframes=["a:0:20", "a:0.5:80", "a:1:20"],
        start_time=start_time
    )
    generator.save(sine_data, os.path.join(output_dir, "sine_wave.pkl"), "structured", "pkl")
    generator.save(sine_data, os.path.join(output_dir, "sine_wave.npy"), "structured", "npy")
    print("  Created sine wave data")
    
    # Generate random walk data
    random_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        load="high",
        noise_scale=2.0,
        start_time=start_time
    )
    generator.save(random_data, os.path.join(output_dir, "random_walk.pkl"), "structured", "pkl")
    generator.save(random_data, os.path.join(output_dir, "random_walk.npy"), "structured", "npy")
    print("  Created random walk data")
    
    # Generate multi-series data
    multi_data = generator.generate(
        minutes=60,
        interval_seconds=10,
        keyframes=[
            "a:0:10", "a:0.25:90", "a:0.5:20", "a:0.75:75", "a:1:30",
            "b:0:20", "b:0.25:40", "b:0.5:80", "b:0.75:60", "b:1:30",
            "c:0:5", "c:0.25:25", "c:0.5:95", "c:0.75:45", "c:1:15"
        ],
        start_time=start_time
    )
    generator.save(multi_data, os.path.join(output_dir, "multi_series.pkl"), "structured", "pkl")
    print("  Created multi-series data")


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