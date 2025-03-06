"""Field configuration management for ChronoSynth."""

import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FieldConfig:
    """Manages field definitions and properties."""
    
    def __init__(self, config: Optional[str] = None):
        """
        Initialize field configurations with json, defaults or from a file.
        
        Args:
            config: Optional path to a JSON configuration file or json string
        """
        # Default field configurations
        self.fields = {}
        default_fields = {
            "alpha": {
                "shorthand": "a",
                "data_type": "float",
                "min": 0.0,
                "max": 100.0,
                "mean": 20.0,
                "color": "blue",
                "movement_type": "linear",
                "noise_amount": 0.5
            },
            "beta": {
                "shorthand": "b",
                "data_type": "float",
                "min": 0.0,
                "max": 32.0,
                "mean": 8.0,
                "color": "green",
                "movement_type": "linear",
                "noise_amount": 0.3
            }
        }
        
        # Build shorthand lookup map
        self.shorthand_map = {}
        self._rebuild_shorthand_map()
        
        # Load custom config if provided
        if config:
            has_config = False
            if os.path.exists(config):
                has_config = self.load_from_file(config)
                logger.info(f"Loaded config from file: {config}")
                logger.info(f"Fields configured: {list(self.fields.keys())}")
                # Show sample color values
                for field_name, field_config in self.fields.items():
                    if 'color' in field_config:
                        logger.info(f"Field {field_name} has color: {field_config['color']}")
            
            if not has_config:
                try:
                    cfg_json = json.loads(config)
                    has_config = self.load_from_dict(cfg_json)
                except Exception as e:
                    pass
            if not has_config:
                logger.error(f"Failed to load config: {config}")

        else:
            self.load_from_dict(default_fields)

    
    def _rebuild_shorthand_map(self):
        """Rebuild the shorthand lookup map."""
        self.shorthand_map = {
            config["shorthand"]: field_name 
            for field_name, config in self.fields.items()
        }
    
    def load_from_file(self, config_file: str, append: bool = False) -> bool:
        """
        Load configuration from a JSON file.
        
        Args:
            config_file: Path to a JSON configuration file
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not append:
            self.fields = {}
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Update or add field configurations
            for field, field_config in config.items():
                if field in self.fields:
                    self.fields[field].update(field_config)
                else:
                    self.fields[field] = field_config
            
            # Rebuild shorthand map
            self._rebuild_shorthand_map()
            return True
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
            return False
    
    def load_from_dict(self, config: Dict[str, Dict[str, Any]], append: bool = False) -> bool:
        """
        Load configuration from a dictionary.
        
        Args:
            config: Dictionary containing field configurations
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if not append:
            self.fields = {}

        try:
            # Update or add field configurations
            for field, field_config in config.items():
                if field in self.fields:
                    self.fields[field].update(field_config)
                else:
                    self.fields[field] = field_config
            
            # Rebuild shorthand map
            self._rebuild_shorthand_map()
            return True
        except Exception as e:
            logger.error(f"Failed to load config dict: {e}")
            return False
    
    def get_field(self, field_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Dict containing field configuration
        """
        return self.fields.get(field_name, {})
    
    def get_field_by_shorthand(self, shorthand: str) -> Dict[str, Any]:
        """
        Get the configuration for a field by its shorthand.
        
        Args:
            shorthand: Shorthand of the field
            
        Returns:
            Tuple containing field name and configuration
        """
        field_name = self.shorthand_map.get(shorthand)
        if field_name:
            return field_name, self.fields.get(field_name, {})
        return None, {}
    
    def add_field(self, field_name: str, config: Dict[str, Any]) -> bool:
        """
        Add a new field configuration.
        
        Args:
            field_name: Name of the field
            config: Configuration dictionary
            
        Returns:
            bool: True if added successfully, False if field exists
        """
        if field_name in self.fields:
            return False
        
        self.fields[field_name] = config
        
        # Update shorthand map
        if "shorthand" in config:
            self.shorthand_map[config["shorthand"]] = field_name
        
        return True
    
    def update_field(self, field_name: str, config: Dict[str, Any]) -> bool:
        """
        Update an existing field configuration.
        
        Args:
            field_name: Name of the field
            config: Configuration dictionary
            
        Returns:
            bool: True if updated successfully, False if field doesn't exist
        """
        if field_name not in self.fields:
            return False
        
        old_shorthand = self.fields[field_name].get("shorthand")
        self.fields[field_name].update(config)
        
        # Update shorthand map if shorthand changed
        new_shorthand = self.fields[field_name].get("shorthand")
        if old_shorthand != new_shorthand:
            if old_shorthand in self.shorthand_map:
                del self.shorthand_map[old_shorthand]
            if new_shorthand:
                self.shorthand_map[new_shorthand] = field_name
        
        return True
    
    def get_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all field configurations.
        
        Returns:
            Dict containing all field configurations
        """
        return self.fields
    
    def get_shorthand_map(self) -> Dict[str, str]:
        """
        Get the shorthand to field name map.
        
        Returns:
            Dict mapping shorthands to field names
        """
        return self.shorthand_map