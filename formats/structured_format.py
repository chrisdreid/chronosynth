"""Structured timeslots format handler for ChronoSynth."""

import json
import pickle
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Try to import numpy if available
try:
    import numpy as np
    HAVE_NUMPY = True
except ImportError:
    HAVE_NUMPY = False


class StructuredFormatOutput:
    """Converts internal data structure to structured timeslots format."""
    
    @staticmethod
    def format(data: Dict[str, Any], field_config: Dict[str, Dict[str, Any]], normalize: bool = False) -> Dict[str, Any]:
        """
        Format data to structured timeslots format.
        
        Args:
            data: Internal data structure
            field_config: Field configuration dictionary
            normalize: If True, normalize all output values to 0-1 range
            
        Returns:
            Dict in structured timeslots format
        """
        result = {
            "version": "1.0.0",
            "type": "ts-structured",
            "fields": {},
            "timeslots": [],
            "data": {}
        }
        
        # Add field configurations (simplified for structured format)
        for field, config in field_config.items():
            result["fields"][field] = {
                "shorthand": config["shorthand"],
                "data_type": config.get("data_type", "float"),
                "min": config["min"],
                "max": config["max"]
            }
            # Include color if present
            if "color" in config:
                result["fields"][field]["color"] = config["color"]
        
        # Add timestamps
        result["timeslots"] = [StructuredFormatOutput._format_timestamp(ts) for ts in data["timestamps"]]
        
        # Add data
        result["data"] = {}
        
        for item_name, item_data in data["items"].items():
            result["data"][item_name] = {}
            
            for field, values in item_data.items():
                if field in field_config:
                    field_min = field_config[field]["min"]
                    field_max = field_config[field]["max"]
                    field_range = field_max - field_min
                    
                    # Apply normalization if requested
                    if normalize and field_range > 0:
                        if HAVE_NUMPY and isinstance(values, np.ndarray):
                            # Use numpy for efficient normalization if available
                            normalized_values = np.clip((values - field_min) / field_range, 0.0, 1.0)
                            result["data"][item_name][field] = normalized_values.tolist() if hasattr(normalized_values, 'tolist') else normalized_values
                        else:
                            # Python list normalization
                            normalized_values = []
                            for value in values:
                                # Calculate normalized value and clamp to [0, 1]
                                norm_value = (value - field_min) / field_range
                                norm_value = max(0.0, min(1.0, norm_value))
                                normalized_values.append(norm_value)
                            result["data"][item_name][field] = normalized_values
                    else:
                        result["data"][item_name][field] = values
        
        return result
    
    @staticmethod
    def _format_timestamp(timestamp: datetime) -> str:
        """
        Format a timestamp for the structured format.
        
        Args:
            timestamp: Datetime object
            
        Returns:
            Formatted timestamp string
        """
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    
    @staticmethod
    def save(data: Dict[str, Any], file_path: str, format_type: str = "json") -> bool:
        """
        Save data in the specified format.
        
        Args:
            data: Formatted data
            file_path: Output file path
            format_type: Format type ("json", "pkl", "npy")
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Create directory if it doesn't exist
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Save based on format type
            if format_type == "json":
                with open(file_path, "w") as f:
                    json.dump(data, f, indent=2, default=str)
            elif format_type == "pkl":
                with open(file_path, "wb") as f:
                    pickle.dump(data, f)
            elif format_type == "npy" and HAVE_NUMPY:
                # For npy format, we need to convert to a numpy-compatible structure
                np.save(file_path, data)
            else:
                raise ValueError(f"Unsupported format type: {format_type}")
            
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
    @staticmethod
    def load(file_path: str) -> Optional[Dict[str, Any]]:
        """
        Load data from a file.
        
        Args:
            file_path: Input file path
            
        Returns:
            Dict containing loaded data, or None if loading failed
        """
        try:
            # Support loading from URL
            if file_path.startswith(("http://", "https://")):
                try:
                    import requests
                    response = requests.get(file_path)
                    response.raise_for_status()
                    
                    content_type = response.headers.get('content-type', '')
                    if 'json' in content_type:
                        return json.loads(response.text)
                    elif 'octet-stream' in content_type or 'binary' in content_type:
                        print("Binary content from URL requires local download first.")
                        return None
                    else:
                        try:
                            return json.loads(response.text)
                        except json.JSONDecodeError:
                            print(f"Cannot parse URL content as JSON: {file_path}")
                            return None
                except ImportError:
                    print("The requests library is not available. Install with 'pip install requests'")
                    return None
                except Exception as e:
                    print(f"Error loading from URL: {e}")
                    return None
                    
            # Load from local file
            # Determine file format from extension
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if ext == ".json":
                with open(file_path, "r") as f:
                    return json.load(f)
            elif ext == ".pkl":
                with open(file_path, "rb") as f:
                    return pickle.load(f)
            elif ext == ".npy" and HAVE_NUMPY:
                # Load from numpy file
                data = np.load(file_path, allow_pickle=True).item()
                return data
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as e:
            print(f"Error loading data: {e}")
            return None