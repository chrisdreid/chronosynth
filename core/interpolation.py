"""Interpolation methods for ChronoSynth."""

import math
from typing import List, Dict, Any, Optional


class InterpolationEngine:
    """Handles interpolation between keyframe points with enhanced behaviors."""
    
    @staticmethod
    def interpolate(start_val: float, end_val: float, steps: int, 
                   method: str = "linear", params: Optional[Dict[str, Any]] = None) -> List[float]:
        """
        Interpolate between two values using specified method.
        
        Args:
            start_val: Starting value
            end_val: Ending value
            steps: Number of steps
            method: Interpolation method
            params: Optional parameters for the method
            
        Returns:
            list: Interpolated values
        """
        if steps < 1:
            return []
        
        if steps == 1:
            return [start_val]
        
        # Dispatch to appropriate method
        if method == "linear":
            return InterpolationEngine.linear(start_val, end_val, steps)
        elif method == "smooth":
            return InterpolationEngine.smooth(start_val, end_val, steps)
        elif method == "step":
            return InterpolationEngine.step(start_val, end_val, steps)
        elif method == "pulse":
            # For pulse, we go to the target and then back to start
            # This is handled in the generator for better control
            return InterpolationEngine.pulse(start_val, end_val, steps)
        elif method == "sin":
            return InterpolationEngine.sin(start_val, end_val, steps)
        elif method == "pow":
            power = params.get("power", 2.0) if params else 2.0
            return InterpolationEngine.pow(start_val, end_val, steps, power)
        elif method == "hold":
            # Hold just keeps the same value throughout
            return [start_val] * steps
        else:
            # Default to linear
            return InterpolationEngine.linear(start_val, end_val, steps)
    
    @staticmethod
    def linear(start_val: float, end_val: float, steps: int) -> List[float]:
        """Linear interpolation."""
        step_size = (end_val - start_val) / (steps - 1)
        return [start_val + i * step_size for i in range(steps)]
    
    @staticmethod
    def smooth(start_val: float, end_val: float, steps: int) -> List[float]:
        """Smooth (cosine) interpolation."""
        result = []
        diff = end_val - start_val
        
        for i in range(steps):
            t = i / (steps - 1)
            # Cosine easing
            factor = (1 - math.cos(t * math.pi)) / 2
            result.append(start_val + factor * diff)
        
        return result
    
    @staticmethod
    def step(start_val: float, end_val: float, steps: int) -> List[float]:
        """Step function (sudden change)."""
        return [start_val] * (steps - 1) + [end_val]
    
    @staticmethod
    def pulse(start_val: float, end_val: float, steps: int) -> List[float]:
        """Pulse function (up then down)."""
        mid = steps // 2
        
        # Rising part
        rise = []
        for i in range(mid):
            t = i / (mid - 1) if mid > 1 else 1
            rise.append(start_val + t * (end_val - start_val))
        
        # Falling part
        fall = []
        for i in range(steps - mid):
            t = i / (steps - mid - 1) if (steps - mid) > 1 else 0
            fall.append(end_val - t * (end_val - start_val))
        
        # Combine
        if len(fall) > 0:
            return rise + fall
        else:
            return rise
    
    @staticmethod
    def sin(start_val: float, end_val: float, steps: int) -> List[float]:
        """Sine wave interpolation."""
        result = []
        
        for i in range(steps):
            t = i / (steps - 1)
            # Sine wave
            factor = math.sin(t * math.pi)
            result.append(start_val + factor * (end_val - start_val))
        
        return result
    
    @staticmethod
    def pow(start_val: float, end_val: float, steps: int, power: float = 2.0) -> List[float]:
        """Power function interpolation."""
        result = []
        diff = end_val - start_val
        
        for i in range(steps):
            t = i / (steps - 1)
            # Power function
            factor = t ** power
            result.append(start_val + factor * diff)
        
        return result