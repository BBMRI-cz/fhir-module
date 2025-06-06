import datetime
import logging
import unittest
from typing import List, Generator

import pytest
import requests

from exception.patient_not_found import PatientNotFoundError
from model.condition import Condition
from model.gender import Gender
from model.sample import Sample
from model.sample_collection import SampleCollection
from model.sample_donor import SampleDonor
from model.storage_temperature import StorageTemperature
from persistence.condition_repository import ConditionRepository
from persistence.factories.repository_factory import RepositoryFactory
from persistence.sample_collection_repository import SampleCollectionRepository
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.sample_repository import SampleRepository
from service.blaze_service import BlazeService
from service.condition_service import ConditionService
from service.patient_service import PatientService
from service.sample_service import SampleService


class SampleDonorRepoStub(SampleDonorRepository):
    donors = [SampleDonor(identifier="newId",
                          gender=Gender.FEMALE,
                          birth_date=datetime.datetime.now()),
              SampleDonor(identifier="fakeId",
                          gender=Gender.FEMALE,
                          birth_date=datetime.datetime.now())]

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


class SampleRepoStub(SampleRepository):
    samples = [Sample(identifier="fakeId", donor_id="newId", diagnoses=["C50.4"], material_type="1",
                        sample_collection_id="test:collection:1",
                      collected_datetime=datetime.datetime(year=2020, month=2, day=2),storage_temperature=StorageTemperature.TEMPERATURE_GN),
               Sample(identifier="fakeId2", donor_id="fakeId", material_type="2")]

    def get_all(self) -> List[Sample]:
        yield from self.samples

    def add(self, sample: Sample):
        self.samples.append(sample)

    def pop(self) -> Sample:
        return self.samples.pop()


class SampleCollectionRepoStub(SampleCollectionRepository):
    sample_collections = [SampleCollection(identifier="test:collection:1")]

    def get_all(self) -> Generator[SampleCollection, None, None]:
        yield from self.sample_collections


class TestBlazeStore(unittest.TestCase):

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.blaze_service = BlazeService(patient_service=PatientService(SampleDonorRepoStub()),
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(SampleRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          sample_collection_repository=SampleCollectionRepoStub())
        yield  # run test
        try:
            for sample in SampleRepoStub().get_all():
                self.blaze_service.delete_fhir_resource("Specimen", sample.identifier)
            for donor in SampleDonorRepoStub().get_all():
                self.blaze_service.delete_fhir_resource("Patient", donor.identifier)
            for organization in SampleCollectionRepoStub().get_all():
                self.blaze_service.delete_fhir_resource("Organization", organization.identifier)
        except requests.exceptions.ConnectionError:
            logging.info("Could not teardown correctly")

    def test_upload_all_patients(self):
        self.assertEqual(200, self.blaze_service.initial_upload_of_all_patients())

    def test_delete_patient_resource_by_identifier_ok(self):
        self.blaze_service.sync_patients()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                        identifier="newId"))
        self.assertEqual(204, self.blaze_service.delete_fhir_resource("PATIENT", "newId"))
        self.assertFalse(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                         identifier="newId"))

    def test_delete_nonexistent_resource_type_404(self):
        self.assertEqual(404, self.blaze_service.delete_fhir_resource("WRONG", "newId"))

    def test_delete_nonexistent_resource_404(self):
        self.assertEqual(404, self.blaze_service.delete_fhir_resource("Patient", "newId"))

    def test_upload_all_patients_when_blaze_unreachable(self):
        self.blaze_service = BlazeService(PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:44/wrong',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(SampleRepoStub()),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.assertEqual(404, self.blaze_service.initial_upload_of_all_patients())

    def test_is_present_in_blaze(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                        identifier="fakeId"))
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                        identifier="newId"))

    def test_sync_one_new_patient(self):
        donor_repo = SampleDonorRepoStub()
        self.blaze_service.initial_upload_of_all_patients()
        num_of_patients_before_sync = self.blaze_service.get_number_of_resources("Patient")
        donor_repo.add(SampleDonor("uniqueNewPatient5"))
        self.blaze_service = BlazeService(PatientService(donor_repo),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(SampleRepoStub()),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.sync_patients()
        self.assertEqual(num_of_patients_before_sync + 1, self.blaze_service.get_number_of_resources("Patient"))

    def test_sync_samples_one_same_sample_with_new_diagnosis(self):
        sample_repo = SampleRepoStub()
        sample_repo.add(Sample(identifier="fakeId", donor_id="newId", diagnoses=["C505"], material_type="1",
                               sample_collection_id="test:collection:1",
                               collected_datetime=datetime.datetime(year=2020, month=2, day=2)))
        self.blaze_service = BlazeService(patient_service=PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(sample_repo),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.sync_samples()
        diagnoses = self.blaze_service.get_diagnoses_from_sample("fakeId")
        self.assertEqual(2, len(diagnoses))
        sample_repo.pop()

    def test_delete_patient(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                        identifier="fakeId"))
        self.blaze_service.delete_fhir_resource("Patient", "fakeId")
        self.assertFalse(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                         identifier="fakeId"))

    def test_upload_patient_and_their_condition(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="patient",
                                                                        identifier="fakeId"))
        self.blaze_service.sync_conditions()
        self.assertTrue(self.blaze_service.patient_has_condition("fakeId", "C50.4"))

    def test_sync_one_new_condition(self):
        condition_repo = ConditionRepoStub()
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.sync_conditions()
        self.assertFalse(self.blaze_service.patient_has_condition("fakeId", "C50.6"))
        condition_repo.add(Condition(patient_id="fakeId", icd_10_code="C50.6"))
        self.blaze_service = BlazeService(PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(condition_repo),
                                          sample_service=SampleService(SampleRepoStub()),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.sync_conditions()
        self.assertTrue(self.blaze_service.patient_has_condition("fakeId", "C50.6"))

    def test_sync_conditions_if_patient_not_present_skips(self):
        self.blaze_service.sync_conditions()
        with self.assertRaises(PatientNotFoundError):
            self.assertFalse(self.blaze_service.
                             patient_has_condition("fakeId", "C50.4"))

    def test_delete_all_patients(self):
        self.blaze_service.initial_upload_of_all_patients()
        self.assertEqual(2, self.blaze_service.get_number_of_resources("Patient"))
        for donor in SampleDonorRepoStub().get_all():
            self.blaze_service.delete_fhir_resource("Patient", donor.identifier)
        self.assertEqual(0, self.blaze_service.get_number_of_resources("Patient"))

    def test_sync_samples_with_donors_not_present_in_blaze_no_upload(self):
        self.blaze_service.sync_samples()
        self.assertEqual(0, self.blaze_service.get_number_of_resources("Specimen"))

    def test_sync_samples_ok(self):
        self.blaze_service.sync_patients()
        self.blaze_service.sync_samples()
        self.assertEqual(2, self.blaze_service.get_number_of_resources("Specimen"))

    def test_sync_same_samples_twice_no_duplicates(self):
        self.blaze_service.upload_sample_collections()
        self.blaze_service.sync_patients()
        self.blaze_service.sync_samples()
        self.assertEqual(2, self.blaze_service.get_number_of_resources("Specimen"))
        self.blaze_service.sync_samples()
        self.assertEqual(2, self.blaze_service.get_number_of_resources("Specimen"))

    def test_upload_sample_collections(self):
        self.blaze_service.upload_sample_collections()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="Organization",
                                                                        identifier="test:collection:1"))

    def test_delete_sample_collections(self):
        self.blaze_service.upload_sample_collections()
        self.assertTrue(self.blaze_service.is_resource_present_in_blaze(resource_type="Organization",
                                                                        identifier="test:collection:1"))
        self.blaze_service.delete_fhir_resource("Organization", "test:collection:1")
        self.assertFalse(self.blaze_service.is_resource_present_in_blaze(resource_type="Organization",
                                                                         identifier="test:collection:1"))

    def test_upload_sample_collection_twice_no_duplicates(self):
        self.assertEqual(0, self.blaze_service.get_number_of_resources("Organization"))
        self.blaze_service.upload_sample_collections()
        self.assertEqual(1, self.blaze_service.get_number_of_resources("Organization"))
        self.blaze_service.upload_sample_collections()
        self.assertEqual(1, self.blaze_service.get_number_of_resources("Organization"))

    def test_sync_samples_with_collections_add_new_diagnosis(self):
        sample_repo = SampleRepoStub()
        sample_repo.add(Sample(identifier="fakeId", donor_id="newId", diagnoses=["C505"], material_type="1",
                               sample_collection_id="test:collection:1",
                               collected_datetime=datetime.datetime(year=2020, month=2, day=2)))
        self.blaze_service = BlazeService(patient_service=PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(sample_repo),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.upload_sample_collections()
        self.blaze_service.sync_samples()
        diagnoses = self.blaze_service.get_diagnoses_from_sample("fakeId")
        self.assertEqual(2, len(diagnoses))
        sample_repo.pop()

    def test_sync_same_sample_add_collection_id(self):
        sample_repo = SampleRepoStub()
        sample_repo.add(Sample(identifier="fakeId2", donor_id="newId", diagnoses=["C505"], material_type="1",
                               sample_collection_id="test:collection:1",
                               collected_datetime=datetime.datetime(year=2020, month=2, day=2)))
        self.blaze_service = BlazeService(patient_service=PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(sample_repo),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.sync_samples()
        self.assertIsNone(self.blaze_service.get_sample_collection_id(sample_identifier="fakeId2"))
        self.blaze_service.upload_sample_collections()
        self.blaze_service.sync_samples()
        self.assertIsNotNone(self.blaze_service.get_sample_collection_id(sample_identifier="fakeId2"))
        sample_repo.pop()

    def test_sync_sample_add_different_storage_temperature(self):
        sample_repo = SampleRepoStub()
        self.blaze_service = BlazeService(patient_service=PatientService(SampleDonorRepoStub()),
                                          blaze_url='http://localhost:8080/fhir',
                                          condition_service=ConditionService(ConditionRepoStub()),
                                          sample_service=SampleService(sample_repo),
                                          sample_collection_repository=SampleCollectionRepoStub())
        self.blaze_service.initial_upload_of_all_patients()
        self.blaze_service.sync_samples()
        prev_st= self.blaze_service.get_storage_temperature_from_sample("fakeId")
        self.assertEqual(StorageTemperature.TEMPERATURE_GN.value,prev_st)
        sample_repo.add(Sample(identifier="fakeId", donor_id="newId", diagnoses=["C505"], material_type="1",
                               sample_collection_id="test:collection:1",
                               collected_datetime=datetime.datetime(year=2020, month=2, day=2), storage_temperature=StorageTemperature.TEMPERATURE_OTHER))
        self.blaze_service.sync_samples()
        curr_st= self.blaze_service.get_storage_temperature_from_sample("fakeId")
        self.assertEqual(StorageTemperature.TEMPERATURE_OTHER.value,curr_st)

