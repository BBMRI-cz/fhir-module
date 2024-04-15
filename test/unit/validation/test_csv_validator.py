import unittest

from pyfakefs.fake_filesystem_unittest import patchfs

from exception.no_files_provided import NoFilesProvidedException
from exception.nonexistent_attribute_parsing_map import NonexistentAttributeParsingMapException
from exception.wrong_parsing_map import WrongParsingMapException
from util.config import PARSING_MAP_CSV
from validation.csv_validator import CsvValidator


class TestCsvValidator(unittest.TestCase):
    header = "sample_ID;patient_pseudonym;sex;birth_year;date_of_diagnosis;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples\n"

    header_missing_sample_id_field = "patient_pseudonym;sex;birth_year;date_of_diagnosis;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples\n"

    samples = "34;1112;f;1958;2100-10-16;M0600;85;2007-10-30;serum;-20;0\n35;1113;m;1959;2100-10-22;M329;49;2007-10-22;serum;-20;1"

    missing_donor_parsing_map = {
        "sample_map": {
            "sample_details": {
                "id": "sample_ID",
                "material_type": "sampling_type",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient_pseudonym"
        },
        "condition_map": {
            "icd-10_code": "diagnosis",
            "patient_id": "patient_pseudonym"
        }
    }

    missing_sample_parsing_map = {
        "donor_map": {
            "id": "patient_pseudonym",
            "gender": "sex",
            "birthDate": "birth_year"
        },
        "condition_map": {
            "icd-10_code": "diagnosis",
            "patient_id": "patient_pseudonym"
        }
    }

    missing_condition_parsing_map = {
        "donor_map": {
            "id": "patient_pseudonym",
            "gender": "sex",
            "birthDate": "birth_year"
        },
        "sample_map": {
            "sample_details": {
                "id": "sample_ID",
                "material_type": "sampling_type",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient_pseudonym"
        }
    }

    missing_donor_gender_parsing_map = {
        "donor_map": {
            "id": "patient_pseudonym",
            "birthDate": "birth_year"
        },
        "sample_map": {
            "sample_details": {
                "id": "sample_ID",
                "material_type": "sampling_type",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient_pseudonym"
        },
        "condition_map": {
            "icd-10_code": "diagnosis",
            "patient_id": "patient_pseudonym"
        }
    }

    missing_sample_material_type_parsing_map = {
        "donor_map": {
            "id": "patient_pseudonym",
            "gender": "sex",
            "birthDate": "birth_year"
        },
        "sample_map": {
            "sample_details": {
                "id": "sample_ID",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient_pseudonym"
        },
        "condition_map": {
            "icd-10_code": "diagnosis",
            "patient_id": "patient_pseudonym"
        }
    }
    missing_condition_icd_10_code = {
        "donor_map": {
            "id": "patient_pseudonym",
            "gender": "sex",
            "birthDate": "birth_year"
        },
        "sample_map": {
            "sample_details": {
                "id": "sample_ID",
                "material_type": "sampling_type",
                "diagnosis": "diagnosis"
            },
            "donor_id": "patient_pseudonym"
        },
        "condition_map": {
            "patient_id": "patient_pseudonym"
        }
    }

    dir_path = "/mock/dir/"

    @patchfs
    def test_csv_validator_correct_parsing_map_and_file(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(PARSING_MAP_CSV, self.dir_path, ";")
        self.assertTrue(self.validator.validate())

    @patchfs
    def test_csv_validator_no_csv_files_present_in_records_directory_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path+"bad_file_format.txt")
        self.validator = CsvValidator(PARSING_MAP_CSV, self.dir_path, ";")
        self.assertRaises(NoFilesProvidedException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_donor_map_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_donor_parsing_map, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_sample_maps_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_sample_parsing_map, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_condition_map_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_condition_parsing_map, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_donor_gender_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_donor_gender_parsing_map, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_sample_material_type_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_sample_material_type_parsing_map, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_validator_missing_condition_icd_10_code_throws_exception(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.validator = CsvValidator(self.missing_condition_icd_10_code, self.dir_path, ";")
        self.assertRaises(WrongParsingMapException, self.validator.validate)

    @patchfs
    def test_csv_actual_file_missing_defined_sample_id_field_in_header(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header_missing_sample_id_field)
        self.validator = CsvValidator(PARSING_MAP_CSV, self.dir_path, ";")
        self.assertRaises(NonexistentAttributeParsingMapException, self.validator.validate)
