import logging
import unittest
from typing import List

import pytest
import requests

from model.condition import Condition
from model.sample_donor import SampleDonor
from persistence.condition_repository import ConditionRepository
from persistence.sample_donor_repository import SampleDonorRepository
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService


class SampleDonorRepoStub(SampleDonorRepository):
    donors = [SampleDonor("newId"), SampleDonor("fakeId")]

    def get_all(self) -> List[SampleDonor]:
        return self.donors

    def add(self, donor: SampleDonor):
        self.donors.append(donor)


class ConditionRepoStub(ConditionRepository):
    conditions = [Condition("C504", "fakeId"), Condition("C505", "fakeId")]

    def get_all(self) -> List[Condition]:
        return self.conditions

    def add(self, condition: Condition):
        self.conditions.append(condition)


class TestBlazeStore(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.blaze_service = BlazeService(PatientService(SampleDonorRepoStub()),
                                          ConditionService(ConditionRepoStub()),
                                          'http://localhost:8080/fhir')
        yield
        try:
            for donor in SampleDonorRepoStub().get_all():
                self.blaze_service.delete_patient(donor.identifier)
        except requests.exceptions.ConnectionError:
            logging.info("Could not teardown correctly")

    def test_upload_all_patients(self):
        self.assertEqual(200, self.blaze_service.initial_upload_of_all_patients())

    def test_upload_all_patients_when_blaze_unreachable(self):
        self.blaze_service = BlazeService(PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:44/wrong',
                                          condition_service=ConditionService(ConditionRepoStub()))
        self.assertEqual(404, self.blaze_service.initial_upload_of_all_patients())

    def test_is_present_in_blaze(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_patient_present_in_blaze("fakeId"))
        self.assertTrue(self.blaze_service.is_patient_present_in_blaze("newId"))

    def test_sync_one_new_patient(self):
        donor_repo = SampleDonorRepoStub()
        self.blaze_service.initial_upload_of_all_patients()
        num_of_patients_before_sync = self.blaze_service.get_num_of_patients()
        donor_repo.add(SampleDonor("uniqueNewPatient5"))
        self.blaze_service = BlazeService(PatientService(donor_repo),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()))
        self.blaze_service.sync_patients()
        self.assertEqual(num_of_patients_before_sync + 1, self.blaze_service.get_num_of_patients())

    def test_delete_patient(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_patient_present_in_blaze("fakeId"))
        self.blaze_service.delete_patient("fakeId")
        self.assertFalse(self.blaze_service.is_patient_present_in_blaze("fakeId"))

    def test_upload_patient_and_their_condition(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_patient_present_in_blaze("fakeId"))
        self.blaze_service.sync_conditions()
        self.assertTrue(self.blaze_service.patient_has_condition("fakeId", "C50.4"))

    def test_sync_one_new_condition(self):
        condition_repo = ConditionRepoStub()
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.sync_conditions()
        self.assertFalse(self.blaze_service.patient_has_condition("fakeId", "C39.4"))
        condition_repo.add(Condition(patient_id="fakeId", icd_10_code="C394"))
        self.blaze_service = BlazeService(PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(condition_repo))
        self.assertTrue(self.blaze_service.patient_has_condition("fakeId", "C39.4"))

    def test_delete_all_patients(self):
        for donor in SampleDonorRepoStub().get_all():
            self.blaze_service.delete_patient(donor.identifier)


if __name__ == '__main__':
    unittest.main()
