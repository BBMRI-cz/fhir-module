import unittest
from typing import List

from fhirclient.models.bundle import Bundle

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from service.patient_service import PatientService


class SampleDonorRepoStub(SampleDonorRepository):

    def get_all(self) -> List[SampleDonor]:
        return [SampleDonor("newId"), SampleDonor("patient2")]


class TestPatientService(unittest.TestCase):
    patient_service = PatientService(SampleDonorRepoStub())

    def test_get_all_patients_in_fhir_returns_bundle(self):
        bundle = self.patient_service.get_all_patients_in_fhir_transaction()
        self.assertIsInstance(bundle, Bundle)
        self.assertEqual("transaction", bundle.type)

    def test_get_all_patients_in_fhir_entry(self):
        bundle = self.patient_service.get_all_patients_in_fhir_transaction()
        self.assertEqual(2, len(bundle.entry))
        self.assertEqual("Patient", bundle.entry[0].resource.resource_type)
        self.assertEqual("newId", bundle.entry[0].resource.identifier[0].value)


if __name__ == '__main__':
    unittest.main()
