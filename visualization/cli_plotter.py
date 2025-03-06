"""CLI-based plotting for TimeSeriesGenerator."""

import os
from typing import Dict, List, Any, Optional, Tuple


class CLIPlotter:
    """Terminal-based plotting for time series data."""
    
    def __init__(self):
        """Initialize the plotter."""
        self.has_matplotlib = False
        
        # Try to import matplotlib if available
        try:
            import matplotlib.pyplot as plt
            self.plt = plt
            self.has_matplotlib = True
        except ImportError:
            pass
    
    def plot(self, data: Dict[str, Any], title: Optional[str] = None, 
            field_config: Optional[Dict[str, Dict[str, Any]]] = None) -> bool:
        """
        Plot the data in the terminal using matplotlib.
        
        Args:
            data: Internal data structure
            title: Plot title
            field_config: Field configuration dictionary
            
        Returns:
            bool: True if plotted successfully, False otherwise
        """
        if not self.has_matplotlib:
            print("Matplotlib is not available. Install it using 'pip install matplotlib'.")
            return False
        
        if not data or "timestamps" not in data or "items" not in data:
            print("Invalid data structure for plotting.")
            return False
        
        # Create a figure
        plt = self.plt
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Use field_config if provided, otherwise use data["fields"]
        if field_config is None and "fields" in data:
            # Extract field config from data
            field_config = {}
            for field, field_data in data["fields"].items():
                if "config" in field_data:
                    field_config[field] = field_data["config"]
        
        # Plot each field for the default item
        if "default" in data["items"]:
            for field, values in data["items"]["default"].items():
                # Get color if available
                color = None
                if field_config and field in field_config:
                    color = field_config[field].get("color")
                
                ax.plot(data["timestamps"], values, label=field, color=color)
        
        # Set title and labels
        ax.set_title(title or "Time Series Data")
        ax.set_xlabel("Time")
        ax.set_ylabel("Value")
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        # Show the plot
        plt.tight_layout()
        plt.show()
        
        return True
    
    def plot_ascii(self, data: Dict[str, Any], width: int = 80, height: int = 20, 
                 field: Optional[str] = None) -> bool:
        """
        Plot the data as ASCII art in the terminal.
        
        Args:
            data: Internal data structure
            width: Plot width in characters
            height: Plot height in characters
            field: Field to plot (plots all fields if None)
            
        Returns:
            bool: True if plotted successfully, False otherwise
        """
        if not data or "timestamps" not in data or "items" not in data:
            print("Invalid data structure for plotting.")
            return False
        
        # Get terminal size if possible
        try:
            terminal_size = os.get_terminal_size()
            width = min(width, terminal_size.columns - 10)
            height = min(height, terminal_size.lines - 5)
        except (AttributeError, OSError):
            pass
        
        # Select fields to plot
        fields_to_plot = []
        if field is not None:
            if field in data["items"]["default"]:
                fields_to_plot = [field]
            else:
                print(f"Field '{field}' not found in data.")
                return False
        else:
            fields_to_plot = list(data["items"]["default"].keys())
        
        # Plot each field
        for field in fields_to_plot:
            values = data["items"]["default"][field]
            
            # Skip if no values
            if not values:
                continue
            
            # Get min and max values
            min_val = min(values)
            max_val = max(values)
            value_range = max_val - min_val
            
            # Avoid division by zero
            if value_range <= 0:
                value_range = 1
            
            # Create plot area
            plot = [[' ' for _ in range(width)] for _ in range(height)]
            
            # Scale values to plot height
            scaled_values = [int((height - 1) * (v - min_val) / value_range) for v in values]
            
            # Sample values to fit plot width
            step = max(1, len(values) // width)
            sampled_indices = range(0, len(values), step)
            sampled_values = [scaled_values[i] for i in sampled_indices]
            
            # Draw plot
            for x, y in enumerate(sampled_values[:width]):
                for i in range(height):
                    if i == height - 1 - y:
                        plot[i][x] = '*'
                    elif i == height - 1:
                        plot[i][x] = '-'  # x-axis
            
            # Add y-axis
            for i in range(height):
                plot[i][0] = '|'
            
            # Print field name and plot
            print(f"\n{field} ({min_val:.2f} to {max_val:.2f}):")
            for row in plot:
                print(''.join(row))
            print()
        
        return True