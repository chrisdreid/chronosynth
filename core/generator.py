"""Main generator class for TimeSeriesGenerator."""

import json
import pickle
import os
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any, Union

from .field_config import FieldConfig
from .keyframe_parser import KeyframeParser
from .interpolation import InterpolationEngine
from .mask import MaskEngine
from .resampler import Resampler
from ..formats.raw_format import RawFormatOutput
from ..formats.structured_format import StructuredFormatOutput


class TimeSeriesGenerator:
    """Main generator class for time series data creation."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize the generator with optional configuration.
        
        Args:
            config_file: Path to field configuration file
        """
        # Initialize field configurations
        self.field_config = FieldConfig(config_file)
        
        # Initialize keyframe parser
        self.keyframe_parser = KeyframeParser(self.field_config)
        
        # Initialize interpolation engine
        self.interpolation_engine = InterpolationEngine()
        
        # Initialize mask engine
        self.mask_engine = MaskEngine()
        
        # Initialize resampler
        self.resampler = Resampler()
    
    def configure_fields(self, field_config: Dict[str, Dict[str, Any]]) -> None:
        """
        Configure or update field definitions.
        
        Args:
            field_config: Dictionary of field configurations
        """
        self.field_config.load_from_dict(field_config)
    
    def generate(self, 
                minutes: int = 30, 
                interval_seconds: float = 5.0,
                keyframes: Optional[List[str]] = None,
                load: str = "medium",
                noise_scale: float = 1.0,
                masks: Optional[List[str]] = None,
                normalize: bool = False,
                start_time: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate time series data based on parameters.
        
        Args:
            minutes: Duration in minutes
            interval_seconds: Time between data points
            keyframes: List of keyframe expressions
            load: Predefined load profile ("low", "medium", "high")
            noise_scale: Global noise multiplier
            masks: List of mask expressions
            normalize: If True, interpret numeric values as normalized [0-1]
            start_time: Starting timestamp (default: current time - minutes)
            
        Returns:
            Dict containing generated time series data
        """
        # Calculate number of data points - add one extra point to ensure we include the end time
        # This ensures a 1 minute dataset really goes from 0 to 60 seconds inclusive
        num_points = int(minutes * 60 / interval_seconds) + 1
        
        # Set start time
        if start_time is None:
            start_time = datetime.now() - timedelta(minutes=minutes)
        
        # Generate timestamps
        timestamps = [start_time + timedelta(seconds=i * interval_seconds) 
                    for i in range(num_points)]
        
        # Calculate timestamps in seconds from start for easier calculations
        seconds_timestamps = [i * interval_seconds for i in range(num_points)]
        
        # Initialize data structure
        data = {
            "timestamps": timestamps,
            "seconds_timestamps": seconds_timestamps,
            "fields": {},
            "items": {"default": {}}
        }
        
        # Initialize values for each field
        for field, config in self.field_config.fields.items():
            data["fields"][field] = {
                "values": [config["min"]] * num_points,
                "config": config
            }
            data["items"]["default"][field] = [config["min"]] * num_points
        
        # Apply keyframes if provided
        if keyframes and len(keyframes) > 0:
            self._apply_keyframes(data, keyframes, interval_seconds, num_points, normalize, noise_scale)
        else:
            # Apply default patterns based on load
            self._apply_default_pattern(data, load, interval_seconds, num_points, noise_scale)
        
        # Apply masks if provided
        if masks and len(masks) > 0:
            self._apply_masks(data, masks, interval_seconds)
        
        return data
    
    def _apply_keyframes(self, 
                       data: Dict[str, Any], 
                       keyframes: List[str],
                       interval_seconds: float,
                       num_points: int,
                       normalize: bool,
                       noise_scale: float) -> None:
        """
        Apply keyframes to the data.
        
        Args:
            data: Data dictionary to modify
            keyframes: List of keyframe expressions
            interval_seconds: Time between data points
            num_points: Number of data points
            normalize: If True, interpret numeric values as normalized
            noise_scale: Global noise multiplier
        """
        total_seconds = num_points * interval_seconds
        
        # Parse keyframes
        parsed_keyframes = {}
        field_options = {}
        
        # Initialize with default options
        for field in self.field_config.fields:
            parsed_keyframes[field] = [(0, self.field_config.fields[field]["min"])]
            field_options[field] = {
                "noise": self.field_config.fields[field].get("noise_amount", 1.0),
                "movement_type": self.field_config.fields[field].get("movement_type", "linear")
            }
        
        # Process each keyframe
        for kf_str in keyframes:
            try:
                time_val, field, value, options, relationships = self.keyframe_parser.parse(kf_str, total_seconds)
                
                # Check if this is a default setting keyframe (no time part)
                if time_val is None:
                    # This is just setting default options for the field
                    if options:
                        field_options[field].update(options)
                    continue
                
                # Store options for this specific keyframe using a unique key
                kf_key = f"{field}_{time_val}"
                if options:
                    field_options[kf_key] = options.copy()
                
                # Resolve value if it's relative
                current_values = [kf[1] for kf in parsed_keyframes[field]]
                current_val = current_values[-1] if current_values else self.field_config.fields[field]["min"]
                
                resolved_value = self.keyframe_parser.resolve_value(
                    field, value, current_val, normalize, self.field_config.fields
                )
                
                # Add to parsed keyframes
                parsed_keyframes[field].append((time_val, resolved_value))
                
                # Update global field options if provided
                if options:
                    for key, val in options.items():
                        if key not in ('post_behavior', 'post_value'):
                            field_options[field][key] = val
                
                # Process relationships (other fields affected by this keyframe)
                for rel_field, rel_op, rel_val in relationships:
                    if rel_field in parsed_keyframes:
                        # Calculate the related field's value
                        rel_current_values = [kf[1] for kf in parsed_keyframes[rel_field]]
                        rel_current_val = rel_current_values[-1] if rel_current_values else self.field_config.fields[rel_field]["min"]
                        
                        # Apply the relationship (multiply, add, etc.)
                        if normalize:
                            # Convert to fractions
                            field_min = self.field_config.fields[field]["min"]
                            field_max = self.field_config.fields[field]["max"]
                            field_range = field_max - field_min
                            
                            rel_min = self.field_config.fields[rel_field]["min"]
                            rel_max = self.field_config.fields[rel_field]["max"]
                            rel_range = rel_max - rel_min
                            
                            # Normalize resolved_value
                            frac_val = (resolved_value - field_min) / field_range if field_range > 0 else 0
                            
                            # Apply relationship in normalized space
                            if rel_op == '*':
                                frac_new = frac_val * rel_val
                            elif rel_op == '+':
                                frac_new = frac_val + rel_val
                            elif rel_op == '-':
                                frac_new = frac_val - rel_val
                            elif rel_op == '/':
                                frac_new = frac_val / rel_val if rel_val != 0 else frac_val
                            elif rel_op == '^':
                                frac_new = frac_val ** rel_val
                            else:
                                frac_new = frac_val
                            
                            # Clamp and denormalize
                            frac_new = max(0.0, min(1.0, frac_new))
                            new_val = rel_min + frac_new * rel_range
                        else:
                            # Direct operation
                            if rel_op == '*':
                                new_val = resolved_value * rel_val
                            elif rel_op == '+':
                                new_val = resolved_value + rel_val
                            elif rel_op == '-':
                                new_val = resolved_value - rel_val
                            elif rel_op == '/':
                                new_val = resolved_value / rel_val if rel_val != 0 else resolved_value
                            elif rel_op == '^':
                                new_val = resolved_value ** rel_val
                            else:
                                new_val = resolved_value
                        
                        # Clamp to field range
                        new_val = max(
                            self.field_config.fields[rel_field]["min"], 
                            min(self.field_config.fields[rel_field]["max"], new_val)
                        )
                        
                        # Add to the related field's keyframes
                        parsed_keyframes[rel_field].append((time_val, new_val))
            except Exception as e:
                print(f"Error parsing keyframe '{kf_str}': {e}")
        
        # Sort keyframes by time for each field
        for field in parsed_keyframes:
            parsed_keyframes[field].sort(key=lambda x: x[0])
        
        # Process field_options to handle default transition types
        default_field_transitions = {}
        for field, options in field_options.items():
            # Save default transition type for the field
            # This allows for setting a different default with just the shorthand e.g. "g~" 
            default_field_transitions[field] = options.get("movement_type", "linear")
        
        # Interpolate between keyframes and handle hold/return behaviors
        for field in self.field_config.fields:
            # Get the keyframes for this field
            keyframes_list = parsed_keyframes[field]
            
            field_values = data["items"]["default"][field]
            
            # Initialize field with starting value from first keyframe if present 
            if len(keyframes_list) > 0:
                first_time, first_val = keyframes_list[0]
                first_idx = max(0, int(first_time / interval_seconds))
                
                # Set the initial value at the first keyframe
                if first_idx < num_points:
                    field_values[first_idx] = first_val
                    
                    # Fill from beginning to first keyframe if needed 
                    if first_idx > 0:
                        for i in range(first_idx):
                            field_values[i] = first_val
            
            # Skip interpolation if not enough keyframes
            if len(keyframes_list) < 2:
                continue
            
            # Process each segment between keyframes
            for i in range(len(keyframes_list) - 1):
                start_time, start_val = keyframes_list[i]
                end_time, end_val = keyframes_list[i + 1]
                
                # Special case for the last keyframe
                if i == len(keyframes_list) - 2 and end_time > (num_points - 3) * interval_seconds:
                    # This is the last keyframe pointing to near the end (within 2 intervals)
                    # Need to handle specially for smooth transitions
                    start_idx = int(start_time / interval_seconds)
                    if start_idx < 0:
                        start_idx = 0
                        
                    end_idx = num_points - 1  # Last point in the dataset
                    
                    # Calculate exact idx for the end time 
                    exact_end_idx = min(num_points - 1, int(end_time / interval_seconds))
                    
                    # For endpoint keyframes, set the value at the exact time specified
                    # This ensures the graph reaches the exact value specified in the keyframe
                    field_values[exact_end_idx] = end_val
                    
                    # For smooth transition, we need to interpolate from previous point
                    if field_options[field].get("movement_type") == "smooth":
                        steps = end_idx - start_idx
                        if steps > 1:
                            interpolated = self.interpolation_engine.interpolate(
                                start_val, end_val, steps, "smooth")
                            
                            for j, val in enumerate(interpolated):
                                idx = start_idx + j
                                if idx < num_points:
                                    field_values[idx] = val
                    continue
                    
                # Normal case - convert to indices
                start_idx = int(start_time / interval_seconds)
                end_idx = int(end_time / interval_seconds)
                
                # Check for out of bounds indices
                if start_idx < 0:
                    start_idx = 0
                
                # Handle edge case when end_idx is at or beyond the end of the dataset
                if end_idx >= num_points:
                    # Make sure we don't go out of bounds
                    end_idx = num_points - 1
                
                if end_idx <= start_idx:
                    continue
                
                # Number of steps
                steps = end_idx - start_idx
                
                # Get interpolation method 
                # First check if this specific keyframe has a movement type
                method = None
                
                # Store unique key for this keyframe based on field and time
                kf_key = f"{field}_{end_time}"
                
                # Look for method in the keyframe options
                if kf_key in field_options:
                    method = field_options[kf_key].get("movement_type", None)
                
                # If not found, use the default for this field
                if not method:
                    method = default_field_transitions.get(field, "linear")
                    
                # Set params for special methods
                params = {"power": field_options[field].get("pow", 2.0)} if method == "pow" else None
                
                # Interpolate
                interpolated = self.interpolation_engine.interpolate(start_val, end_val, steps, method, params)
                
                # Apply to data
                for j, val in enumerate(interpolated):
                    idx = start_idx + j
                    if idx < num_points:
                        field_values[idx] = val
                
                # Check if this keyframe has "return" post-behavior (^)
                if kf_key in field_options and field_options[kf_key].get("post_behavior") == "return":
                    # This is a pulse keyframe that should return to previous value
                    # Get next segment for the return trip
                    next_idx = end_idx + 1
                    if next_idx < num_points:
                        # Calculate how many steps for return
                        # By default use same number of steps for the return
                        return_steps = steps
                        
                        # Calculate return value - either previous value or specified
                        return_val = start_val  # Default return to previous value
                        
                        # Check if there's a specified return value
                        if "post_value" in field_options[kf_key]:
                            op, val = field_options[kf_key]["post_value"]
                            # Apply the operation to the previous value
                            if op == '+':
                                return_val = start_val + (val or 0)
                            elif op == '-':
                                return_val = start_val - (val or 0)
                            elif op == '*':
                                return_val = start_val * (val or 1)
                            elif op == '/':
                                return_val = start_val / (val or 1) if val != 0 else start_val
                        
                        # Make sure we don't go beyond array bounds
                        if next_idx + return_steps >= num_points:
                            return_steps = num_points - next_idx
                        
                        if return_steps > 0:
                            # Interpolate back
                            return_interpolated = self.interpolation_engine.interpolate(
                                end_val, return_val, return_steps, method, params)
                            
                            # Apply to data
                            for j, val in enumerate(return_interpolated):
                                idx = next_idx + j
                                if idx < num_points:
                                    field_values[idx] = val
            
            # Apply noise
            noise_amount = field_options[field].get("noise", 1.0) * noise_scale
            min_val = self.field_config.fields[field]["min"]
            max_val = self.field_config.fields[field]["max"]
            range_val = max_val - min_val
            
            for i in range(num_points):
                # Same noise calculation regardless of normalize flag
                # This makes normalize flag only affect how values are interpreted
                noise = random.uniform(-range_val * 0.01 * noise_amount, 
                                     range_val * 0.01 * noise_amount)
                
                # Apply noise and clamp
                field_values[i] = max(min_val, min(max_val, field_values[i] + noise))
            
            # Update data structure
            data["fields"][field]["values"] = field_values.copy()
    
    def _apply_default_pattern(self, 
                             data: Dict[str, Any], 
                             load: str,
                             interval_seconds: float,
                             num_points: int,
                             noise_scale: float) -> None:
        """
        Apply a default pattern based on load level.
        
        Args:
            data: Data dictionary to modify
            load: Load level ("low", "medium", "high")
            interval_seconds: Time between data points
            num_points: Number of data points
            noise_scale: Global noise multiplier
        """
        # Configure load-specific parameters
        load_factors = {
            "low": {"freq": 0.3, "min_pause": 60, "max_pause": 120, "intensity": 0.4},
            "medium": {"freq": 0.6, "min_pause": 20, "max_pause": 60, "intensity": 0.7},
            "high": {"freq": 1.0, "min_pause": 5, "max_pause": 20, "intensity": 0.9}
        }
        
        # Default configuration
        rise_time = int(30 / interval_seconds)  # 30 seconds to rise
        hold_time = int(120 / interval_seconds)  # 2 minutes at peak
        fall_time = int(60 / interval_seconds)   # 1 minute to fall
        
        # Total pattern length
        pattern_length = rise_time + hold_time + fall_time
        
        # Select primary field for pattern generation
        primary_field = next(iter(self.field_config.fields.keys()))
        
        # Generate patterns
        current_point = 0
        while current_point + pattern_length < num_points:
            # Decide whether to create a pattern based on frequency
            if random.random() < load_factors[load]["freq"] * (interval_seconds / 60):
                # Calculate peak value for primary field
                primary_max = self.field_config.fields[primary_field]["max"]
                primary_peak = primary_max * load_factors[load]["intensity"] * random.uniform(0.8, 1.0)
                
                # Generate pattern
                ramp_up = self.interpolation_engine.interpolate(
                    self.field_config.fields[primary_field]["min"], 
                    primary_peak, 
                    rise_time, 
                    "smooth"
                )
                
                hold = [primary_peak] * hold_time
                
                ramp_down = self.interpolation_engine.interpolate(
                    primary_peak, 
                    self.field_config.fields[primary_field]["min"], 
                    fall_time, 
                    "smooth"
                )
                
                pattern = ramp_up + hold + ramp_down
                
                # Apply pattern to primary field
                end_idx = min(current_point + len(pattern), num_points)
                for i in range(end_idx - current_point):
                    val = pattern[i]
                    data["items"]["default"][primary_field][current_point + i] = val
                    data["fields"][primary_field]["values"][current_point + i] = val
                
                # Apply correlated patterns to other fields
                for field in self.field_config.fields:
                    if field == primary_field:
                        continue
                    
                    # Calculate correlation factor
                    correlation = random.uniform(0.5, 0.9)
                    field_max = self.field_config.fields[field]["max"]
                    
                    # Apply correlated pattern
                    for i in range(end_idx - current_point):
                        val = min(pattern[i] * correlation, field_max)
                        data["items"]["default"][field][current_point + i] = val
                        data["fields"][field]["values"][current_point + i] = val
                
                # Move pointer
                current_point += pattern_length
            else:
                # Add a pause
                pause_length = random.randint(
                    int(load_factors[load]["min_pause"] / interval_seconds),
                    int(load_factors[load]["max_pause"] / interval_seconds)
                )
                current_point += pause_length
        
        # Apply noise to all fields
        for field in self.field_config.fields:
            noise_amount = self.field_config.fields[field].get("noise_amount", 1.0) * noise_scale
            field_min = self.field_config.fields[field]["min"]
            field_max = self.field_config.fields[field]["max"]
            field_range = field_max - field_min
            
            for i in range(num_points):
                noise = random.uniform(-field_range * 0.01 * noise_amount, 
                                     field_range * 0.01 * noise_amount)
                
                current_val = data["items"]["default"][field][i]
                noised_val = max(field_min, min(field_max, current_val + noise))
                
                data["items"]["default"][field][i] = noised_val
                data["fields"][field]["values"][i] = noised_val
    
    def _apply_masks(self, 
                   data: Dict[str, Any], 
                   masks: List[str],
                   interval_seconds: float) -> None:
        """
        Apply masks to the data.
        
        Args:
            data: Data dictionary to modify
            masks: List of mask expressions
            interval_seconds: Time between data points
        """
        if not masks:
            return
        
        # Apply masks using MaskEngine
        field_values = {field: data["items"]["default"][field] for field in self.field_config.fields}
        self.mask_engine.apply_masks(
            field_values, 
            masks, 
            data["seconds_timestamps"], 
            self.field_config.fields
        )
        
        # Update data structure
        for field in self.field_config.fields:
            data["fields"][field]["values"] = field_values[field].copy()
            data["items"]["default"][field] = field_values[field].copy()
    
    def to_raw_format(self, data: Dict[str, Any], normalize: bool = False) -> Dict[str, Any]:
        """
        Convert internal data structure to raw timeslots format.
        
        Args:
            data: Internal data structure
            normalize: If True, normalize all output values to 0-1 range
            
        Returns:
            Dict in raw timeslots format
        """
        return RawFormatOutput.format(data, self.field_config.fields, normalize)
    
    def to_structured_format(self, data: Dict[str, Any], normalize: bool = False) -> Dict[str, Any]:
        """
        Convert internal data structure to structured timeslots format.
        
        Args:
            data: Internal data structure
            normalize: If True, normalize all output values to 0-1 range
            
        Returns:
            Dict in structured timeslots format
        """
        return StructuredFormatOutput.format(data, self.field_config.fields, normalize)
    
    def save(self, data: Dict[str, Any], filename: str, format: str = "structured", 
             output_format: str = "json", normalize: bool = False) -> None:
        """
        Save data to a file in the specified format.
        
        Args:
            data: Internal data structure
            filename: Output filename
            format: Output data format ("raw" or "structured")
            output_format: Output file format ("json", "pkl", "npy")
            normalize: If True, normalize all output values to 0-1 range
        """
        # Determine output format from file extension if not specified
        if output_format == "auto":
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            if ext == ".json":
                output_format = "json"
            elif ext == ".pkl":
                output_format = "pkl"
            elif ext == ".npy":
                output_format = "npy"
            else:
                output_format = "json"  # Default
        
        # Convert data to specified format
        if format == "raw":
            formatted_data = self.to_raw_format(data, normalize)
            RawFormatOutput.save(formatted_data, filename, output_format)
        else:  # Default to structured
            formatted_data = self.to_structured_format(data, normalize)
            StructuredFormatOutput.save(formatted_data, filename, output_format)
    
    def load(self, filename: str) -> Dict[str, Any]:
        """
        Load data from a file.
        
        Args:
            filename: Input filename
            
        Returns:
            Dict containing loaded data
        """
        # Determine file format from extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        
        if ext == ".json":
            with open(filename, "r") as f:
                loaded_data = json.load(f)
        elif ext == ".pkl":
            with open(filename, "rb") as f:
                loaded_data = pickle.load(f)
        else:
            try:
                import numpy as np
                loaded_data = np.load(filename, allow_pickle=True).item()
            except (ImportError, ValueError, IOError) as e:
                raise ValueError(f"Unsupported file format or error loading file: {e}")
        
        # Check if it's a valid data structure
        if not isinstance(loaded_data, dict):
            raise ValueError("Invalid data format")
        
        # Check format type
        if "type" in loaded_data:
            if loaded_data["type"] == "ts-raw":
                # Convert raw format to internal format
                return self._convert_raw_to_internal(loaded_data)
            elif loaded_data["type"] == "ts-structured":
                # Convert structured format to internal format
                return self._convert_structured_to_internal(loaded_data)
        
        # Try to determine format from structure
        if "timeslots" in loaded_data and "data" in loaded_data:
            # Likely structured format
            return self._convert_structured_to_internal(loaded_data)
        elif "data" in loaded_data and any("timeseries" in d for d in loaded_data["data"].values()):
            # Likely raw format
            return self._convert_raw_to_internal(loaded_data)
        
        # If all else fails, return as is (might not work correctly)
        return loaded_data
    
    def _convert_raw_to_internal(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw format data to internal format.
        
        Args:
            raw_data: Data in raw format
            
        Returns:
            Dict in internal format
        """
        result = {
            "timestamps": [],
            "seconds_timestamps": [],
            "fields": {},
            "items": {"default": {}}
        }
        
        # Extract field configurations
        for field, config in raw_data.get("fields", {}).items():
            result["fields"][field] = {
                "values": [],
                "config": config
            }
            result["items"]["default"][field] = []
        
        # Get first item to extract timestamps
        if raw_data.get("data") and len(raw_data["data"]) > 0:
            item_name = next(iter(raw_data["data"].keys()))
            item_data = raw_data["data"][item_name]
            
            if "timeseries" in item_data:
                # Get first field to extract timestamps
                if len(item_data["timeseries"]) > 0:
                    field_name = next(iter(item_data["timeseries"].keys()))
                    timestamps = list(item_data["timeseries"][field_name].keys())
                    timestamps.sort()  # Ensure chronological order
                    
                    # Convert timestamps to datetime objects
                    result["timestamps"] = [
                        datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps
                    ]
                    # TODO: make UTC format if flagged
                    
                    # Calculate seconds from start
                    start_time = result["timestamps"][0]
                    result["seconds_timestamps"] = [
                        (ts - start_time).total_seconds() for ts in result["timestamps"]
                    ]
                    
                    # Extract values for each field and item
                    for item_name, item_data in raw_data["data"].items():
                        if item_name not in result["items"]:
                            result["items"][item_name] = {}
                        
                        for field, field_data in item_data["timeseries"].items():
                            if field in result["fields"]:
                                values = [field_data.get(ts, 0) for ts in timestamps]
                                result["items"][item_name][field] = values
                                if item_name == "default":
                                    result["fields"][field]["values"] = values
        
        return result
    
    def _convert_structured_to_internal(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert structured format data to internal format.
        
        Args:
            structured_data: Data in structured format
            
        Returns:
            Dict in internal format
        """
        result = {
            "timestamps": [],
            "seconds_timestamps": [],
            "fields": {},
            "items": {"default": {}}
        }
        
        # Extract field configurations
        for field, config in structured_data.get("fields", {}).items():
            result["fields"][field] = {
                "values": [],
                "config": config
            }
            result["items"]["default"][field] = []
        
        # Convert timestamps
        if "timeslots" in structured_data:
            timestamps = structured_data["timeslots"]
            
            # Convert timestamps to datetime objects
            result["timestamps"] = [
                datetime.strptime(ts, "%Y-%m-%d %H:%M:%S") for ts in timestamps
            ]
            
            # Calculate seconds from start
            if result["timestamps"]:
                start_time = result["timestamps"][0]
                result["seconds_timestamps"] = [
                    (ts - start_time).total_seconds() for ts in result["timestamps"]
                ]
            
            # Extract values for each field and item
            for item_name, item_data in structured_data.get("data", {}).items():
                if item_name not in result["items"]:
                    result["items"][item_name] = {}
                
                for field, values in item_data.items():
                    if field in result["fields"]:
                        result["items"][item_name][field] = values
                        if item_name == "default":
                            result["fields"][field]["values"] = values
        
        return result
    
    def _parse_keyframe_time(self, time_part: str, total_seconds: float = 3600.0) -> float:
        """
        Parse a keyframe time string into seconds.
        This is a helper method that exposes the keyframe parser's time parsing logic.
        
        Args:
            time_part: Time part of keyframe string (e.g., "30s", "5m", "1h", "1:30")
            total_seconds: Total seconds for relative times
            
        Returns:
            Time in seconds
        """
        return self.keyframe_parser._parse_time(time_part, total_seconds)
    
    def resample(self, data: Dict[str, Any], method: str, 
                target_interval: Optional[float] = None, 
                target_points: Optional[int] = None) -> Dict[str, Any]:
        """
        Resample the data using the specified method.
        
        Args:
            data: Internal data structure
            method: Resampling method ("mean", "minmax", "linear", "lttb")
            target_interval: Target interval in seconds (for mean, minmax, linear)
            target_points: Target number of points (for lttb)
            
        Returns:
            Dict containing resampled data
        """
        if not data or "timestamps" not in data or "items" not in data:
            raise ValueError("Invalid data structure")
        
        original_timestamps = data["seconds_timestamps"]
        result = {
            "timestamps": [],
            "seconds_timestamps": [],
            "fields": {},
            "items": {"default": {}}
        }
        
        # Apply appropriate resampling method
        if method == "mean" and target_interval is not None:
            for field in self.field_config.fields:
                if field in data["items"]["default"]:
                    values = data["items"]["default"][field]
                    new_times, new_values = self.resampler.mean_resample(
                        original_timestamps, values, target_interval
                    )
                    
                    if not result["seconds_timestamps"]:
                        result["seconds_timestamps"] = new_times
                        result["timestamps"] = [
                            data["timestamps"][0] + timedelta(seconds=t) 
                            for t in new_times
                        ]
                    
                    result["items"]["default"][field] = new_values
                    result["fields"][field] = {
                        "values": new_values,
                        "config": self.field_config.fields[field]
                    }
        
        elif method == "minmax" and target_interval is not None:
            for field in self.field_config.fields:
                if field in data["items"]["default"]:
                    values = data["items"]["default"][field]
                    new_times, min_values, max_values = self.resampler.minmax_resample(
                        original_timestamps, values, target_interval
                    )
                    
                    if not result["seconds_timestamps"]:
                        result["seconds_timestamps"] = new_times
                        result["timestamps"] = [
                            data["timestamps"][0] + timedelta(seconds=t) 
                            for t in new_times
                        ]
                    
                    # Store min values in default item
                    result["items"]["default"][field] = min_values
                    result["fields"][field] = {
                        "values": min_values,
                        "config": self.field_config.fields[field]
                    }
                    
                    # Add max values in a separate item
                    if "max" not in result["items"]:
                        result["items"]["max"] = {}
                    result["items"]["max"][field] = max_values
        
        elif method == "lttb" and target_points is not None:
            for field in self.field_config.fields:
                if field in data["items"]["default"]:
                    values = data["items"]["default"][field]
                    new_times, new_values = self.resampler.lttb_resample(
                        original_timestamps, values, target_points
                    )
                    
                    if not result["seconds_timestamps"]:
                        result["seconds_timestamps"] = new_times
                        result["timestamps"] = [
                            data["timestamps"][0] + timedelta(seconds=t) 
                            for t in new_times
                        ]
                    
                    result["items"]["default"][field] = new_values
                    result["fields"][field] = {
                        "values": new_values,
                        "config": self.field_config.fields[field]
                    }
        
        elif method == "linear" and target_interval is not None:
            # Create new timestamps at regular intervals
            start_time = original_timestamps[0]
            end_time = original_timestamps[-1]
            new_timestamps = []
            current_time = start_time
            
            while current_time <= end_time:
                new_timestamps.append(current_time)
                current_time += target_interval
            
            result["seconds_timestamps"] = new_timestamps
            result["timestamps"] = [
                data["timestamps"][0] + timedelta(seconds=t) 
                for t in new_timestamps
            ]
            
            # Interpolate values at new timestamps
            for field in self.field_config.fields:
                if field in data["items"]["default"]:
                    values = data["items"]["default"][field]
                    new_values = self.resampler.linear_interpolate_resample(
                        original_timestamps, values, new_timestamps
                    )
                    
                    result["items"]["default"][field] = new_values
                    result["fields"][field] = {
                        "values": new_values,
                        "config": self.field_config.fields[field]
                    }
        
        else:
            raise ValueError(f"Invalid resampling method or parameters: {method}")
        
        return result