import datetime
import json
import os
import unittest
from typing import cast

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.miabis.sample_miabis import SampleMiabis
from model.sample import Sample
from model.storage_temperature import StorageTemperature
from miabis_model.storage_temperature import StorageTemperature as MiabisStorageTemperature
from persistence.sample_json_repository import SampleJsonRepository
from util.config import STORAGE_TEMP_MAP


class TestSampleJsonRepository(unittest.TestCase):
    one_sample_correct = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "N880",
        "SamplingDate": "2010-10-10T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]

    one_sample_missing_storage_temperature = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "N880",
        "SamplingDate": "2010-10-10T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
    }]
    one_sample_missing_diagnosis = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "SamplingDate": "2010-10-10T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]

    one_sample_missing_collection_date = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "N880",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]
    one_sample_missing_material_type = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "N880",
        "SamplingDate": "2010-10-10T00:00:00",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]
    wrong_diagnosis = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "wrong",
        "SamplingDate": "2010-10-10T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]
    multiple_diagnosis = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2000-02-02T00:00:00",
        "Diagnosis": "N880,C50",
        "SamplingDate": "2010-10-10T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]

    multiple_samples = [
        {
            "PatientId": "1",
            "SpecimenId": "11",
            "DateOfDiagnosis": "2000-02-02T00:00:00",
            "Diagnosis": "C51",
            "SamplingDate": "2010-10-10T00:00:00",
            "SampleType": "tumor-tissue-ffpe",
            "Sex": "M",
            "StorageTemperature": "temperatureRoom"
        },
        {
            "PatientId": "1",
            "SpecimenId": "12",
            "DateOfDiagnosis": "2024-03-05T00:00:00",
            "Diagnosis": "D105",
            "SamplingDate": "2020-11-25T00:00:00",
            "SampleType": "tumor-tissue-ffpe",
            "Sex": "M",
            "StorageTemperature": "temperatureRoom"
        }
    ]
    parsing_map = {

        "sample_map": {
            "sample_details": {
                "id": "SpecimenId",
                "material_type": "SampleType",
                "diagnosis": "Diagnosis",
                "collection_date": "SamplingDate",
                "diagnosis_date": "DateOfDiagnosis",
                "storage_temperature": "StorageTemperature",
                "collection": "SampleType"
            },
            "donor_id": "PatientId"
        }
    }

    dir_path = "/mock/dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map["sample_map"],
                                                      material_type_map={"tumor-tissue-ffpe": "tumor-tissue-ffpe"})
        yield  # run test

    @patchfs
    def test_get_all_one_sample_ok(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(1, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)

    @patchfs
    def test_miabis_get_all_one_sample_ok(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      material_type_map={"tumor-tissue-ffpe": "TissueFixed"},
                                                      storage_temp_map=STORAGE_TEMP_MAP,
                                                      miabis_on_fhir_model=True,
                                                      standardized=False)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(1, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_two_samples_ok(self, fake_fs):
        content = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(2, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, Sample)
            self.assertIn(sample.identifier, ["11", "12"])

    @patchfs
    def test_miabis_get_all_two_samples_ok(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      material_type_map={"tumor-tissue-ffpe": "TissueFixed"},
                                                      miabis_on_fhir_model=True,
                                                      storage_temp_map=STORAGE_TEMP_MAP,
                                                      standardized=False)
        content = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(2, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, SampleMiabis)
            self.assertIn(sample.identifier, ["11", "12"])

    @patchfs
    def test_with_wrong_parsing_map(self, fake_fs):
        wrong_map = {
            "id": ".",
            "donor_id": "wrong_string"
        }
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path, sample_parsing_map=wrong_map)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_miabis_with_wrong_parsing_map(self, fake_fs):
        wrong_map = {
            "id": ".",
            "donor_id": "wrong_string"
        }
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path, sample_parsing_map=wrong_map,
                                                      material_type_map={"tumor-tissue-ffpe": "TissueFixed"},
                                                      miabis_on_fhir_model=True,
                                                      storage_temp_map=STORAGE_TEMP_MAP,
                                                      standardized=False)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))


    @patchfs
    def test_file_with_no_permissions_trows_no_error(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        # set permission to no access
        os.chmod(self.dir_path + "mock_file.json", 0o000)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_three_samples_from_two_collections_ok(self, fake_fs):
        content1 = json.dumps(self.one_sample_correct)
        content2 = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file1.json", contents=content1)
        fake_fs.create_file(self.dir_path + "mock_file2.json", contents=content2)
        self.assertEqual(3, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_miabis_get_all_three_samples_from_two_collections_ok(self, fake_fs):
        content1 = json.dumps(self.one_sample_correct)
        content2 = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file1.json", contents=content1)
        fake_fs.create_file(self.dir_path + "mock_file2.json", contents=content2)
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      material_type_map={"tumor-tissue-ffpe": "TissueFixed"},
                                                      storage_temp_map=STORAGE_TEMP_MAP,
                                                      miabis_on_fhir_model=True,
                                                      standardized=False)
        self.assertEqual(3, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_with_wrong_diagnosis_skips(self, fake_fs):
        content = json.dumps(self.wrong_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_three_samples_not_none_diagnosis(self, fake_fs):
        content1 = json.dumps(self.one_sample_correct)
        content2 = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file1.json", contents=content1)
        fake_fs.create_file(self.dir_path + "mock_file2.json", contents=content2)
        self.assertEqual(3, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsNotNone(sample.diagnoses)

    @patchfs
    def test_with_type_to_collection_map_ok(self, fake_fs):
        spm = self.parsing_map["sample_map"]
        spm['sample_details']['collection'] = "Diagnosis"
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=spm,
                                                      type_to_collection_map={"N880": "test:collection:id"})
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual("test:collection:id", next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_with_wrong_type_to_collection_map_id_is_none(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      type_to_collection_map={"not_present": "test:collection:id"})
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        sample = next(self.sample_repository.get_all())
        self.assertEqual(None, sample.sample_collection_id)

    @patchfs
    def test_with_type_to_collection_sampling_type_as_attribute_to_collection_ok(self, fake_fs):
        spm = self.parsing_map["sample_map"]
        spm['sample_details']['collection'] = "SampleType"
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=spm,
                                                      type_to_collection_map={
                                                          "tumor-tissue-ffpe": "test:collection:id"},
                                                      )
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual("test:collection:id", next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_with_wrong_type_to_collection_sampling_type_as_attribute_to_collection_id_is_none(self, fake_fs):
        spm = self.parsing_map["sample_map"]
        spm['sample_details']['collection'] = "SampleType"
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=spm,
                                                      type_to_collection_map={"not_present": "test:collection:id"})
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(None, next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_with_non_existent_attribute_to_collection(self, fake_fs):
        spm = self.parsing_map["sample_map"]
        spm['sample_details']['collection'] = "non_existent"
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=spm,
                                                      type_to_collection_map={"not_present": "test:collection:id"})
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(None, next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_storage_temp_map_ok(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(StorageTemperature.TEMPERATURE_ROOM,
                         next(self.sample_repository.get_all()).storage_temperature)

    @patchfs
    def test_storage_temp_map_code_not_found(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map={"bad": "map"})
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        self.assertEqual(None, next(self.sample_repository.get_all()).storage_temperature)

    @patchfs
    def test_missing_storage_temp_field(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.one_sample_missing_storage_temperature)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)
            self.assertEqual(None, sample.storage_temperature)
            self.assertEqual("tumor-tissue-ffpe", sample.material_type)
            self.assertEqual("N88.0", sample.diagnoses[0])
            self.assertEqual(datetime.datetime(2010, 10, 10), sample.collected_datetime)

    @patchfs
    def test_missing_material_type_field(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.one_sample_missing_material_type)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)
            self.assertEqual(StorageTemperature.TEMPERATURE_ROOM, sample.storage_temperature)
            self.assertEqual(None, sample.material_type)
            self.assertEqual("N88.0", sample.diagnoses[0])
            self.assertEqual(datetime.datetime(2010, 10, 10), sample.collected_datetime)

    @patchfs
    def test_missing_diagnosis_field(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.one_sample_missing_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)
            self.assertEqual(StorageTemperature.TEMPERATURE_ROOM, sample.storage_temperature)
            self.assertEqual("tumor-tissue-ffpe", sample.material_type)
            self.assertEqual(None, sample.diagnoses[0])
            self.assertEqual(datetime.date(2010, 10, 10), sample.collected_datetime)

    @patchfs
    def test_missing_collection_date_field(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.one_sample_missing_collection_date)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)
            self.assertEqual(StorageTemperature.TEMPERATURE_ROOM, sample.storage_temperature)
            self.assertEqual("tumor-tissue-ffpe", sample.material_type)
            self.assertEqual("N88.0", sample.diagnoses[0])
            self.assertEqual(None, sample.collected_datetime)

    @patchfs
    def test_multiple_diagnosis_one_sample(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP)
        content = json.dumps(self.multiple_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for sample in self.sample_repository.get_all():
            self.assertEqual("10", sample.identifier)
            self.assertEqual(StorageTemperature.TEMPERATURE_ROOM, sample.storage_temperature)
            self.assertEqual("tumor-tissue-ffpe", sample.material_type)
            self.assertEqual("N88.0", sample.diagnoses[0])
            self.assertEqual("C50", sample.diagnoses[1])
            self.assertEqual(datetime.datetime(2010, 10, 10), sample.collected_datetime)

    @patchfs
    def test_diagnosis_observed_miabis_repo(self, fake_fs):
        self.sample_repository = SampleJsonRepository(records_path=self.dir_path,
                                                      sample_parsing_map=self.parsing_map['sample_map'],
                                                      storage_temp_map=STORAGE_TEMP_MAP,
                                                      material_type_map={"tumor-tissue-ffpe": "TissueFixed"},
                                                      miabis_on_fhir_model=True,
                                                      standardized=False)
        content = json.dumps(self.multiple_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)

        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, SampleMiabis)
            sample = cast(SampleMiabis, sample)
            observations = sample._observations
            self.assertEqual(observations[0].diagnosis_observed_datetime,
                             datetime.datetime(year=2000, month=2, day=2))
            self.assertEqual("10", sample.identifier)
            self.assertEqual(MiabisStorageTemperature.TEMPERATURE_ROOM, sample.storage_temperature)
            self.assertEqual("TissueFixed", sample.material_type)
            self.assertEqual("N88.0", sample.diagnoses[0])
            self.assertEqual("C50", sample.diagnoses[1])
            self.assertEqual(datetime.datetime(2010, 10, 10), sample.collected_datetime)
