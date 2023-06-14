import unittest
from typing import List

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService

from mock import patch


class SampleDonorRepoStub(SampleDonorRepository):

    def get_all(self) -> List[SampleDonor]:
        return [SampleDonor("newId"), SampleDonor("fakeId")]


class TestBlazeStore(unittest.TestCase):


    def test_upload_all_patients(self):
        blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:8080/fhir')
        self.assertEqual(200, blaze_service.initial_upload_of_all_patients())

    def test_upload_all_patients_when_blaze_unreachable(self):
        blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:4444/fhir')
        self.assertEqual(404, blaze_service.initial_upload_of_all_patients())


if __name__ == '__main__':
    unittest.main()
