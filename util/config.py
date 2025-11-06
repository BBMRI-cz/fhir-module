"""Module containing application configuration variables"""
import json
import logging
import os
import sys
from json import JSONDecodeError
from distutils.util import strtobool
from typing import Any, Dict, Optional

from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


class ConfigLoader:
    """Dynamic configuration loader that reads from JSON file and allows runtime updates"""
    
    def __init__(self, config_file_path: Optional[str] = None):
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        
        local_config_path = os.path.join(self.root_dir, 'shared_config.json')
        
        if config_file_path:
            self.config_file_path = config_file_path
        elif os.path.exists(local_config_path):

            self.config_file_path = local_config_path
            logger.info(f"Using local configuration from {local_config_path}")
        else:
            logger.error(f"Configuration file not found at {local_config_path}")
            self.config_file_path = local_config_path

        self._loaded_maps = {}
        
        # Mapping between config keys and their fallback (env_var_key, default_value)
        self._fallback_map = {
            'RECORDS_DIR_PATH': ('DIR_PATH', '/mock_dir/'),
            'PARSING_MAP_PATH': ('PARSING_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_map.json')),
            'MATERIAL_TYPE_MAP_PATH': ('MATERIAL_TYPE_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_material_type_map.json')),
            'MIABIS_MATERIAL_TYPE_MAP_PATH': ('MIABIS_MATERIAL_TYPE_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_miabis_material_type_map.json')),
            'SAMPLE_COLLECTIONS_PATH': ('SAMPLE_COLLECTIONS_PATH', lambda: os.path.join(self.root_dir, 'default_sample_collection.json')),
            'BIOBANK_PATH': ('BIOBANK_PATH', lambda: os.path.join(self.root_dir, 'default_biobank.json')),
            'TYPE_TO_COLLECTION_MAP_PATH': ('TYPE_TO_COLLECTION_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_type_to_collection_map.json')),
            'STORAGE_TEMP_MAP_PATH': ('STORAGE_TEMP_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_storage_temp_map.json')),
            'MIABIS_STORAGE_TEMP_MAP_PATH': ('MIABIS_STORAGE_TEMP_MAP_PATH', lambda: os.path.join(self.root_dir, 'default_miabis_storage_temp_map.json')),
            'CSV_SEPARATOR': ('CSV_SEPARATOR', ';'),
            'RECORDS_FILE_TYPE': ('RECORDS_FILE_TYPE', 'xml'),
        }
        
    def _load_config(self) -> Dict[str, Any]:
        config = None
        try:
            with open(self.config_file_path, 'r') as f:
                config = json.load(f)
            logger.debug(f"Loaded configuration from {self.config_file_path}")
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_file_path}")
            sys.exit(1)
        except JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            sys.exit(1)
        return config
    
    def get(self, key: str, default: Any = None) -> Any:
        config = self._load_config()
        
        value = config.get(key, default)

        # If the value is not set, try to get it from the environment variables - keep the backward compatibility
        if (value is None or value == ''):
            if key in self._fallback_map:
                env_var_key, fallback_default = self._fallback_map[key]
                if callable(fallback_default):
                    fallback_default = fallback_default()
                value = os.getenv(env_var_key, fallback_default)
            else:
                value = os.getenv(key, default)
        
        if key.endswith('_PATH') and value and not os.path.isabs(value):
            return os.path.join(self.root_dir, value)
            
        return value

    def set(self, key: str, value: Any) -> bool:
        try:
            config = self._load_config()
            config[key] = value
            
            with open(self.config_file_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            self._loaded_maps.clear()
            
            logger.info(f"Updated configuration: {key} = {value}")
            return True
        except Exception as e:
            logger.error(f"Failed to update configuration: {e}")
            return False
    
    def get_all(self) -> Dict[str, Any]:
        return self._load_config().copy()
    
    def get_map(self, map_type: str, force_reload: bool = False) -> Dict[str, Any]:
        if not force_reload and map_type in self._loaded_maps:
            return self._loaded_maps[map_type]
        
        map_path_key = f"{map_type.upper()}_MAP_PATH"
        if map_type.upper() == 'PARSING_MAP':
            map_path_key = f"{map_type.upper()}_PATH"
        
        map_path = self.get(map_path_key)
        if not map_path:
            logger.error(f"No path configured for map type: {map_type}")
            return {}
        
        try:
            with open(map_path) as json_file:
                map_data = json.load(json_file)
                self._loaded_maps[map_type] = map_data
                if force_reload:
                    logger.debug(f"Force reloaded map: {map_type} from {map_path}")
                return map_data
        except FileNotFoundError:
            logger.error(f"Map file not found: {map_path}")
            return {}
        except JSONDecodeError:
            logger.error(f"Map file does not have correct JSON format: {map_path}")
            return {}
    
    def reload_all_maps(self) -> None:
        """Clear the map cache and force reload all maps on next access"""
        self._loaded_maps.clear()
        logger.info("Cleared all cached maps")
    
    def reload_map(self, map_type: str) -> Dict[str, Any]:
        """Force reload a specific map"""
        if map_type in self._loaded_maps:
            del self._loaded_maps[map_type]
        return self.get_map(map_type, force_reload=True)


_config = ConfigLoader()

def get_config_value(key: str, default: Any = None) -> Any:
    return _config.get(key, default)

def set_config_value(key: str, value: Any) -> bool:
    return _config.set(key, value)

def get_blaze_url(): 
    return os.getenv("BLAZE_URL", "http://localhost:8080/fhir")

def get_miabis_blaze_url(): 
    return os.getenv("MIABIS_BLAZE_URL", "http://localhost:5432/fhir")

def get_root_dir(): 
    return _config.get('ROOT_DIR', os.path.dirname(os.path.abspath(__file__)))

def get_records_dir_path(): 
    return _config.get('RECORDS_DIR_PATH')

def get_log_level(): 
    return os.getenv("LOG_LEVEL", "INFO")

def get_parsing_map_path(): 
    return _config.get('PARSING_MAP_PATH')

def get_material_type_map_path(): 
    return _config.get('MATERIAL_TYPE_MAP_PATH')

def get_miabis_material_type_map_path(): 
    return _config.get('MIABIS_MATERIAL_TYPE_MAP_PATH')

def get_sample_collections_path(): 
    return _config.get('SAMPLE_COLLECTIONS_PATH')

def get_biobank_path(): 
    return _config.get('BIOBANK_PATH')

def get_type_to_collection_map_path(): 
    return _config.get('TYPE_TO_COLLECTION_MAP_PATH')

def get_storage_temp_map_path(): 
    return _config.get('STORAGE_TEMP_MAP_PATH')

def get_miabis_storage_temp_map_path(): 
    return _config.get('MIABIS_STORAGE_TEMP_MAP_PATH')

def get_standardised(): 
    return bool(strtobool(os.getenv("STANDARDISED", "False")))

def get_miabis_on_fhir(): 
    return bool(strtobool(os.getenv("MIABIS_ON_FHIR", "False")))

def get_csv_separator(): 
    return _config.get('CSV_SEPARATOR')

def get_records_file_type(): 
    return _config.get('RECORDS_FILE_TYPE')

def get_new_file_period_days(): 
    return os.getenv("NEW_FILE_PERIOD_DAYS", 30)

def get_blaze_auth(): 
    return (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))

def get_miabis_blaze_auth(): 
    return (os.getenv("BLAZE_USER", ""), os.getenv("BLAZE_PASS", ""))

def get_smtp_host(): 
    return os.getenv("SMTP_HOST", "localhost")

def get_smtp_port(): 
    return os.getenv("SMTP_PORT", "1025")

def get_email_receiver(): 
    return os.getenv("EMAIL_RECEIVER", "test@example.com")

# Map getter functions
def get_parsing_map(force_reload: bool = False): 
    return _config.get_map('parsing_map', force_reload=force_reload)

def get_material_type_map(force_reload: bool = False): 
    return _config.get_map('material_type', force_reload=force_reload)

def get_type_to_collection_map(force_reload: bool = False): 
    return _config.get_map('type_to_collection', force_reload=force_reload)

def get_storage_temp_map(force_reload: bool = False): 
    return _config.get_map('storage_temp', force_reload=force_reload)

def get_miabis_storage_temp_map(force_reload: bool = False): 
    return _config.get_map('miabis_storage_temp', force_reload=force_reload)

def get_miabis_material_type_map(force_reload: bool = False): 
    return _config.get_map('miabis_material_type', force_reload=force_reload)

def reload_all_maps() -> None:
    _config.reload_all_maps()

def reload_map(map_type: str) -> Dict[str, Any]:
    return _config.reload_map(map_type)

ROOT_DIR = _config.root_dir


def write_to_file(content, map_type, mode='w', encoding='utf-8'):    
    path_mapping = {
        'parsing_map': _config.get('PARSING_MAP_PATH'),
        'blaze_material_mapping': _config.get('MATERIAL_TYPE_MAP_PATH'),
        'blaze_temperature_mapping': _config.get('STORAGE_TEMP_MAP_PATH'),
        'type_to_collection_map': _config.get('TYPE_TO_COLLECTION_MAP_PATH'),
        'miabis_material_mapping': _config.get('MIABIS_MATERIAL_TYPE_MAP_PATH'),
        'miabis_temperature_mapping': _config.get('MIABIS_STORAGE_TEMP_MAP_PATH'),
    }
    
    if map_type not in path_mapping:
        return {
            'success': False,
            'message': f"Invalid map_type '{map_type}'. Valid types are: {list(path_mapping.keys())}"
        }
    
    file_path = path_mapping[map_type]
    
    if not file_path:
        return {
            'success': False,
            'message': f"No path configured for map_type '{map_type}'"
        }
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, mode, encoding=encoding) as file:
            file.write(content)
        
        logger.info(f"Successfully wrote content to {file_path} (map_type: {map_type})")
        return {
            'success': True,
            'message': f"Successfully wrote content to {file_path}"
        }
        
    except (OSError) as e:
        return {
            'success': False,
            'message': f"Failed to write to file {file_path}: {e}"
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Unexpected error writing to file {file_path}: {e}"
        }
