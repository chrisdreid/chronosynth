# ChronoSynth Examples

This directory contains examples demonstrating how to use ChronoSynth to generate synthetic time series data.

## Directory Structure

- `configs/`: Configuration files for field definitions
- `batch/`: Batch processing configuration files
- `outputs/`: Directory where example outputs are stored
- `tests_from_readme.py`: Script to test examples from the main README file
- `viewer_server.py`: Interactive viewer server with support for all file formats
- `viewer_example.py`: Example of using the viewer server from Python code

## Running Examples

### Basic Example

```bash
python basic_example.py
```

This demonstrates the basic usage of ChronoSynth with the At-Sign keyframe format. It generates 30 minutes of data with various transitions and keyframes.

### Server Workload Pattern

```bash
python server_workload.py
```

A more complex example that simulates server workload patterns with CPU, GPU, and memory metrics over time.

### Batch Processing

```bash
python batch_processing.py
```

This example demonstrates how to use batch processing to generate multiple datasets in a single run.

### Interactive Viewer Server

#### Setup (Important)

For optimal functionality, run the setup script to download the required JavaScript libraries:

```bash
# Run the setup script to download libraries
python setup_viewer_libs.py
```

This script will download the necessary JavaScript libraries to the `lib` directory:
- **pickletojson.js**: For parsing Python pickle files (.pkl)
- **numjs.min.js**: For handling NumPy array files (.npy)

If you can't run the setup script, the viewer will use built-in fallback implementations with limited functionality. See the `lib/README.md` file for manual setup instructions.

#### Running the Viewer Server

First, generate sample datasets (if none exist yet):

```bash
# Generate sample datasets in the outputs directory
python viewer_example.py
```

To see what files are available for viewing:

```bash
# Show all available files in the outputs directory
python viewer_server.py --show-files
```

Then run the viewer server to visualize your data:

```bash
# Start the viewer server (loads empty viewer)
python viewer_server.py

# View a specific dataset file
python viewer_server.py --file dataset1.json

# View multiple datasets in comparison mode
python viewer_server.py --files dataset1.json dataset2.json dataset3.json

# Set a specific port (default is auto-selected)
python viewer_server.py --port 8000
```

#### How Files Are Located

The viewer server automatically searches for files in these locations (in order):

1. **Exact path as provided** (if it's an absolute path)
2. **Relative to examples directory** (the default root)
3. **In the outputs subdirectory** (`examples/outputs/`)

For example, when you run:
```bash
python viewer_server.py --file dataset1.json
```

The server will search for:
- `./dataset1.json` (current directory)
- `./examples/dataset1.json` (examples directory)
- `./examples/outputs/dataset1.json` (outputs directory)

If you're having trouble loading files, use the `--show-files` option to see what's available.

#### Features

The interactive viewer server provides a web-based interface for visualizing ChronoSynth datasets with support for all file formats (JSON, PKL, NPY). It includes:

- **Full Format Support**: View JSON, PKL, and NPY files (with libraries installed)
- **Live Data Loading**: Load files directly from the browser
- **Drag-and-Drop**: Easily load files by dragging them into the browser
- **Multi-Chart View**: Compare multiple datasets simultaneously
- **Interactive Elements**: Time markers and value callouts for precise data inspection
- **Customization**: Control plot appearance, scaling, and view modes
- **Responsive Design**: Works on various screen sizes

### Viewer API Example

```bash
python viewer_example.py
```

This example demonstrates how to control the viewer server from Python code. It generates sample datasets, starts the viewer server, and loads the datasets for comparison.

## Testing README Examples

To run all examples from the main README file:

```bash
python tests_from_readme.py
```

This script extracts code blocks from the README.md file and runs them to verify they work correctly.

## Custom Examples

Feel free to modify these examples or create your own. The key components to understand are:

1. **Field Configuration**: Define your metrics with min/max values and visual properties
2. **Keyframes**: Use the At-Sign format for time-based organization of events  
3. **Transitions**: Control how values change between keyframes (~, |, etc.)
4. **Output Formats**: Choose between raw and structured formats
5. **Visualization**: Generate CLI, ASCII, or HTML visualizations of your data
6. **Interactive Viewer**: Use the viewer server for real-time data exploration