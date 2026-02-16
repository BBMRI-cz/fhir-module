import unittest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock, mock_open
from datetime import datetime
from flask import Flask

from service.configuration_info_service import register_details_routes
from model.storage_temperature import StorageTemperature


class TestConfigurationInfoService(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__) # NOSONAR
        register_details_routes(self.app)
        self.client = self.app.test_client()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_donor_mapping_schema(self):
        response = self.client.get('/donor-mapping-schema')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('id', data)
        self.assertIn('gender', data)
        self.assertIn('birth_date', data)
        self.assertTrue(data['id']['required'])
        self.assertTrue(data['gender']['required'])
        self.assertTrue(data['birth_date']['required'])

    def test_get_sample_mapping_schema(self):
        with patch('service.configuration_info_service.get_miabis_on_fhir', return_value=False):
            response = self.client.get('/sample-mapping-schema')
            self.assertEqual(200, response.status_code)
            
            data = json.loads(response.data)
            self.assertIn('donor_id', data)
            self.assertIn('sample', data)
            self.assertIn('id', data)
            self.assertIn('material_type', data)
            self.assertIn('diagnosis', data)
            self.assertTrue(data['donor_id']['required'])

    def test_get_sample_mapping_schema_miabis_mode(self):
        with patch('service.configuration_info_service.get_miabis_on_fhir', return_value=True):
            response = self.client.get('/sample-mapping-schema')
            self.assertEqual(200, response.status_code)
            
            data = json.loads(response.data)
            self.assertIn('collection', data)
            self.assertTrue(data['collection']['required'])

    def test_get_condition_mapping_schema(self):
        response = self.client.get('/condition-mapping-schema')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('icd-10_code', data)
        self.assertIn('patient_id', data)
        self.assertIn('diagnosis_date', data)
        self.assertTrue(data['icd-10_code']['required'])
        self.assertTrue(data['patient_id']['required'])
        self.assertFalse(data['diagnosis_date']['required'])

    def test_get_storage_temperatures(self):
        response = self.client.get('/storage-temperatures')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('storage_temperature', data)
        self.assertIsInstance(data['storage_temperature'], list)
        self.assertGreater(len(data['storage_temperature']), 0)
        for temp in StorageTemperature:
            self.assertIn(temp.name, data['storage_temperature'])

    @patch('service.configuration_info_service.get')
    def test_get_material_types_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "concept": [
                {"code": "tissue-ffpe"},
                {"code": "whole-blood"},
                {"code": "plasma"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        response = self.client.get('/material-types')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('material_type', data)

    @patch('service.configuration_info_service.get')
    def test_get_material_types_api_failure(self, mock_get):
        from requests import HTTPError
        mock_get.side_effect = HTTPError("API Error")
        
        response = self.client.get('/material-types')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('material_type', data)
        self.assertIsNone(data['material_type'])

    @patch('service.configuration_info_service.get_miabis_on_fhir')
    def test_get_configuration_info(self, mock_get_miabis):
        mock_get_miabis.return_value = True
        
        response = self.client.get('/configuration-info')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('miabis_on_fhir', data)
        self.assertTrue(data['miabis_on_fhir'])

    @patch('service.configuration_info_service.get_config_value')
    def test_get_setup_status(self, mock_get_config):
        mock_get_config.return_value = True
        
        response = self.client.get('/setup-status')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('initial_setup_complete', data)
        self.assertTrue(data['initial_setup_complete'])

    @patch('service.configuration_info_service.get_config_value')
    def test_get_setup_status_error_handling(self, mock_get_config):
        mock_get_config.side_effect = Exception("Config error")
        
        response = self.client.get('/setup-status')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertFalse(data['initial_setup_complete'])

    @patch('service.configuration_info_service.set_config_value')
    def test_update_setup_status(self, mock_set_config):
        payload = {'initial_setup_complete': True}
        
        response = self.client.post(
            '/setup-status',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)
        data = json.loads(response.data)
        self.assertTrue(data['success'])
        mock_set_config.assert_called_once_with('INITIAL_SETUP_COMPLETE', True)

    def test_update_setup_status_empty_body(self):
        response = self.client.post(
            '/setup-status',
            content_type='application/json'
        )
        self.assertIn(response.status_code, [400, 500])

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.path.isdir')
    @patch('service.configuration_info_service.os.listdir')
    def test_list_directories_root(self, mock_listdir, mock_isdir, mock_exists, 
                                   mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base'
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.return_value = []
        
        response = self.client.get('/list-directories?path=/')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('path', data)
        self.assertIn('entries', data)

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    def test_list_directories_path_not_exists(self, mock_exists, mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base/nonexistent'
        mock_exists.return_value = False
        
        response = self.client.get('/list-directories?path=/nonexistent')
        self.assertEqual(404, response.status_code)

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.path.isdir')
    def test_list_directories_path_not_directory(self, mock_isdir, mock_exists, 
                                                 mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base/file.txt'
        mock_exists.return_value = True
        mock_isdir.return_value = False
        
        response = self.client.get('/list-directories?path=/file.txt')
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    def test_list_directories_access_denied(self, mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.side_effect = lambda x: x if x == '/test/base' else '/other/path'
        
        response = self.client.get('/list-directories?path=/../../../other')
        self.assertEqual(403, response.status_code)


    def test_parse_folder_data_success(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', tempfile.gettempdir()):
            test_file = os.path.join(self.test_dir, 'test.json')
            test_content = '{"test": "data"}'
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            payload = {'folderPath': self.test_dir}
            
            response = self.client.post(
                '/parse-folder-data',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertIn('fileContent', data)
            self.assertIn('fileName', data)
            self.assertEqual('test.json', data['fileName'])

    def test_parse_folder_data_no_folder_path(self):
        response = self.client.post(
            '/parse-folder-data',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_parse_folder_data_nonexistent_folder(self):
        payload = {'folderPath': '/nonexistent/path'}
        
        response = self.client.post(
            '/parse-folder-data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_parse_folder_data_not_directory(self):
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        payload = {'folderPath': test_file}
        
        response = self.client.post(
            '/parse-folder-data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    def test_parse_folder_data_no_supported_files(self):
        test_file = os.path.join(self.test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        payload = {'folderPath': self.test_dir}
        
        response = self.client.post(
            '/parse-folder-data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertFalse(data['success'])

    def test_validate_mappings_missing_file_type(self):
        payload = {
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'test_records_path': self.test_dir
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('file_type is required', data['message'])

    def test_validate_mappings_missing_donor_mapping(self):
        payload = {
            'file_type': 'json',
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'test_records_path': self.test_dir
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    def test_validate_mappings_invalid_json(self):
        response = self.client.post(
            '/validate-mappings',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    # Tests for __change_configuration with validate=False (change-mappings endpoint)
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.get_material_type_map')
    @patch('service.configuration_info_service.get_storage_temp_map')
    def test_change_mappings_success(self, mock_storage_map, mock_material_map,
                                     mock_exists, mock_copy, mock_makedirs,
                                     mock_get_config, mock_set_config, mock_write, mock_reload):
        mock_material_map.return_value = {"test": "material"}
        mock_storage_map.return_value = {"test": "storage"}
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'sync_target': 'blaze'
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)
        mock_reload.assert_called_once()

    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.get_miabis_material_type_map')
    @patch('service.configuration_info_service.get_miabis_storage_temp_map')
    def test_change_mappings_miabis_mode(self, mock_storage_map, mock_material_map,
                                         mock_exists, mock_copy, mock_makedirs,
                                         mock_get_config, mock_set_config, mock_write, mock_reload):
        mock_material_map.return_value = {"test": "miabis_material"}
        mock_storage_map.return_value = {"test": "miabis_storage"}
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'sync_target': 'miabis'
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.get_material_type_map')
    @patch('service.configuration_info_service.get_storage_temp_map')
    @patch('service.configuration_info_service.get_miabis_material_type_map')
    @patch('service.configuration_info_service.get_miabis_storage_temp_map')
    def test_change_mappings_both_mode(self, mock_miabis_storage, mock_miabis_material,
                                       mock_storage_map, mock_material_map,
                                       mock_exists, mock_copy, mock_makedirs,
                                       mock_get_config, mock_set_config, mock_write, mock_reload):
        mock_material_map.return_value = {"test": "material"}
        mock_storage_map.return_value = {"test": "storage"}
        mock_miabis_material.return_value = {"test": "miabis_material"}
        mock_miabis_storage.return_value = {"test": "miabis_storage"}
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'sync_target': 'both'
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.get_material_type_map')
    @patch('service.configuration_info_service.get_storage_temp_map')
    def test_change_mappings_with_csv_separator(self, mock_storage_map, mock_material_map,
                                                mock_exists, mock_copy, mock_makedirs,
                                                mock_get_config, mock_set_config, mock_write, mock_reload):
        mock_material_map.return_value = {"test": "material"}
        mock_storage_map.return_value = {"test": "storage"}
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        
        payload = {
            'file_type': 'csv',
            'test_records_path': self.test_dir,
            'csv_separator': ';',
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'sync_target': 'blaze'
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    def test_change_mappings_test_records_path_error(self, mock_makedirs, mock_get_config, mock_set_config):
        mock_get_config.return_value = '/test/path'
        
        payload = {
            'file_type': 'json',
            'test_records_path': '/nonexistent/path',
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(500, response.status_code)

    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.get_material_type_map')
    @patch('service.configuration_info_service.get_storage_temp_map')
    @patch('service.configuration_info_service.get_type_to_collection_map')
    def test_change_mappings_with_optional_mappings(self, mock_type_to_collection, mock_storage_map,
                                                    mock_material_map, mock_exists, mock_copy,
                                                    mock_makedirs, mock_get_config, mock_set_config,
                                                    mock_write, mock_reload):
        mock_material_map.return_value = {"test": "material"}
        mock_storage_map.return_value = {"test": "storage"}
        mock_type_to_collection.return_value = {"test": "collection"}
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'blaze_material_mapping': json.dumps({'custom': 'material'}),
            'blaze_temperature_mapping': json.dumps({'custom': 'temp'}),
            'type_to_collection_mapping': json.dumps({'custom': 'collection'}),
            'sync_target': 'blaze'
        }
        
        response = self.client.post(
            '/change-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(200, response.status_code)

    # Tests for validation with optional mappings
    def test_validate_mappings_with_material_mapping(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'material_mapping': json.dumps({'material': 'type'})
        }
        
        with patch('service.configuration_info_service.__perform_dummy_sync_test') as mock_sync:
            with patch('service.configuration_info_service.reload_all_maps'):
                with patch('service.configuration_info_service.write_to_file'):
                    with patch('service.configuration_info_service.set_config_value'):
                        with patch('service.configuration_info_service.get_config_value', return_value='/test'):
                            with patch('service.configuration_info_service.os.makedirs'):
                                with patch('service.configuration_info_service.shutil.copy2'):
                                    with patch('service.configuration_info_service.os.path.exists', return_value=True):
                                        with patch('service.configuration_info_service.shutil.rmtree'):
                                            mock_sync.return_value = {
                                                'generic_errors': [],
                                                'patient_errors': [],
                                                'sample_errors': [],
                                                'condition_errors': []
                                            }
                                            
                                            response = self.client.post(
                                                '/validate-mappings',
                                                data=json.dumps(json.dumps(payload)),
                                                content_type='application/json'
                                            )
                                            
                                            self.assertEqual(200, response.status_code)

    def test_validate_mappings_invalid_material_mapping_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'material_mapping': 'invalid json'
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('material_mapping', data['message'])

    def test_validate_mappings_invalid_temperature_mapping_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'temperature_mapping': 'invalid json'
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('temperature_mapping', data['message'])

    def test_validate_mappings_invalid_type_to_collection_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
            'type_to_collection_mapping': 'invalid json'
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('type_to_collection_mapping', data['message'])

    def test_validate_mappings_missing_sample_mapping(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('sample_mapping', data['message'])

    def test_validate_mappings_missing_condition_mapping(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('condition_mapping', data['message'])

    def test_validate_mappings_missing_test_records_path(self):
        payload = {
            'file_type': 'json',
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('test_records_path', data['message'])

    def test_validate_mappings_invalid_donor_mapping_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': 'invalid json',
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('donor_mapping', data['message'])

    def test_validate_mappings_invalid_sample_mapping_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': 'invalid json',
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('sample_mapping', data['message'])

    def test_validate_mappings_invalid_condition_mapping_json(self):
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': 'invalid json'
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('condition_mapping', data['message'])

    def test_validate_mappings_no_content(self):
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(None)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertIn('No JSON content', data['message'])

    # Tests for __fetch_material_types_from_api caching
    @patch('service.configuration_info_service.get')
    @patch('service.configuration_info_service._cache_timestamp', None)
    @patch('service.configuration_info_service._material_types_cache', None)
    def test_get_material_types_caching(self, mock_get):
        from datetime import datetime, timedelta
        mock_response = MagicMock()
        mock_response.json.return_value = {"concept": [{"code": "test"}]}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # First call should fetch from API
        response1 = self.client.get('/material-types')
        self.assertEqual(200, response1.status_code)
        
        # Second call should use cache (within cache duration)
        with patch('service.configuration_info_service._cache_timestamp', datetime.now()):
            with patch('service.configuration_info_service._material_types_cache', ["test"]):
                response2 = self.client.get('/material-types')
                self.assertEqual(200, response2.status_code)

    # Tests for folder path validation edge cases
    def test_parse_folder_data_folder_path_not_string(self):
        payload = {'folderPath': 123}
        
        response = self.client.post(
            '/parse-folder-data',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('must be a string', data['message'])

    def test_parse_folder_data_outside_safe_root(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', '/safe/root'):
            with patch('service.configuration_info_service.os.path.realpath') as mock_realpath:
                mock_realpath.side_effect = lambda x: x
                with patch('service.configuration_info_service.os.path.commonpath') as mock_commonpath:
                    mock_commonpath.side_effect = ValueError("Paths on different drives")
                    
                    payload = {'folderPath': 'C:\\different\\drive'}
                    
                    response = self.client.post(
                        '/parse-folder-data',
                        data=json.dumps(payload),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(400, response.status_code)
                    data = json.loads(response.data)
                    self.assertFalse(data['success'])

    # Tests for list_directories with include_files parameter
    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.path.isdir')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.join')
    def test_list_directories_with_files(self, mock_join, mock_listdir, mock_isdir,
                                        mock_exists, mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base/subdir'
        mock_exists.return_value = True
        mock_isdir.side_effect = lambda x: x.endswith('subdir') or x.endswith('folder')
        mock_listdir.return_value = ['file.txt', 'folder']
        mock_join.side_effect = lambda a, b: f"{a}/{b}"
        
        response = self.client.get('/list-directories?path=/subdir&include_files=true')
        self.assertEqual(200, response.status_code)
        
        data = json.loads(response.data)
        self.assertIn('entries', data)

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.path.isdir')
    @patch('service.configuration_info_service.os.listdir')
    def test_list_directories_permission_error(self, mock_listdir, mock_isdir,
                                               mock_exists, mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base/restricted'
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.side_effect = PermissionError("Access denied")
        
        response = self.client.get('/list-directories?path=/restricted')
        self.assertEqual(403, response.status_code)

    @patch('service.configuration_info_service.os.environ.get')
    @patch('service.configuration_info_service.os.path.realpath')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.path.isdir')
    @patch('service.configuration_info_service.os.listdir')
    def test_list_directories_generic_error(self, mock_listdir, mock_isdir,
                                           mock_exists, mock_realpath, mock_env_get):
        mock_env_get.return_value = '/test/base'
        mock_realpath.return_value = '/test/base/error'
        mock_exists.return_value = True
        mock_isdir.return_value = True
        mock_listdir.side_effect = Exception("Generic error")
        
        response = self.client.get('/list-directories?path=/error')
        self.assertEqual(500, response.status_code)

    @patch('service.configuration_info_service.os.environ.get')
    def test_list_directories_top_level_exception(self, mock_env_get):
        mock_env_get.side_effect = Exception("Config error")
        
        response = self.client.get('/list-directories')
        self.assertEqual(500, response.status_code)

    # Tests for file finding with security checks
    def test_parse_folder_data_permission_error_reading(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', tempfile.gettempdir()):
            test_file = os.path.join(self.test_dir, 'test.json')
            with open(test_file, 'w') as f:
                f.write('{}')
            
            payload = {'folderPath': self.test_dir}
            
            with patch('builtins.open', side_effect=PermissionError("No access")):
                response = self.client.post(
                    '/parse-folder-data',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                
                self.assertEqual(500, response.status_code)

    def test_parse_folder_data_generic_error_reading(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', tempfile.gettempdir()):
            test_file = os.path.join(self.test_dir, 'test.json')
            with open(test_file, 'w') as f:
                f.write('{}')
            
            payload = {'folderPath': self.test_dir}
            
            with patch('builtins.open', side_effect=Exception("Read error")):
                response = self.client.post(
                    '/parse-folder-data',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                
                self.assertEqual(500, response.status_code)

    def test_parse_folder_data_csv_file(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', tempfile.gettempdir()):
            test_file = os.path.join(self.test_dir, 'test.csv')
            test_content = 'col1,col2\nval1,val2'
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            payload = {'folderPath': self.test_dir}
            
            response = self.client.post(
                '/parse-folder-data',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual('test.csv', data['fileName'])
            self.assertEqual('.csv', data['fileExtension'])

    def test_parse_folder_data_xml_file(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', tempfile.gettempdir()):
            test_file = os.path.join(self.test_dir, 'test.xml')
            test_content = '<root><item>test</item></root>'
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            payload = {'folderPath': self.test_dir}
            
            response = self.client.post(
                '/parse-folder-data',
                data=json.dumps(payload),
                content_type='application/json'
            )
            
            self.assertEqual(200, response.status_code)
            data = json.loads(response.data)
            self.assertTrue(data['success'])
            self.assertEqual('test.xml', data['fileName'])
            self.assertEqual('.xml', data['fileExtension'])

    def test_parse_folder_data_top_level_exception(self):
        with patch('service.configuration_info_service.SAFE_ROOT_FOLDER', '/test/root'):
            with patch('service.configuration_info_service.os.path.realpath', side_effect=Exception("Error")):
                payload = {'folderPath': self.test_dir}
                
                response = self.client.post(
                    '/parse-folder-data',
                    data=json.dumps(payload),
                    content_type='application/json'
                )
                
                self.assertEqual(500, response.status_code)

    # Tests for validation with sync test
    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.get_repository_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_csv_validation(self, mock_get_config, mock_set_config,
                                                   mock_write, mock_reload, mock_repo_factory,
                                                   mock_validator_factory, mock_file_type,
                                                   mock_isfile, mock_listdir, mock_exists,
                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.csv']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'csv'
        
        mock_validator = MagicMock()
        mock_validator.validate.return_value = None
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        mock_patient_service = MagicMock()
        mock_patient_service.smoke_validate.return_value = []
        mock_sample_service = MagicMock()
        mock_sample_service.smoke_validate.return_value = []
        mock_condition_service = MagicMock()
        mock_condition_service.smoke_validate.return_value = []
        
        with patch('service.configuration_info_service.PatientService', return_value=mock_patient_service):
            with patch('service.configuration_info_service.SampleService', return_value=mock_sample_service):
                with patch('service.configuration_info_service.ConditionService', return_value=mock_condition_service):
                    payload = {
                        'file_type': 'csv',
                        'test_records_path': self.test_dir,
                        'donor_mapping': json.dumps({'id': 'donor.id'}),
                        'sample_mapping': json.dumps({'id': 'sample.id'}),
                        'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
                        'validate_all_files': True
                    }
                    
                    response = self.client.post(
                        '/validate-mappings',
                        data=json.dumps(json.dumps(payload)),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.get_repository_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_xml_validation(self, mock_get_config, mock_set_config,
                                                   mock_write, mock_reload, mock_repo_factory,
                                                   mock_validator_factory, mock_file_type,
                                                   mock_isfile, mock_listdir, mock_exists,
                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.xml']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'xml'
        
        mock_validator = MagicMock()
        mock_validator.validate.return_value = None
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        mock_patient_service = MagicMock()
        mock_patient_service.smoke_validate.return_value = []
        mock_sample_service = MagicMock()
        mock_sample_service.smoke_validate.return_value = []
        mock_condition_service = MagicMock()
        mock_condition_service.smoke_validate.return_value = []
        
        with patch('service.configuration_info_service.PatientService', return_value=mock_patient_service):
            with patch('service.configuration_info_service.SampleService', return_value=mock_sample_service):
                with patch('service.configuration_info_service.ConditionService', return_value=mock_condition_service):
                    payload = {
                        'file_type': 'xml',
                        'test_records_path': self.test_dir,
                        'donor_mapping': json.dumps({'id': 'donor.id'}),
                        'sample_mapping': json.dumps({'id': 'sample.id'}),
                        'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
                    }
                    
                    response = self.client.post(
                        '/validate-mappings',
                        data=json.dumps(json.dumps(payload)),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_structural_validation_failure(self, mock_get_config, mock_set_config,
                                                            mock_write, mock_reload,
                                                            mock_validator_factory, mock_file_type,
                                                            mock_isfile, mock_listdir, mock_exists,
                                                            mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.csv']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'csv'
        
        validation_error = Exception("Structural validation failed")
        validation_error.concept = 'sample'
        validation_error.error_message = 'Missing required field'
        
        mock_validator = MagicMock()
        mock_validator.validate.side_effect = validation_error
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        payload = {
            'file_type': 'csv',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.get_repository_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_patient_errors(self, mock_get_config, mock_set_config,
                                                   mock_write, mock_reload, mock_repo_factory,
                                                   mock_validator_factory, mock_file_type,
                                                   mock_isfile, mock_listdir, mock_exists,
                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        
        mock_patient_service = MagicMock()
        mock_patient_service.smoke_validate.return_value = ['Patient error 1']
        mock_sample_service = MagicMock()
        mock_sample_service.smoke_validate.return_value = []
        mock_condition_service = MagicMock()
        mock_condition_service.smoke_validate.return_value = []
        
        with patch('service.configuration_info_service.PatientService', return_value=mock_patient_service):
            with patch('service.configuration_info_service.SampleService', return_value=mock_sample_service):
                with patch('service.configuration_info_service.ConditionService', return_value=mock_condition_service):
                    payload = {
                        'file_type': 'json',
                        'test_records_path': self.test_dir,
                        'donor_mapping': json.dumps({'id': 'donor.id'}),
                        'sample_mapping': json.dumps({'id': 'sample.id'}),
                        'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
                    }
                    
                    response = self.client.post(
                        '/validate-mappings',
                        data=json.dumps(json.dumps(payload)),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_no_test_files(self, mock_get_config, mock_set_config,
                                            mock_write, mock_reload, mock_listdir, mock_exists,
                                            mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = []
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_test_records_path_access_error(self, mock_get_config, mock_set_config,
                                                              mock_write, mock_reload, mock_listdir,
                                                              mock_exists, mock_makedirs, mock_copy,
                                                              mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.side_effect = PermissionError("Access denied")
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_repository_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_service_creation_error(self, mock_get_config, mock_set_config,
                                                      mock_write, mock_reload, mock_repo_factory,
                                                      mock_file_type, mock_isfile, mock_listdir,
                                                      mock_exists, mock_makedirs, mock_copy,
                                                      mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        mock_repo_factory.side_effect = Exception("Service creation failed")
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.get_repository_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_miabis_mode(self, mock_get_config, mock_set_config,
                                                mock_write, mock_reload, mock_repo_factory,
                                                mock_validator_factory, mock_file_type,
                                                mock_isfile, mock_listdir, mock_exists,
                                                mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        
        mock_patient_service = MagicMock()
        mock_patient_service.smoke_validate.return_value = []
        mock_sample_service = MagicMock()
        mock_sample_service.smoke_validate.return_value = []
        mock_condition_service = MagicMock()
        mock_condition_service.smoke_validate.return_value = []
        
        with patch('service.configuration_info_service.PatientService', return_value=mock_patient_service):
            with patch('service.configuration_info_service.SampleService', return_value=mock_sample_service):
                with patch('service.configuration_info_service.ConditionService', return_value=mock_condition_service):
                    payload = {
                        'file_type': 'json',
                        'test_records_path': self.test_dir,
                        'donor_mapping': json.dumps({'id': 'donor.id'}),
                        'sample_mapping': json.dumps({'id': 'sample.id'}),
                        'condition_mapping': json.dumps({'icd-10_code': 'condition.code'}),
                        'sync_target': 'miabis'
                    }
                    
                    response = self.client.post(
                        '/validate-mappings',
                        data=json.dumps(json.dumps(payload)),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(200, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_donor_error_categorization(self, mock_get_config, mock_set_config,
                                                               mock_write, mock_reload,
                                                               mock_validator_factory, mock_file_type,
                                                               mock_isfile, mock_listdir, mock_exists,
                                                               mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        
        validation_error = Exception("Donor validation failed")
        validation_error.concept = 'donor'
        validation_error.error_message = 'Invalid donor field'
        
        mock_validator = MagicMock()
        mock_validator.validate.side_effect = validation_error
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_condition_error_categorization(self, mock_get_config, mock_set_config,
                                                                   mock_write, mock_reload,
                                                                   mock_validator_factory, mock_file_type,
                                                                   mock_isfile, mock_listdir, mock_exists,
                                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        
        validation_error = Exception("Condition validation failed")
        validation_error.concept = 'condition'
        validation_error.error_message = 'Invalid condition field'
        
        mock_validator = MagicMock()
        mock_validator.validate.side_effect = validation_error
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)

    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.listdir')
    @patch('service.configuration_info_service.os.path.isfile')
    @patch('service.configuration_info_service.get_records_file_type')
    @patch('service.configuration_info_service.get_validator_factory')
    @patch('service.configuration_info_service.reload_all_maps')
    @patch('service.configuration_info_service.write_to_file')
    @patch('service.configuration_info_service.set_config_value')
    @patch('service.configuration_info_service.get_config_value')
    def test_validate_mappings_with_generic_error_categorization(self, mock_get_config, mock_set_config,
                                                                 mock_write, mock_reload,
                                                                 mock_validator_factory, mock_file_type,
                                                                 mock_isfile, mock_listdir, mock_exists,
                                                                 mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_listdir.return_value = ['test.json']
        mock_isfile.return_value = True
        mock_file_type.return_value = 'json'
        
        validation_error = Exception("Generic validation error")
        
        mock_validator = MagicMock()
        mock_validator.validate.side_effect = validation_error
        mock_validator_factory_inst = MagicMock()
        mock_validator_factory_inst.create_validator.return_value = mock_validator
        mock_validator_factory.return_value = mock_validator_factory_inst
        
        payload = {
            'file_type': 'json',
            'test_records_path': self.test_dir,
            'donor_mapping': json.dumps({'id': 'donor.id'}),
            'sample_mapping': json.dumps({'id': 'sample.id'}),
            'condition_mapping': json.dumps({'icd-10_code': 'condition.code'})
        }
        
        response = self.client.post(
            '/validate-mappings',
            data=json.dumps(json.dumps(payload)),
            content_type='application/json'
        )
        
        self.assertEqual(400, response.status_code)


if __name__ == '__main__':
    unittest.main()

