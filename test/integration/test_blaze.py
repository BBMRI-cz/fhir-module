import unittest
from typing import List

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService

from mock import patch


class SampleDonorRepoStub(SampleDonorRepository):
    donors = [SampleDonor("newId"), SampleDonor("fakeId")]

    def get_all(self) -> List[SampleDonor]:
        return self.donors

    def add(self, donor: SampleDonor):
        self.donors.append(donor)


class TestBlazeStore(unittest.TestCase):

    def test_upload_all_patients(self):
        blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:8080/fhir')
        self.assertEqual(200, blaze_service.initial_upload_of_all_patients())

    def test_upload_all_patients_when_blaze_unreachable(self):
        blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:4444/fhir')
        self.assertEqual(404, blaze_service.initial_upload_of_all_patients())

    def test_is_present_in_blaze(self):
        blaze_service = BlazeService(PatientService(SampleDonorRepoStub()), 'http://localhost:8080/fhir')
        blaze_service.initial_upload_of_all_patients()
        self.assertTrue(blaze_service.is_present_in_blaze("fakeId"))
        self.assertTrue(blaze_service.is_present_in_blaze("newId"))

    def test_sync_one_new_patient(self):
        donor_repo = SampleDonorRepoStub()
        blaze_service = BlazeService(PatientService(donor_repo), 'http://localhost:8080/fhir')
        blaze_service.initial_upload_of_all_patients()
        num_of_patients_before_sync = blaze_service.get_num_of_patients()
        donor_repo.add(SampleDonor("uniqueNewPatient5"))
        blaze_service = BlazeService(PatientService(donor_repo), 'http://localhost:8080/fhir')
        blaze_service.sync_patients()
        self.assertEqual(num_of_patients_before_sync + 1, blaze_service.get_num_of_patients())


if __name__ == '__main__':
    unittest.main()
