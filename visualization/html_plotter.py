"""HTML output for ChronoSynth."""

import json
import os
import base64
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime


class HTMLPlotter:
    """HTML-based plotting for time series data."""
    
    @staticmethod
    def generate_html(data: Dict[str, Any], title: Optional[str] = None, 
                    field_config: Optional[Dict[str, Dict[str, Any]]] = None,
                    output_file: str = "timeseries_plot.html",
                    open_browser: bool = False) -> bool:
        """
        Generate an HTML file with an interactive plot.
        
        Args:
            data: Internal data structure
            title: Plot title
            field_config: Field configuration dictionary
            output_file: Output file path
            open_browser: Whether to open the browser after generating the HTML
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        if not data or "timestamps" not in data or "items" not in data:
            print("Invalid data structure for plotting.")
            return False
        
        # Use field_config if provided, otherwise use data["fields"]
        if field_config is None and "fields" in data:
            # Extract field config from data
            field_config = {}
            for field, field_data in data["fields"].items():
                if "config" in field_data:
                    field_config[field] = field_data["config"]
        
        # Create standalone HTML file with embedded data
        try:
            # Convert data to a JSON string
            plot_data = {
                "timestamps": [ts.isoformat() if isinstance(ts, datetime) else ts for ts in data["timestamps"]],
                "items": {}
            }
            
            # Add items data
            for item_name, item_data in data["items"].items():
                plot_data["items"][item_name] = {}
                for field, values in item_data.items():
                    if not field_config or field in field_config:
                        plot_data["items"][item_name][field] = values
            
            # Embed data and field config
            field_config_json = json.dumps(field_config) if field_config else "{}"
            plot_data_json = json.dumps(plot_data)
            
            # Create HTML content with embedded viewer
            html_content = HTMLPlotter._generate_viewer_html(title or "Time Series Data", field_config_json, plot_data_json)
                
            # Write to file
            with open(output_file, "w") as f:
                f.write(html_content)
            
            print(f"HTML plot saved to: {output_file}")
            
            # Open browser if requested
            if open_browser:
                import webbrowser
                webbrowser.open('file://' + os.path.abspath(output_file))
            
            return True
            
        except Exception as e:
            print(f"Error generating HTML file: {e}")
            return False
    
    @staticmethod
    def generate_viewer(output_file: str = "timeseries_viewer.html") -> bool:
        """
        Generate a standalone viewer HTML file that can load data from external files.
        
        Args:
            output_file: Output file path
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            # Create HTML content
            html_content = HTMLPlotter._generate_viewer_html("TimeSeriesData Viewer", "{}", "{}")
            
            # Write to file
            with open(output_file, "w") as f:
                f.write(html_content)
            
            print(f"TimeSeriesData viewer saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error generating viewer file: {e}")
            return False
    
    @staticmethod
    def _generate_viewer_html(title: str, field_config_json: str, plot_data_json: str) -> str:
        """
        Generate HTML content for the viewer.
        
        Args:
            title: Plot title
            field_config_json: Field configuration as JSON string
            plot_data_json: Plot data as JSON string
            
        Returns:
            HTML content
        """
        # Read the JS libraries and embed them directly
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        base_dir = os.path.dirname(script_dir)
        
        # Load the JS libraries
        try:
            with open(os.path.join(base_dir, "lib", "pickletojson.js"), "r") as f:
                pickle_js = f.read()
            
            with open(os.path.join(base_dir, "lib", "numjs.min.js"), "r") as f:
                numjs_js = f.read()
        except Exception as e:
            print(f"Warning: Could not load JS libraries: {e}")
            pickle_js = ""
            numjs_js = ""
        
        # Basic HTML template with embedded JavaScript for loading and displaying time series data
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/dayjs@1.10.4/dayjs.min.js"></script>
    <!-- Embedded pickleparser for .pkl files -->
    <script>
    {pickle_js}
    </script>
    <!-- Embedded numjs for .npy files -->
    <script>
    {numjs_js}
    </script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #1e1e1e;
            color: white;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            text-align: center;
        }}
        .chart-container {{
            width: 100%;
            height: 600px;
            margin: 20px 0;
            background-color: #222;
            border-radius: 5px;
            position: relative;
        }}
        .controls {{
            margin: 20px 0;
            padding: 10px;
            background-color: #333;
            border-radius: 5px;
            position: relative;
        }}
        .controls select, .controls button, .controls input {{
            background-color: #444;
            color: white;
            border: 1px solid #555;
            padding: 3px;
            margin: 5px;
            border-radius: 3px;
            font-size: 12px;
        }}
        .controls button {{
            cursor: pointer;
        }}
        .controls button:hover {{
            background-color: #555;
        }}
        .file-input {{
            display: none;
        }}
        .file-input-label {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: auto;
            background-color: #444;
            color: white;
            padding: 8px 15px;
            margin: 5px;
            border-radius: 3px;
            cursor: pointer;
        }}
        .drop-overlay {{
            display: none;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(76, 175, 80, 0.1);
            border: 2px dashed #4CAF50;
            border-radius: 5px;
            z-index: 100;
            pointer-events: none;
            justify-content: center;
            align-items: center;
        }}
        .drop-overlay-text {{
            background-color: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            font-size: 16px;
        }}
        .field-selector {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
        }}
        .field-checkbox {{
            display: flex;
            align-items: center;
            gap: 5px;
            background-color: #444;
            padding: 5px 10px;
            border-radius: 15px;
        }}
        .field-checkbox input {{
            margin: 0;
        }}
        .color-indicator {{
            width: 15px;
            height: 15px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
        }}
        .multi-chart-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .chart-wrapper {{
            flex: 1 1 100%;
            min-width: 400px;
            position: relative;
        }}
        .chart-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        .chart-title {{
            font-size: 16px;
            font-weight: bold;
            margin: 0;
        }}
        .chart-close {{
            cursor: pointer;
            background: none;
            border: none;
            color: #ff5555;
            font-size: 20px;
        }}
        @media (min-width: 1200px) {{
            .chart-wrapper {{
                flex: 1 1 calc(50% - 20px);
            }}
        }}
        .log {{
            font-family: monospace;
            padding: 10px;
            background-color: #333;
            border-radius: 5px;
            max-height: 100px;
            overflow-y: auto;
            margin-top: 10px;
        }}
        /* Time marker styles */
        .time-marker {{
            position: absolute;
            top: 0;
            height: 100%;
            width: 1px;
            background-color: rgba(255, 255, 255, 0.2);
            z-index: 50;
            pointer-events: none;
            display: none;
        }}
        .y-marker {{
            position: absolute;
            left: 0;
            width: 100%;
            height: 1px;
            background-color: rgba(255, 255, 255, 0.2);
            z-index: 50;
            pointer-events: none;
            display: none;
        }}
        .x-callout {{
            position: absolute;
            top: 0px; /* Position above the chart */
            background-color: rgba(0, 0, 0, 0.7);
            color: rgba(255, 255, 255, 0.9);
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            z-index: 100;
            pointer-events: none; /* Prevent interference with mouse events */
        }}
        .y-callout {{
            position: absolute;
            left: -0px; /* Position to the left of the chart */
            background-color: rgba(0, 0, 0, 0.7);
            color: rgba(255, 255, 255, 0.9);
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 12px;
            z-index: 100;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 id="plot-title">{title}</h1>
        
        <div class="controls">
            <div>
                <label class="file-input-label">
                    Load Data File
                    <input type="file" id="data-file-input" class="file-input" accept=".json,.pkl,.npy" multiple>
                </label>
                <select id="plot-type">
                    <option value="lines">Lines</option>
                    <option value="markers">Points</option>
                    <option value="lines+markers">Lines + Points</option>
                </select>
                <select id="y-scale">
                    <option value="linear">Linear Scale</option>
                    <option value="log">Log Scale</option>
                </select>
                <select id="x-tick-format">
                    <option value="local">Local Time (HH:MM:SS)</option>
                    <option value="absolute">Absolute Time (HH:MM:SS)</option>
                    <option value="relative">Relative Time (D:HH:MM:SS:MS)</option>
                    <option value="timecode">Timecode (HH:MM:SS:FF)</option>
                </select>
                <button id="toggle-legend">Toggle Legend</button>
                <button id="reset-zoom">Reset Zoom</button>
                <button id="download-png">Download PNG</button>
                <button id="download-svg">Download SVG</button>
                <button id="view-all">View All Charts</button>
            </div>
            <div id="drop-overlay" class="drop-overlay">
                <div class="drop-overlay-text">Drop Files Here</div>
            </div>
            <div id="field-selector" class="field-selector"></div>
        </div>
        
        <div id="main-chart-container">
            <div id="chart" class="chart-container">
                <div id="time-marker" class="time-marker"></div>
                <div id="y-marker" class="y-marker"></div>
                <div id="x-callout" class="x-callout">X: --</div>
                <div id="y-callout" class="y-callout">Y: --</div>
            </div>
        </div>
        
        <div id="multi-chart-container" class="multi-chart-container" style="display: none;"></div>
        
        <div id="log" class="log">Ready to load data...</div>
    </div>

    <script>
        let fieldConfig = {field_config_json};
        let plotData = {plot_data_json};
        let chartData = [];
        let multiChartData = {{}};
        let plotTitle = "{title}";
        let legendVisible = true;
        let plotType = "lines";
        let yScale = "linear";
        let fieldVisibility = {{}};
        let viewMode = "single";
        let currentPlot = null;
        let xTickFormat = "local";
        
        document.addEventListener('DOMContentLoaded', function() {{
            function updatePlotType(e) {{
                plotType = e.target.value;
                chartData.forEach(trace => trace.mode = plotType);
                updatePlot();
                if (viewMode === 'multi') updateMultiChartView();
            }}

            document.getElementById('plot-type').addEventListener('change', updatePlotType);
            document.getElementById('y-scale').addEventListener('change', updateYScale);
            document.getElementById('x-tick-format').addEventListener('change', function(e) {{
                xTickFormat = e.target.value;
                updatePlot();
                if (viewMode === 'multi') updateMultiChartView();
            }});
            document.getElementById('toggle-legend').addEventListener('click', toggleLegend);
            document.getElementById('reset-zoom').addEventListener('click', resetZoom);
            document.getElementById('data-file-input').addEventListener('change', handleFileUpload);
            document.getElementById('download-png').addEventListener('click', () => downloadPlot('png'));
            document.getElementById('download-svg').addEventListener('click', () => downloadPlot('svg'));
            document.getElementById('view-all').addEventListener('click', toggleViewMode);
            
            const dropOverlay = document.getElementById('drop-overlay');
            document.addEventListener('dragover', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                dropOverlay.style.display = 'flex';
            }});
            
            document.addEventListener('dragleave', function(e) {{
                e.preventDefault();
                if (e.clientX <= 0 || e.clientY <= 0 || 
                    e.clientX >= window.innerWidth || e.clientY >= window.innerHeight) {{
                    dropOverlay.style.display = 'none';
                }}
            }});
            
            document.addEventListener('drop', function(e) {{
                e.preventDefault();
                e.stopPropagation();
                dropOverlay.style.display = 'none';
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {{
                    handleFiles(e.dataTransfer.files);
                }}
            }});
            
            if (plotData && plotData.timestamps && plotData.timestamps.length > 0) {{
                processTimeSeriesData(plotData, fieldConfig);
            }}
            
            checkUrlParameters();
        }});
        
        function checkUrlParameters() {{
            const urlParams = new URLSearchParams(window.location.search);
            const filepath = urlParams.get('filepath');
            if (filepath) {{
                log(`Loading file from URL: ${{filepath}}`);
                
                // Handle both absolute and relative paths
                // If path starts with file:// or /, treat as absolute path (which may fail with CORS)
                // Otherwise, treat as relative path from the current page
                let url = filepath;
                if (!url.startsWith('file://') && !url.startsWith('http://') && !url.startsWith('https://')) {{
                    // If it's a relative path, make it relative to the current page
                    // This avoids CORS issues when running locally
                    if (url.startsWith('/')) {{
                        url = url.substring(1); // Remove leading slash
                    }}
                    
                    // Get the current directory path from the current URL
                    const currentPath = window.location.pathname;
                    const currentDir = currentPath.substring(0, currentPath.lastIndexOf('/') + 1);
                    
                    // Combine with the current directory path
                    url = window.location.origin + currentDir + url;
                    log(`Resolved to relative URL: ${{url}}`);
                }}
                
                fetchFileFromUrl(url);
            }}
        }}
        
        function fetchFileFromUrl(url) {{
            // For local files, add cache-busting query parameter to avoid caching issues
            const fetchUrl = url.startsWith('http') ? url : url + '?_=' + new Date().getTime();
            
            fetch(fetchUrl)
                .then(response => {{
                    if (!response.ok) throw new Error(`Network response was not ok: ${{response.status}}`);
                    // Check content type
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {{
                        return response.text();
                    }} else if (url.endsWith('.pkl') || url.endsWith('.npy')) {{
                        // For binary files
                        return response.arrayBuffer();
                    }} else {{
                        // Default to text
                        return response.text();
                    }}
                }})
                .then(content => {{
                    const filename = url.split('/').pop().split('?')[0]; // Remove query params
                    
                    if (typeof content === 'string') {{
                        try {{
                            // Try to parse as JSON
                            processJsonContent(content, filename);
                        }} catch (e) {{
                            log(`Error processing content as JSON: ${{e.message}}`);
                        }}
                    }} else if (content instanceof ArrayBuffer) {{
                        // Process as binary file
                        const extension = filename.split('.').pop().toLowerCase();
                        if (extension === 'pkl') {{
                            loadPklFile(filename, content);
                        }} else if (extension === 'npy') {{
                            loadNpyFile(filename, content);
                        }} else {{
                            log(`Unsupported binary file extension: ${{extension}}`);
                        }}
                    }}
                }})
                .catch(error => log(`Error fetching file: ${{error.message}}`));
        }}
        
        function processJsonContent(content, fileName) {{
            try {{
                const jsonData = JSON.parse(content);
                if (!jsonData.type && !jsonData.fields && !jsonData.data && typeof jsonData === 'object') {{
                    let hasRecognizedFormat = false;
                    for (const machineName in jsonData) {{
                        const machineData = jsonData[machineName];
                        if (machineData.type === 'ts-raw' || machineData.type === 'ts-structured') {{
                            hasRecognizedFormat = true;
                            log(`Found machine data: ${{machineName}} (${{machineData.type}})`);
                            let timeseriesData = {{ timestamps: [], items: {{}} }};
                            if (machineData.type === 'ts-raw') processRawFormat(machineData, timeseriesData);
                            else processStructuredFormat(machineData, timeseriesData);
                            const chartName = `${{fileName}} - ${{machineName}}`;
                            multiChartData[chartName] = {{ data: timeseriesData, config: machineData.fields || {{}} }};
                            if (Object.keys(chartData).length === 0) {{
                                plotTitle = chartName;
                                document.getElementById('plot-title').textContent = plotTitle;
                                processTimeSeriesData(timeseriesData, machineData.fields || {{}});
                            }}
                        }}
                    }}
                    if (hasRecognizedFormat && Object.keys(multiChartData).length > 1) {{
                        viewMode = 'multi';
                        document.getElementById('main-chart-container').style.display = 'none';
                        document.getElementById('multi-chart-container').style.display = 'flex';
                        document.getElementById('view-all').textContent = 'View Single Chart';
                        updateMultiChartView();
                    }}
                    return;
                }}
                if (jsonData.type === 'ts-raw' || jsonData.type === 'ts-structured') {{
                    log(`Loading ${{jsonData.type}} data from ${{fileName}}...`);
                    let timeseriesData = {{ timestamps: [], items: {{}} }};
                    if (jsonData.type === 'ts-raw') processRawFormat(jsonData, timeseriesData);
                    else processStructuredFormat(jsonData, timeseriesData);
                    plotTitle = `${{fileName}} (${{jsonData.type}})`;
                    document.getElementById('plot-title').textContent = plotTitle;
                    multiChartData[fileName] = {{ data: timeseriesData, config: jsonData.fields || {{}} }};
                    processTimeSeriesData(timeseriesData, jsonData.fields || {{}});
                    if (viewMode === 'multi') updateMultiChartView();
                }} else {{
                    log('JSON format not recognized.');
                }}
            }} catch (error) {{
                log(`Error parsing JSON: ${{error.message}}`);
            }}
        }}
        
        function handleFiles(files) {{
            chartData = [];
            fieldVisibility = {{}};
            document.getElementById('field-selector').innerHTML = '';
            for (let i = 0; i < files.length; i++) {{
                const file = files[i];
                if (!file) continue;
                const fileExt = file.name.split('.').pop().toLowerCase();
                
                if (fileExt === 'json') {{
                    const reader = new FileReader();
                    reader.onload = function(e) {{
                        processJsonContent(e.target.result, file.name);
                    }};
                    reader.onerror = function() {{ 
                        log(`Error reading file: ${{file.name}}`); 
                    }};
                    reader.readAsText(file);
                }} else if (fileExt === 'pkl' || fileExt === 'npy') {{
                    handleBinaryFile(file);
                }} else {{
                    log(`Unsupported file format: ${{fileExt}}`);
                }}
            }}
        }}
        
        function handleFileUpload(event) {{
            if (event.target.files && event.target.files.length > 0) handleFiles(event.target.files);
        }}
        
        function handleBinaryFile(file) {{
            log(`Loading binary file: ${{file.name}}`);
            const fileExt = file.name.split('.').pop().toLowerCase();
            const reader = new FileReader();
            
            reader.onload = function(e) {{
                const arrayBuffer = e.target.result;
                try {{
                    if (fileExt === 'npy') {{
                        loadNpyFile(file.name, arrayBuffer);
                    }} else if (fileExt === 'pkl') {{
                        loadPklFile(file.name, arrayBuffer);
                    }} else {{
                        log(`Unsupported binary format: ${{fileExt}}`);
                    }}
                }} catch (error) {{
                    log(`Error processing ${{fileExt.toUpperCase()}} file: ${{error.message}}`);
                }}
            }};
            
            reader.onerror = function() {{
                log(`Error reading binary file: ${{file.name}}`);
            }};
            
            reader.readAsArrayBuffer(file);
        }}
        
        async function loadNpyFile(filename, arrayBuffer) {{
            try {{
                const uint8Array = new Uint8Array(arrayBuffer);
                
                const magic = String.fromCharCode.apply(null, uint8Array.slice(0, 6));
                if (magic !== '\x93NUMPY') {{
                    throw new Error('Invalid NPY file: magic string not found');
                }}
                
                const versionMajor = uint8Array[6];
                const versionMinor = uint8Array[7];
                let headerLength;
                if (versionMajor >= 2) {{
                    headerLength = new DataView(arrayBuffer).getUint32(8, true);
                }} else {{
                    headerLength = new DataView(arrayBuffer).getUint16(8, true);
                }}
                
                const headerStart = versionMajor >= 2 ? 12 : 10;
                const headerBytes = uint8Array.slice(headerStart, headerStart + headerLength);
                const headerStr = new TextDecoder().decode(headerBytes);
                
                const dtypeMatch = headerStr.match(/'descr':\s*['"]([^'"]+)['"]/);
                const fortranMatch = headerStr.match(/'fortran_order':\s*(True|False)/i);
                const shapeMatch = headerStr.match(/'shape':\s*\(([^)]*)\)/);
                
                if (!dtypeMatch || !fortranMatch || !shapeMatch) {{
                    throw new Error('Invalid NPY header format - missing required fields');
                }}
                
                const dtype = dtypeMatch[1];
                const fortranOrder = fortranMatch[1].toLowerCase() === 'true';
                let shapeStr = shapeMatch[1].replace(/\s/g, '');
                const shape = shapeStr ? shapeStr.split(',').map(s => s ? parseInt(s) : 1).filter(n => !isNaN(n)) : [];
                
                const dataStart = headerStart + headerLength;
                const dataBytes = uint8Array.slice(dataStart);
                
                let timeseriesData = {{ timestamps: [], items: {{ "default": {{}} }} }};
                let fieldConfig = {{}};
                
                if (dtype === '|O') {{
                    const parser = new pickleparser.Parser();
                    const pickledData = parser.parse(dataBytes);
                    
                    let rawOrStructuredData = null;
                    if (typeof pickledData === 'object' && pickledData !== null) {{
                        if (Array.isArray(pickledData["4"]) && pickledData["4"].length > 0) {{
                            const dataType = pickledData["4"][0].type;
                            if (dataType === 'ts-raw' || dataType === 'ts-structured') {{
                                rawOrStructuredData = pickledData["4"][0];
                            }}
                        }}
                        if (!rawOrStructuredData) {{
                            for (const key in pickledData) {{
                                if (Array.isArray(pickledData[key]) && pickledData[key].length > 0) {{
                                    const dataType = pickledData[key][0].type;
                                    if (dataType === 'ts-raw' || dataType === 'ts-structured') {{
                                        rawOrStructuredData = pickledData[key][0];
                                        break;
                                    }}
                                }}
                            }}
                        }}
                    }}
                    
                    if (rawOrStructuredData) {{
                        fieldConfig = rawOrStructuredData.fields || {{}};
                        if (rawOrStructuredData.type === 'ts-raw') {{
                            processRawFormat(rawOrStructuredData, timeseriesData);
                        }} else if (rawOrStructuredData.type === 'ts-structured') {{
                            processStructuredFormat(rawOrStructuredData, timeseriesData);
                        }}
                    }} else if (Array.isArray(pickledData)) {{
                        const length = pickledData.length;
                        const now = new Date();
                        for (let i = 0; i < length; i++) {{
                            timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                        }}
                        if (typeof pickledData[0] === 'number') {{
                            timeseriesData.items.default.value = pickledData;
                            fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                        }} else if (Array.isArray(pickledData[0])) {{
                            const cols = pickledData[0].length;
                            for (let j = 0; j < cols; j++) {{
                                const fieldName = `field${{j+1}}`;
                                const fieldValues = pickledData.map(row => row[j]);
                                timeseriesData.items.default[fieldName] = fieldValues;
                                fieldConfig[fieldName] = {{
                                    color: getRandomColor(fieldName),
                                    label: `Field ${{j+1}}`
                                }};
                            }}
                        }} else {{
                            timeseriesData.items.default.value = pickledData.map(item => item !== null ? item.toString() : null);
                            fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                        }}
                    }} else if (typeof pickledData === 'object' && pickledData !== null) {{
                        let maxLength = 0;
                        let hasNumeric = false;
                        for (const key in pickledData) {{
                            if (Array.isArray(pickledData[key]) && typeof pickledData[key][0] === 'number') {{
                                timeseriesData.items.default[key] = pickledData[key];
                                fieldConfig[key] = {{
                                    color: getRandomColor(key),
                                    label: key
                                }};
                                maxLength = Math.max(maxLength, pickledData[key].length);
                                hasNumeric = true;
                            }}
                        }}
                        if (!hasNumeric) {{
                            const values = Object.values(pickledData).map(val => val !== null ? val.toString() : null);
                            timeseriesData.items.default.value = values;
                            fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                            const now = new Date();
                            for (let i = 0; i < values.length; i++) {{
                                timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                            }}
                        }} else {{
                            const now = new Date();
                            for (let i = 0; i < maxLength; i++) {{
                                timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                            }}
                        }}
                    }} else {{
                        const now = new Date();
                        timeseriesData.timestamps.push(now.toISOString());
                        timeseriesData.items.default.value = [pickledData !== null ? pickledData.toString() : null];
                        fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                    }}
                }} else {{
                    const floatArray = new Float32Array(dataBytes.buffer, dataBytes.byteOffset, dataBytes.length / 4);
                    const now = new Date();
                    if (shape.length === 0) {{
                        timeseriesData.timestamps.push(now.toISOString());
                        timeseriesData.items.default.value = [floatArray[0]];
                        fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                    }} else if (shape.length === 1) {{
                        for (let i = 0; i < shape[0]; i++) {{
                            timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                        }}
                        timeseriesData.items.default.value = Array.from(floatArray);
                        fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                    }} else {{
                        return;
                    }}
                }}
                
                if (timeseriesData.timestamps.length === 0 || 
                    Object.keys(timeseriesData.items.default).length === 0) {{
                    return;
                }}
                
                plotTitle = `${{filename}} (NPY)`;
                document.getElementById('plot-title').textContent = plotTitle;
                multiChartData[filename] = {{ data: timeseriesData, config: fieldConfig }};
                
                processTimeSeriesData(timeseriesData, fieldConfig);
                
                if (viewMode === 'multi') {{
                    updateMultiChartView();
                }}
                
            }} catch (error) {{
                log(`Error processing NPY file: ${{error.message}}`);
            }}
        }}

        function loadPklFile(filename, arrayBuffer) {{
            try {{
                const uint8Array = new Uint8Array(arrayBuffer);
                const parser = new pickleparser.Parser(); // Using the Parser from pickletojson.js
                const pklData = parser.parse(uint8Array);
                log(`PKL file loaded successfully`);
                
                let timeseriesData = {{ timestamps: [], items: {{ "default": {{}} }} }};
                let fieldConfig = {{}};
                
                if (pklData.type === 'ts-raw' || pklData.type === 'ts-structured') {{
                    if (pklData.type === 'ts-raw') {{
                        processRawFormat(pklData, timeseriesData);
                    }} else {{
                        processStructuredFormat(pklData, timeseriesData);
                    }}
                    fieldConfig = pklData.fields || {{}};
                }} else if (Array.isArray(pklData)) {{
                    const now = new Date();
                    for (let i = 0; i < pklData.length; i++) {{
                        timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                    }}
                    
                    if (typeof pklData[0] === 'number') {{
                        timeseriesData.items.default.value = pklData;
                        fieldConfig.value = {{ color: "#1f77b4", label: "Value" }};
                    }} else if (Array.isArray(pklData[0])) {{
                        const numFields = pklData[0].length;
                        for (let j = 0; j < numFields; j++) {{
                            const fieldName = `field${{j+1}}`;
                            timeseriesData.items.default[fieldName] = pklData.map(row => row[j]);
                            fieldConfig[fieldName] = {{
                                color: getRandomColor(fieldName),
                                label: `Field ${{j+1}}`
                            }};
                        }}
                    }}
                }} else if (typeof pklData === 'object') {{
                    const now = new Date();
                    let maxLength = 0;
                    for (const key in pklData) {{
                        if (Array.isArray(pklData[key]) && typeof pklData[key][0] === 'number') {{
                            timeseriesData.items.default[key] = pklData[key];
                            fieldConfig[key] = {{
                                color: getRandomColor(key),
                                label: key
                            }};
                            maxLength = Math.max(maxLength, pklData[key].length);
                        }}
                    }}
                    for (let i = 0; i < maxLength; i++) {{
                        timeseriesData.timestamps.push(new Date(now.getTime() + i * 1000).toISOString());
                    }}
                }}
                
                if (timeseriesData.timestamps.length > 0 && Object.keys(timeseriesData.items.default).length > 0) {{
                    plotTitle = `${{filename}} (PKL)`;
                    document.getElementById('plot-title').textContent = plotTitle;
                    multiChartData[filename] = {{ data: timeseriesData, config: fieldConfig }};
                    processTimeSeriesData(timeseriesData, fieldConfig);
                    if (viewMode === 'multi') updateMultiChartView();
                }} else {{
                    log('No valid time series data found in PKL file');
                }}
                
            }} catch (error) {{
                log(`Error parsing PKL file: ${{error.message}}`);
            }}
        }}
        
        function toggleViewMode() {{
            viewMode = viewMode === 'single' ? 'multi' : 'single';
            if (viewMode === 'single') {{
                document.getElementById('main-chart-container').style.display = 'block';
                document.getElementById('multi-chart-container').style.display = 'none';
                document.getElementById('view-all').textContent = 'View All Charts';
                if (chartData.length > 0) updatePlot();
            }} else {{
                document.getElementById('main-chart-container').style.display = 'none';
                document.getElementById('multi-chart-container').style.display = 'flex';
                document.getElementById('view-all').textContent = 'View Single Chart';
                updateMultiChartView();
            }}
        }}
        
        function formatDuration(seconds) {{
            const days = Math.floor(seconds / 86400);
            const hours = Math.floor((seconds % 86400) / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = Math.floor(seconds % 60);
            if (days > 0) return `${{days}}d ${{hours}}h`;
            if (hours > 0) return `${{hours}}h ${{minutes}}m`;
            if (minutes > 0) return `${{minutes}}m ${{secs}}s`;
            return `${{secs}}s`;
        }}

        function getAdaptiveTicks(timestamps, plotWidth) {{
            if (!timestamps || timestamps.length === 0) return {{ tickvals: [], ticktext: [] }};
            
            let startTime, endTime;
            try {{
                startTime = new Date(timestamps[0]).getTime();
                endTime = new Date(timestamps[timestamps.length - 1]).getTime();
            }} catch (e) {{
                console.log('Error parsing timestamps:', e);
                return {{ tickvals: [], ticktext: [] }};
            }}
            
            const durationMs = endTime - startTime;
            const durationSec = durationMs / 1000;
            
            // Estimate pixels per tick (aim for ~100-200px between major ticks)
            const maxTicks = Math.floor(plotWidth / 50);
            const minTickIntervalSec = durationSec / maxTicks;

            // Define possible intervals (in seconds)
            const intervals = [
                1, 5, 10, 30,      // seconds
                60, 300, 600,      // minutes
                3600, 7200,        // hours
                86400, 172800      // days
            ];

            // Find appropriate major interval
            let majorIntervalSec = intervals.find(i => i >= minTickIntervalSec) || intervals[intervals.length - 1];
            
            const tickvals = [];
            const ticktext = [];
            
            if (xTickFormat === 'relative') {{
                for (let t = 0; t <= durationMs; t += majorIntervalSec * 1000) {{
                    tickvals.push(new Date(startTime + t));
                    ticktext.push(formatTick(t, xTickFormat));
                }}
            }} else {{
                for (let t = startTime; t <= endTime; t += majorIntervalSec * 1000) {{
                    tickvals.push(new Date(t));
                    ticktext.push(formatTick(t - startTime, xTickFormat));
                }}
            }}

            return {{ tickvals, ticktext }};
        }}

        function formatTick(ms, format) {{
            const date = new Date(ms);
            const baseTime = chartData[0]?.x[0] ? new Date(chartData[0].x[0]).getTime() : 0;
            const absoluteTime = new Date(baseTime + ms);
            const days = Math.floor(ms / 86400000);
            const hours = Math.floor((ms % 86400000) / 3600000);
            const minutes = Math.floor((ms % 3600000) / 60000);
            const seconds = Math.floor((ms % 60000) / 1000);
            const millis = Math.floor(ms % 1000);
            const frames = Math.floor((ms % 1000) / 40); // Assuming 25fps

            switch (format) {{
                case 'local':
                    return absoluteTime.toLocaleTimeString('en-US', {{ hour12: false }});
                case 'absolute':
                    return new Date(absoluteTime.getTime() + absoluteTime.getTimezoneOffset() * 60000)
                        .toLocaleTimeString('en-US', {{ hour12: false }});
                case 'relative':
                    return `${{days}}:${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}.${{millis.toString().padStart(3, '0')}}`;
                case 'timecode':
                    return `${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}:${{frames.toString().padStart(2, '0')}}`;
            }}
        }}

        function updateMultiChartView() {{
            const container = document.getElementById('multi-chart-container');
            container.innerHTML = '';
            for (const filename in multiChartData) {{
                createChartForFile(filename, multiChartData[filename], container);
            }}
        }}
        
        function createChartForFile(filename, fileData, container) {{
            const wrapper = document.createElement('div');
            wrapper.className = 'chart-wrapper';
            wrapper.id = `chart-wrapper-${{filename.replace(/\\W/g, '')}}`;
            
            const header = document.createElement('div');
            header.className = 'chart-header';
            const title = document.createElement('h3');
            title.className = 'chart-title';
            title.textContent = filename;
            const closeBtn = document.createElement('button');
            closeBtn.className = 'chart-close';
            closeBtn.innerHTML = '×';
            closeBtn.onclick = function() {{ removeChart(filename); }};
            header.appendChild(title);
            header.appendChild(closeBtn);
            
            const chartDiv = document.createElement('div');
            chartDiv.className = 'chart-container';
            chartDiv.id = `chart-${{filename.replace(/\\W/g, '')}}`;
            
            const timeMarker = document.createElement('div');
            timeMarker.className = 'time-marker';
            timeMarker.id = `time-marker-${{filename.replace(/\\W/g, '')}}`;
            
            const yMarker = document.createElement('div');
            yMarker.className = 'y-marker';
            yMarker.id = `y-marker-${{filename.replace(/\\W/g, '')}}`;
            
            const xCallout = document.createElement('div');
            xCallout.className = 'x-callout';
            xCallout.id = `x-callout-${{filename.replace(/\\W/g, '')}}`;
            xCallout.textContent = 'X: --';
            
            const yCallout = document.createElement('div');
            yCallout.className = 'y-callout';
            yCallout.id = `y-callout-${{filename.replace(/\\W/g, '')}}`;
            yCallout.textContent = 'Y: --';
            
            chartDiv.appendChild(timeMarker);
            chartDiv.appendChild(yMarker);
            chartDiv.appendChild(xCallout);
            chartDiv.appendChild(yCallout);
            
            wrapper.appendChild(header);
            wrapper.appendChild(chartDiv);
            container.appendChild(wrapper);
            
            const chartTraces = [];
            for (const itemName in fileData.data.items) {{
                for (const fieldName in fileData.data.items[itemName]) {{
                    if (!fileData.config[fieldName]) continue;
                    // Prioritize color from field config if provided
                    let color;
                    if (fileData.config[fieldName] && typeof fileData.config[fieldName].color !== 'undefined') {{
                        color = fileData.config[fieldName].color;
                    }} else {{
                        color = getRandomColor(fieldName);
                    }}
                    const label = `${{fieldName}} (${{itemName}})`;
                    chartTraces.push({{
                        x: fileData.data.timestamps,
                        y: fileData.data.items[itemName][fieldName],
                        type: 'scatter',
                        mode: plotType,
                        name: label,
                        line: {{ color: color, width: 2 }},
                        hovertemplate: '<b>%{{fullData.name}}</b><br>X: %{{x}}<br>Y: %{{y:.2f}}<extra></extra>'
                    }});
                }}
            }}
            
            let startTime, endTime, duration;
            try {{
                startTime = new Date(fileData.data.timestamps[0]);
                endTime = new Date(fileData.data.timestamps[fileData.data.timestamps.length - 1]);
                duration = (endTime - startTime) / 1000;
            }} catch (e) {{
                console.log('Error parsing timestamps:', e);
                startTime = new Date();
                endTime = new Date();
                duration = 0;
            }}
            
            const {{ tickvals, ticktext }} = getAdaptiveTicks(fileData.data.timestamps, 1100);

            const layout = {{
                title: `${{startTime.toLocaleString()}} to ${{endTime.toLocaleString()}} (${{formatDuration(duration)}})`,
                plot_bgcolor: '#222',
                paper_bgcolor: '#222',
                font: {{ color: 'white' }},
                xaxis: {{ 
                    title: 'Time',
                    gridcolor: 'rgba(255,255,255,0.1)',
                    tickfont: {{ color: 'white' }},
                    tickvals: tickvals,
                    ticktext: ticktext,
                    hoverformat: '%Y-%m-%d %H:%M:%S'
                }},
                yaxis: {{ 
                    title: 'Value',
                    gridcolor: 'rgba(255,255,255,0.1)',
                    tickfont: {{ color: 'white' }},
                    type: yScale
                }},
                showlegend: legendVisible,
                legend: {{ font: {{ color: 'white' }} }},
                margin: {{ l: 50, r: 20, t: 30, b: 50 }},
                height: 400,
                hovermode: 'x unified'
            }};
            
            const config = {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToAdd: ['hoverclosest', 'hovercompare'],
                modeBarButtonsToRemove: ['toImage']
            }};
            
            Plotly.newPlot(chartDiv, chartTraces, layout, config).then(function() {{
                // Get the actual plot area width from the rendered plot
                const xaxis = chartDiv._fullLayout.xaxis;
                const actualPlotWidth = xaxis._length;
                
                // Recalculate ticks based on actual width
                const {{ tickvals, ticktext }} = getAdaptiveTicks(fileData.data.timestamps, actualPlotWidth);
                
                // Update the plot with the new ticks
                Plotly.relayout(chartDiv, {{
                    'xaxis.tickvals': tickvals,
                    'xaxis.ticktext': ticktext
                }});
                
                chartDiv.addEventListener('mousemove', function(e) {{
                    const plotRect = chartDiv.getBoundingClientRect();
                    const x = e.clientX - plotRect.left;
                    const y = e.clientY - plotRect.top;
                    
                    updateTimeMarker(chartDiv, x, `time-marker-${{filename.replace(/\\W/g, '')}}`);
                    updateYMarker(chartDiv, y, `y-marker-${{filename.replace(/\\W/g, '')}}`);
                    
                    if (chartDiv._fullLayout && chartDiv._fullLayout.xaxis && chartDiv._fullLayout.yaxis) {{
                        const xaxis = chartDiv._fullLayout.xaxis;
                        const yaxis = chartDiv._fullLayout.yaxis;
                        if (e.clientX >= plotRect.left + xaxis._offset && 
                            e.clientX <= plotRect.left + xaxis._offset + xaxis._length &&
                            e.clientY >= plotRect.top + yaxis._offset &&
                            e.clientY <= plotRect.top + yaxis._offset + yaxis._length) {{
                            const xpixel = x - xaxis._offset;
                            const ypixel = y - yaxis._offset;
                            const xvalue = xaxis.p2d(xpixel);
                            const yvalue = yaxis.p2d(ypixel);
                            updateCallouts(xvalue, yvalue, x, y, chartTraces,
                                        `x-callout-${{filename.replace(/\\W/g, '')}}`, 
                                        `y-callout-${{filename.replace(/\\W/g, '')}}`);
                        }}
                    }}
                }});
                
                chartDiv.addEventListener('mouseleave', function() {{
                    document.getElementById(`time-marker-${{filename.replace(/\\W/g, '')}}`).style.display = 'none';
                    document.getElementById(`y-marker-${{filename.replace(/\\W/g, '')}}`).style.display = 'none';
                    document.getElementById(`x-callout-${{filename.replace(/\\W/g, '')}}`).textContent = 'X: --';
                    document.getElementById(`y-callout-${{filename.replace(/\\W/g, '')}}`).textContent = 'Y: --';
                }});
            }});
        }}
        
        function updateTimeMarker(plotEl, xpos, markerId) {{
            const marker = document.getElementById(markerId);
            if (marker) {{
                marker.style.display = 'block';
                marker.style.left = `${{xpos}}px`;
            }}
        }}
        
        function updateYMarker(plotEl, ypos, markerId) {{
            const marker = document.getElementById(markerId);
            if (marker) {{
                marker.style.display = 'block';
                marker.style.top = `${{ypos}}px`;
            }}
        }}
        
        function updateCallouts(xvalue, yvalue, xPos, yPos, chartTraces, xCalloutId, yCalloutId) {{
            const xCallout = document.getElementById(xCalloutId);
            const yCallout = document.getElementById(yCalloutId);
            if (xCallout && yCallout && chartTraces && chartTraces.length > 0) {{
                let xDisplay;
                try {{
                    // This is the key function that needed to be fixed
                    function parseCustomTimestamp(ts) {{
                        if (typeof ts === 'number') return ts;
                        if (typeof ts !== 'string') throw new Error('Unsupported timestamp type');
                        
                        // Try to parse as standard datetime format first (YYYY-MM-DD HH:MM:SS)
                        let date = new Date(ts);
                        if (!isNaN(date.getTime())) return date.getTime();
                        
                        // Try to parse hyphen-separated format (YYYY-MM-DD-HH-MM-SS)
                        const parts = ts.split('-');
                        if (parts.length === 6) {{
                            const [year, month, day, hour, minute, second] = parts;
                            const formatted = `${{year}}-${{month}}-${{day}} ${{hour}}:${{minute}}:${{second}}`;
                            date = new Date(formatted);
                            if (!isNaN(date.getTime())) return date.getTime();
                        }}
                        
                        console.log('Failed to parse timestamp:', ts);
                        throw new Error('Invalid timestamp format');
                    }}

                    const mss = 1000 * 60;
                    const startTime = parseCustomTimestamp(chartTraces[0].x[0]);
                    const currentTime = parseCustomTimestamp(xvalue);
                    const diffMs = currentTime - startTime;
                    if (isNaN(diffMs)) throw new Error('Invalid time difference');
                    const hours = Math.floor(diffMs / (mss * 60));
                    const minutes = Math.floor((diffMs % (mss * 60)) / (mss));
                    const seconds = Math.floor((diffMs % (mss)) / 1000);
                    xDisplay = `${{String(hours).padStart(2, '0')}}:${{String(minutes).padStart(2, '0')}}:${{String(seconds).padStart(2, '0')}}`;
                }} catch (err) {{
                    console.log('Error in updateCallouts:', err.message, 'xvalue:', xvalue, 'start:', chartTraces[0].x[0]);
                    xDisplay = xvalue !== undefined && xvalue !== null ? xvalue.toString() : '--';
                }}
                
                xCallout.textContent = `X: ${{xDisplay}}`;
                yCallout.textContent = `Y: ${{yvalue !== undefined && yvalue !== null ? yvalue.toFixed(2) : '--'}}`;
                
                xCallout.style.left = `${{xPos}}px`;
                xCallout.style.transform = 'translateX(-50%)';
                yCallout.style.top = `${{yPos}}px`;
                yCallout.style.transform = 'translateY(-50%)';
            }}
        }}
        
        function removeChart(filename) {{
            if (multiChartData[filename]) delete multiChartData[filename];
            const wrapper = document.getElementById(`chart-wrapper-${{filename.replace(/\\W/g, '')}}`);
            if (wrapper) wrapper.remove();
            if (Object.keys(multiChartData).length === 0) {{
                viewMode = 'single';
                document.getElementById('main-chart-container').style.display = 'block';
                document.getElementById('multi-chart-container').style.display = 'none';
                document.getElementById('view-all').textContent = 'View All Charts';
            }}
        }}
        
        function processTimeSeriesData(data, config) {{
            log('Processing time series data...');
            if (!data.timestamps || !data.items) {{
                log('Invalid data format. Missing timestamps or items.');
                return;
            }}
            chartData = [];
            fieldVisibility = {{}};
            const fieldSelector = document.getElementById('field-selector');
            fieldSelector.innerHTML = '';

            for (const itemName in data.items) {{
                for (const fieldName in data.items[itemName]) {{
                    if (!config[fieldName]) continue;
                    // Prioritize color from field config if provided
                    let color;
                    if (config[fieldName] && typeof config[fieldName].color !== 'undefined') {{
                        color = config[fieldName].color;
                    }} else {{
                        color = getRandomColor(fieldName);
                    }}
                    const label = `${{fieldName}} (${{itemName}})`;
                    fieldVisibility[label] = true;
                    chartData.push({{
                        x: data.timestamps,
                        y: data.items[itemName][fieldName],
                        type: 'scatter',
                        mode: plotType,
                        name: label,
                        line: {{ color: color, width: 2 }},
                        hovertemplate: '%{{customdata.padded}} - %{{fullData.name}}<extra></extra>',
                        customdata: data.items[itemName][fieldName].map(y => ({{
                            padded: y.toFixed(2).padStart(6, ' ')
                        }})),
                    }});
                }}
            }}
            updatePlot();
            log('Data loaded and plotted successfully.');
        }}
        
        function addFieldCheckbox(fieldName, itemName, color) {{
            const fieldSelector = document.getElementById('field-selector');
            const label = `${{fieldName}} (${{itemName}})`;
            const checkbox = document.createElement('div');
            checkbox.className = 'field-checkbox';
            const colorIndicator = document.createElement('span');
            colorIndicator.className = 'color-indicator';
            colorIndicator.style.backgroundColor = color;
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.id = `field-${{fieldName}}-${{itemName}}`;
            input.checked = true;
            input.addEventListener('change', function() {{
                fieldVisibility[label] = this.checked;
                updatePlot();
            }});
            const labelElem = document.createElement('label');
            labelElem.htmlFor = input.id;
            labelElem.textContent = label;
            checkbox.appendChild(colorIndicator);
            checkbox.appendChild(input);
            checkbox.appendChild(labelElem);
            fieldSelector.appendChild(checkbox);
        }}
        
        function updatePlot() {{
            const plot = document.getElementById('chart');
            const timeMarker = document.getElementById('time-marker');
            const yMarker = document.getElementById('y-marker');
            const xCallout = document.getElementById('x-callout');
            const yCallout = document.getElementById('y-callout');
            
            const visibleTraces = chartData.filter(trace => fieldVisibility[trace.name] === true);
            let startTime, endTime, duration;
            try {{
                startTime = new Date(chartData[0]?.x[0]);
                endTime = new Date(chartData[0]?.x[chartData[0]?.x.length - 1]);
                duration = (endTime - startTime) / 1000;
            }} catch (e) {{
                console.log('Error parsing timestamps:', e);
                startTime = new Date();
                endTime = new Date();
                duration = 0;
            }}
            
            const {{ tickvals, ticktext }} = getAdaptiveTicks(chartData[0]?.x || [], 1100);

            const layout = {{
                title: `${{startTime.toLocaleString()}} to ${{endTime.toLocaleString()}} (${{formatDuration(duration)}})`,
                plot_bgcolor: '#222',
                paper_bgcolor: '#222',
                font: {{ color: 'white' }},
                xaxis: {{ 
                    title: 'Time',
                    gridcolor: 'rgba(255,255,255,0.1)',
                    tickfont: {{ color: 'white' }},
                    tickvals: tickvals,
                    ticktext: ticktext,
                    hoverformat: '%Y-%m-%d %H:%M:%S'
                }},
                yaxis: {{ 
                    title: 'Value',
                    gridcolor: 'rgba(255,255,255,0.1)',
                    tickfont: {{ color: 'white' }},
                    type: yScale
                }},
                showlegend: legendVisible,
                legend: {{ font: {{ color: 'white' }} }},
                margin: {{ l: 50, r: 20, t: 50, b: 50 }},
                hovermode: 'x unified'
            }};
            
            const config = {{
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToAdd: ['hoverclosest', 'hovercompare'],
                modeBarButtonsToRemove: ['toImage']
            }};
            
            // First create the plot with default ticks
            Plotly.newPlot(plot, visibleTraces, layout, config).then(function() {{
                // Now get the actual plot area width from the rendered plot
                const xaxis = plot._fullLayout.xaxis;
                const actualPlotWidth = xaxis._length;
                
                // Recalculate ticks based on actual width
                const {{ tickvals, ticktext }} = getAdaptiveTicks(chartData[0]?.x || [], actualPlotWidth);
                
                // Update the plot with the new ticks
                Plotly.relayout(plot, {{
                    'xaxis.tickvals': tickvals,
                    'xaxis.ticktext': ticktext
                }});
                
                currentPlot = plot;
                
                plot.addEventListener('mousemove', function(e) {{
                    const plotRect = plot.getBoundingClientRect();
                    const x = e.clientX - plotRect.left;
                    const y = e.clientY - plotRect.top;
                    
                    updateTimeMarker(plot, x, 'time-marker');
                    updateYMarker(plot, y, 'y-marker');
                    
                    if (plot._fullLayout && plot._fullLayout.xaxis && plot._fullLayout.yaxis) {{
                        const xaxis = plot._fullLayout.xaxis;
                        const yaxis = plot._fullLayout.yaxis;
                        if (e.clientX >= plotRect.left + xaxis._offset && 
                            e.clientX <= plotRect.left + xaxis._offset + xaxis._length &&
                            e.clientY >= plotRect.top + yaxis._offset &&
                            e.clientY <= plotRect.top + yaxis._offset + yaxis._length) {{
                            const xpixel = x - xaxis._offset;
                            const ypixel = y - yaxis._offset;
                            const xvalue = xaxis.p2d(xpixel);
                            const yvalue = yaxis.p2d(ypixel);
                            updateCallouts(xvalue, yvalue, x, y, chartData, 'x-callout', 'y-callout');
                        }}
                    }}
                }});
                
                plot.addEventListener('mouseleave', function() {{
                    timeMarker.style.display = 'none';
                    yMarker.style.display = 'none';
                    xCallout.textContent = 'X: --';
                    yCallout.textContent = 'Y: --';
                }});
            }});
        }}
        
        function updateYScale(e) {{
            yScale = e.target.value;
            updatePlot();
            if (viewMode === 'multi') updateMultiChartView();
        }}
        
        function toggleLegend() {{
            legendVisible = !legendVisible;
            updatePlot();
            if (viewMode === 'multi') updateMultiChartView();
        }}
        
        function resetZoom() {{
            const plot = document.getElementById('chart');
            Plotly.relayout(plot, {{ 'xaxis.autorange': true, 'yaxis.autorange': true }});
            if (viewMode === 'multi') {{
                for (const filename in multiChartData) {{
                    const chartId = `chart-${{filename.replace(/\\W/g, '')}}`;
                    const chartElement = document.getElementById(chartId);
                    if (chartElement) Plotly.relayout(chartElement, {{ 'xaxis.autorange': true, 'yaxis.autorange': true }});
                }}
            }}
        }}
        
        function downloadPlot(format) {{
            const plot = document.getElementById('chart');
            Plotly.toImage(plot, {{format: format, width: 1200, height: 800}})
                .then(function(dataUrl) {{
                    const link = document.createElement('a');
                    link.href = dataUrl;
                    link.download = `timeseries_plot.${{format}}`;
                    link.click();
                }});
        }}
        
        function processRawFormat(rawData, timeseriesData) {{
            if (rawData.data && Object.keys(rawData.data).length > 0) {{
                const firstItem = Object.keys(rawData.data)[0];
                const itemData = rawData.data[firstItem];
                if (itemData.timeseries && Object.keys(itemData.timeseries).length > 0) {{
                    const firstField = Object.keys(itemData.timeseries)[0];
                    const timestamps = Object.keys(itemData.timeseries[firstField]).sort();
                    timeseriesData.timestamps = timestamps;
                    for (const itemName in rawData.data) {{
                        timeseriesData.items[itemName] = {{}};
                        for (const fieldName in rawData.data[itemName].timeseries) {{
                            const fieldData = rawData.data[itemName].timeseries[fieldName];
                            timeseriesData.items[itemName][fieldName] = timestamps.map(ts => fieldData[ts] || null);
                        }}
                    }}
                }}
            }}
        }}
        
        function processStructuredFormat(structuredData, timeseriesData) {{
            timeseriesData.timestamps = structuredData.timeslots || [];
            if (structuredData.data) {{
                for (const itemName in structuredData.data) {{
                    timeseriesData.items[itemName] = {{}};
                    for (const fieldName in structuredData.data[itemName]) {{
                        timeseriesData.items[itemName][fieldName] = structuredData.data[itemName][fieldName];
                    }}
                }}
            }}
        }}
        
        function getRandomColor(str) {{
            let hash = 0;
            for (let i = 0; i < str.length; i++) {{
                hash = str.charCodeAt(i) + ((hash << 5) - hash);
            }}
            const hue = Math.abs(hash % 360);
            return `hsl(${{hue}}, 70%, 60%)`;
        }}
        
        function log(message) {{
            const logElement = document.getElementById('log');
            const time = new Date().toLocaleTimeString();
            logElement.innerHTML += `<div>[${{time}}] ${{message}}</div>`;
            logElement.scrollTop = logElement.scrollHeight;
        }}
    </script>
</body>
</html>"""
        return html_content
    
    @staticmethod
    def generate_svg(data: Dict[str, Any], title: Optional[str] = None, 
                   field_config: Optional[Dict[str, Dict[str, Any]]] = None,
                   output_file: str = "timeseries_plot.svg") -> bool:
        """
        Generate an SVG file with a plot.
        
        Args:
            data: Internal data structure
            title: Plot title
            field_config: Field configuration dictionary
            output_file: Output file path
            
        Returns:
            bool: True if generated successfully, False otherwise
        """
        try:
            import svgwrite
        except ImportError:
            print("svgwrite is not available. Install it using 'pip install svgwrite'.")
            return False
        
        if not data or "timestamps" not in data or "items" not in data:
            print("Invalid data structure for plotting.")
            return False
        
        # Use field_config if provided, otherwise use data["fields"]
        if field_config is None and "fields" in data:
            # Extract field config from data
            field_config = {}
            for field, field_data in data["fields"].items():
                if "config" in field_data:
                    field_config[field] = field_data["config"]
                    
        try:
            # Create SVG drawing
            dwg = svgwrite.Drawing(output_file, profile='tiny', size=('800px', '500px'))
            
            # Add title
            dwg.add(dwg.text(title or "Time Series Visualization", insert=('400px', '30px'), 
                           text_anchor='middle', font_size='20px', font_family='Arial',
                           fill='black'))
            
            # Create plot area
            plot_width = 700
            plot_height = 400
            margin_left = 50
            margin_top = 50
            
            # Draw axes
            dwg.add(dwg.line(start=(margin_left, margin_top), 
                           end=(margin_left, margin_top + plot_height), 
                           stroke='black'))
            dwg.add(dwg.line(start=(margin_left, margin_top + plot_height), 
                           end=(margin_left + plot_width, margin_top + plot_height), 
                           stroke='black'))
            
            # Get time range
            timestamps = data["timestamps"]
            time_min = min(timestamps).timestamp() if isinstance(timestamps[0], datetime) else min(timestamps)
            time_max = max(timestamps).timestamp() if isinstance(timestamps[0], datetime) else max(timestamps)
            time_range = time_max - time_min
            
            # Plot each field
            legend_items = []
            legend_y = 50
            
            if "default" in data["items"]:
                for field, values in data["items"]["default"].items():
                    # Skip if field not in config
                    if not field_config or field not in field_config:
                        continue
                    
                    # Get color if available
                    # Use color from field config if available, else use a default color
                    color = field_config[field].get("color", "blue") if field_config and field in field_config else "blue"
                    
                    # Get value range
                    value_min = min(values)
                    value_max = max(values)
                    value_range = value_max - value_min if value_max > value_min else 1
                    
                    # Scale values to plot height
                    points = []
                    for i, value in enumerate(values):
                        ts = timestamps[i].timestamp() if isinstance(timestamps[i], datetime) else timestamps[i]
                        x = margin_left + (ts - time_min) / time_range * plot_width
                        y = margin_top + plot_height - (value - value_min) / value_range * plot_height
                        points.append((x, y))
                    
                    # Create polyline
                    polyline = dwg.polyline(points=points, fill='none', stroke=color, stroke_width=2)
                    dwg.add(polyline)
                    
                    # Add to legend
                    dwg.add(dwg.line(start=(margin_left + plot_width + 20, legend_y), 
                                   end=(margin_left + plot_width + 50, legend_y), 
                                   stroke=color, stroke_width=2))
                    dwg.add(dwg.text(field, insert=(margin_left + plot_width + 60, legend_y + 5), 
                                   font_size='12px', font_family='Arial'))
                    legend_y += 20
            
            # Save SVG file
            dwg.save()
            print(f"SVG plot saved to: {output_file}")
            return True
            
        except Exception as e:
            print(f"Error generating SVG file: {e}")
            return False
    
    @staticmethod
    def save_plot(data: Dict[str, Any], output_file: str, 
                title: Optional[str] = None, 
                field_config: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """
        Save a plot to a file based on the file extension.
        
        Args:
            data: Internal data structure
            output_file: Output file path
            title: Plot title
            field_config: Field configuration dictionary
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        # Determine output format from file extension
        _, ext = os.path.splitext(output_file)
        ext = ext.lower()
        
        if ext == ".html":
            return HTMLPlotter.generate_html(data, title, field_config, output_file)
        elif ext == ".svg":
            return HTMLPlotter.generate_svg(data, title, field_config, output_file)
        elif ext in [".png", ".pdf"]:
            try:
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                
                # Use field_config if provided, otherwise use data["fields"]
                if field_config is None and "fields" in data:
                    # Extract field config from data
                    field_config = {}
                    for field, field_data in data["fields"].items():
                        if "config" in field_data:
                            field_config[field] = field_data["config"]
                
                fig, ax = plt.subplots(figsize=(12, 8))
                
                timestamps = data["timestamps"]
                
                # Plot each field
                for item_name, item_data in data["items"].items():
                    for field, values in item_data.items():
                        # Skip if field not in config
                        if not field_config or field not in field_config:
                            continue
                        
                        # Get color if available
                        # Use color from field config if available
                        color = field_config[field].get("color") if field_config and field in field_config else None
                        
                        label = f"{field} ({item_name})" if item_name != "default" else field
                        ax.plot(timestamps, values, label=label, color=color)
                
                # Configure plot
                ax.set_title(title or "Time Series Visualization")
                ax.set_xlabel("Time")
                ax.set_ylabel("Value")
                ax.grid(True, alpha=0.3)
                ax.legend()
                
                # Format x-axis dates
                if isinstance(timestamps[0], datetime):
                    fig.autofmt_xdate()
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
                
                # Save to file
                plt.tight_layout()
                plt.savefig(output_file, dpi=300)
                plt.close(fig)
                
                print(f"Plot saved to: {output_file}")
                return True
                
            except ImportError:
                print(f"Matplotlib is not available. Install it using 'pip install matplotlib'.")
                return False
            except Exception as e:
                print(f"Error saving plot: {e}")
                return False
        else:
            print(f"Unsupported file format: {ext}")
            return False