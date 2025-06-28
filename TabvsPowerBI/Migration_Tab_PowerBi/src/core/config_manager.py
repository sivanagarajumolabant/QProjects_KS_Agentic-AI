"""
Configuration Manager for Generic Tableau to Power BI Migration Engine
Handles all configuration settings, mappings, and rules for universal conversion.
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

class ConfigManager:
    """Manages configuration for universal Tableau to Power BI conversion"""
    
    def __init__(self, config_dir: str = None):
        """Initialize configuration manager"""
        if config_dir is None:
            # Default to config directory relative to this file
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
        
        self._tableau_mappings = None
        self._function_mappings = None
        self._visual_mappings = None
        self._data_type_mappings = None
        self._connection_mappings = None
        
    def load_tableau_mappings(self) -> Dict[str, Any]:
        """Load Tableau version and schema mappings"""
        if self._tableau_mappings is None:
            mapping_file = self.config_dir / "tableau_mappings.json"
            self._tableau_mappings = self._load_json_config(mapping_file)
        return self._tableau_mappings
    
    def load_function_mappings(self) -> Dict[str, Any]:
        """Load Tableau function to DAX function mappings"""
        if self._function_mappings is None:
            mapping_file = self.config_dir / "function_mappings.json"
            self._function_mappings = self._load_json_config(mapping_file)
        return self._function_mappings
    
    def load_visual_mappings(self) -> Dict[str, Any]:
        """Load Tableau visual to Power BI visual mappings"""
        if self._visual_mappings is None:
            mapping_file = self.config_dir / "visual_mappings.json"
            self._visual_mappings = self._load_json_config(mapping_file)
        return self._visual_mappings
    
    def load_data_type_mappings(self) -> Dict[str, Any]:
        """Load data type mappings between Tableau and Power BI"""
        if self._data_type_mappings is None:
            mapping_file = self.config_dir / "data_type_mappings.json"
            self._data_type_mappings = self._load_json_config(mapping_file)
        return self._data_type_mappings
    
    def load_connection_mappings(self) -> Dict[str, Any]:
        """Load data source connection mappings"""
        if self._connection_mappings is None:
            mapping_file = self.config_dir / "connection_mappings.json"
            self._connection_mappings = self._load_json_config(mapping_file)
        return self._connection_mappings
    
    def get_function_mapping(self, tableau_function: str) -> Optional[str]:
        """Get Power BI DAX equivalent for any Tableau function"""
        mappings = self.load_function_mappings()
        
        # Check in different function categories
        for category in mappings.values():
            if isinstance(category, dict) and tableau_function in category:
                return category[tableau_function]
        
        return None
    
    def get_visual_mapping(self, tableau_visual_type: str, subtype: str = None) -> Optional[str]:
        """Get Power BI visual equivalent for any Tableau visual type"""
        mappings = self.load_visual_mappings()
        
        if tableau_visual_type in mappings.get("chart_mappings", {}):
            chart_mapping = mappings["chart_mappings"][tableau_visual_type]
            if subtype and subtype in chart_mapping:
                return chart_mapping[subtype]
            elif "default" in chart_mapping:
                return chart_mapping["default"]
            elif isinstance(chart_mapping, str):
                return chart_mapping
        
        return None
    
    def get_data_type_mapping(self, tableau_data_type: str) -> str:
        """Get Power BI data type for any Tableau data type"""
        mappings = self.load_data_type_mappings()
        return mappings.get("type_mappings", {}).get(tableau_data_type, "String")
    
    def get_connection_mapping(self, tableau_connection_class: str) -> Optional[Dict[str, Any]]:
        """Get Power BI connection configuration for any Tableau connection"""
        mappings = self.load_connection_mappings()
        return mappings.get("connection_mappings", {}).get(tableau_connection_class)
    
    def get_tableau_version_info(self, version: str) -> Dict[str, Any]:
        """Get version-specific information for any Tableau version"""
        mappings = self.load_tableau_mappings()
        version_info = mappings.get("version_mappings", {}).get(version, {})
        
        # If exact version not found, try to find compatible version
        if not version_info:
            version_info = self._find_compatible_version(version, mappings.get("version_mappings", {}))
        
        return version_info
    
    def _find_compatible_version(self, target_version: str, version_mappings: Dict[str, Any]) -> Dict[str, Any]:
        """Find compatible version mapping for unsupported versions"""
        try:
            target_major = float(target_version.split('.')[0])
            
            # Find the closest supported version
            compatible_version = None
            min_diff = float('inf')
            
            for version, mapping in version_mappings.items():
                try:
                    version_major = float(version.split('.')[0])
                    diff = abs(target_major - version_major)
                    if diff < min_diff:
                        min_diff = diff
                        compatible_version = mapping
                except:
                    continue
            
            return compatible_version or {}
        except:
            # Return default configuration if version parsing fails
            return version_mappings.get("default", {})
    
    def _load_json_config(self, config_file: Path) -> Dict[str, Any]:
        """Load JSON configuration file with error handling"""
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default configuration if file doesn't exist
                return self._get_default_config(config_file.name)
        except Exception as e:
            print(f"Warning: Could not load config file {config_file}: {e}")
            return self._get_default_config(config_file.name)
    
    def _get_default_config(self, config_filename: str) -> Dict[str, Any]:
        """Get default configuration when config file is not available"""
        defaults = {
            "tableau_mappings.json": {
                "version_mappings": {
                    "default": {
                        "supported": True,
                        "schema_version": "18.1",
                        "features": ["basic_charts", "calculations", "dashboards"]
                    }
                }
            },
            "function_mappings.json": {
                "aggregation_functions": {
                    "SUM": "SUM",
                    "AVG": "AVERAGE",
                    "COUNT": "COUNT",
                    "COUNTD": "DISTINCTCOUNT",
                    "MIN": "MIN",
                    "MAX": "MAX"
                },
                "string_functions": {
                    "LEFT": "LEFT",
                    "RIGHT": "RIGHT",
                    "LEN": "LEN",
                    "UPPER": "UPPER",
                    "LOWER": "LOWER"
                },
                "date_functions": {
                    "YEAR": "YEAR",
                    "MONTH": "MONTH",
                    "DAY": "DAY"
                },
                "logical_functions": {
                    "IF": "IF",
                    "AND": "AND",
                    "OR": "OR"
                }
            },
            "visual_mappings.json": {
                "chart_mappings": {
                    "bar": {
                        "horizontal": "clusteredBarChart",
                        "vertical": "clusteredColumnChart",
                        "default": "clusteredBarChart"
                    },
                    "line": {
                        "default": "lineChart"
                    },
                    "scatter": {
                        "default": "scatterChart"
                    },
                    "pie": {
                        "default": "pieChart"
                    }
                }
            },
            "data_type_mappings.json": {
                "type_mappings": {
                    "integer": "Int64",
                    "real": "Double",
                    "string": "String",
                    "datetime": "DateTime",
                    "boolean": "Boolean"
                }
            },
            "connection_mappings.json": {
                "connection_mappings": {
                    "sqlserver": {
                        "powerbi_type": "SqlServer",
                        "supported": True
                    },
                    "oracle": {
                        "powerbi_type": "Oracle",
                        "supported": True
                    },
                    "mysql": {
                        "powerbi_type": "MySQL",
                        "supported": True
                    }
                }
            }
        }
        
        return defaults.get(config_filename, {})
    
    def validate_configuration(self) -> Dict[str, bool]:
        """Validate all configuration files and mappings"""
        validation_results = {}
        
        config_files = [
            "tableau_mappings.json",
            "function_mappings.json", 
            "visual_mappings.json",
            "data_type_mappings.json",
            "connection_mappings.json"
        ]
        
        for config_file in config_files:
            try:
                config_path = self.config_dir / config_file
                config_data = self._load_json_config(config_path)
                validation_results[config_file] = bool(config_data)
            except Exception:
                validation_results[config_file] = False
        
        return validation_results
    
    def get_supported_tableau_versions(self) -> list:
        """Get list of supported Tableau versions"""
        mappings = self.load_tableau_mappings()
        return list(mappings.get("version_mappings", {}).keys())
    
    def get_supported_visual_types(self) -> list:
        """Get list of supported visual types"""
        mappings = self.load_visual_mappings()
        return list(mappings.get("chart_mappings", {}).keys())
    
    def get_supported_functions(self) -> Dict[str, list]:
        """Get list of supported functions by category"""
        mappings = self.load_function_mappings()
        supported = {}
        
        for category, functions in mappings.items():
            if isinstance(functions, dict):
                supported[category] = list(functions.keys())
        
        return supported
