"""Resampling algorithms for ChronoSynth."""

from typing import List, Tuple, Optional
import math


class Resampler:
    """Provides methods for resampling time series data."""
    
    @staticmethod
    def mean_resample(timestamps: List[float], values: List[float], interval: float) -> Tuple[List[float], List[float]]:
        """
        Resample time series using mean aggregation.
        
        Args:
            timestamps: Original timestamps (in seconds from start)
            values: Original values
            interval: Target interval (in seconds)
            
        Returns:
            tuple: (resampled_timestamps, resampled_values)
        """
        if not timestamps or not values:
            return [], []
        
        result_times = []
        result_values = []
        
        current_bin_start = timestamps[0]
        bin_values = []
        
        for t, v in zip(timestamps, values):
            if t < current_bin_start + interval:
                bin_values.append(v)
            else:
                if bin_values:
                    result_times.append(current_bin_start)
                    result_values.append(sum(bin_values) / len(bin_values))
                
                # Move to next bin, handle gaps
                current_bin_start += interval
                while t >= current_bin_start + interval:
                    current_bin_start += interval
                
                bin_values = [v]
        
        # Handle last bin
        if bin_values:
            result_times.append(current_bin_start)
            result_values.append(sum(bin_values) / len(bin_values))
        
        return result_times, result_values
    
    @staticmethod
    def minmax_resample(timestamps: List[float], values: List[float], interval: float) -> Tuple[List[float], List[float], List[float]]:
        """
        Resample preserving min and max values in each bin.
        
        Args:
            timestamps: Original timestamps (in seconds from start)
            values: Original values
            interval: Target interval (in seconds)
            
        Returns:
            tuple: (resampled_timestamps, min_values, max_values)
        """
        if not timestamps or not values:
            return [], [], []
        
        result_times = []
        result_min = []
        result_max = []
        
        current_bin_start = timestamps[0]
        bin_values = []
        
        for t, v in zip(timestamps, values):
            if t < current_bin_start + interval:
                bin_values.append(v)
            else:
                if bin_values:
                    result_times.append(current_bin_start)
                    result_min.append(min(bin_values))
                    result_max.append(max(bin_values))
                
                current_bin_start += interval
                while t >= current_bin_start + interval:
                    current_bin_start += interval
                
                bin_values = [v]
        
        # Handle last bin
        if bin_values:
            result_times.append(current_bin_start)
            result_min.append(min(bin_values))
            result_max.append(max(bin_values))
        
        return result_times, result_min, result_max
    
    @staticmethod
    def linear_interpolate_resample(timestamps: List[float], values: List[float], 
                                  target_timestamps: List[float]) -> List[float]:
        """
        Resample time series using linear interpolation.
        
        Args:
            timestamps: Original timestamps (in seconds from start)
            values: Original values
            target_timestamps: Target timestamps for resampling
            
        Returns:
            list: Resampled values at target timestamps
        """
        if not timestamps or not values or not target_timestamps:
            return []
        
        result = []
        
        for target_t in target_timestamps:
            # Find surrounding points
            if target_t <= timestamps[0]:
                # Before first point
                result.append(values[0])
            elif target_t >= timestamps[-1]:
                # After last point
                result.append(values[-1])
            else:
                # Find indices of surrounding points
                right_idx = next(i for i, t in enumerate(timestamps) if t >= target_t)
                left_idx = right_idx - 1
                
                # Linear interpolation
                t_left = timestamps[left_idx]
                t_right = timestamps[right_idx]
                v_left = values[left_idx]
                v_right = values[right_idx]
                
                # Calculate interpolated value
                t_factor = (target_t - t_left) / (t_right - t_left) if t_right > t_left else 0
                interp_val = v_left + t_factor * (v_right - v_left)
                
                result.append(interp_val)
        
        return result
    
    @staticmethod
    def lttb_resample(timestamps: List[float], values: List[float], target_points: int) -> Tuple[List[float], List[float]]:
        """
        Largest-Triangle-Three-Buckets downsampling.
        
        Args:
            timestamps: Original timestamps (in seconds from start)
            values: Original values
            target_points: Target number of points
            
        Returns:
            tuple: (resampled_timestamps, resampled_values)
        """
        if len(timestamps) <= target_points:
            return timestamps, values
        
        # Always keep first and last points
        result_times = [timestamps[0]]
        result_values = [values[0]]
        
        # Bucket size
        bucket_size = (len(timestamps) - 2) / (target_points - 2)
        
        # For each output point
        for i in range(1, target_points - 1):
            # Calculate the average point for this bucket
            bucket_start = int((i - 1) * bucket_size) + 1
            bucket_end = int(i * bucket_size) + 1
            
            if bucket_start >= len(timestamps) or bucket_end >= len(timestamps):
                break
            
            # Calculate the average point of the next bucket
            next_bucket_start = int(i * bucket_size) + 1
            next_bucket_end = min(int((i + 1) * bucket_size) + 1, len(timestamps))
            
            next_avg_x = sum(timestamps[next_bucket_start:next_bucket_end]) / (next_bucket_end - next_bucket_start)
            next_avg_y = sum(values[next_bucket_start:next_bucket_end]) / (next_bucket_end - next_bucket_start)
            
            # Find point in current bucket that creates largest triangle with
            # the last selected point and the average of the next bucket
            prev_x, prev_y = result_times[-1], result_values[-1]
            
            max_area = -1
            max_idx = bucket_start
            
            for j in range(bucket_start, bucket_end):
                # Calculate triangle area
                area = abs((prev_x - next_avg_x) * (values[j] - prev_y) - 
                         (prev_x - timestamps[j]) * (next_avg_y - prev_y)) * 0.5
                
                if area > max_area:
                    max_area = area
                    max_idx = j
            
            # Add the point that forms the largest triangle
            result_times.append(timestamps[max_idx])
            result_values.append(values[max_idx])
        
        # Add the last point
        result_times.append(timestamps[-1])
        result_values.append(values[-1])
        
        return result_times, result_values