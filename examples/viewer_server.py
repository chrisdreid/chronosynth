#!/usr/bin/env python
"""
Interactive ChronoSynth Viewer Server

This script launches a local HTTP server that hosts the ChronoSynth viewer
with proper JavaScript support for all file formats (JSON, PKL, NPY).
It also provides an API for controlling the viewer from Python.
"""

import os
import json
import http.server
import socketserver
import webbrowser
import threading
import argparse
import socket
import time
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

# Add support for communicating with the viewer
from urllib.request import Request, urlopen
from http import HTTPStatus

class ViewerAPI:
    """API for communicating with the ChronoSynth viewer."""
    
    def __init__(self, host: str = 'localhost', port: int = 8000):
        """
        Initialize the API with the host and port of the viewer server.
        
        Args:
            host: The hostname of the viewer server
            port: The port of the viewer server
        """
        self.base_url = f"http://{host}:{port}"
        self.connected = False
    
    def wait_for_connection(self, timeout: int = 10) -> bool:
        """
        Wait for the viewer server to be available.
        
        Args:
            timeout: Maximum time to wait in seconds
            
        Returns:
            bool: True if the connection was established, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                req = Request(f"{self.base_url}/api/ping")
                with urlopen(req, timeout=1) as response:
                    if response.getcode() == 200:
                        self.connected = True
                        return True
            except Exception:
                time.sleep(0.5)
        return False
    
    def load_file(self, file_path: str) -> bool:
        """
        Load a file into the viewer.
        
        Args:
            file_path: The path to the file to load
            
        Returns:
            bool: True if the file was loaded, False otherwise
        """
        if not self.connected:
            if not self.wait_for_connection():
                return False
                
        try:
            # Get the absolute path
            abs_path = os.path.abspath(file_path)
            if not os.path.exists(abs_path):
                print(f"File not found: {abs_path}")
                
                # Check if there's an outputs directory relative to the examples directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                example_outputs_path = os.path.join(script_dir, "outputs", os.path.basename(file_path))
                if os.path.exists(example_outputs_path):
                    print(f"Found at: {example_outputs_path}")
                    abs_path = example_outputs_path
                else:
                    return False
                
            # Send the load command
            encoded_path = urllib.parse.quote(abs_path)
            req = Request(f"{self.base_url}/api/load?filepath={encoded_path}")
            with urlopen(req) as response:
                return response.getcode() == 200
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def load_multiple_files(self, file_paths: List[str]) -> bool:
        """
        Load multiple files into the viewer for comparison.
        
        Args:
            file_paths: List of file paths to load
            
        Returns:
            bool: True if all files were loaded, False otherwise
        """
        if not self.connected:
            if not self.wait_for_connection():
                return False
                
        try:
            # Process paths to ensure they all exist
            valid_paths = []
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            for path in file_paths:
                abs_path = os.path.abspath(path)
                if os.path.exists(abs_path):
                    valid_paths.append(abs_path)
                else:
                    # Try to find in examples/outputs
                    example_outputs_path = os.path.join(script_dir, "outputs", os.path.basename(path))
                    if os.path.exists(example_outputs_path):
                        print(f"Found {os.path.basename(path)} at: {example_outputs_path}")
                        valid_paths.append(example_outputs_path)
                    else:
                        print(f"File not found: {abs_path}")
            
            if not valid_paths:
                print("No valid files found.")
                return False
                
            # Encode all paths
            encoded_paths = [urllib.parse.quote(path) for path in valid_paths]
            paths_param = ','.join(encoded_paths)
            
            # Send the load command
            req = Request(f"{self.base_url}/api/load-multiple?filepaths={paths_param}")
            with urlopen(req) as response:
                return response.getcode() == 200
        except Exception as e:
            print(f"Error loading multiple files: {e}")
            return False
    
    def set_view_mode(self, mode: str) -> bool:
        """
        Set the view mode of the viewer.
        
        Args:
            mode: "single" or "multi"
            
        Returns:
            bool: True if the mode was set, False otherwise
        """
        if not self.connected:
            if not self.wait_for_connection():
                return False
                
        try:
            req = Request(f"{self.base_url}/api/view-mode?mode={mode}")
            with urlopen(req) as response:
                return response.getcode() == 200
        except Exception as e:
            print(f"Error setting view mode: {e}")
            return False


class ViewerRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for the ChronoSynth viewer server."""
    
    def __init__(self, *args, **kwargs):
        # Store reference to the HTML content and lib paths
        self.html_content = kwargs.pop('html_content', None)
        self.lib_paths = kwargs.pop('lib_paths', {})
        self.data_files = []
        self.base_dir = kwargs.pop('base_dir', os.getcwd())
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET requests."""
        # API endpoints
        if self.path.startswith('/api/'):
            return self.handle_api()
            
        # Serve the viewer HTML for the root path
        if self.path == '/' or self.path == '/index.html':
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(self.html_content.encode())
            return
            
        # Serve library files
        if self.path.startswith('/lib/'):
            lib_name = self.path[5:]  # Remove '/lib/'
            if lib_name in self.lib_paths:
                content = self.lib_paths[lib_name]
                self.send_response(HTTPStatus.OK)
                if lib_name.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(content.encode() if isinstance(content, str) else content)
                return
                
        # Fall back to normal file serving for other paths
        return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    def handle_api(self):
        """Handle API requests."""
        if self.path == '/api/ping':
            # Simple ping endpoint to check if server is running
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
            return
            
        elif self.path.startswith('/api/load'):
            # Handle file loading
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'filepath' in params:
                filepath = params['filepath'][0]
                # Add to the list of data files
                self.data_files.append(filepath)
                
                # Determine if the file needs to be accessed via file system or URL
                # For server loading, we need to make the path relative to the web server root
                browser_path = filepath
                if os.path.exists(filepath):
                    # Make path relative to server root if inside server directory
                    rel_path = None
                    try:
                        rel_path = os.path.relpath(filepath, self.base_dir)
                        # If the path starts with .. it's outside web root
                        if rel_path.startswith('..'):
                            # Keep the absolute path for file:// access
                            browser_path = f"file://{filepath}"
                        else:
                            # Use the relative path for server access
                            browser_path = f"/{rel_path}"
                    except ValueError:
                        # If paths are on different drives, use file:// protocol
                        browser_path = f"file://{filepath}"
                
                # Redirect to viewer with the file path
                self.send_response(HTTPStatus.FOUND)
                self.send_header('Location', f'/?filepath={urllib.parse.quote(browser_path)}')
                self.end_headers()
                return
                
        elif self.path.startswith('/api/load-multiple'):
            # Handle multiple file loading
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'filepaths' in params:
                filepaths = params['filepaths'][0].split(',')
                # Add to the list of data files
                self.data_files.extend(filepaths)
                
                # Process each path to make it accessible in the browser
                browser_paths = []
                for filepath in filepaths:
                    browser_path = filepath
                    if os.path.exists(filepath):
                        try:
                            rel_path = os.path.relpath(filepath, self.base_dir)
                            if rel_path.startswith('..'):
                                browser_path = f"file://{filepath}"
                            else:
                                browser_path = f"/{rel_path}"
                        except ValueError:
                            browser_path = f"file://{filepath}"
                    browser_paths.append(browser_path)
                
                # Redirect to viewer with all file paths
                self.send_response(HTTPStatus.FOUND)
                path_param = '&'.join([f'filepath={urllib.parse.quote(path)}' for path in browser_paths])
                self.send_header('Location', f'/?{path_param}&view=multi')
                self.end_headers()
                return
                
        elif self.path.startswith('/api/view-mode'):
            # Handle view mode setting
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            if 'mode' in params:
                mode = params['mode'][0]
                
                # Redirect to viewer with the mode parameter
                self.send_response(HTTPStatus.FOUND)
                self.send_header('Location', f'/?view={mode}')
                self.end_headers()
                return
                
        # Default response for unhandled API endpoints
        self.send_response(HTTPStatus.NOT_FOUND)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'error': 'Endpoint not found'}).encode())


def find_free_port() -> int:
    """Find a free port to use for the server."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def get_js_libraries() -> Dict[str, Union[str, bytes]]:
    """
    Get JavaScript libraries needed for the viewer.
    
    Returns:
        Dict[str, Union[str, bytes]]: Dictionary of library name -> content
    """
    libraries = {}
    
    # Path to the lib directory
    lib_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
    
    # Check if the lib directory exists
    if os.path.exists(lib_dir) and os.path.isdir(lib_dir):
        # Load libraries from the lib directory
        for lib_file in os.listdir(lib_dir):
            if lib_file.endswith(".js"):
                lib_path = os.path.join(lib_dir, lib_file)
                try:
                    with open(lib_path, "r") as f:
                        libraries[lib_file] = f.read()
                    print(f"Loaded JS library: {lib_file}")
                except Exception as e:
                    print(f"Error loading JS library {lib_file}: {e}")
    else:
        print(f"Warning: Lib directory not found at {lib_dir}. Using fallback libraries.")
    
    # If the required libraries are not found, use fallback implementations
    if 'pickletojson.js' not in libraries:
        # Simple pickle parser for JavaScript
        pickle_js = """
        // Simple pickle parser for JavaScript (minimalist implementation)
        var pickleparser = pickleparser || {};
        pickleparser.Parser = function() {
            this.parse = function(data) {
                // Basic implementation to handle simple pickle files
                try {
                    // Convert binary data to string for simple parsing
                    let str = '';
                    if (data instanceof Uint8Array) {
                        for (let i = 0; i < data.length; i++) {
                            str += String.fromCharCode(data[i]);
                        }
                    } else {
                        str = data;
                    }
                    
                    // Very basic parser that tries to extract JSON-like structures
                    let result = {};
                    let jsonMatches = str.match(/\\{[^}]*\\}/g);
                    if (jsonMatches) {
                        try {
                            for (let i = 0; i < jsonMatches.length; i++) {
                                let parsed = JSON.parse(jsonMatches[i].replace(/'/g, '"'));
                                if (parsed && typeof parsed === 'object') {
                                    result[i] = parsed;
                                }
                            }
                        } catch (e) {
                            console.error("Error parsing JSON from pickle:", e);
                        }
                    }
                    
                    // Try to find arrays too
                    let arrayMatches = str.match(/\\[[^\\]]*\\]/g);
                    if (arrayMatches) {
                        try {
                            for (let i = 0; i < arrayMatches.length; i++) {
                                let parsed = JSON.parse(arrayMatches[i].replace(/'/g, '"'));
                                if (Array.isArray(parsed)) {
                                    result[i + 100] = parsed;
                                }
                            }
                        } catch (e) {
                            console.error("Error parsing arrays from pickle:", e);
                        }
                    }
                    
                    // Look for type markers that might indicate our format
                    if (str.includes('ts-raw') || str.includes('ts-structured')) {
                        result["4"] = [{
                            type: str.includes('ts-structured') ? 'ts-structured' : 'ts-raw',
                            fields: {},
                            data: { default: {} },
                            timeslots: []
                        }];
                    }
                    
                    return result;
                } catch (e) {
                    console.error("Pickle parsing error:", e);
                    return null;
                }
            };
        };
        """
        libraries['pickletojson.js'] = pickle_js
        print("Using fallback pickletojson.js implementation")
    
    if 'numjs.min.js' not in libraries:
        # Minimal NumPy.js implementation
        numjs_js = """
        // Minimal NumPy.js implementation for parsing .npy files
        var nj = nj || {};
        nj.array = function(data) {
            return { data: data };
        };
        """
        libraries['numjs.min.js'] = numjs_js
        print("Using fallback numjs.min.js implementation")
    
    return libraries


def generate_viewer_html() -> str:
    """
    Generate the HTML content for the viewer.
    
    Returns:
        str: HTML content
    """
    from chronosynth.visualization.html_plotter import HTMLPlotter
    return HTMLPlotter._generate_viewer_html(
        "ChronoSynth Interactive Viewer", 
        "{}", 
        "{}"
    )


def run_server(port: Optional[int] = None, open_browser: bool = True, 
              directory: Optional[str] = None) -> int:
    """
    Run the viewer server.
    
    Args:
        port: The port to use (or None to use a free port)
        open_browser: Whether to open the browser automatically
        directory: The directory to serve files from
        
    Returns:
        int: The port the server is running on
    """
    # Choose port if not specified
    if port is None:
        port = find_free_port()
    
    # Generate viewer HTML
    html_content = generate_viewer_html()
    
    # Get JavaScript libraries
    lib_paths = get_js_libraries()
    
    # Use the current directory if not specified
    if directory is None:
        directory = os.getcwd()
    
    # Make sure the directory is absolute
    base_dir = os.path.abspath(directory)
    
    # Get the original directory before changing
    original_dir = os.getcwd()
    
    # Change to the specified directory
    os.chdir(base_dir)
    
    # Start server with our custom handler
    handler = lambda *args, **kwargs: ViewerRequestHandler(
        *args, 
        html_content=html_content,
        lib_paths=lib_paths,
        base_dir=base_dir,
        **kwargs
    )
    
    # Create server on the specified port
    httpd = socketserver.ThreadingTCPServer(("", port), handler)
    
    # Start the server in a separate thread
    server_thread = threading.Thread(target=httpd.serve_forever)
    server_thread.daemon = True
    server_thread.start()
    
    print(f"ChronoSynth Viewer Server running at http://localhost:{port}")
    print(f"Serving files from: {base_dir}")
    
    # Open browser if requested
    if open_browser:
        webbrowser.open(f"http://localhost:{port}")
    
    return port


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ChronoSynth Interactive Viewer Server")
    parser.add_argument("--port", type=int, help="Port to run the server on (default: auto-detect)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open the browser automatically")
    parser.add_argument("--dir", help="Directory to serve files from (default: current directory)")
    parser.add_argument("--file", help="Open a specific file in the viewer")
    parser.add_argument("--files", nargs="+", help="Open multiple files in multi-view mode")
    parser.add_argument("--show-files", action="store_true", help="Show available files in the outputs directory")
    args = parser.parse_args()
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if outputs directory exists
    outputs_dir = os.path.join(script_dir, "outputs")
    if not os.path.exists(outputs_dir):
        os.makedirs(outputs_dir, exist_ok=True)
        print(f"Created outputs directory: {outputs_dir}")
    
    # If show-files flag is set, display available files
    if args.show_files:
        print(f"\nFiles available in {outputs_dir}:")
        if os.path.exists(outputs_dir):
            files = sorted([f for f in os.listdir(outputs_dir) if os.path.isfile(os.path.join(outputs_dir, f))])
            if files:
                for file in files:
                    print(f"  - {file}")
            else:
                print("  (No files found)")
        else:
            print("  (Outputs directory not found)")
        print("\nTo load a file directly: --file <filename>")
        print("Example: --file dataset1.json")
        return
    
    # Determine the base directory (use examples directory by default)
    base_dir = os.path.abspath(args.dir) if args.dir else script_dir
    
    # Run the server
    port = run_server(
        port=args.port,
        open_browser=not args.no_browser,
        directory=base_dir
    )
    
    # Create API instance
    api = ViewerAPI(port=port)
    
    # Wait for server to be ready
    if not api.wait_for_connection():
        print("Failed to connect to the viewer server")
        return
    
    # Process and resolve file paths
    if args.file:
        # Check if path is absolute or relative
        file_path = args.file
        resolved_path = None
        
        # Series of path resolution attempts
        paths_to_try = [
            file_path,  # As provided
            os.path.join(base_dir, file_path),  # Relative to base dir
            os.path.join(outputs_dir, file_path)  # In outputs directory
        ]
        
        # Try each path until one exists
        for path in paths_to_try:
            if os.path.exists(path) and os.path.isfile(path):
                resolved_path = path
                break
        
        if resolved_path:
            # Load file
            if api.load_file(resolved_path):
                print(f"Loaded file: {resolved_path}")
            else:
                print(f"Failed to load file: {resolved_path}")
        else:
            print(f"File not found: {file_path}")
            print("Tried looking in:")
            for path in paths_to_try:
                print(f"  - {path}")
            print("\nRun with --show-files to see available files.")
    
    # Load multiple files if provided
    elif args.files:
        resolved_paths = []
        
        for file_path in args.files:
            found = False
            
            # Try different path combinations
            paths_to_try = [
                file_path,  # As provided
                os.path.join(base_dir, file_path),  # Relative to base dir
                os.path.join(outputs_dir, file_path)  # In outputs directory
            ]
            
            # Use the first path that exists
            for path in paths_to_try:
                if os.path.exists(path) and os.path.isfile(path):
                    resolved_paths.append(path)
                    found = True
                    break
            
            if not found:
                print(f"Warning: File not found: {file_path}")
        
        if resolved_paths:
            if api.load_multiple_files(resolved_paths):
                print(f"Loaded {len(resolved_paths)} files in multi-view mode:")
                for path in resolved_paths:
                    print(f"  - {path}")
                api.set_view_mode("multi")
            else:
                print("Failed to load files via API")
        else:
            print("No valid files found.")
            print("Run with --show-files to see available files.")
    
    # Keep the server running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")


if __name__ == "__main__":
    main()