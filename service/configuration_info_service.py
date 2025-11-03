import logging
import os
import json
import shutil
import html
from typing import Any, cast
from requests import HTTPError, get
from datetime import datetime
from flask import Flask, jsonify, make_response, request
from werkzeug.utils import secure_filename

from model.storage_temperature import StorageTemperature
from service.condition_service import ConditionService
from util.custom_logger import setup_logger

from validation.factory.validator_factory_util import get_validator_factory

from persistence.factories.factory_util import get_repository_factory
from service.patient_service import PatientService
from service.sample_service import SampleService

from util.config import write_to_file, get_config_value, set_config_value, get_material_type_map, get_storage_temp_map, get_type_to_collection_map, reload_all_maps, get_miabis_on_fhir, get_miabis_material_type_map, get_miabis_storage_temp_map, get_root_dir, get_records_file_type

setup_logger()
logger = logging.getLogger()

_material_types_cache = None
_cache_timestamp = None
CACHE_DURATION_MINUTES = 60

SAFE_ROOT_FOLDER = get_root_dir()

def register_details_routes(flask_app):
    
    @flask_app.route('/donor-mapping-schema', methods=['GET'])
    def get_donor_mapping_schema():
        return jsonify(__get_donor_mapping_schema())

    @flask_app.route('/sample-mapping-schema', methods=['GET'])
    def get_sample_mapping_schema():
        return jsonify(__get_sample_mapping_schema())

    @flask_app.route('/condition-mapping-schema', methods=['GET'])
    def get_condition_mapping_schema():
        return jsonify(__get_condition_mapping_schema())

    @flask_app.route('/storage-temperatures', methods=['GET'])
    def get_storage_temperatures():
        return jsonify(__get_storage_temperatures())
    
    @flask_app.route('/material-types', methods=['GET'])
    def get_material_types():
        return jsonify(__get_material_types())
    
    @flask_app.route('/configuration-info', methods=['GET'])
    def get_configuration_info():
        return jsonify(__get_configuration_info())

    @flask_app.route('/validate-mappings', methods=['POST'])
    def validate_mappings():
        return __change_configuration(request, validate=True)

    @flask_app.route('/change-mappings', methods=['POST'])
    def change_mappings():
        return __change_configuration(request)

    @flask_app.route('/list-directories', methods=['GET'])
    def list_directories():
        return __list_directories(request)
    
    @flask_app.route('/parse-folder-data', methods=['POST'])
    def parse_folder_data():
        return __parse_folder_data(request)
    
    @flask_app.route('/setup-status', methods=['GET'])
    def get_setup_status():
        return __get_setup_status()
    
    @flask_app.route('/setup-status', methods=['POST'])
    def update_setup_status():
        return __update_setup_status(request)


# Based on the validate value temporary changes the configuration and validates the mapping correctness,
# or permanently changes the configuration to prepare for actual data synchronization
def __change_configuration(request, validate=False):
        content = request.get_json()
    
        try:
            content = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return make_response(jsonify({'message': 'Invalid JSON format'}), 400)
        
        if validate:
            validation_error = __validate_test_mapping_request(content)
            if validation_error:
                return make_response(jsonify({
                    'message': validation_error
                }), 400)

        file_type = content.get('file_type')
        test_records_path = content.get('test_records_path')
        csv_separator = content.get('csv_separator', ',')
        validate_all_files = content.get('validate_all_files', False)

        sync_target = content.get('sync_target', 'blaze')
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        original_paths = {}
        new_paths = {}
        
        try:
            __redirect_config_paths(timestamp, file_type, test_records_path, original_paths, new_paths, csv_separator)
            
            __write_mapping_files(content)

            reload_all_maps()

            sync_test_result = None
            if validate:
                test_records_path_str = new_paths.get('RECORDS_DIR_PATH', '')
                sync_test_result = __perform_dummy_sync_test(test_records_path_str, validate_all_files, sync_target == 'miabis')

                __cleanup_on_after_test(original_paths, new_paths)

            successful = sync_test_result is None or all(len(errors) == 0 for errors in sync_test_result.values())
            if not successful:
                logger.info(f"Validation failed with errors: {sync_test_result}")
                return make_response(jsonify({
                    'message': sync_test_result,
                }), 400)

            return make_response(jsonify({}), 200)

        except Exception as e:
            __cleanup_on_after_test(original_paths, new_paths)
            return make_response(jsonify({'message': f'Error during validity testing: {str(e)}'}), 500)

def __validate_test_mapping_request(content):
    if not content:
        return 'No JSON content provided'
    
    file_type = content.get('file_type')
    donor_mapping = content.get('donor_mapping')
    sample_mapping = content.get('sample_mapping')
    condition_mapping = content.get('condition_mapping')
    test_records_path = content.get('test_records_path')
    
    if not file_type:
        return 'file_type is required (xml, json, csv)'
        
    if not donor_mapping:
        return 'donor_mapping is required'

    try:
        donor_mapping = json.loads(donor_mapping)
    except json.JSONDecodeError:
        return 'donor_mapping must be a valid JSON string or object'

    if not sample_mapping:
        return 'sample_mapping is required'
    
    try:
        sample_mapping = json.loads(sample_mapping)
    except json.JSONDecodeError:
        return 'sample_mapping must be a valid JSON string or object'
    
    if not condition_mapping:
        return 'condition_mapping is required'

    try:
        condition_mapping = json.loads(condition_mapping)
    except json.JSONDecodeError:
        return 'condition_mapping must be a valid JSON string or object'
    
        
    if not test_records_path:
        return 'test_records_path is required'

    optional_mappings = ['material_mapping', 'temperature_mapping', 'type_to_collection_mapping']
    for mapping in optional_mappings:
        current_mapping = content.get(mapping)
        if current_mapping:
            try:
                current_mapping = json.loads(current_mapping)
            except json.JSONDecodeError:
                return f'{mapping} must be a valid JSON string or object'
        
    
    return None

def __redirect_config_paths(timestamp, file_type, test_records_path, original_paths, new_paths, csv_separator=','):
    paths_to_redirect = [
        'PARSING_MAP_PATH',
        'MATERIAL_TYPE_MAP_PATH',
        'STORAGE_TEMP_MAP_PATH',
        'MIABIS_MATERIAL_TYPE_MAP_PATH',
        'MIABIS_STORAGE_TEMP_MAP_PATH',
        'TYPE_TO_COLLECTION_MAP_PATH',
        'RECORDS_DIR_PATH'
    ]
    
    config_snapshot_dir = __create_config_snapshot_directory(timestamp, file_type)
    new_paths['CONFIG_SNAPSHOT_DIR'] = config_snapshot_dir
    
    for path_key in paths_to_redirect:
        original_path = get_config_value(path_key)

        if original_path == '' or original_path is None:
            original_path = f'{path_key}.json'
        original_paths[path_key] = original_path
        
        if path_key == 'RECORDS_DIR_PATH':
            new_path = __setup_test_records_directory(test_records_path)
            new_paths[path_key] = new_path
        else:
            new_path = __copy_mapping_file_to_snapshot(original_path, config_snapshot_dir)
            new_paths[path_key] = new_path
        
        set_config_value(path_key, new_path)
        logger.info(f"Redirected {path_key} from {original_path} to {new_path}")
    
    original_file_type = get_config_value('RECORDS_FILE_TYPE')
    if original_file_type:
        original_paths['RECORDS_FILE_TYPE'] = original_file_type
        set_config_value('RECORDS_FILE_TYPE', file_type)
        logger.info(f"Updated RECORDS_FILE_TYPE from {original_file_type} to {file_type}")
    
    if file_type == 'csv':
        original_csv_separator = get_config_value('CSV_SEPARATOR')
        if original_csv_separator:
            original_paths['CSV_SEPARATOR'] = original_csv_separator
        set_config_value('CSV_SEPARATOR', csv_separator)
        logger.info(f"Updated CSV_SEPARATOR to '{csv_separator}'")

def __setup_test_records_directory(test_records_path):
    if not os.path.exists(test_records_path):
        raise ValueError(f'Test records path does not exist: {test_records_path}')
    
    logger.info(f"Using test records path: {test_records_path}")
    return test_records_path

def __create_config_snapshot_directory(timestamp, file_type):
    """
    Create a timestamped directory for config snapshots in /opt/config-snapshots.
    """
    base_dir = "/opt/config-snapshots"
    safe_file_type = secure_filename(str(file_type))
    snapshot_dir_name = f"config_{timestamp}_{safe_file_type}"
    snapshot_dir = os.path.join(base_dir, snapshot_dir_name)

    if not os.path.realpath(snapshot_dir).startswith(os.path.realpath(base_dir) + os.sep):
        raise ValueError("Invalid file_type for directory name")
    
    os.makedirs(snapshot_dir, exist_ok=True)
    logger.info(f"Created config snapshot directory: {snapshot_dir}")
    
    return snapshot_dir

def __copy_mapping_file_to_snapshot(original_path, snapshot_dir):
    """
    Copy a mapping file to the snapshot directory, keeping its original filename.
    """
    filename = os.path.basename(original_path)
    new_path = os.path.join(snapshot_dir, filename)
    
    if os.path.exists(original_path):
        shutil.copy2(original_path, new_path)
        logger.info(f"Copied {original_path} to {new_path}")
    
    return new_path

def __write_mapping_files(content):
    sync_target = content.get('sync_target', 'blaze')
    
    # Parsing maps are shared between BLAZE and MIABIS
    data_to_write = {
        'donor_map': json.loads(content.get('donor_mapping')),
        'sample_map': json.loads(content.get('sample_mapping')),
        'condition_map': json.loads(content.get('condition_mapping'))
    }

    content_to_write = json.dumps(data_to_write, indent=2)
    write_to_file(content_to_write, 'parsing_map')
    
    # Determine which map files to write based on sync_target
    mappings_to_write = []
    
    if sync_target == 'miabis':
        mappings_to_write.append({
            'material_map_type': 'miabis_material_mapping',
            'storage_map_type': 'miabis_temperature_mapping',
            'default_material_getter': get_miabis_material_type_map,
            'default_storage_getter': get_miabis_storage_temp_map
        })
    elif sync_target == 'both':
        # Write both MIABIS and BLAZE mappings
        mappings_to_write.append({
            'material_map_type': 'miabis_material_mapping',
            'storage_map_type': 'miabis_temperature_mapping',
            'default_material_getter': get_miabis_material_type_map,
            'default_storage_getter': get_miabis_storage_temp_map
        })
        mappings_to_write.append({
            'material_map_type': 'blaze_material_mapping',
            'storage_map_type': 'blaze_temperature_mapping',
            'default_material_getter': get_material_type_map,
            'default_storage_getter': get_storage_temp_map
        })
    else:  # 'blaze' or default
        mappings_to_write.append({
            'material_map_type': 'blaze_material_mapping',
            'storage_map_type': 'blaze_temperature_mapping',
            'default_material_getter': get_material_type_map,
            'default_storage_getter': get_storage_temp_map
        })
    
    # Write all required mappings
    for mapping in mappings_to_write:
        material_map_type = mapping['material_map_type']
        storage_map_type = mapping['storage_map_type']
        default_material_getter = mapping['default_material_getter']
        default_storage_getter = mapping['default_storage_getter']
        
        # Write material type mapping
        if content.get(material_map_type, None) is not None:
            material_data = json.loads(content.get(material_map_type))
        else:
            material_data = default_material_getter()

        content_to_write = json.dumps(material_data, indent=2)
        write_to_file(content_to_write, material_map_type)
        
        # Write temperature mapping
        if content.get(storage_map_type, None) is not None:
            temperature_data = json.loads(content.get(storage_map_type))
        else:
            temperature_data = default_storage_getter()
        
        content_to_write = json.dumps(temperature_data, indent=2)
        write_to_file(content_to_write, storage_map_type)
    
    # Type to collection mapping (shared, so only write once regardless of sync_target)
    if content.get('type_to_collection_mapping', None) is not None:
        type_to_collection_data = json.loads(content.get('type_to_collection_mapping'))
    else:
        type_to_collection_data = get_type_to_collection_map()
    
    content_to_write = json.dumps(type_to_collection_data, indent=2)
    write_to_file(content_to_write, 'type_to_collection_map')

def __cleanup_on_after_test(original_paths, new_paths):
    # Restore original config values
    for path_key, original_path in original_paths.items():
        set_config_value(path_key, original_path)
        logger.info(f"Restored {path_key} to {original_path}")
    
    # Clean up directories
    if 'CONFIG_SNAPSHOT_DIR' in new_paths:
        config_dir = new_paths['CONFIG_SNAPSHOT_DIR']
        if os.path.exists(config_dir):
            shutil.rmtree(config_dir)
            logger.info(f"Cleaned up config snapshot directory {config_dir}")

def __get_donor_mapping_schema():
    return {
        "id": {"required": True},
        "gender": {"required": True},
        "birth_date": {"required": True}
    }


def __get_sample_mapping_schema():
    is_miabis_mode = get_miabis_on_fhir()
    return {
        "donor_id": {"required": True},
        "sample": {"required": True, "only_for_formats": ["xml"]},
        "id": {"required": True, "xml_depends_on": "sample"},
        "material_type": {"required": True, "xml_depends_on": "sample"},
        "diagnosis": {"required": True, "xml_depends_on": "sample"},
        "diagnosis_date": {"required": False, "xml_depends_on": "sample"},
        "collection_date": {"required": False, "xml_depends_on": "sample"},
        "storage_temperature": {"required": False, "xml_depends_on": "sample"},
        "collection": {"required": is_miabis_mode, "xml_depends_on": "sample"},
    }


def __get_condition_mapping_schema():
    return {
        "icd-10_code": {"required": True},
        "patient_id": {"required": True},
        "diagnosis_date": {"required": False}
    }

def __fetch_material_types_from_api():
    """
    Fetch material types from BBMRI.de Simplifier API with caching.
    Returns a list of material type codes or fallback values if API call fails.
    """
    global _material_types_cache, _cache_timestamp
    
    if (_material_types_cache is not None and 
        _cache_timestamp is not None and 
        (datetime.now() - _cache_timestamp).total_seconds() < CACHE_DURATION_MINUTES * 60):
        return _material_types_cache
    
    try:
        url = "https://simplifier.net/bbmri.de/samplematerialtype/$download?format=json"
        response = get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        material_types = __extract_concepts_from_fetch(data)


        return material_types
    
    except HTTPError as http_err:
        logger.error(f"HTTP error occurred while fetching material types: {http_err}")
        return None

def __get_storage_temperatures():
        return {
        "storage_temperature": [temp.name for temp in StorageTemperature],
    }

def __get_material_types():
    return {
        "material_type": __fetch_material_types_from_api()
    }

def __get_configuration_info():
    return {
        "miabis_on_fhir": get_miabis_on_fhir()
    }


def __extract_concepts_from_fetch(data: dict[str, Any]) -> list[str]:
    concepts = []
    
    if isinstance(data, dict):
        code = data.get("code", None)
        if code:
            concepts.append(code)

        concept = data.get("concept", None)
        if concept is None:
            return concepts
        
        concept = cast(dict[str, Any], concept)
        concepts.extend(__extract_concepts_from_fetch(concept))

    if isinstance(data, list):
        for item in cast(list[dict[str, Any]], data):
            concepts.extend(__extract_concepts_from_fetch(item))


    return concepts


def __validate_directory_path(base_dir: str, relative_path: str) -> tuple[str, dict | None]:
    """
    Validate and resolve directory path.
    Returns (resolved_path, error_response) where error_response is None if validation succeeds.
    """
    if relative_path == '/':
        path = base_dir
    else:
        path = relative_path
    
    path = os.path.realpath(path)
    
    if not path.startswith(base_dir):
        logger.warning(f"Attempted access outside base directory: {path} (base: {base_dir})")
        return path, make_response(jsonify({'error': 'Access denied: path outside allowed directory'}), 403)
    
    if not os.path.exists(path):
        return path, make_response(jsonify({'error': 'Path does not exist'}), 404)
    
    if not os.path.isdir(path):
        return path, make_response(jsonify({'error': 'Path is not a directory'}), 400)
    
    return path, None


def __build_directory_entries(path: str, relative_path: str, base_dir: str, include_files: bool) -> list[dict]:
    """Build list of directory entries with metadata."""
    entries = []
    
    if relative_path == '/':
        entries.append({
            'name': os.path.basename(base_dir) or 'root',
            'path': base_dir,
            'isDirectory': True
        })
    else:
        for entry_name in os.listdir(path):
            entry_path = os.path.join(path, entry_name)
            is_directory = os.path.isdir(entry_path)
            
            if is_directory or include_files:
                entries.append({
                    'name': entry_name,
                    'path': entry_path,
                    'isDirectory': is_directory
                })
    
    entries.sort(key=lambda x: (not x['isDirectory'], x['name'].lower()))
    return entries


def __list_directories(request):
    """
    List directories inside the container.
    Supports optional 'path' query parameter to list subdirectories.
    """
    try:
        base_dir = get_root_dir()
        base_dir = os.path.realpath(base_dir)
        
        relative_path = request.args.get('path', '/')
        include_files = request.args.get('include_files', 'false').lower() == 'true'
        
        path, error_response = __validate_directory_path(base_dir, relative_path)
        if error_response:
            return error_response
        
        try:
            entries = __build_directory_entries(path, relative_path, base_dir, include_files)
            return jsonify({'path': path, 'entries': entries})
            
        except PermissionError:
            return make_response(jsonify({'error': 'Permission denied'}), 403)
        except Exception as e:
            logger.error(f"Error listing directory {path}: {str(e)}")
            return make_response(jsonify({'error': 'Error listing directory'}), 500)
            
    except Exception as e:
        logger.error(f"Error in list_directories: {str(e)}")
        return make_response(jsonify({'error': 'Internal server error'}), 500)


def __validate_folder_path_request(content: dict) -> tuple[str, dict | None]:
    """
    Validate folder path from request content.
    Returns (folder_path, error_response) where error_response is None if validation succeeds.
    Limits access to a safe root directory.
    """
    if not content or 'folderPath' not in content:
        return '', make_response(jsonify({
            'success': False,
            'message': 'folderPath parameter is required'
        }), 400)

    folder_path_input = content['folderPath']
    if not isinstance(folder_path_input, str):
        return '', make_response(jsonify({
            'success': False,
            'message': 'folderPath must be a string'
        }), 400)


    safe_root_real = os.path.realpath(SAFE_ROOT_FOLDER)
    candidate_real = os.path.realpath(folder_path_input)
    try:
        if os.path.commonpath([safe_root_real, candidate_real]) != safe_root_real:
            return candidate_real, make_response(jsonify({
                'success': False,
                'message': 'Access to the requested folder is not allowed'
            }), 400)
    except ValueError:
        return candidate_real, make_response(jsonify({
            'success': False,
            'message': 'Access to the requested folder is not allowed'
        }), 400)

    if not os.path.exists(candidate_real):
        return candidate_real, make_response(jsonify({
            'success': False,
            'message': f'Folder path does not exist: {html.escape(candidate_real)}'
        }), 400)

    if not os.path.isdir(candidate_real):
        return candidate_real, make_response(jsonify({
            'success': False,
            'message': f'Path is not a directory: {html.escape(candidate_real)}'
        }), 400)

    return candidate_real, None


def __find_supported_data_files(folder_path: str) -> tuple[list[dict], dict | None]:
    """
    Find supported data files in folder.
    Returns (data_files, error_response) where error_response is None if successful.
    """
    # Security check: ensure folder_path is within SAFE_ROOT_FOLDER
    try:
        normalized_root = os.path.realpath(SAFE_ROOT_FOLDER)
        normalized_path = os.path.realpath(folder_path)
        
        if os.path.commonpath([normalized_root, normalized_path]) != normalized_root:
            return [], make_response(jsonify({
                'success': False,
                'message': 'Access to the requested folder is not allowed'
            }), 400)
    except (ValueError, OSError):
        # ValueError: paths on different drives on Windows
        # OSError: invalid path
        return [], make_response(jsonify({
            'success': False,
            'message': 'Access to the requested folder is not allowed'
        }), 400)
    
    supported_extensions = ['.json', '.csv', '.xml']
    data_files = []
    
    try:
        files = os.listdir(folder_path)
        for file_name in files:
            file_path = os.path.join(folder_path, file_name)
            real_file_path = os.path.realpath(file_path)
            
            real_file_path = os.path.normpath(os.path.abspath(file_path))
            if os.path.commonpath([normalized_path, real_file_path]) != normalized_path:
                continue

            if os.path.isfile(real_file_path):
                ext = os.path.splitext(file_name.lower())[1]
                if ext in supported_extensions:
                    data_files.append({'path': real_file_path, 'ext': ext, 'name': file_name})
    except PermissionError:
        return [], make_response(jsonify({
            'success': False,
            'message': 'Permission denied accessing folder'
        }), 400)
    
    if not data_files:
        return [], make_response(jsonify({
            'success': False,
            'message': f'No supported data files found in {html.escape(folder_path)}. Supported formats: JSON, CSV, XML'
        }), 400)
    
    return data_files, None


def __read_first_data_file(data_files: list[dict]) -> tuple[str, str, str, dict | None]:
    """
    Read the first data file from the list.
    Returns (file_content, file_name, file_ext, error_response) where error_response is None if successful.
    """
    file_info = data_files[0]
    file_path = file_info['path']
    file_ext = file_info['ext']
    file_name = file_info['name']
    
    real_file_path = os.path.realpath(file_path)
    safe_root_real = os.path.realpath(SAFE_ROOT_FOLDER)
    if os.path.commonpath([safe_root_real, real_file_path]) != safe_root_real:
        return '', file_name, file_ext, make_response(jsonify({
            'success': False,
            'message': f'Access to the requested file is not allowed: {html.escape(file_name)}'
        }), 400)
    
    try:
        with open(real_file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        return file_content, file_name, file_ext, None
    except Exception as read_error:
        return '', file_name, file_ext, make_response(jsonify({
            'success': False,
            'message': f'Error reading {html.escape(file_name)}'
        }), 500)


def __parse_folder_data(request):
    """
    Get file content from a folder for frontend parsing.
    Expects JSON body with 'folderPath' parameter.
    """
    try:
        content = request.get_json()
        
        folder_path, error_response = __validate_folder_path_request(content)
        if error_response:
            return error_response
        
        data_files, error_response = __find_supported_data_files(folder_path)
        if error_response:
            return error_response
        
        file_content, file_name, file_ext, error_response = __read_first_data_file(data_files)
        if error_response:
            return error_response
        
        return jsonify({
            'success': True,
            'message': f'Successfully read {file_name} (first file found)',
            'fileContent': file_content,
            'fileName': file_name,
            'fileExtension': file_ext
        })
        
    except Exception as e:
        logger.error(f"Error in parse_folder_data: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'message': f'Internal server error: {str(e)}'
        }), 500)


def __create_empty_error_dict() -> dict[str, list[str]]:
    """Create an empty error dictionary structure."""
    return {
        'generic_errors': [],
        'patient_errors': [],
        'sample_errors': [],
        'condition_errors': []
    }


def __validate_test_records_path(test_records_path: str, errors: dict[str, list[str]]) -> list[str] | None:
    """
    Validate test records path and return list of test files.
    Returns None if validation fails (errors dict is populated).
    """
    if not test_records_path or not os.path.exists(test_records_path):
        errors['generic_errors'].append('Test records path not found')
        return None
    
    try:
        test_files = [f for f in os.listdir(test_records_path) 
                     if os.path.isfile(os.path.join(test_records_path, f))]
    except Exception as e:
        errors['generic_errors'].append(f'Error accessing test records path: {str(e)}')
        return None

    if not test_files:
        errors['generic_errors'].append('No test files found in test records directory')
        return None
    
    return test_files


def __categorize_validation_error(validation_error: Exception, errors: dict[str, list[str]]) -> None:
    """Categorize validation error into appropriate error list."""
    error_msg = str(validation_error)
    
    if hasattr(validation_error, 'concept') and validation_error.concept:
        concept = validation_error.concept
        if concept == 'donor':
            errors['patient_errors'].append(validation_error.error_message)
        elif concept == 'sample':
            errors['sample_errors'].append(validation_error.error_message)
        elif concept == 'condition':
            errors['condition_errors'].append(validation_error.error_message)
    else:
        errors['generic_errors'].append(error_msg)


def __run_structural_validation(errors: dict[str, list[str]]) -> bool:
    """
    Run Stage 1 structural validation for CSV/XML files.
    Returns True if validation passes or is skipped, False if it fails.
    """
    try:
        file_type = get_records_file_type().lower()
        
        if file_type in ['csv', 'xml']:
            logger.info(f"Stage 1: Running structural validation for {file_type} files...")
            validator_factory = get_validator_factory()
            validator = validator_factory.create_validator()
            validator.validate()
            logger.info("Stage 1: Structural validation passed")
        else:
            logger.info(f"Stage 1: Skipping structural validation for {file_type} (no validator available)")
        
        return True
        
    except Exception as validation_error:
        logger.error(f"Stage 1: Structural validation failed: {str(validation_error)}")
        __categorize_validation_error(validation_error, errors)
        return False


def __run_data_parsing_validation(validate_all_files: bool, errors: dict[str, list[str]], miabis_on_fhir: bool = False) -> bool:
    """
    Run Stage 2 data parsing validation.
    Returns True if validation succeeds, False otherwise.
    """
    try:
        logger.info("Stage 2: Running data parsing validation...")
        repository_factory = get_repository_factory()
        
        patient_service = PatientService(repository_factory.create_sample_donor_repository(miabis_on_fhir))
        sample_service = SampleService(repository_factory.create_sample_repository(miabis_on_fhir))
        condition_service = ConditionService(repository_factory.create_condition_repository())
        
        logger.info(f"Stage 2: Validating {'all files' if validate_all_files else 'first file only'}")
        errors['patient_errors'] = patient_service.smoke_validate(validate_all_files)
        errors['sample_errors'] = sample_service.smoke_validate(validate_all_files)
        errors['condition_errors'] = condition_service.smoke_validate(validate_all_files)
        
        logger.info("Stage 2: Data parsing validation completed")
        return True
        
    except Exception as service_error:
        error_msg = f'Service creation or data parsing failed: {str(service_error)}'
        logger.error(f"Stage 2: {error_msg}")
        errors['patient_errors'].append(error_msg)
        return False


def __perform_dummy_sync_test(test_records_path: str, validate_all_files: bool = False, miabis_on_fhir: bool = False) -> dict[str, list[str]] | None:
    """
    Perform a dummy sync test to validate configuration without actually syncing data.
    Returns a dictionary of categorized errors.
    """
    errors = __create_empty_error_dict()
    
    try:
        # Validate test records path and get files
        test_files = __validate_test_records_path(test_records_path, errors)
        if test_files is None:
            return errors
        
        # Run Stage 1: Structural validation
        if not __run_structural_validation(errors):
            return errors
        
        # Run Stage 2: Data parsing validation
        __run_data_parsing_validation(validate_all_files, errors, miabis_on_fhir)
        return errors

    except Exception as e:
        error_msg = f'Sync test failed: {str(e)}'
        logger.error(error_msg)
        return {'generic_errors': [error_msg]}


def __get_setup_status():
    """
    Get the current setup status from shared_config.json
    """
    try:
        initial_setup_complete = get_config_value('INITIAL_SETUP_COMPLETE', False)
        
        return jsonify({
            'initial_setup_complete': initial_setup_complete
        })
    except Exception as e:
        logger.error(f"Error getting setup status: {str(e)}")
        return make_response(jsonify({
            'initial_setup_complete': False
        }), 200)


def __update_setup_status(request):
    """
    Update the setup status in shared_config.json
    """
    try:
        content = request.get_json()
        
        if not content:
            return make_response(jsonify({'message': 'Invalid request body'}), 400)
        
        if 'initial_setup_complete' in content:
            set_config_value('INITIAL_SETUP_COMPLETE', content['initial_setup_complete'])
            logger.info(f"Updated INITIAL_SETUP_COMPLETE to {content['initial_setup_complete']}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating setup status: {str(e)}")
        return make_response(jsonify({
            'success': False,
            'message': str(e)
        }), 500)

