"""Command-line interface for TimeSeriesGenerator."""

import argparse
import os
import sys
import json
import webbrowser
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import logging

# set up logger
# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Define log levels for easier access
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL


try:
    from ..core.generator import TimeSeriesGenerator
    from ..visualization.cli_plotter import CLIPlotter
    from ..visualization.html_plotter import HTMLPlotter
except ImportError:
    # Support for direct script execution
    from timeseries_generator.core.generator import TimeSeriesGenerator
    from timeseries_generator.visualization.cli_plotter import CLIPlotter
    from timeseries_generator.visualization.html_plotter import HTMLPlotter


def parse_arguments(args=None):
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Generate synthetic time series data with advanced configuration options.")
    
    # Basic options
    parser.add_argument("--config-file", type=str, help="Path to field configuration file")
    parser.add_argument("--batch-file", type=str, help="Path to batch configuration file")
    parser.add_argument("--input-file", type=str, help="Path to input file to load and modify")
    parser.add_argument("--minutes", type=int, default=30, help="Duration in minutes")
    parser.add_argument("--interval-seconds", type=float, default=5.0, help="Time between data points")
    parser.add_argument("--start-time", type=str, help="Starting timestamp (YYYY-MM-DD HH:MM:SS)")
    parser.add_argument("--load", type=str, choices=["low", "medium", "high"], default="medium", help="Predefined load profile")
    parser.add_argument("--noise-scale", type=float, default=1.0, help="Global noise multiplier")
    
    # Advanced options
    parser.add_argument("--keyframe", type=str, nargs="+", help="Keyframe expressions (without quotes)")
    parser.add_argument("--mask", type=str, action="append", help="Mask expressions (without quotes)")
    parser.add_argument("--normalize-input", action="store_true", help="Interpret numeric values in keyframes as fractions [0-1]")
    parser.add_argument("--normalize", action="store_true", help="Normalize all values to 0-1 range in output")
    
    # Output options
    parser.add_argument("--output-dir", type=str, default="output", help="Output directory")
    parser.add_argument("--output-file", type=str, help="Output file name")
    parser.add_argument("--format", type=str, choices=["raw", "structured"], default="structured", help="Output data format")
    parser.add_argument("--output-format", type=str, choices=["json", "pkl", "npy", "auto"], default="auto", 
                      help="Output file format (json, pkl, npy, or auto to detect from extension)")
    
    # Visualization options
    parser.add_argument("--plot", type=str, help="Visualization type or output file path (cli, html, html:open, path/to/file.[png|svg|pdf|html])")
    parser.add_argument("--plot-label", type=str, help="Plot title")
    
    # Resampling options
    parser.add_argument("--resample", type=str, choices=["mean", "minmax", "linear", "lttb"], help="Resampling algorithm")
    parser.add_argument("--resample-interval", type=float, help="Target interval for resampling (in seconds)")
    parser.add_argument("--resample-points", type=int, help="Target number of points for LTTB resampling")
    
    # Special commands
    parser.add_argument("--generate-viewer", action="store_true", help="Generate a standalone viewer HTML file")
    parser.add_argument("--viewer-file", type=str, default="timeseries_viewer.html", help="Output path for viewer HTML file")
    
    if not args:
        args = sys.argv[1:]
    return parser.parse_args(args)


def parse_batch_file(batch_file: str, default_options: argparse.Namespace) -> List[Dict[str, Any]]:
    """
    Parse a batch file containing multiple configurations.
    
    Args:
        batch_file: Path to batch file
        default_options: Default argument values from the command line
        
    Returns:
        List of batch specifications
    """
    if not os.path.exists(batch_file):
        logger.error(f"Batch file not found: {batch_file}")
        return []
    
    batch_specs = []
    
    try:
        with open(batch_file, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
        for line_idx, line in enumerate(lines):
            # Default output file name based on line number if not specified
            output_file = f"dataset_{line_idx + 1}.json"
            
            # Parse arguments for this dataset
            parser = argparse.ArgumentParser(add_help=False)
            
            # All parameters that can be overridden in batch entries
            parser.add_argument("--output-file", type=str, default=output_file)
            parser.add_argument("--minutes", type=int, default=default_options.minutes)
            parser.add_argument("--interval-seconds", type=float, default=default_options.interval_seconds)
            parser.add_argument("--start-time", type=str, default=default_options.start_time)
            parser.add_argument("--load", type=str, choices=["low", "medium", "high"], default=default_options.load)
            parser.add_argument("--noise-scale", type=float, default=default_options.noise_scale)
            parser.add_argument("--keyframe", type=str, nargs="+", default=default_options.keyframe)
            parser.add_argument("--mask", type=str, action="append")
            parser.add_argument("--normalize-input", action="store_true", default=getattr(default_options, 'normalize_input', False))
            parser.add_argument("--normalize", action="store_true", default=default_options.normalize)
            parser.add_argument("--output-dir", type=str, default=default_options.output_dir)
            parser.add_argument("--format", type=str, choices=["raw", "structured"], default=default_options.format)
            parser.add_argument("--output-format", type=str, choices=["json", "pkl", "npy", "auto"], default=default_options.output_format)
            parser.add_argument("--plot-label", type=str, default=default_options.plot_label)
            parser.add_argument("--resample", type=str, choices=["mean", "minmax", "linear", "lttb"], default=default_options.resample)
            parser.add_argument("--resample-interval", type=float, default=default_options.resample_interval)
            parser.add_argument("--resample-points", type=int, default=default_options.resample_points)
            
            try:
                # Handle the special case of mask: if default_options.mask is None, set to empty list
                if getattr(default_options, 'mask', None) is None:
                    parser.set_defaults(mask=[])
                else:
                    parser.set_defaults(mask=default_options.mask)

                # Split the line into arguments, but respect quoted strings
                import shlex
                args = shlex.split(line)
                parsed = parser.parse_args(args)
                spec = vars(parsed)
                spec["dataset_index"] = line_idx + 1  # Store the dataset index for reference
                batch_specs.append(spec)
            except SystemExit:
                logger.warning(f"Failed to parse arguments for dataset {line_idx + 1}, skipping...")
                continue
    except Exception as e:
        logger.error(f"Error parsing batch file: {e}")
    
    return batch_specs


def handle_plot_request(generator, data: Dict[str, Any], plot_arg: str, title: Optional[str] = None) -> None:
    """
    Handle plot request based on the --plot argument.
    
    Args:
        generator: TimeSeriesGenerator instance
        data: Data to plot
        plot_arg: Plot argument value
        title: Plot title
    """
    # Make sure field_config includes all field properties, including color
    field_config = generator.field_config.fields
    
    # Special case for HTML with browser opening
    if plot_arg == "html:open":
        HTMLPlotter.generate_html(data, title, field_config, open_browser=True)
        return
    
    # Check if plot_arg is a file path (contains a dot or slash)
    if "." in plot_arg or "/" in plot_arg:
        # It's a file path
        HTMLPlotter.save_plot(data, plot_arg, title, field_config)
    else:
        # It's a plot type
        if plot_arg == "cli":
            # Display in terminal using matplotlib
            plotter = CLIPlotter()
            plotter.plot(data, title, field_config)
        elif plot_arg == "html":
            # Generate HTML file
            HTMLPlotter.generate_html(data, title, field_config)
        elif plot_arg == "svg":
            # Generate SVG file
            HTMLPlotter.generate_svg(data, title, field_config)
        elif plot_arg == "ascii":
            # Generate ASCII plot (no dependencies)
            plotter = CLIPlotter()
            plotter.plot_ascii(data)
        else:
            logger.error(f"Unknown plot type: {plot_arg}")


def main(args=None):
    """Command-line interface for TimeSeriesGenerator."""
    options = parse_arguments(args)
    
    # Handle special commands
    if options.generate_viewer:
        HTMLPlotter.generate_viewer(options.viewer_file)
        sys.exit(0)
    
    # Create generator with global config
    config_file = options.config_file
    generator = TimeSeriesGenerator(config_file)
    
    # Process batch file if provided
    if options.batch_file:
        batch_specs = parse_batch_file(options.batch_file, options)
        if not batch_specs:
            logger.error(f"No valid configurations found in batch file: {options.batch_file}")
            sys.exit(1)
        
        # Process each batch
        results = {}
        for i, spec in enumerate(batch_specs):
            dataset_idx = spec["dataset_index"]
            logger.info(f"Generating dataset {i+1}/{len(batch_specs)}: dataset_{dataset_idx}")
            
            # Parse start time if provided
            start_time = None
            if spec.get("start_time"):
                try:
                    start_time = datetime.strptime(spec["start_time"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Invalid start time format: {spec['start_time']}")
            
            # Generate data
            data = generator.generate(
                minutes=spec["minutes"],
                interval_seconds=spec["interval_seconds"],
                keyframes=spec.get("keyframe", []),
                load=spec["load"],
                noise_scale=spec["noise_scale"],
                masks=spec.get("mask", []),
                normalize=spec.get("normalize_input", False),
                start_time=start_time
            )
            
            # Resample if requested
            if spec.get("resample"):
                if spec["resample"] == "lttb" and spec.get("resample_points"):
                    data = generator.resample(data, spec["resample"], target_points=spec["resample_points"])
                elif spec.get("resample_interval"):
                    data = generator.resample(data, spec["resample"], target_interval=spec["resample_interval"])
                else:
                    logger.warning(f"Missing parameters for resampling method: {spec['resample']}")
            
            # Use batch-specific output directory
            batch_output_dir = spec["output_dir"]
            os.makedirs(batch_output_dir, exist_ok=True)
            
            # Save individual file
            output_file = spec["output_file"]
            
            # Handle the case where output_file might already include the output_dir
            if os.path.dirname(output_file) and not os.path.isabs(output_file):
                # If output_file has a directory component but is not absolute, use it as is
                output_path = os.path.join(batch_output_dir, output_file)
            else:
                # Otherwise, join with the batch_output_dir
                output_path = os.path.join(batch_output_dir, os.path.basename(output_file))
            
            # Use batch-specific format and output_format
            generator.save(
                data, 
                output_path, 
                spec["format"], 
                spec["output_format"], 
                spec.get("normalize", False)
            )
            logger.info(f"  Saved to: {output_path}")
            
            # Store for reference
            results[f"dataset_{dataset_idx}"] = {
                "data": data,
                "output_path": output_path,
                "spec": spec
            }
            
            # Plot if requested and individual plots are enabled
            if options.plot:
                plot_label = spec["plot_label"] or f"Dataset {dataset_idx}"
                handle_plot_request(generator, data, options.plot, plot_label)
        
        logger.info(f"Batch processing complete. Generated {len(batch_specs)} datasets.")
    else:
        # Single dataset generation
        
        # Parse start time if provided
        start_time = None
        if options.start_time:
            try:
                start_time = datetime.strptime(options.start_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.warning(f"Invalid start time format: {options.start_time}")
        
        # Check if we're loading data from an input file
        if options.input_file:
            logger.info(f"Loading data from: {options.input_file}")
            try:
                data = generator.load(options.input_file)
                if not data:
                    logger.error(f"Failed to load data from {options.input_file}")
                    sys.exit(1)
                logger.info("Data loaded successfully")
                
                # If keyframes are provided, apply them to the loaded data
                if options.keyframe:
                    logger.info("Applying keyframes to loaded data...")
                    # Extract information from loaded data
                    if "timestamps" in data and len(data["timestamps"]) > 0:
                        # Calculate total duration in minutes from timestamps
                        total_minutes = (data["timestamps"][-1] - data["timestamps"][0]).total_seconds() / 60
                        # Use the same interval as in the loaded data
                        if "seconds_timestamps" in data and len(data["seconds_timestamps"]) > 1:
                            interval = data["seconds_timestamps"][1] - data["seconds_timestamps"][0]
                        else:
                            interval = options.interval_seconds
                        
                        # Apply keyframes to the loaded data
                        data = generator.generate(
                            minutes=total_minutes,
                            interval_seconds=interval,
                            keyframes=options.keyframe,
                            load=options.load,
                            noise_scale=options.noise_scale,
                            masks=options.mask,
                            normalize=options.normalize_input,
                            start_time=data["timestamps"][0]
                        )
            except Exception as e:
                logger.error(f"Error loading or processing input file: {e}")
                sys.exit(1)
        else:
            # Generate new data
            data = generator.generate(
                minutes=options.minutes,
                interval_seconds=options.interval_seconds,
                keyframes=options.keyframe,
                load=options.load,
                noise_scale=options.noise_scale,
                masks=options.mask,
                normalize=options.normalize_input,
                start_time=start_time
            )
        
        # Resample if requested
        if options.resample:
            if options.resample == "lttb" and options.resample_points:
                data = generator.resample(data, options.resample, target_points=options.resample_points)
            elif options.resample_interval:
                data = generator.resample(data, options.resample, target_interval=options.resample_interval)
            else:
                logger.warning(f"Missing parameters for resampling method: {options.resample}")
        
        # Save output
        if options.output_file:
            output_path = options.output_file
        else:
            os.makedirs(options.output_dir, exist_ok=True)
            output_path = os.path.join(options.output_dir, "timeseries_data.json")
        
        generator.save(data, output_path, options.format, options.output_format, options.normalize)
        logger.info(f"Data saved to: {output_path}")
        
        # Plot if requested
        if options.plot:
            handle_plot_request(generator, data, options.plot, options.plot_label)


if __name__ == "__main__":
    main()