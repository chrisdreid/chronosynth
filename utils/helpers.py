"""Helper functions for TimeSeriesGenerator."""

import os
import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union


def create_directory(directory_path: str) -> bool:
    """
    Create a directory if it doesn't exist.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        bool: True if directory exists or was created successfully
    """
    if not os.path.exists(directory_path):
        try:
            os.makedirs(directory_path)
            return True
        except Exception as e:
            print(f"Error creating directory: {e}")
            return False
    return True


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp.
    
    Args:
        timestamp: Datetime object
        format_str: Format string
        
    Returns:
        Formatted timestamp string
    """
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    Parse a timestamp string.
    
    Args:
        timestamp_str: Timestamp string
        format_str: Format string
        
    Returns:
        Datetime object or None if parsing failed
    """
    try:
        return datetime.strptime(timestamp_str, format_str)
    except ValueError:
        return None


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between min and max.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return max(min_val, min(max_val, value))


def normalize(value: float, min_val: float, max_val: float) -> float:
    """
    Normalize a value to range [0, 1].
    
    Args:
        value: Value to normalize
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Normalized value clamped to [0, 1]
    """
    if max_val == min_val:
        return 0.5
    # Calculate normalized value
    norm_value = (value - min_val) / (max_val - min_val)
    # Clamp to [0, 1] range
    return max(0.0, min(1.0, norm_value))


def denormalize(value: float, min_val: float, max_val: float) -> float:
    """
    Denormalize a value from range [0, 1] to range [min_val, max_val].
    
    Args:
        value: Value to denormalize
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Denormalized value
    """
    return min_val + value * (max_val - min_val)


def apply_noise(value: float, noise_amount: float, value_range: float) -> float:
    """
    Apply random noise to a value.
    
    Args:
        value: Value to add noise to
        noise_amount: Noise amount factor
        value_range: Value range (max - min)
        
    Returns:
        Value with noise applied
    """
    noise = random.uniform(-value_range * 0.01 * noise_amount, value_range * 0.01 * noise_amount)
    return value + noise


def save_json(data: Any, filename: str, indent: int = 2) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data: Data to save
        filename: Output filename
        indent: JSON indentation
        
    Returns:
        bool: True if saved successfully, False otherwise
    """
    try:
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(filename, "w") as f:
            json.dump(data, f, indent=indent, default=str)
        return True
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        return False


def load_json(filename: str) -> Optional[Any]:
    """
    Load data from a JSON file.
    
    Args:
        filename: Input filename
        
    Returns:
        Loaded data or None if loading failed
    """
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None