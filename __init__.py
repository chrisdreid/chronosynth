"""
ChronoSynth - A powerful, flexible library for generating synthetic time series data
with advanced configuration options, intuitive keyframe controls, and multiple output formats.

Core functionality works with no dependencies, with optional enhanced capabilities when 
libraries like numpy, pandas, matplotlib, and svgwrite are available.
"""

from .core.generator import TimeSeriesGenerator
from .core.field_config import FieldConfig
from .core.keyframe_parser import KeyframeParser
from .core.interpolation import InterpolationEngine
from .core.mask import MaskEngine
from .core.resampler import Resampler

__version__ = "1.0.0"
__all__ = [
    "TimeSeriesGenerator",
    "FieldConfig",
    "KeyframeParser",
    "InterpolationEngine",
    "MaskEngine",
    "Resampler"
]