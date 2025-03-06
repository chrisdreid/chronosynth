# ChronoSynth Viewer

The ChronoSynth Viewer is a self-contained web-based visualization tool for time series data generated with ChronoSynth. It allows you to:

- View data in `.pkl`, `.npy`, and `.json` formats
- Compare multiple data series
- Explore data with interactive zooming and panning 
- Apply different visualizations (lines, points, or both)
- Download plots as PNG or SVG

## Setup

Before using the viewer, you need to set up the JavaScript libraries:

```bash
# Run the setup script
python setup_viewer_libs.py

# If you need to force a re-download of the libraries:
python setup_viewer_libs.py --force
```

This script downloads all necessary JavaScript libraries from CDNs:

- `pickletojson.js` - For parsing Python pickled objects
- `numjs.min.js` - For working with numerical arrays and parsing NumPy .npy files
- `plotly.min.js` - For interactive visualizations
- `dayjs.min.js` - For date/time handling

Having these libraries locally allows the HTML generator to embed them directly into any generated viewer HTML file. This makes each generated viewer completely self-contained and able to work offline in air-gapped environments.

## Running the Test Viewer

To test the viewer with sample data:

```bash
# Generate sample data and create a test viewer
python test_viewer.py

# Open the generated index.html in a web browser
xdg-open outputs/index.html  # Linux
open outputs/index.html      # macOS
# On Windows, simply double-click the file
```

The test viewer generates:
- Sample data files in multiple formats
- An embedded viewer HTML file
- An index.html file to navigate between the sample files

## Creating a Viewer Package

To create a self-contained viewer package that can be shared with others:

```bash
# Create a viewer package with sample data
python create_viewer_package.py --output-dir my_viewer_package

# Create a viewer package without sample data
python create_viewer_package.py --output-dir my_viewer_package --no-samples
```

The viewer package contains:
- A self-contained viewer HTML file (viewer.html)
- An index.html file for easy navigation
- Sample data files (optional)

This package can be distributed to users who want to view time series data without installing ChronoSynth.

## Using the Viewer

The viewer supports several ways to load data:

1. Pass a file parameter in the URL:
   ```
   viewer.html?filepath=my_data.pkl
   ```

2. Drag and drop files onto the viewer 

3. Use the file selector button in the viewer

Once data is loaded, you can:
- Toggle between line, point, and combined visualizations
- Switch between linear and logarithmic Y scale
- Change time display format
- Show/hide the legend
- Reset zoom
- Download the plot as PNG or SVG
- Toggle between single and multi-view modes

## JavaScript Libraries

The viewer embeds these JavaScript libraries directly in the HTML:

| Library | Source | Purpose |
|---------|--------|---------|
| pickletojson.js | [pickleparser](https://github.com/bfolder/pickleparser) | Parse Python pickle files |
| numjs.min.js | [NumJs](https://github.com/nicolaspanel/numjs) | Array manipulation and parsing NumPy .npy files |
| plotly.min.js | [Plotly.js](https://plotly.com/javascript/) | Interactive data visualization |
| dayjs.min.js | [DayJS](https://day.js.org/) | Date manipulation and formatting |

All these libraries are downloaded once by the `setup_viewer_libs.py` script to the `lib/` directory and then embedded directly into any generated HTML viewer files. This means:

1. The libraries only need to be downloaded once
2. Each generated HTML viewer is completely self-contained
3. Viewers can be distributed and used without any internet connection
4. No additional JavaScript files need to be included alongside the HTML

## Browser Compatibility

The viewer works best in modern browsers:
- Chrome/Chromium-based browsers (recommended)
- Firefox
- Safari
- Edge

When viewing locally (file:// URLs), some browsers may have security restrictions that prevent loading local data files. In these cases, it's recommended to use a simple HTTP server or drag-and-drop files directly.