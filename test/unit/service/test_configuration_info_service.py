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
        self.app = Flask(__name__)
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
        
        self.assertEqual(404, response.status_code)
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
        
        self.assertEqual(404, response.status_code)
        data = json.loads(response.data)
        self.assertFalse(data['success'])
        self.assertIn('No supported data files', data['message'])

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


if __name__ == '__main__':
    unittest.main()

