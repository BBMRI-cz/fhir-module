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
    blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:8080/fhir')

    def test_upload_all_patients(self):
        self.assertEqual(200, self.blaze_service.initial_upload_of_all_patients())


if __name__ == '__main__':
    unittest.main()
