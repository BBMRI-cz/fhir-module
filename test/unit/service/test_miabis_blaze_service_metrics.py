import unittest
from unittest.mock import Mock, patch

from model.miabis.sample_donor_miabis import SampleDonorMiabis
from model.miabis.sample_miabis import SampleMiabis
from model.miabis.collection_miabis import CollectionMiabis
from service.miabis_blaze_service import MiabisBlazeService
from service.patient_service import PatientService
from service.sample_service import SampleService
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.biobank_repository import BiobankRepository
from blaze_client import NonExistentResourceException
from requests import HTTPError
import requests


class TestMiabisBlazeServiceMetrics(unittest.TestCase):
    """Test class for MiabisBlazeService metrics (processed/failed/skipped counts)."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_patient_service = Mock(spec=PatientService)
        self.mock_sample_service = Mock(spec=SampleService)
        self.mock_sample_collection_repository = Mock(spec=SampleCollectionRepository)
        self.mock_biobank_repository = Mock(spec=BiobankRepository)
        self.mock_blaze_client = Mock()
        
        # Create MiabisBlazeService instance with mocked dependencies
        with patch('service.miabis_blaze_service.BlazeClient') as mock_blaze_client_class, \
             patch('service.miabis_blaze_service.setup_logger'), \
             patch('service.miabis_blaze_service.MIABIS_BLAZE_AUTH', ('user', 'pass')), \
             patch('service.miabis_blaze_service.get_metrics_for_service'):
            
            mock_blaze_client_class.return_value = self.mock_blaze_client
            self.miabis_service = MiabisBlazeService(
                patient_service=self.mock_patient_service,
                sample_service=self.mock_sample_service,
                blaze_url="http://test-blaze", # NOSONAR
                sample_collection_repository=self.mock_sample_collection_repository,
                biobank_repository=self.mock_biobank_repository
            )

    def test_sync_biobank_already_present_metrics(self):
        """Test biobank sync metrics when biobank already exists."""
        test_biobank = Mock()
        test_biobank.identifier = "existing_biobank"
        self.mock_biobank_repository.get_biobank.return_value = test_biobank
        self.mock_sample_collection_repository.get_all.return_value = []
        
        # Mock biobank as already present
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True
        
        result = self.miabis_service.sync_biobank_and_collections()
        
        self.assertEqual(result['biobank'], {'processed': 0, 'failed': 0, 'skipped': 1})
        self.assertEqual(result['collections'], {'processed': 0, 'failed': 0, 'skipped': 0})

    def test_sync_biobank_connection_error_metrics(self):
        """Test biobank sync metrics when connection error occurs."""
        test_biobank = Mock()
        test_biobank.identifier = "test_biobank"
        self.mock_biobank_repository.get_biobank.return_value = test_biobank
        
        # Mock connection error
        self.mock_blaze_client.is_resource_present_in_blaze.side_effect = requests.exceptions.ConnectionError()
        
        result = self.miabis_service.sync_biobank_and_collections()
        
        self.assertEqual(result['biobank'], {'processed': 0, 'failed': 1, 'skipped': 0})

    def test_sync_collections_invalid_type_metrics(self):
        """Test collections sync metrics when invalid collection type is encountered."""
        test_biobank = Mock()
        test_biobank.identifier = "test_biobank"
        self.mock_biobank_repository.get_biobank.return_value = test_biobank
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True  # Biobank present
        
        # Return invalid collection type
        invalid_collection = "not_a_collection_object"
        self.mock_sample_collection_repository.get_all.return_value = [invalid_collection]
        
        result = self.miabis_service.sync_biobank_and_collections()
        
        self.assertEqual(result['biobank'], {'processed': 0, 'failed': 0, 'skipped': 1})
        self.assertEqual(result['collections'], {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_patients_successful_processing(self):
        """Test patient upload with successful processing count."""
        test_donor = SampleDonorMiabis("test_donor_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        # Mock donor not present in blaze
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = False
        
        result = self.miabis_service.upload_patients()
        
        self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_upload_patients_invalid_type_metrics(self):
        """Test patient upload metrics when invalid donor type is encountered."""
        invalid_donor = "not_a_donor_object"
        self.mock_patient_service.get_all.return_value = [invalid_donor]
        
        result = self.miabis_service.upload_patients()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_patients_http_error_metrics(self):
        """Test patient upload metrics when HTTP error occurs."""
        test_donor = SampleDonorMiabis("test_donor_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = False
        self.mock_blaze_client.upload_donor.side_effect = HTTPError("HTTP 400: Bad Request")
        
        result = self.miabis_service.upload_patients()
        
        self.assertEqual(result, {'processed': 0, 'failed': 1, 'skipped': 0})

    def test_upload_patients_already_present_same_data_metrics(self):
        """Test patient upload metrics when patient exists with same data."""
        test_donor = SampleDonorMiabis("existing_donor_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        # Mock donor as already present
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True
        self.mock_blaze_client.get_fhir_id.return_value = "donor_fhir_id"
        
        # Mock same donor from blaze
        same_donor = SampleDonorMiabis("existing_donor_123")
        self.mock_blaze_client.build_donor_from_json.return_value = same_donor
        
        result = self.miabis_service.upload_patients()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_patients_already_present_different_data_metrics(self):
        """Test patient upload metrics when patient exists with different data."""
        test_donor = SampleDonorMiabis("existing_donor_123")
        self.mock_patient_service.get_all.return_value = [test_donor]
        
        # Mock donor as already present
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True
        self.mock_blaze_client.get_fhir_id.return_value = "donor_fhir_id"
        
        # Mock different donor from blaze - just mock it as different without setting properties
        different_donor = Mock()
        different_donor.identifier = "existing_donor_123"
        self.mock_blaze_client.build_donor_from_json.return_value = different_donor
        
        result = self.miabis_service.upload_patients()
        
        self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_upload_samples_successful_processing(self):
        """Test sample upload with successful processing count."""
        test_sample = SampleMiabis(
            identifier="test_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Plasma"  # Use valid material type
        )
        test_sample.condition = Mock()
        test_sample.sample_collection_id = "test_collection_123"
        
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        # Mock sample not present, patient present, condition not present
        self.mock_blaze_client.is_resource_present_in_blaze.side_effect = [False, False]  # Sample, condition
        self.mock_blaze_client.upload_sample.return_value = "sample_fhir_id"
        self.mock_blaze_client.get_fhir_id.side_effect = ["patient_fhir_id", "collection_fhir_id"]
        self.mock_blaze_client.add_already_present_samples_to_existing_collection.return_value = True
        
        result = self.miabis_service.upload_samples()
        
        self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_upload_samples_invalid_type_metrics(self):
        """Test sample upload metrics when invalid sample type is encountered."""
        invalid_sample = "not_a_sample_object"
        self.mock_sample_service.get_all.return_value = [invalid_sample]
        
        result = self.miabis_service.upload_samples()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_samples_already_present_same_data_metrics(self):
        """Test sample upload metrics when sample exists with same data."""
        test_sample = SampleMiabis(
            identifier="existing_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Plasma"
        )
        
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        # Mock sample as already present
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True
        self.mock_blaze_client.get_fhir_id.return_value = "sample_fhir_id"
        
        # Mock same sample from blaze
        same_sample = SampleMiabis(
            identifier="existing_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Plasma"
        )
        self.mock_blaze_client.build_sample_from_json.return_value = same_sample
        
        result = self.miabis_service.upload_samples()
        
        self.assertEqual(result, {'processed': 0, 'failed': 0, 'skipped': 1})

    def test_upload_samples_already_present_different_data_metrics(self):
        """Test sample upload metrics when sample exists with different data."""
        test_sample = SampleMiabis(
            identifier="existing_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Plasma"
        )
        
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        # Mock sample as already present
        self.mock_blaze_client.is_resource_present_in_blaze.return_value = True
        self.mock_blaze_client.get_fhir_id.return_value = "sample_fhir_id"
        
        # Mock different sample from blaze
        different_sample = SampleMiabis(
            identifier="existing_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Serum"  # Different material type
        )
        self.mock_blaze_client.build_sample_from_json.return_value = different_sample
        self.mock_blaze_client.update_sample.return_value = "updated_sample_fhir_id"
        
        result = self.miabis_service.upload_samples()
        
        self.assertEqual(result, {'processed': 1, 'failed': 0, 'skipped': 0})

    def test_upload_samples_nonexistent_resource_error_metrics(self):
        """Test sample upload metrics when NonExistentResourceException occurs."""
        test_sample = SampleMiabis(
            identifier="test_sample_123",
            donor_id="test_donor_123",
            diagnoses_with_observed_datetime=[("C50.9", None)],
            material_type="Plasma"
        )
        self.mock_sample_service.get_all.return_value = [test_sample]
        
        self.mock_blaze_client.is_resource_present_in_blaze.side_effect = NonExistentResourceException("Resource not found")
        
        result = self.miabis_service.upload_samples()
        
        self.assertEqual(result, {'processed': 0, 'failed': 1, 'skipped': 0})

if __name__ == '__main__':
    unittest.main()
