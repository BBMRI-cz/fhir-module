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

    # Tests for validation with sync test
    @patch('service.configuration_info_service.shutil.rmtree')
    @patch('service.configuration_info_service.shutil.copy2')
    @patch('service.configuration_info_service.os.makedirs')
    @patch('service.configuration_info_service.os.path.exists')
    @patch('service.configuration_info_service.os.scandir')
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
                                                   mock_scandir, mock_exists,
                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_entry = MagicMock()
        mock_entry.is_file.return_value = True
        mock_entry.name = 'test.csv'
        mock_scandir.return_value = [mock_entry]
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
    @patch('service.configuration_info_service.os.scandir')
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
                                                   mock_scandir, mock_exists,
                                                   mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_entry = MagicMock()
        mock_entry.is_file.return_value = True
        mock_entry.name = 'test.xml'
        mock_scandir.return_value = [mock_entry]
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
    @patch('service.configuration_info_service.os.scandir')
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
                                                mock_scandir, mock_exists,
                                                mock_makedirs, mock_copy, mock_rmtree):
        mock_get_config.return_value = '/test/path'
        mock_exists.return_value = True
        mock_entry = MagicMock()
        mock_entry.is_file.return_value = True
        mock_entry.name = 'test.json'
        mock_scandir.return_value = [mock_entry]
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

