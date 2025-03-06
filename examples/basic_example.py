#!/usr/bin/env python
"""Basic ChronoSynth example demonstrating keyframe generation and visualization."""

from chronosynth import TimeSeriesGenerator
import os
import json

# Ensure outputs directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), "outputs"), exist_ok=True)

# Create generator with config file
generator = TimeSeriesGenerator()
config_file = os.path.join(os.path.dirname(__file__), "configs/standard_fields.json")

# Load the config file manually
with open(config_file, 'r') as f:
    config = json.load(f)

# Configure fields
generator.configure_fields(config)

# Generate data with At-Sign keyframe format
data = generator.generate(
    minutes=30,
    interval_seconds=5,
    keyframes=[
        # Set default transitions to smooth
        "c~", "g~",
        # Initial values with at-sign format
        "@0s;c20;m10;g5",
        # Time-based events with multiple fields
        "@5m;c60",
        "@10m;m20~", 
        "@15m;g80;c70^",
        "@20m;m25|", 
        # Advanced patterns
        "@25m;g50^75,55:5s",
        "@end;c80"
    ]
)

# Output in structured format
output_file = os.path.join(os.path.dirname(__file__), "outputs/basic_example.json")
generator.save(data, output_file, format="structured")

print(f"Data saved to {output_file}")

# Optional visualization if matplotlib is installed
try:
    from chronosynth.visualization.cli_plotter import CLIPlotter
    cli_plot = CLIPlotter()
    cli_plot.plot(data)
    print("Displaying plot...")
except ImportError:
    print("Matplotlib not installed. Install with: pip install matplotlib")

# Optional HTML plot generation
try:
    from chronosynth.visualization.html_plotter import HTMLPlotter
    html_file = os.path.join(os.path.dirname(__file__), "outputs/basic_example.html")
    HTMLPlotter.generate_html(data, title="Basic ChronoSynth Example", output_file=html_file)
    print(f"HTML plot saved to {html_file}")
except ImportError:
    print("HTML plotting dependencies not installed.")