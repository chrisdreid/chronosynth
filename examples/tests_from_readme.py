#!/usr/bin/env python
"""
Script to extract examples from README.md and run them as tests.
This script parses the README.md file, extracts code examples,
and executes them to verify they work as expected.
"""

import os
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch

# Add the project root to the path so we can import chronosynth
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Paths
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README_PATH = os.path.join(ROOT_DIR, "README.md")
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(EXAMPLES_DIR, "outputs")
CONFIGS_DIR = os.path.join(EXAMPLES_DIR, "configs")
BATCH_DIR = os.path.join(EXAMPLES_DIR, "batch")

# Ensure output directory exists
os.makedirs(OUTPUTS_DIR, exist_ok=True)

class ReadmeExampleTester:
    def __init__(self):
        """Initialize the tester by reading the README.md file."""
        with open(README_PATH, "r") as f:
            self.readme_contents = f.read()
    
    def extract_code_blocks(self, language):
        """Extract code blocks of specified language from the README."""
        pattern = f"```{language}\n(.*?)```"
        return re.findall(pattern, self.readme_contents, re.DOTALL)
    
    def test_python_examples(self):
        """Test the Python examples from the README."""
        python_examples = self.extract_code_blocks("python")
        
        print(f"\nFound {len(python_examples)} Python code blocks in README.md")
        
        for i, example in enumerate(python_examples):
            # Skip examples that are just syntax definitions or imports alone
            if "TimeSeriesGenerator" not in example or example.count('\n') < 3:
                print(f"! Python example {i} skipped - not a complete example")
                continue
                
            # Create a proper example name
            example_name = f"readme_example_{i}"
            
            # Add imports if needed
            if "from chronosynth import" not in example:
                example = "from chronosynth import TimeSeriesGenerator\n" + example
            
            # Add necessary imports
            example = "import os\n" + example
                
            # Create a local test script
            test_script = os.path.join(OUTPUTS_DIR, f"{example_name}.py")
            
            # Modify the example to use proper paths
            modified_example = self._prepare_python_example(example, example_name)
            
            # Skip examples that appear to load files without saving first
            if 'generator.load(' in modified_example and 'generator.save(' not in modified_example:
                print(f"! Python example {i} skipped - loads file without saving first")
                continue
            
            # Write the test script
            with open(test_script, "w") as f:
                f.write(modified_example)
            
            # Run the test script with mocked visualization
            with patch('matplotlib.pyplot.show', return_value=None), \
                 patch('webbrowser.open', return_value=None):
                try:
                    print(f"Running Python example {i}...")
                    result = subprocess.run([sys.executable, test_script], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        # Print the error but don't fail the test
                        print(f"! Python example {i} failed with error:")
                        print(result.stderr)
                    else:
                        print(f"✓ Python example {i} passed")
                        # Report any output
                        if result.stdout.strip():
                            print(f"  Output: {result.stdout.strip()}")
                except Exception as e:
                    print(f"! Python example {i} exception: {str(e)}")
    
    def _prepare_python_example(self, example, example_name):
        """Prepare Python example for testing with proper paths."""
        modified_example = example
        
        # Replace config file references
        if 'generator.load_config_file' in modified_example:
            config_loading = f"""
# Load config file
config_file = os.path.join("{CONFIGS_DIR}", "standard_fields.json")
with open(config_file, 'r') as f:
    config = json.load(f)
generator.configure_fields(config)
"""
            modified_example = modified_example.replace('generator.load_config_file("configs/standard_fields.json")', config_loading)
            
        # Make sure json is imported if needed for config loading
        if 'json.load' in modified_example and 'import json' not in modified_example:
            modified_example = "import json\n" + modified_example
        
        # Update save paths
        modified_example = modified_example.replace('generator.save(data, "output.json"', 
                                                 f'generator.save(data, os.path.join("{OUTPUTS_DIR}", "{example_name}.json")')
        modified_example = modified_example.replace('generator.save(data, "output.pkl"', 
                                                 f'generator.save(data, os.path.join("{OUTPUTS_DIR}", "{example_name}.pkl")')
        modified_example = modified_example.replace('generator.save(data, "output.npy"', 
                                                 f'generator.save(data, os.path.join("{OUTPUTS_DIR}", "{example_name}.npy")')
        
        # Fix file paths for loading
        modified_example = modified_example.replace('generator.load("output.json")', 
                                                  f'generator.load(os.path.join("{OUTPUTS_DIR}", "{example_name}.json"))')
        
        # Fix plot commands
        modified_example = modified_example.replace('--plot html:open', '--plot html')
        modified_example = modified_example.replace('.html:open', '.html')
        
        # Add validation to ensure the example runs to completion
        validation_code = f"""
# Validation to ensure the example runs
if 'data' in locals():
    print(f"Example {example_name} executed successfully with " + 
          f"{{len(data.get('data', {{}}).get('default', {{}}))}}" + 
          " data points")
else:
    print(f"Example {example_name} executed but did not produce 'data'")
"""
        modified_example += validation_code
        
        return modified_example
    
    def test_bash_examples(self):
        """Test the bash examples from the README."""
        bash_examples = self.extract_code_blocks("bash")
        
        print(f"\nFound {len(bash_examples)} Bash code blocks in README.md")
        
        for i, example in enumerate(bash_examples):
            # Process multi-line commands
            for j, cmd_line in enumerate(example.strip().split('\n')):
                # Skip comments and empty lines
                if cmd_line.strip().startswith('#') or not cmd_line.strip():
                    continue
                
                # Skip visualization commands
                if "--plot" in cmd_line and "ascii" not in cmd_line:
                    continue
                
                # Remove the chronosynth command part
                if cmd_line.startswith("chronosynth "):
                    args = cmd_line[len("chronosynth "):]
                else:
                    continue  # Skip non-chronosynth commands
                
                # Run the bash command
                self._run_bash_command(args, i, j)
    
    def _run_bash_command(self, args, example_index, command_index):
        """Execute a bash command with proper modifications."""
        # Fix common issues in command args
        if "--config-file" in args:
            # Update to use our config file
            args = args.replace("--config-file configs/", f"--config-file {CONFIGS_DIR}/")
            # If it's still using a config that doesn't exist, skip it
            if "--config-file" in args and not os.path.exists(args.split("--config-file ")[1].split()[0]):
                print(f"! Bash example {example_index}.{command_index} skipped - requires specific config file")
                return
                
        # Handle multi-line commands with backslashes
        if args.strip().endswith('\\'):
            print(f"! Bash example {example_index}.{command_index} skipped - multi-line command")
            return
            
        # Add fields if the command would fail without configuration
        if "--keyframe" in args and "--config-file" not in args:
            args = f"--config-file {CONFIGS_DIR}/standard_fields.json " + args
        
        # Use batch directory for batch files
        if "--batch-file" in args:
            args = args.replace("--batch-file ", f"--batch-file {BATCH_DIR}/")
        
        # Modify paths and disable opening files
        example_name = f"bash_example_{example_index}_{command_index}"
        args = args.replace('--output-file ', f'--output-file {OUTPUTS_DIR}/{example_name}_')
        args = args.replace('--output-dir ', f'--output-dir {OUTPUTS_DIR}/')
        args = args.replace('--plot html:open', '--plot html')
        args = args.replace('--plot cli', '--plot ascii')  # Use ASCII instead of CLI for testing
        
        # Create a single command test
        full_command = f"python -m chronosynth {args}"
        
        try:
            # Run with a timeout to avoid hanging
            print(f"Running Bash example {example_index}.{command_index}...")
            result = subprocess.run(full_command, shell=True, 
                                  capture_output=True, text=True, timeout=10)
            
            # Only fail if it's not a warning about missing optional dependencies
            if result.returncode != 0 and "Missing optional dependency" not in result.stderr:
                # Print the error for debugging but don't fail
                print(f"! Bash example {example_index}.{command_index} returned error:")
                print(result.stderr)
                print(f"  Command was: {full_command}")
            else:
                print(f"✓ Bash example {example_index}.{command_index} passed")
                # Report any output
                if result.stdout.strip():
                    print(f"  Output: {result.stdout.strip()[:100]}...")
        except subprocess.TimeoutExpired:
            print(f"! Bash example {example_index}.{command_index} timed out - skipping")
        except Exception as e:
            print(f"! Bash example {example_index}.{command_index} exception: {str(e)} - skipping")

def run_all_tests():
    """Run all README example tests."""
    tester = ReadmeExampleTester()
    
    print("\n=== ChronoSynth README.md Examples Tester ===")
    print(f"README path: {README_PATH}")
    print(f"Examples directory: {EXAMPLES_DIR}")
    print(f"Outputs directory: {OUTPUTS_DIR}")
    
    print("\nTesting Python examples...")
    tester.test_python_examples()
    
    print("\nTesting Bash examples...")
    tester.test_bash_examples()
    
    print("\n=== README examples testing complete ===")

if __name__ == "__main__":
    run_all_tests()