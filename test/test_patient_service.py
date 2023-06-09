import unittest

from fhirclient.models.bundle import Bundle

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from service.patient_service import PatientService
from mock import patch


class TestPatientService(unittest.TestCase):
    patient_service = PatientService(SampleDonorRepository())

    def test_get_all_patients_in_fhir_returns_bundle(self):
        bundle = self.patient_service.get_all_patients_in_fhir_transaction()
        self.assertIsInstance(bundle, Bundle)
        self.assertEqual("transaction", bundle.type)

    @patch('persistence.sample_donor_repository.SampleDonorRepository.get_all')
    def test_get_all_patients_in_fhir_entry(self, get_all_mock):
        get_all_mock.return_value = [SampleDonor("newId")]
        bundle = self.patient_service.get_all_patients_in_fhir_transaction()
        self.assertEqual(1, len(bundle.entry))
        self.assertEqual("Patient", bundle.entry[0].resource.resource_type)
        self.assertEqual("newId", bundle.entry[0].resource.identifier[0].value)


if __name__ == '__main__':
    unittest.main()
