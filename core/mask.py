"""Timeline masks for ChronoSynth."""

import math
import re
from typing import Dict, List, Any, Optional


class MaskEngine:
    """Provides methods for applying masks to time series data."""
    
    @staticmethod
    def apply_masks(data: Dict[str, List[float]], masks: List[str], 
                   timestamps: List[float], field_config: Dict[str, Dict[str, Any]]) -> None:
        """
        Apply masks to the time series data.
        
        Args:
            data: Dictionary of field values
            masks: List of mask expressions
            timestamps: List of timestamps (in seconds from start)
            field_config: Field configuration dictionary
        """
        if not masks:
            return
        
        num_points = len(next(iter(data.values())))
        
        for mask_str in masks:
            mask_str = mask_str.strip()
            
            # Parse sine wave mask
            if mask_str.startswith("sin(") and mask_str.endswith(")"):
                # Extract parameters
                params_str = mask_str[4:-1]  # Remove sin( and )
                params = {}
                
                # Default values
                params["amp"] = 0.3
                params["freq"] = 0.01
                params["phase"] = 0.0
                params["offset"] = 1.0
                
                # Parse parameters
                for param in params_str.split(","):
                    if "=" in param:
                        key, value = param.strip().split("=", 1)
                        params[key.strip()] = float(value.strip())
                
                # Apply sine wave mask
                for field in data:
                    field_values = data[field]
                    
                    for i in range(num_points):
                        t = timestamps[i]
                        sin_factor = params["amp"] * math.sin(2 * math.pi * params["freq"] * t + params["phase"]) + params["offset"]
                        
                        field_values[i] *= sin_factor
            
            # Parse power function mask
            elif mask_str.startswith("pow="):
                power = float(mask_str.split("=", 1)[1])
                
                for field in data:
                    field_values = data[field]
                    field_min = field_config[field]["min"]
                    field_max = field_config[field]["max"]
                    
                    for i in range(num_points):
                        # Normalize value to [0,1] range
                        norm_val = (field_values[i] - field_min) / (field_max - field_min) if field_max > field_min else 0
                        # Clamp normalized value to [0,1]
                        norm_val = max(0.0, min(1.0, norm_val))
                        
                        # Apply power function
                        pow_val = norm_val ** power
                        
                        # Denormalize
                        new_val = field_min + pow_val * (field_max - field_min)
                        
                        field_values[i] = new_val
    
    @staticmethod
    def parse_sin_mask(mask_str: str) -> Dict[str, float]:
        """
        Parse a sine wave mask expression.
        
        Args:
            mask_str: Mask expression string
            
        Returns:
            Dictionary of parameters
        """
        # Default values
        params = {
            "amp": 0.3,
            "freq": 0.01,
            "phase": 0.0,
            "offset": 1.0
        }
        
        # Extract parameters string
        match = re.match(r"sin\((.+)\)", mask_str)
        if not match:
            return params
        
        params_str = match.group(1)
        
        # Parse parameters
        for param in params_str.split(","):
            if "=" in param:
                key, value = param.strip().split("=", 1)
                key = key.strip()
                if key in params:
                    try:
                        params[key] = float(value.strip())
                    except ValueError:
                        pass  # Ignore invalid values
        
        return params
    
    @staticmethod
    def apply_sin_mask(values: List[float], timestamps: List[float], params: Dict[str, float]) -> None:
        """
        Apply a sine wave mask to a list of values.
        
        Args:
            values: List of values to mask
            timestamps: List of timestamps (in seconds from start)
            params: Dictionary of parameters
        """
        for i in range(len(values)):
            t = timestamps[i]
            sin_factor = params["amp"] * math.sin(2 * math.pi * params["freq"] * t + params["phase"]) + params["offset"]
            values[i] *= sin_factor
    
    @staticmethod
    def apply_pow_mask(values: List[float], power: float, field_min: float, field_max: float) -> None:
        """
        Apply a power function mask to a list of values.
        
        Args:
            values: List of values to mask
            power: Power exponent
            field_min: Minimum field value
            field_max: Maximum field value
        """
        # Check if we can use numpy for efficiency
        try:
            import numpy as np
            if isinstance(values, np.ndarray):
                # Normalize values to [0,1] range
                norm_vals = np.clip((values - field_min) / (field_max - field_min), 0.0, 1.0) if field_max > field_min else np.zeros_like(values)
                
                # Apply power function
                pow_vals = norm_vals ** power
                
                # Denormalize
                values[:] = field_min + pow_vals * (field_max - field_min)
                return
        except ImportError:
            pass
            
        # Standard Python implementation
        for i in range(len(values)):
            # Normalize value to [0,1] range
            norm_val = (values[i] - field_min) / (field_max - field_min) if field_max > field_min else 0
            # Clamp to [0,1]
            norm_val = max(0.0, min(1.0, norm_val))
            
            # Apply power function
            pow_val = norm_val ** power
            
            # Denormalize
            values[i] = field_min + pow_val * (field_max - field_min)