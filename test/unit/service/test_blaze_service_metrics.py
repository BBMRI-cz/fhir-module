import unittest
from unittest.mock import Mock, patch

from model.sample_donor import SampleDonor
from model.sample import Sample
from model.condition import Condition
from model.sample_collection import SampleCollection
from service.blaze_service import BlazeService
from service.patient_service import PatientService
from service.condition_service import ConditionService
from service.sample_service import SampleService
from persistence.sample_collection_repository import SampleCollectionRepository
from exception.patient_not_found import PatientNotFoundError
import requests


class TestBlazeServiceMetrics(unittest.TestCase):
    """Test class for BlazeService metrics (processed/failed/skipped counts)."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_patient_service = Mock(spec=PatientService)
        self.mock_condition_service = Mock(spec=ConditionService)
        self.mock_sample_service = Mock(spec=SampleService)
        self.mock_sample_collection_repository = Mock(spec=SampleCollectionRepository)
        
        # Mock session and requests
        self.mock_session = Mock()
        
        # Create BlazeService instance with mocked dependencies
        with patch('service.blaze_service.requests.session') as mock_session_factory, \
             patch('service.blaze_service.setup_logger'), \
             patch('service.blaze_service.BLAZE_AUTH', ('user', 'pass')), \
             patch('service.blaze_service.get_metrics_for_service'):
            
            mock_session_factory.return_value = self.mock_session
            self.blaze_service = BlazeService(
                patient_service=self.mock_patient_service,
                condition_service=self.mock_condition_service,
                sample_service=self.mock_sample_service,
                blaze_url="http://test-blaze", # NOSONAR
                sample_collection_repository=self.mock_sample_collection_repository
            )

    def test_sync_patients_successful_processing(self):
        """Test patient sync with successful processing count."""
        test_donor = SampleDonor("test_patient_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        mock_response = Mock()
        mock_response.status_code = 201
        self.mock_session.post.return_value = mock_response
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=False):
            result = self.blaze_service.sync_patients()
            
            self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_sync_patients_connection_error_metrics(self):
        """Test patient sync metrics when connection error occurs."""
        test_donor = SampleDonor("test_patient_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=False), \
             patch.object(self.blaze_service, '_BlazeService__upload_donor', side_effect=requests.exceptions.ConnectionError()):
            
            result = self.blaze_service.sync_patients()
            
            self.assertEqual(result, {'processed': 0, 'failed': 1, 'skipped': 0})

    def test_sync_patients_invalid_type_metrics(self):
        """Test patient sync metrics when invalid donor type is encountered."""
        invalid_donor = "not_a_donor_object"
        self.mock_patient_service.get_all.return_value = [invalid_donor]
        
        result = self.blaze_service.sync_patients()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_sync_patients_already_present_metrics(self):
        """Test patient sync metrics when patient already exists."""
        test_donor = SampleDonor("existing_patient_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=True):
            result = self.blaze_service.sync_patients()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_sync_conditions_successful_processing(self):
        """Test condition sync with successful processing count."""
        test_condition = Condition("C50.9", "test_patient_123")
        self.mock_condition_service.get_all.return_value = [test_condition]
        
        with patch.object(self.blaze_service, 'patient_has_condition', return_value=False), \
             patch.object(self.blaze_service, '_BlazeService__upload_condition', return_value=201), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[10, 11]):
            
            result = self.blaze_service.sync_conditions()
            
            self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_sync_conditions_patient_not_found_metrics(self):
        """Test condition sync metrics when patient is not found."""
        test_condition = Condition("C50.9", "nonexistent_patient")
        self.mock_condition_service.get_all.return_value = [test_condition]
        
        with patch.object(self.blaze_service, 'patient_has_condition', side_effect=PatientNotFoundError()), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[10, 10]):
            
            result = self.blaze_service.sync_conditions()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_sync_conditions_already_exists_metrics(self):
        """Test condition sync metrics when condition already exists."""
        test_condition = Condition("C50.9", "test_patient_123")
        self.mock_condition_service.get_all.return_value = [test_condition]
        
        with patch.object(self.blaze_service, 'patient_has_condition', return_value=True), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[10, 10]):
            
            result = self.blaze_service.sync_conditions()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_sync_samples_successful_processing(self):
        """Test sample sync with successful processing count."""
        test_sample = Sample("test_sample_123", "test_patient_123")
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        with patch.object(self.blaze_service, '_BlazeService__check_sample_and_patient_presence', return_value=(False, True)), \
             patch.object(self.blaze_service, '_BlazeService__process_new_sample_upload', return_value=(1, 0)), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[5, 6]):
            
            result = self.blaze_service.sync_samples()
            
            self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_sync_samples_patient_not_present_metrics(self):
        """Test sample sync metrics when patient is not present."""
        test_sample = Sample("test_sample_123", "nonexistent_patient")
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        with patch.object(self.blaze_service, '_BlazeService__check_sample_and_patient_presence', return_value=(False, False)), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[5, 5]):
            
            result = self.blaze_service.sync_samples()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_sync_samples_already_present_and_up_to_date_metrics(self):
        """Test sample sync metrics when sample already exists and is up to date."""
        test_sample = Sample("test_sample_123", "test_patient_123")
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        with patch.object(self.blaze_service, '_BlazeService__check_sample_and_patient_presence', return_value=(True, True)), \
             patch.object(self.blaze_service, '_BlazeService__process_existing_sample_update', return_value=(0, 0, 1)), \
             patch.object(self.blaze_service, 'get_number_of_resources', side_effect=[5, 5]):
            
            result = self.blaze_service.sync_samples()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_sample_collections_successful_processing(self):
        """Test sample collection upload with successful processing count."""
        test_collection = SampleCollection("test_collection_123")
        self.mock_sample_collection_repository.get_all.return_value = [test_collection]
        
        mock_response = Mock()
        mock_response.status_code = 201
        self.mock_session.post.return_value = mock_response
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=False), \
             patch.object(self.blaze_service, 'get_number_of_resources', return_value=1):
            
            result = self.blaze_service.upload_sample_collections()
            
            self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_upload_sample_collections_invalid_type_metrics(self):
        """Test sample collection upload metrics with invalid type."""
        invalid_collection = "not_a_sample_collection"
        self.mock_sample_collection_repository.get_all.return_value = [invalid_collection]
        
        result = self.blaze_service.upload_sample_collections()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_sample_collections_already_present_metrics(self):
        """Test sample collection upload metrics when already present."""
        test_collection = SampleCollection("existing_collection_123")
        self.mock_sample_collection_repository.get_all.return_value = [test_collection]
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=True):
            
            result = self.blaze_service.upload_sample_collections()
            
            self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 0})

    def test_upload_sample_collections_upload_failure_metrics(self):
        """Test sample collection upload metrics when upload fails."""
        test_collection = SampleCollection("test_collection_123")
        self.mock_sample_collection_repository.get_all.return_value = [test_collection]
        
        mock_response = Mock()
        mock_response.status_code = 400
        self.mock_session.post.return_value = mock_response
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=False):
            
            result = self.blaze_service.upload_sample_collections()
            
            self.assertEqual(result, {'processed': 0, 'failed': 1, 'skipped': 0})

    def test_multiple_entities_mixed_results(self):
        """Test sync with mixed results across different entity types."""
        # Test patients: 2 processed, 1 failed, 1 skipped
        donors = [
            SampleDonor("patient_1"),  # Will be processed
            SampleDonor("patient_2"),  # Will be processed 
            SampleDonor("patient_3"),  # Will fail
            "invalid_donor"            # Will be skipped
        ]
        self.mock_patient_service.get_all.return_value = donors
        
        mock_response_success = Mock()
        mock_response_success.status_code = 201
        mock_response_fail = Mock()
        mock_response_fail.status_code = 400
        
        self.mock_session.post.side_effect = [mock_response_success, mock_response_success, mock_response_fail]
        
        with patch.object(self.blaze_service, 'is_resource_present_in_blaze', return_value=False):
            result = self.blaze_service.sync_patients()
            
            self.assertEqual(result, {'processed': 2, 'failed': 1, 'skipped': 1})


if __name__ == '__main__':
    unittest.main()
