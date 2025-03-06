# ChronoSynth

### What Is ChronoSynth?
A powerful, flexible library for generating synthetic time series data. The name blends "Chrono" (Greek for "time"), emphasizing its focus on precise, sequential timelines, with "Synth" (short for "synthesis" and "synthetic"), capturing the creation of customizable, synthetic data through advanced configuration options, intuitive keyframe controls, and multiple output formats. It’s built to be strong, flexible, scalable, and intuitive—named to reflect its dynamic core.


## Table of Contents
1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Installation](#installation)
4. [Advanced Keyframe System](#advanced-keyframe-system)
5. [Basic Usage](#basic-usage)
6. [Normalization Features](#normalization-features)
7. [Field Colors and Visualization](#field-colors-and-visualization)
8. [Timeline Masks](#timeline-masks)
9. [Data Formats](#data-formats)
10. [Input File Support](#input-file-support)
11. [Visualization](#visualization)
12. [Resampling Algorithms](#resampling-algorithms)
13. [Enhanced Batch Processing](#enhanced-batch-processing)
14. [Python API](#python-api)
15. [Example Usage](#example-usage)
16. [License](#license)

## Overview


ChronoSynth is designed for creating realistic, customizable time series datasets for testing, visualization, simulation, and algorithm development. The library offers fine-grained control over the generated data through keyframes, transitions, noise levels, and masks, making it suitable for a wide range of applications including:

- Monitoring system simulation
- Algorithm testing and benchmarking
- Visualization demos
- Machine learning dataset generation
- Performance testing of time series processing systems

## Key Features

- **Two Data Structure Formats**: 
  - Raw timeslots format (flexible, allows irregular timestamps)
  - Structured timeslots format (uniform timestamps for all items)

- **Advanced Keyframe System**:
  - Control values at specific points in time
  - Multiple transition types (linear, smooth, step, pulse, sin, pow)
  - Relative keyframe values (`+10`, `-5`, `*1.2`, etc.)
  - Relationship expressions between metrics (`g80@30s(c*0.75)` sets CPU to 75% of GPU)
  - Post-behavior modifiers like pulses with returns (`c80@20s^`, `c60@30s^+10`)
  - Default transition settings for fields (`c~`, `g|`)

- **Flexible Time Formats**:
  - Support for seconds, minutes, hours (`30s`, `5m`, `2h`)
  - Combined formats (`1h30m`, `4h20m45s`)
  - Colon notation (`1:30`, `2:45:30`)
  - Fractional time formats (`.5` for half of total time)

- **Normalization Options**:
  - Input normalization (`--normalize-input`) to treat values as fractions [0-1]
  - Output normalization (`--normalize`) to scale all values to 0-1 range
  - Flexible control for comparing metrics with different scales

- **Precise Control**:
  - Adjustable noise levels (per-metric and global)
  - Built-in resampling algorithms
  - Timeline masks (apply sin waves, power functions across all data)

- **Enhanced Batch Processing**:
  - Generate multiple datasets with different parameters
  - Process specifications from config files
  - Global parameters with batch-specific overrides
  - Flexible configuration with shared settings

- **Visualization Options**:
  - CLI-based plotting
  - Interactive HTML output with standalone viewer
  - Export to PNG, SVG, PDF formats
  - ASCII plotting (no dependencies required)

- **Input File Support**:
  - Load and modify existing time series data
  - Apply new keyframes to loaded data
  - Create variations of existing datasets

- **Multiple Output Formats**:
  - JSON for human-readable data
  - Pickle (.pkl) for binary Python storage
  - NumPy (.npy) for efficient numerical processing

- **Zero Dependencies for Core Functionality**:
  - Works with standard Python libraries
  - Optional enhanced capabilities with numpy, pandas, matplotlib, and svgwrite
  
- **Enhanced Visualization**:
  - Field-specific colors configuration in field definitions
  - Colors preserved in saved data files
  - Interactive HTML plots with proper field coloring
  - Customizable plot styles and appearance

## Installation

### Basic Installation

```bash
pip install chronosynth
```

### Installation with Optional Dependencies

```bash
# Full installation with all dependencies
pip install chronosynth[full]

# Install with specific optional components
pip install chronosynth[visualization]  # Matplotlib, svgwrite
pip install chronosynth[analysis]       # Numpy, pandas
pip install chronosynth[safe_eval]      # Asteval (for safe evaluation of expressions)
```

## Advanced Keyframe System

The keyframe system is the core feature for defining time series behavior. Keyframes allow you to specify exact values at specific points in time, with automatic interpolation between points. 

ChronoSynth now supports two different keyframe syntax formats that can be mixed freely:
1. **Classic Format**: `field@time` (e.g., `c80@30s`) - Field-based organization
2. **At-Sign Format**: `@time;field1value;field2value` (e.g., `@30s;c80;g50`) - Time-based organization

### Classic Format Examples

```python
keyframes = [
    # Simple values
    "c20@0s",                   # CPU=20 at 0s
    "g60@30s",                  # GPU=60 at 30s
    
    # Advanced transitions
    "c80@60s~",                 # CPU=80 at 60s with smooth transition
    "m24@90s|",                 # Memory=24 at 90s with step transition
    
    # Default transition settings
    "g~",                       # Set default GPU transition to smooth
    "c|",                       # Set default CPU transition to step
    
    # Pulse/spike behavior
    "c90@120s^",                # CPU spike to 90 at 120s, then return
    "g70@150s^+10",             # GPU spike to 70, then return to previous+10
    
    # Formula, relationships, and options
    "c(max*0.8)@180s(pow=2)",   # CPU to 80% of max with pow interpolation
    "g80@210s(n=0.7,c*0.6)",    # GPU=80 at 210s, noise=0.7, also affects CPU
]
```

### At-Sign Format Examples

```python
keyframes = [
    # Simple values
    "@0s;c20;g10;m8",           # At 0s: CPU=20, GPU=10, Memory=8
    "@60s;c80;g60",             # At 60s: CPU=80, GPU=60
    
    # Transition types 
    "@120s;c90~",               # At 120s: CPU=90 with smooth transition
    "@180s;g70|",               # At 180s: GPU=70 with step transition
    
    # Advanced patterns
    "@240s;c50^75,55:5s",       # CPU=50, spike to 75, return to 55 over 5s
    "@300s;g60^10^+10",         # GPU=60, pulse to +10, return to +10
    
    # Duration and hold specifications
    "@360s;c70:10s_5s",         # CPU=70 over 10s duration, hold 5s
    "@420s;g50^75,55:5s_2s;c~-40:3s_2s",  # Complex multi-field keyframe:
                                # - GPU=50, spike to 75, return to 55 over 5s, hold 2s
                                # - CPU smooth decrease by 40 over 3s, hold 2s
]
```

### Mixing Both Formats

```python
keyframes = [
    # Initial setup with classic format
    "c20@0s", "g10@0s", "m8@0s",
    "c~", "g~",                 # Set default transitions to smooth
    
    # Time-based events with @-format 
    "@30s;c60^",                # CPU spike to 60% at 30s
    "@60s;g70;m20",             # GPU=70, Memory=20 at 60s
    
    # Continue with classic format for field-specific events
    "c80@90s~",                 # CPU smooth to 80% at 90s
    
    # Complex patterns with @-format
    "@120s;c50^75,55:5s_2s;g80|", # At 120s:
                                # - CPU=50, spike to 75, return to 55 over 5s, hold 2s
                                # - GPU step to 80
]
```

See [Dual Keyframe Parser Documentation](docs/dual_keyframe_parsers.md) for complete details on both formats.

### Keyframe Parser Formats

#### 1. Classic Format (field@time)

```bash
<shorthand>[<value>][@<time>][<transition>][<post_behavior>][(options)]
```

#### 2. At-Sign Format (@time;field1value;field2value)

```bash
@<time>;<shorthand><value>[<transition>][<post_behavior>][:<duration>][_<hold>][;<shorthand2><value2>...]
```

The parser automatically detects which format to use based on the first character:
- If the keyframe starts with `@`, it uses the At-Sign format
- Otherwise, it uses the Classic format

### Classic Keyframe Syntax

```bash
<shorthand>[<value>][@<time>][<transition>][<post_behavior>][(options)]
```

- `shorthand`: Single character identifier for the field (e.g., 'g' for GPU)
- `value`: Target value (absolute or relative, can be omitted for default settings)
- `time`: Timestamp in various formats:
  - Seconds: `10s`, `30`
  - Minutes: `5m`
  - Hours: `2h`
  - Combined: `1h30m`, `4h20m`, `4h20m45s`
  - Colon format: `1:30` (1h 30m), `2:45` (2h 45m), `1:30:45` (1h 30m 45s)
  - Fraction: `.5` (half of total time)
  - Special: `end` (end of timeline)
- `transition`: Transition type (~ for smooth, | for step)
- `post_behavior`: Post-keyframe behavior (^ for pulse, ^+10, ^-5 for modified returns)
- `options`: Optional parameters and relationships

### Examples

```bash
# Basic keyframes with various time formats
g60@30s       # GPU set to 60 at 30 seconds
c40@5m        # CPU set to 40 at 5 minutes
m16000@1h     # Memory set to 16000 at 1 hour
r80@1h30m     # RAM set to 80 at 1 hour 30 minutes
g70@2:45      # GPU set to 70 at 2 hours 45 minutes
c60@4h20m45s  # CPU set to 60 at 4 hours 20 minutes 45 seconds

# Relative and special values
c^2@.5        # CPU set to (current_value^2) at 50% of timeline
r-5@1m        # RAM reduced by 5 at 1 minute
g+10@20s~     # GPU +10 at 20s with 'smooth' transition
gmax@end(sin) # GPU to max value at end with sine transition

# Advanced options and relationships
c50@45s(pow=2, n=0.5) # CPU=50 at 45s, pow interpolation, noise=0.5
rmin@.8(c*0.75) # RAM=min at 80% of timeline, also sets CPU to 75% of RAM value

# Advanced keyframe behaviors
c~            # Set default CPU transition to smooth
g|            # Set default GPU transition to step
c20@0s        # CPU set to 20 at 0s (uses default transition)
c80@20s^      # CPU spikes to 80 at 20s, then returns to previous value
c60@30s^+10   # CPU spikes to 60 at 30s, then returns to previous value+10
c40@40s|      # CPU changes immediately to 40 at 40s
```

### Key Concepts

#### 1. Hold Behavior

By default, values now stay at their keyframe setting until changed by another keyframe.

```bash
"c50@10s"  # CPU to 50 at 10s and holds at 50 indefinitely
"c80@30s"  # CPU changes to 80 at 30s and holds at 80
```

#### 2. Transition Types

Control how values change between keyframes:

- **Linear** (default): Steady rate of change
- **Smooth** (`~`): Gradual acceleration/deceleration (cosine interpolation)
- **Step** (`|`): Immediate change

```bash
"c50@10s"    # Linear transition to 50
"c80@20s~"   # Smooth transition to 80
"c20@30s|"   # Step/immediate jump to 20
```

#### 3. Default Transitions

Set the default transition type for a field using just the shorthand:

```bash
"g~"         # Set default GPU transition to smooth
"g20@10s"    # Will use smooth transition (from default)
"g80@20s|"   # Override with step transition
"g40@30s"    # Back to smooth transition (from default)
```

#### 4. Pulse Behavior

Use the `^` symbol to create a "pulse" effect where the value spikes to the target, then returns to the previous value:

```bash
"c20@10s"    # CPU to 20 at 10s
"c80@20s^"   # CPU spikes to 80 at 20s, then returns to 20
```

#### 5. Post-Behavior Modifiers

Control what happens after a pulse:

```bash
"c20@10s"      # CPU to 20 at 10s
"c80@20s^"     # Spike to 80, return to 20
"c60@30s^+10"  # Spike to 60, return to 30 (20+10)
"c50@40s^-5"   # Spike to 50, return to 25 (30-5)
```

#### 6. Combined Behaviors

Combine different transition types with pulse behaviors:

```bash
"c~"           # Set default to smooth
"c20@10s"      # CPU to 20 at 10s
"c80@20s^"     # Smooth transition to 80, then return to 20
"c60@30s|^"    # Step to 60, then return to 20
```

## Basic Usage

### Command Line Interface

```bash
# Basic usage with defaults
chronosynth

# Generate 60 minutes of data with 10-second intervals
chronosynth --minutes 60 --interval-seconds 10

# Apply custom keyframes (Classic format)
chronosynth --keyframe "g80@30s" "c+20@1m~" "r50@end(sin)"

# Apply custom keyframes (At-Sign format)
chronosynth --keyframe "@30s;g80;c60" "@1m;r70~" "@2m;g50^75,55:5s"

# Mix both formats freely
chronosynth --keyframe "g~" "c~" "@0s;g10;c20" "g80@30s" "@1m;c70^;r30"

# Normalize values (interpret as fractions of min/max range)
chronosynth --normalize --keyframe "g0.8@30s" "c0.5@1m"

# Apply a sine wave mask across the entire timeline
chronosynth --mask "sin(amp=0.3,freq=0.01,offset=1.0)"

# Generate data for multiple machines using a batch file with global settings
chronosynth --batch-file machines.txt --output-dir batch_output --minutes 30 --noise-scale 0.5

# Generate and visualize data in the terminal
chronosynth --plot cli

# Generate and open an interactive HTML visualization
chronosynth --plot html:open

# Generate HTML with correct field colors from configuration 
chronosynth --config-file configs/cpu-gpu-ram-vram.json --plot html:open

# Save plot to specific file formats
chronosynth --plot output/my_plot.png
chronosynth --plot output/my_plot.svg
chronosynth --plot output/my_plot.pdf
chronosynth --plot output/my_plot.html

# Generate a standalone viewer that can load data files
chronosynth --generate-viewer --viewer-file viewer.html

# Save in different formats
chronosynth --output-file data.json  # JSON (default)
chronosynth --output-file data.pkl   # Pickle
chronosynth --output-file data.npy   # NumPy (if numpy is installed)
```

### Python API

```python
from timeseries_generator import TimeSeriesGenerator

# Create generator
generator = TimeSeriesGenerator()

# Configure fields
generator.configure_fields({
    "cpu_usage": {
        "shorthand": "c",
        "min": 0.0,
        "max": 100.0,
        "noise_amount": 0.5,
        "color": "blue"
    },
    "memory_usage": {
        "shorthand": "m",
        "min": 0.0,
        "max": 32.0,
        "noise_amount": 0.3,
        "color": "green"
    },
    "gpu_usage": {
        "shorthand": "g",
        "min": 0.0,
        "max": 100.0,
        "noise_amount": 0.4,
        "color": "red"
    }
})

# Generate data using mixed keyframe formats
data = generator.generate(
    minutes=30,
    interval_seconds=5,
    keyframes=[
        # Classic format
        "c20@0s", "m10@0s", "g5@0s",
        "c~", "g~",  # Set default transitions to smooth
        "c60@5m", "m20@10m~", 
        # At-Sign format
        "@15m;g80;c70^", "@20m;m25|", 
        # Advanced patterns with both formats
        "@25m;g50^75,55:5s", "c80@end"
    ],
    normalize=True
)

# Output in raw format
raw_format = generator.to_raw_format(data)

# Output in structured format
structured_format = generator.to_structured_format(data)

# Save to file in different formats
generator.save(data, "output.json", format="structured")  # JSON
generator.save(data, "output.pkl", format="structured", output_format="pkl")  # Pickle
generator.save(data, "output.npy", format="structured", output_format="npy")  # NumPy

# Load data from file
loaded_data = generator.load("output.json")
```

## Normalization Features

The ChronoSynth now offers two separate normalization capabilities:

### 1. Input Normalization (`--normalize-input`)

When enabled, this treats numeric values in keyframes as fractions between 0-1, which are then scaled to each field's min/max range.

For example, with a CPU field range of 0-100:
- `c0.5@10s` means "set CPU to 50 at 10 seconds" (50% of the range)
- `c0.8@20s` means "set CPU to 80 at 20 seconds" (80% of the range)

This makes it easier to work with fields that have different scales.

### 2. Output Normalization (`--normalize`)

When enabled, this scales all output values to the 0-1 range, regardless of their original scale. This is useful for:
- Creating normalized datasets for machine learning
- Comparing fields with very different scales
- Standardizing data for visualization

Both normalization features can be used independently or together.

### Example: Normalization

```bash
# Generate data with input normalization
chronosynth --normalize-input --keyframe "c0.5@10s" "m0.75@20s" --output-file normalized_input.json

# Generate data with output normalization
chronosynth --keyframe "c50@10s" "m16000@20s" --normalize --output-file normalized_output.json

# Combined input and output normalization
chronosynth --normalize-input --normalize --keyframe "c0.5@10s" "m0.75@20s" --output-file fully_normalized.json
```

### Basic Keyframe Syntax

```bash
<shorthand>[<value>][@<time>][<transition>][<post_behavior>][(options)]
```

- `shorthand`: Single character identifier for the field (e.g., 'g' for GPU)
- `value`: Target value (absolute or relative, can be omitted for default settings)
- `time`: Timestamp in various formats:
  - Seconds: `10s`, `30`
  - Minutes: `5m`
  - Hours: `2h`
  - Combined: `1h30m`, `4h20m`, `4h20m45s`
  - Colon format: `1:30` (1h 30m), `2:45` (2h 45m), `1:30:45` (1h 30m 45s)
  - Fraction: `.5` (half of total time)
  - Special: `end` (end of timeline)
- `transition`: Transition type (~ for smooth, | for step)
- `post_behavior`: Post-keyframe behavior (^ for pulse, ^+10, ^-5 for modified returns)
- `options`: Optional parameters and relationships

### Examples

```bash
# Basic keyframes with various time formats
g60@30s       # GPU set to 60 at 30 seconds
c40@5m        # CPU set to 40 at 5 minutes
m16000@1h     # Memory set to 16000 at 1 hour
r80@1h30m     # RAM set to 80 at 1 hour 30 minutes
g70@2:45      # GPU set to 70 at 2 hours 45 minutes
c60@4h20m45s  # CPU set to 60 at 4 hours 20 minutes 45 seconds

# Relative and special values
c^2@.5        # CPU set to (current_value^2) at 50% of timeline
r-5@1m        # RAM reduced by 5 at 1 minute
g+10@20s~     # GPU +10 at 20s with 'smooth' transition
gmax@end(sin) # GPU to max value at end with sine transition

# Advanced options and relationships
c50@45s(pow=2, n=0.5) # CPU=50 at 45s, pow interpolation, noise=0.5
rmin@.8(c*0.75) # RAM=min at 80% of timeline, also sets CPU to 75% of RAM value

# Advanced keyframe behaviors
c~            # Set default CPU transition to smooth
g|            # Set default GPU transition to step
c20@0s        # CPU set to 20 at 0s (uses default transition)
c80@20s^      # CPU spikes to 80 at 20s, then returns to previous value
c60@30s^+10   # CPU spikes to 60 at 30s, then returns to previous value+10
c40@40s|      # CPU changes immediately to 40 at 40s
```

### Key Concepts

#### 1. Hold Behavior

By default, values now stay at their keyframe setting until changed by another keyframe.

```bash
"c50@10s"  # CPU to 50 at 10s and holds at 50 indefinitely
"c80@30s"  # CPU changes to 80 at 30s and holds at 80
```

#### 2. Transition Types

Control how values change between keyframes:

- **Linear** (default): Steady rate of change
- **Smooth** (`~`): Gradual acceleration/deceleration (cosine interpolation)
- **Step** (`|`): Immediate change

```bash
"c50@10s"    # Linear transition to 50
"c80@20s~"   # Smooth transition to 80
"c20@30s|"   # Step/immediate jump to 20
```

#### 3. Default Transitions

Set the default transition type for a field using just the shorthand:

```bash
"g~"         # Set default GPU transition to smooth
"g20@10s"    # Will use smooth transition (from default)
"g80@20s|"   # Override with step transition
"g40@30s"    # Back to smooth transition (from default)
```

#### 4. Pulse Behavior

Use the `^` symbol to create a "pulse" effect where the value spikes to the target, then returns to the previous value:

```bash
"c20@10s"    # CPU to 20 at 10s
"c80@20s^"   # CPU spikes to 80 at 20s, then returns to 20
```

#### 5. Post-Behavior Modifiers

Control what happens after a pulse:

```bash
"c20@10s"      # CPU to 20 at 10s
"c80@20s^"     # Spike to 80, return to 20
"c60@30s^+10"  # Spike to 60, return to 30 (20+10)
"c50@40s^-5"   # Spike to 50, return to 25 (30-5)
```

#### 6. Combined Behaviors

Combine different transition types with pulse behaviors:

```bash
"c~"           # Set default to smooth
"c20@10s"      # CPU to 20 at 10s
"c80@20s^"     # Smooth transition to 80, then return to 20
"c60@30s|^"    # Step to 60, then return to 20
```

## Field Colors and Visualization

ChronoSynth now has robust support for field-specific colors that are preserved throughout the data pipeline:

### Color Configuration

Colors can be specified in field definitions in two ways:
- Standard color names: "blue", "red", "green", etc.
- Hex color codes: "#FF5733", "#3498DB", etc.

```json
{
  "cpu": {
    "shorthand": "c",
    "min": 0.0,
    "max": 100.0,
    "color": "blue",        // Standard color name
    "noise_amount": 0.2
  },
  "gpu": {
    "shorthand": "g",
    "min": 0.0,
    "max": 100.0,
    "color": "#FF5733",     // Hex color code
    "noise_amount": 0.2
  }
}
```

### Color Persistence

Colors are now automatically saved in all output file formats (JSON, PKL, NPY) and will be loaded correctly by visualization tools:

```bash
# Generate data with colors in config
chronosynth --config-file configs/colored_fields.json --output-file colored_data.json

# Load and visualize the colored data file
python examples/load_and_plot.py colored_data.json --open-browser
```

### Using Colors in HTML Plots

Generate HTML visualizations that use the field colors from your configuration:

```bash
# Generate an HTML plot with color-coded fields
chronosynth --config-file configs/cpu-gpu-ram-vram.json --plot html:open

# Save the plot to a file with colors preserved
chronosynth --config-file configs/cpu-gpu-ram-vram.json --plot colored_plot.html
```

### Enhanced Visualization Features

The HTMLPlotter and standalone viewer now include these enhanced features:

- **Field-specific colors** from configuration files
- **Multi-chart views** to compare multiple datasets
- **Interactive time markers** that follow mouse movement
- **Value callouts** that display precise data values
- **Toggle-able legend** for better chart readability
- **Multiple plot modes** (lines, points, or both)
- **JSON, PKL, and NPY file support**
- **Drag-and-drop** file loading for easy data viewing
- **Downloadable plots** as PNG or SVG for reports

Example color visualization:

```bash
# Generate a color demo
python examples/color_demo.py --open-browser

# Load an existing file that contains color information
python examples/load_and_plot.py output/timeseries_data.json --open-browser
```

## Timeline Masks

Apply functions across the entire timeline to simulate patterns:

```bash
# Apply a sine wave variation
chronosynth --mask "sin(amp=0.3,freq=0.01,offset=1.0)"

# Apply a power function to all values
chronosynth --mask "pow=2"
```

## Data Formats

All data formats include format version and type metadata:

```json
{
  "version": "1.0.0",
  "type": "ts-structured",
  "fields": { ... },
  "timeslots": [ ... ],
  "data": { ... }
}
```

### Structured Format

Compact, with a single array of timestamps and arrays of values for each field:

```json
{
  "version": "1.0.0",
  "type": "ts-structured",
  "fields": {
    "cpu_usage": {
      "shorthand": "c",
      "data_type": "float",
      "min": 0.0,
      "max": 100.0,
      "color": "blue"
    }
  },
  "timeslots": [
    "2023-04-12-14-30-00",
    "2023-04-12-14-30-05"
  ],
  "data": {
    "default": {
      "cpu_usage": [20.0, 22.3]
    }
  }
}
```

### Raw Format

More flexible, allows different timestamps for each field:

```json
{
  "version": "1.0.0",
  "type": "ts-raw",
  "fields": {
    "cpu_usage": {
      "shorthand": "c",
      "data_type": "float",
      "min": 0.0,
      "max": 100.0,
      "mean": 50.0,
      "color": "blue"
    }
  },
  "data": {
    "default": {
      "timeseries": {
        "cpu_usage": {
          "2023-04-12-14-30-00": 20.0,
          "2023-04-12-14-30-05": 22.3
        }
      }
    }
  }
}
```

## Input File Support

ChronoSynth can load existing time series data files and apply modifications to them:

```bash
# First generate some initial data
chronosynth --keyframe "c20@0s" "c80@30s" --output-file initial_data.json

# Then load and modify it with additional keyframes
chronosynth --input-file initial_data.json --keyframe "c95@45s~" --output-file modified_data.json

# Load existing data and apply normalization
chronosynth --input-file initial_data.json --normalize --output-file normalized_data.json

# Load existing data and apply a new mask
chronosynth --input-file initial_data.json --mask "sin(amp=0.2,freq=0.02)" --output-file masked_data.json

# Load existing data and extend the time range
chronosynth --input-file initial_data.json --minutes 60 --keyframe "c30@45s" "c70@55s" --output-file extended_data.json
```

This feature is useful for:
- Creating variations of existing datasets
- Extending or modifying datasets without regenerating them
- Applying different processing options to the same base data
- Building on existing data to create more complex patterns

## Visualization

### Standalone Viewer

Generate a standalone viewer that can load and visualize time series data:

```bash
chronosynth --generate-viewer --viewer-file viewer.html
```

The enhanced HTML viewer now supports field colors, multiple file formats, and interactive features:

```bash
# Generate a standalone viewer for viewing multiple datasets
chronosynth --generate-viewer

# Specify custom viewer file path and open it immediately
chronosynth --generate-viewer --viewer-file custom_viewer.html

# Generate data with custom colors and create a viewer simultaneously
chronosynth --config-file configs/colored_fields.json --keyframe "c20@0s" "c80@30s" "m8000@10s" "m16000@40s" --output-file dataset1.json --generate-viewer --viewer-file dataset1_viewer.html

# Create multiple datasets for comparison, each with different colors
chronosynth --config-file configs/cpu-gpu-ram-vram.json --keyframe "c20@0s" "c80@60s" --output-file baseline.json
chronosynth --config-file configs/custom_colors.json --keyframe "c20@0s" "c90@30s" "c40@60s" --output-file variation1.json
chronosynth --config-file configs/colored_fields.json --keyframe "c20@0s" "c60@15s" "c90@30s" "c60@45s" "c20@60s" --output-file variation2.json
chronosynth --generate-viewer --viewer-file comparison_viewer.html

# Create a standalone viewer with a custom title
chronosynth --generate-viewer --viewer-file custom_title_viewer.html --plot-label "Time Series Data Viewer"

# Generate data in multiple formats to demonstrate support for all file types
chronosynth --config-file configs/colored_fields.json --output-file data.json
chronosynth --config-file configs/colored_fields.json --output-format pkl --output-file data.pkl
chronosynth --config-file configs/colored_fields.json --output-format npy --output-file data.npy
# Then view all these files with the HTML viewer
```

The standalone viewer supports:
- Loading multiple files simultaneously to compare datasets
- Field-specific colors preserved from data files
- Interactive time markers that follow your cursor
- Value callouts that show exact data points
- Drag-and-drop file loading
- JSON, PKL, and NPY file format support
- Single and multi-chart viewing modes
- Customizable plot appearance

### Plot Types

```bash
# Display in terminal using matplotlib
chronosynth --plot cli

# Generate HTML file
chronosynth --plot html

# Generate HTML and open in browser
chronosynth --plot html:open

# Generate ASCII plot (no dependencies)
chronosynth --plot ascii

# Save to specific file formats
chronosynth --plot output/plot.png
chronosynth --plot output/plot.svg
chronosynth --plot output/plot.pdf
```

## Resampling Algorithms

The library includes several algorithms for resampling time series data:

1. **Mean Aggregation**: Averages values within each time bin
2. **Min/Max Preservation**: Keeps both minimum and maximum values for each bin
3. **Linear Interpolation**: Weighted distribution of values across bins
4. **Adaptive Sampling (LTTB)**: Largest-Triangle-Three-Buckets algorithm for downsampling while preserving visual shape

```bash
# Resample using mean aggregation with 60-second intervals
chronosynth --resample mean --resample-interval 60

# Resample using LTTB algorithm to 100 points
chronosynth --resample lttb --resample-points 100
```

## Enhanced Batch Processing

The batch processing system allows you to generate multiple datasets with different configurations in a single command. You can set global parameters that apply to all entries and override them for specific datasets.

### Batch File Format

```
# Each line configures one dataset with its own parameters
--output-file dataset1.json --keyframe "c20@0s" "c80@30m"

# Override global parameters for specific datasets
--output-file dataset2.json --minutes 60 --keyframe "c20@0s" "c80@60m"

# Apply different noise levels
--output-file dataset3.json --noise-scale 1.0 --keyframe "c20@0s" "c80@30m"
```

### Global vs. Local Parameters

The following parameters can be specified both globally and in batch entries:
- `--start-time`
- `--output-dir`
- `--format`
- `--output-format`
- `--minutes`
- `--interval-seconds`
- `--noise-scale`
- `--keyframe`
- `--plot-label`
- `--resample`
- `--resample-interval`
- `--resample-points`

When a parameter is specified both globally and in a batch entry, the batch entry's value takes precedence for that specific dataset.

```bash
# Global settings with batch-specific overrides
chronosynth --batch-file batch_config.txt --minutes 30 --noise-scale 0.5 --output-dir batch_output
```

This makes it easy to create variations of datasets while minimizing repetition in configuration.

## Python API

### TimeSeriesGenerator Methods

```python
# Generate time series with standard values
data = generator.generate(
    minutes=30,
    interval_seconds=5.0,
    keyframes=["c50@10s", "c80@20s~"],
    normalize_input=False  # Set to True to treat values as fractions
)

# Save with/without normalization
generator.save(data, "output.json", normalize=False)  # Set to True to normalize output

# Convert between formats with normalization
raw_data = generator.to_raw_format(data, normalize=True)
structured_data = generator.to_structured_format(data, normalize=True)
```

## Example Usage

Here are some more example usage patterns:

### Field Configuration Example

Here's an example of a field configuration file (`configs/custom_fields.json`):

```json
{
  "cpu": {
    "shorthand": "c",
    "min": 0.0,
    "max": 100.0,
    "color": "#E74C3C",
    "noise_amount": 0.15,
    "unit": "%",
    "description": "CPU Utilization"
  },
  "memory": {
    "shorthand": "m",
    "min": 0.0,
    "max": 32768.0,
    "color": "#3498DB",
    "noise_amount": 0.1,
    "unit": "MB",
    "description": "Memory Usage"
  },
  "gpu": {
    "shorthand": "g",
    "min": 0.0,
    "max": 100.0,
    "color": "#2ECC71",
    "noise_amount": 0.2,
    "unit": "%",
    "description": "GPU Utilization"
  },
  "temperature": {
    "shorthand": "t",
    "min": 20.0,
    "max": 90.0,
    "color": "#F39C12",
    "noise_amount": 0.05,
    "unit": "°C",
    "description": "System Temperature"
  },
  "io": {
    "shorthand": "i",
    "min": 0.0,
    "max": 500.0,
    "color": "#9B59B6",
    "noise_amount": 0.25,
    "unit": "MB/s",
    "description": "I/O Throughput"
  }
}
```

Usage examples:

```bash
# Use a custom field configuration file
chronosynth --config-file configs/custom_fields.json --keyframe "c20@10s" "g80@30s" "t40@0s" "t75@20s" --output-file config_example.json --plot html:open

# Create a server monitoring simulation with custom fields (mixed formats)
chronosynth --config-file configs/custom_fields.json --minutes 30 \
  --keyframe \
    "c~" "m~" "g~" "t~" "i|" \
    "@0s;c20;m8000;g10;t35;i10" \
    "c80@10m" "m24000@12m" \
    "@15m;g90;t65;i400" \
    "@20m;c40;g30" "m18000@22m" \
    "t50@19m" "i150@20m" \
    "@30m;c20;m10000;g10;t40" "i20@25m" \
  --output-file server_simulation.json --plot html:open --plot-label "Server Monitoring Simulation"

# Focus on specific fields from the configuration
chronosynth --config-file configs/custom_fields.json --keyframe "c20@0s" "c80@10m" "c30@20m" "t30@0s" "t70@10m" "t45@20m" --output-file cpu_temp_correlation.json --plot html:open --plot-label "CPU-Temperature Correlation"
```

### Noise Control

```bash
# Adjust the global noise level
chronosynth --noise-scale 0.5 --keyframe "c20@10s" "c80@30s" --output-file low_noise.json
chronosynth --noise-scale 2.0 --keyframe "c20@10s" "c80@30s" --output-file high_noise.json
```

### Time and Duration Control

```bash
# Set specific duration and interval
chronosynth --minutes 5 --interval-seconds 10 --keyframe "c20@1m" "c80@4m" --output-file custom_duration.json

# Set specific start time
chronosynth --start-time "2025-01-01 00:00:00" --keyframe "c20@10s" "c80@30s" --output-file custom_start.json
```

### Complex Example: Server Workload Pattern

```bash
# Generate a realistic server workload pattern
chronosynth --minutes 5 --interval-seconds 1 --keyframe \
"c~" "g~" "m~" \
"c20@0s" "g10@0s" "m5000@0s" \
"c85@30s" "g50@40s" "m12000@45s" \
"c60@60s" "g30@70s" "m10000@65s" \
"g95@90s^" "c70@95s" \
"m18000@120s" \
"c90@150s" "g80@155s" "m25000@160s" \
"c40@180s" "g30@175s" "m22000@185s" \
"c95@210s" "g90@215s" "m28000@220s" \
"c30@250s" "g20@245s" "m15000@260s" \
"c20@290s" "g10@290s" "m5000@295s" \
--output-file workload.json --plot html:open
```

## License

MIT License