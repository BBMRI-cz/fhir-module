import datetime
import json
import unittest
import pytest
import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_csv_repository import ConditionCsvRepository
from persistence.condition_json_repository import ConditionJsonRepository
from persistence.condition_xml_repository import ConditionXMLRepository
from util.config import PARSING_MAP_CSV


class TestConditionJsonRepository(unittest.TestCase):
    one_sample_correct = [{
        "PatientId": "138331",
        "SpecimenId": "14709",
        "DateOfDiagnosis": "2020-11-20T00:00:00",
        "Diagnosis": "N880",
        "DiagnosisAgeDonor": 47,
        "DonorAge": "1990-09-09",
        "SamplingDate": "2020-11-19T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]
    wrong_diagnosis = [{
        "PatientId": "138331",
        "SpecimenId": "14709",
        "DateOfDiagnosis": "2020-11-20T00:00:00",
        "Diagnosis": "wrong",
        "DiagnosisAgeDonor": 47,
        "DonorAge": "1990-09-09",
        "SamplingDate": "2020-11-19T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]
    multiple_diagnosis = [{
        "PatientId": "138331",
        "SpecimenId": "14709",
        "DateOfDiagnosis": "2020-11-20T00:00:00",
        "Diagnosis": "N880,C50",
        "DiagnosisAgeDonor": 47,
        "DonorAge": "1990-09-09",
        "SamplingDate": "2020-11-19T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]

    multiple_samples = [
        {
            "PatientId": "138331",
            "SpecimenId": "14709",
            "DateOfDiagnosis": "2020-11-20T00:00:00",
            "Diagnosis": "C51",
            "DiagnosisAgeDonor": 47,
            "DonorAge": "1990-09-09",
            "SamplingDate": "2020-11-19T00:00:00",
            "SampleType": "tumor-tissue-ffpe",
            "Sex": "M",
            "StorageTemperature": "temperatureRoom"
        },
        {
            "PatientId": "138327",
            "SpecimenId": "14763",
            "DateOfDiagnosis": "2024-03-05T00:00:00",
            "Diagnosis": "D105",
            "DiagnosisAgeDonor": 65,
            "DonorAge": 62,
            "SamplingDate": "2020-11-25T00:00:00",
            "SampleType": "tumor-tissue-ffpe",
            "Sex": "M",
            "StorageTemperature": "temperatureRoom"
        }
    ]

    parsing_map = {
        "condition_map": {
            "icd-10_code": "Diagnosis",
            "patient_id": "PatientId",
            "diagnosis_date": "DateOfDiagnosis"
        }
    }

    dir_path = "/mock/dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.condition_repository = ConditionJsonRepository(records_path=self.dir_path,
                                                            condition_parsing_map=self.parsing_map['condition_map'])
        yield  # run test

    @patchfs
    def test_get_all_from_one_file_with_one_condition(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for condition in self.condition_repository.get_all():
            self.assertIsInstance(condition, Condition)
            self.assertEqual("N88.0", condition.icd_10_code)
            self.assertEqual(datetime.datetime(year=2020, month=11, day=20), condition.diagnosis_datetime)

    @patchfs
    def test_get_all_from_two_files_with_three_conditions(self, fake_fs):
        one_content = json.dumps(self.one_sample_correct)
        multiple_content = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=one_content)
        fake_fs.create_file(self.dir_path + "mock_file2.json", contents=multiple_content)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(3, len(conditions))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        multiple_content = json.dumps(self.multiple_samples)
        wrong_content = json.dumps(self.wrong_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=multiple_content)
        fake_fs.create_file(self.dir_path + "mock_file2.json", contents=wrong_content)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_get_all_with_multiple_diagnosis_from_one_sample(self, fake_fs):
        multiple_content = json.dumps(self.multiple_samples)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=multiple_content)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))
        self.assertEqual("C51", conditions[0].icd_10_code)


if __name__ == '__main__':
    unittest.main()
