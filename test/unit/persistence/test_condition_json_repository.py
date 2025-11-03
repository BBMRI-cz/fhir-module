import datetime
import json
import os
import unittest
import pytest
import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_csv_repository import ConditionCsvRepository
from persistence.condition_json_repository import ConditionJsonRepository
from persistence.condition_xml_repository import ConditionXMLRepository

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

    @unittest.skipIf(os.name == 'nt', "chmod doesn't work properly on Windows")
    @patchfs
    def test_file_with_no_permissions_trows_no_error(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        # set permission to no access
        os.chmod(self.dir_path + "mock_file.json", 0o000)
        self.assertEqual(0, sum(1 for _ in self.condition_repository.get_all()))

    @patchfs
    def test_validate_conditions_from_json_file_valid_data(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertEqual(0, len(errors))

    @patchfs
    def test_validate_conditions_from_json_file_wrong_diagnosis(self, fake_fs):
        content = json.dumps(self.wrong_diagnosis)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No correct diagnosis has been found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_missing_diagnosis_field(self, fake_fs):
        incomplete_parsing_map = {
            "patient_id": "PatientId",
            "diagnosis_date": "DateOfDiagnosis"
        }
        repo = ConditionJsonRepository(records_path=self.dir_path,
                                      condition_parsing_map=incomplete_parsing_map)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = repo._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No ICD-10 code field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_missing_patient_id_field(self, fake_fs):
        incomplete_parsing_map = {
            "icd-10_code": "Diagnosis",
            "diagnosis_date": "DateOfDiagnosis"
        }
        repo = ConditionJsonRepository(records_path=self.dir_path,
                                      condition_parsing_map=incomplete_parsing_map)
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = repo._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No patient ID field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_invalid_date_format(self, fake_fs):
        invalid_date_sample = [{
            "PatientId": "138331",
            "SpecimenId": "14709",
            "DateOfDiagnosis": "invalid-date-format",
            "Diagnosis": "N880",
            "Sex": "M"
        }]
        content = json.dumps(invalid_date_sample)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Diagnosis date parsing error" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_invalid_json_format(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.json", contents="not valid json {")
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("correct JSON format" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_multiple_conditions_with_errors(self, fake_fs):
        mixed_samples = self.multiple_samples + [self.wrong_diagnosis[0]]
        content = json.dumps(mixed_samples)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("index 2" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_json_file_file_read_error(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        dir_entry = os.scandir(self.dir_path).__next__()
        if os.name != 'nt':
            os.chmod(self.dir_path + "mock_file.json", 0o000)
            errors = self.condition_repository._ConditionJsonRepository__validate_conditions_from_json_file(dir_entry)
            self.assertGreater(len(errors), 0)
            self.assertTrue(any("Error while opening file" in error for error in errors))

    def test_validate_json_diagnosis_field_missing(self):
        validation_errors = []
        condition_json = {"PatientId": "123"}
        result = self.condition_repository._ConditionJsonRepository__validate_json_diagnosis_field(
            condition_json, validation_errors
        )
        self.assertIsNone(result)
        self.assertEqual(1, len(validation_errors))
        self.assertTrue(any("No ICD-10 code field found" in str(exc) for exc in validation_errors))

    def test_validate_json_diagnosis_field_present(self):
        validation_errors = []
        condition_json = {"Diagnosis": "N880", "PatientId": "123"}
        result = self.condition_repository._ConditionJsonRepository__validate_json_diagnosis_field(
            condition_json, validation_errors
        )
        self.assertEqual("N880", result)
        self.assertEqual(0, len(validation_errors))

    def test_validate_json_patient_id_field_missing(self):
        validation_errors = []
        condition_json = {"Diagnosis": "N880"}
        result = self.condition_repository._ConditionJsonRepository__validate_json_patient_id_field(
            condition_json, validation_errors
        )
        self.assertIsNone(result)
        self.assertEqual(1, len(validation_errors))
        self.assertTrue(any("No patient ID field found" in str(exc) for exc in validation_errors))

    def test_validate_json_patient_id_field_present(self):
        validation_errors = []
        condition_json = {"PatientId": "patient_123", "Diagnosis": "N880"}
        result = self.condition_repository._ConditionJsonRepository__validate_json_patient_id_field(
            condition_json, validation_errors
        )
        self.assertEqual("patient_123", result)
        self.assertEqual(0, len(validation_errors))

    def test_parse_json_diagnosis_datetime_valid(self):
        validation_errors = []
        condition_json = {"DateOfDiagnosis": "2020-01-15T00:00:00"}
        result = self.condition_repository._ConditionJsonRepository__parse_json_diagnosis_datetime(
            condition_json, validation_errors
        )
        self.assertIsNotNone(result)
        self.assertEqual(datetime.datetime(2020, 1, 15), result)
        self.assertEqual(0, len(validation_errors))

    def test_parse_json_diagnosis_datetime_invalid(self):
        validation_errors = []
        condition_json = {"DateOfDiagnosis": "not-a-date"}
        self.condition_repository._ConditionJsonRepository__parse_json_diagnosis_datetime(
            condition_json, validation_errors
        )
        self.assertEqual(1, len(validation_errors))

    def test_parse_json_diagnosis_datetime_missing_field(self):
        validation_errors = []
        condition_json = {"Diagnosis": "N880"}
        result = self.condition_repository._ConditionJsonRepository__parse_json_diagnosis_datetime(
            condition_json, validation_errors
        )
        self.assertIsNone(result)
        self.assertEqual(0, len(validation_errors))

    def test_validate_json_diagnoses_valid(self):
        validation_errors = []
        result = self.condition_repository._ConditionJsonRepository__validate_json_diagnoses(
            "C50", "patient_123", validation_errors
        )
        self.assertEqual(["C50"], result)
        self.assertEqual(0, len(validation_errors))

    def test_validate_json_diagnoses_invalid(self):
        validation_errors = []
        result = self.condition_repository._ConditionJsonRepository__validate_json_diagnoses(
            "invalid", "patient_123", validation_errors
        )
        self.assertEqual([], result)
        self.assertEqual(1, len(validation_errors))
        self.assertTrue(any("No correct diagnosis has been found" in str(exc) for exc in validation_errors))

    def test_validate_json_diagnoses_none_field(self):
        validation_errors = []
        result = self.condition_repository._ConditionJsonRepository__validate_json_diagnoses(
            None, "patient_123", validation_errors
        )
        self.assertEqual([], result)
        self.assertEqual(1, len(validation_errors))


if __name__ == '__main__':
    unittest.main()
