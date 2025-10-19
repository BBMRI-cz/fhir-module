import datetime
import os
import unittest
import pytest
import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_csv_repository import ConditionCsvRepository

class TestConditionCsvRepository(unittest.TestCase):
    header = "sample_ID;patient_pseudonym;sex;birth_year;diagnosis_date;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples\n"

    wrong_diagnosis = "32;1111;f;1945;2007-10-16;wrong;85;2100-01-16;blood-serum;-20;0"

    one_sample = "33;1111;m;1947;2007-10-16;M058;85;2100-01-16;serum;-20;0"

    sample_multiple_diagnosis = "33;1111;m;1947;2007-10-16;M058,C51,C50;85;2100-01-16;serum;-20;0"

    samples = "34;1112;f;1958;2100-10-16;M060;85;2007-10-30;serum;-20;0\n35;1113;m;1959;2100-10-22;M329;49;2007-10-22;serum;-20;1"

    dir_path = "/mock/dir/"

    parsing_map = {
        "donor_map": {
            "id": "patient_pseudonym",
            "gender": "sex",
            "birthDate": "birth_year"
        },
        "sample_map": {
            "sample_details": {
            "id": "sample_ID",
            "material_type": "sampling_type",
            "diagnosis": "diagnosis",
            "storage_temperature": "storage_temperature",
            "collection_date": "sampling_date",
            "diagnosis_date": "diagnosis_date",
            "collection": "material_type"
            },
            "donor_id": "patient_pseudonym"
        },
        "condition_map": {
            "icd-10_code": "diagnosis",
            "patient_id": "patient_pseudonym",
            "diagnosis_date": "diagnosis_date"
        }
    }

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.condition_repository = ConditionCsvRepository(records_path=self.dir_path,
                                                           condition_parsing_map=self.parsing_map['condition_map'],
                                                           separator=";")
        yield  # run test

    @patchfs
    def test_get_all_from_one_file_with_one_condition(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        for condition in self.condition_repository.get_all():
            self.assertEqual("M05.8", condition.icd_10_code)
            self.assertEqual(datetime.datetime(year=2007, month=10, day=16), condition.diagnosis_datetime)

    @patchfs
    def test_get_all_from_two_files_with_three_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        fake_fs.create_file(self.dir_path + "mock_file2.csv", contents=self.header + self.one_sample)
        self.assertEqual(3, sum(1 for _ in self.condition_repository.get_all()))

    @unittest.skipIf(os.name == 'nt', "chmod doesn't work properly on Windows")
    @patchfs
    def test_file_with_no_permissions_trows_no_error(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        # set permission to no access
        os.chmod(self.dir_path + "mock_file.csv", 0o000)
        self.assertEqual(0, sum(1 for _ in self.condition_repository.get_all()))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        fake_fs.create_file(self.dir_path + "mock_file2.csv", contents=self.header + self.wrong_diagnosis)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_get_all_with_multiple_diagnosis_from_one_sample(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.sample_multiple_diagnosis)
        self.assertEqual(3, sum(1 for _ in self.condition_repository.get_all()))

    @patchfs
    def test_validate_conditions_from_csv_file_valid_data(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertEqual(0, len(errors))

    @patchfs
    def test_validate_conditions_from_csv_file_wrong_diagnosis(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.wrong_diagnosis)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No correct diagnosis has been found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_csv_file_missing_diagnosis_field(self, fake_fs):
        incomplete_parsing_map = {
            "patient_id": "patient_pseudonym",
            "diagnosis_date": "diagnosis_date"
        }
        repo = ConditionCsvRepository(records_path=self.dir_path,
                                     condition_parsing_map=incomplete_parsing_map,
                                     separator=";")
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = repo._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No ICD-10 code field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_csv_file_missing_patient_id_field(self, fake_fs):
        incomplete_parsing_map = {
            "icd-10_code": "diagnosis",
            "diagnosis_date": "diagnosis_date"
        }
        repo = ConditionCsvRepository(records_path=self.dir_path,
                                     condition_parsing_map=incomplete_parsing_map,
                                     separator=";")
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = repo._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No patient ID field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_csv_file_invalid_date_format(self, fake_fs):
        invalid_date_sample = "33;1111;m;1947;invalid-date;M058;85;2100-01-16;serum;-20;0"
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + invalid_date_sample)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Diagnosis date parsing error" in error or "Error parsing date" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_csv_file_multiple_conditions_with_errors(self, fake_fs):
        mixed_samples = self.one_sample + "\n" + self.wrong_diagnosis
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + mixed_samples)
        dir_entry = os.scandir(self.dir_path).__next__()
        errors = self.condition_repository._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("row 2" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_csv_file_file_read_error(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        dir_entry = os.scandir(self.dir_path).__next__()
        if os.name != 'nt':
            os.chmod(self.dir_path + "mock_file.csv", 0o000)
            errors = self.condition_repository._ConditionCsvRepository__validate_conditions_from_csv_file(dir_entry)
            self.assertGreater(len(errors), 0)
            self.assertTrue(any("Error while opening file" in error for error in errors))

    def test_validate_diagnosis_field_missing(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"patient_pseudonym": 0}  # Missing diagnosis field
        result = self.condition_repository._ConditionCsvRepository__validate_diagnosis_field(validation_errors)
        self.assertIsNone(result)
        self.assertEqual(1, len(validation_errors))

    def test_validate_diagnosis_field_present(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"diagnosis": 0}
        result = self.condition_repository._ConditionCsvRepository__validate_diagnosis_field(validation_errors)
        self.assertEqual(0, result)
        self.assertEqual(0, len(validation_errors))

    def test_validate_patient_id_field_missing(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"diagnosis": 0}  # Missing patient_pseudonym field
        result = self.condition_repository._ConditionCsvRepository__validate_patient_id_field(["test_data"], validation_errors)
        self.assertIsNone(result)
        self.assertEqual(1, len(validation_errors))

    def test_validate_patient_id_field_present(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"patient_pseudonym": 1}
        data = ["test", "patient_123"]
        result = self.condition_repository._ConditionCsvRepository__validate_patient_id_field(data, validation_errors)
        self.assertEqual("patient_123", result)
        self.assertEqual(0, len(validation_errors))

    def test_extract_diagnoses_valid(self):
        validation_errors = []
        data = ["test", "patient_123", "C50"]
        result = self.condition_repository._ConditionCsvRepository__extract_diagnoses(data, 2, "patient_123", validation_errors)
        self.assertEqual(["C50"], result)
        self.assertEqual(0, len(validation_errors))

    def test_extract_diagnoses_invalid(self):
        validation_errors = []
        data = ["test", "patient_123", "invalid"]
        result = self.condition_repository._ConditionCsvRepository__extract_diagnoses(data, 2, "patient_123", validation_errors)
        self.assertEqual([], result)
        self.assertEqual(1, len(validation_errors))

    def test_parse_diagnosis_datetime_valid(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"diagnosis_date": 2}
        data = ["test", "patient_123", "2020-01-15"]
        result = self.condition_repository._ConditionCsvRepository__parse_diagnosis_datetime(data, "patient_123", validation_errors)
        self.assertIsNotNone(result)
        self.assertEqual(datetime.datetime(2020, 1, 15), result)
        self.assertEqual(0, len(validation_errors))

    def test_parse_diagnosis_datetime_invalid(self):
        validation_errors = []
        self.condition_repository._fields_dict = {"diagnosis_date": 2}
        data = ["test", "patient_123", "not-a-date"]
        self.condition_repository._ConditionCsvRepository__parse_diagnosis_datetime(data, "patient_123", validation_errors)
        self.assertEqual(1, len(validation_errors))

    def test_parse_diagnosis_datetime_missing_field(self):
        """Test parsing when diagnosis_date field is not in mapping"""
        validation_errors = []
        self.condition_repository._fields_dict = {"other_field": 0}
        data = ["test", "patient_123", "2020-01-15"]
        result = self.condition_repository._ConditionCsvRepository__parse_diagnosis_datetime(data, "patient_123", validation_errors)
        self.assertIsNone(result)
        self.assertEqual(0, len(validation_errors))

    def test_create_condition_objects(self):
        diagnoses = ["C50", "C51"]
        patient_id = "patient_123"
        diagnosis_datetime = datetime.datetime(2020, 1, 15)
        result = self.condition_repository._ConditionCsvRepository__create_condition_objects(
            diagnoses, patient_id, diagnosis_datetime
        )
        self.assertEqual(2, len(result))
        self.assertIsInstance(result[0], Condition)
        self.assertEqual("C50", result[0].icd_10_code)
        self.assertEqual("patient_123", result[0].patient_id)



if __name__ == '__main__':
    unittest.main()
