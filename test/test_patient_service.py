import unittest

from fhirclient.models.bundle import Bundle

from persistence.sample_donor_repository import SampleDonorRepository
from service.patient_service import PatientService


class TestPatientService(unittest.TestCase):
    patient_service = PatientService(SampleDonorRepository())

    def test_get_all_patients_in_fhir_returns_bundle(self):
        self.assertIsInstance(self.patient_service.get_all_patients_in_fhir(), Bundle)


if __name__ == '__main__':
    unittest.main()
