import os
import unittest
from datetime import datetime

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_xml_repository import ConditionXMLRepository
from util.config import get_parsing_map


class TestConditionXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<diagnosis>C509</diagnosis>' \
             '<diagnosis_date>2007-10-16</diagnosis_date>' \
             '</diagnosisMaterial>' \
             '</STS>'

    wrong_diagnosis = '<STS>' \
                      '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                      '<diagnosis>wrong</diagnosis>' \
                      '</diagnosisMaterial>' \
                      '</STS>'

    samples = '<STS>' \
              '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
              '<diagnosis>C508</diagnosis>' \
              '</diagnosisMaterial>' \
              '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136044" year="2032">' \
              '<diagnosis>C501</diagnosis>' \
              '</diagnosisMaterial>' \
              '</STS>'

    content = '<patient id="9999">{sample}</patient>'

    wrong_content = "THis is not suitable content for an xml."

    dir_path = "/mock_dir/"

    parsing_map = {
        "condition_map": {
            "icd-10_code": "**.diagnosis",
            "diagnosis_date": "**.diagnosis_date",
            "patient_id": "patient.@id"
        }
    }

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.condition_repository = ConditionXMLRepository(records_path=self.dir_path,
                                                           condition_parsing_map=self.parsing_map['condition_map'])
        yield  # run test

    @patchfs
    def test_get_all_from_one_file_with_one_condition(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        for condition in self.condition_repository.get_all():
            self.assertIsInstance(condition, Condition)
            self.assertEqual("C50.9", condition.icd_10_code)
            self.assertEqual(datetime(year=2007, month=10, day=16), condition.diagnosis_datetime)

    @patchfs
    def test_get_all_from_one_file_with_two_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_get_all_from_two_files_with_three_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        fake_fs.create_file(self.dir_path + "mock_file2.xml", contents=self.content
                            .format(sample=self.sample)
                            )
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(3, len(conditions))

    @patchfs
    def test_get_all_from_incorrect_xml_file_format_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.wrong_content)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(0, len(conditions))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        fake_fs.create_file(self.dir_path + "mock_file2.xml", contents=self.content
                            .format(sample=self.wrong_diagnosis))
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_validate_conditions_from_xml_file_valid_data(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        errors = self.condition_repository._ConditionXMLRepository__validate_conditions_from_xml_file(dir_entry)
        self.assertEqual(0, len(errors))

    @patchfs
    def test_validate_conditions_from_xml_file_missing_diagnosis_path(self, fake_fs):
        incomplete_parsing_map = {
            "patient_id": "patient.@id",
            "diagnosis_date": "**.diagnosis_date"
        }
        repo = ConditionXMLRepository(records_path=self.dir_path,
                                     condition_parsing_map=incomplete_parsing_map)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        errors = repo._ConditionXMLRepository__validate_conditions_from_xml_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No ICD-10 code field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_xml_file_missing_patient_id_path(self, fake_fs):
        incomplete_parsing_map = {
            "icd-10_code": "**.diagnosis",
            "diagnosis_date": "**.diagnosis_date"
        }
        repo = ConditionXMLRepository(records_path=self.dir_path,
                                     condition_parsing_map=incomplete_parsing_map)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        errors = repo._ConditionXMLRepository__validate_conditions_from_xml_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("No patient ID field found" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_xml_file_invalid_date_format(self, fake_fs):
        invalid_date_sample = '<STS>' \
                             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                             '<diagnosis>C509</diagnosis>' \
                             '<diagnosis_date>invalid-date</diagnosis_date>' \
                             '</diagnosisMaterial>' \
                             '</STS>'
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=invalid_date_sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        errors = self.condition_repository._ConditionXMLRepository__validate_conditions_from_xml_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Diagnosis date parsing error" in error for error in errors))

    @patchfs
    def test_validate_conditions_from_xml_file_wrong_xml_format(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.wrong_content)
        dir_entry = list(os.scandir(self.dir_path))[0]
        errors = self.condition_repository._ConditionXMLRepository__validate_conditions_from_xml_file(dir_entry)
        self.assertGreater(len(errors), 0)
        self.assertTrue(any("Wrong XLM format" in error for error in errors))

    def test_validate_xml_diagnosis_path_missing(self):
        errors = []
        self.condition_repository._sample_parsing_map = {"patient_id": "patient.@id"}
        result = self.condition_repository._ConditionXMLRepository__validate_xml_diagnosis_path(errors)
        self.assertIsNone(result)
        self.assertEqual(1, len(errors))
        self.assertTrue(any("No ICD-10 code field found" in error for error in errors))

    def test_validate_xml_diagnosis_path_present(self):
        errors = []
        result = self.condition_repository._ConditionXMLRepository__validate_xml_diagnosis_path(errors)
        self.assertEqual("**.diagnosis", result)
        self.assertEqual(0, len(errors))

    def test_validate_xml_patient_id_path_missing(self):
        errors = []
        self.condition_repository._sample_parsing_map = {"icd-10_code": "**.diagnosis"}
        result = self.condition_repository._ConditionXMLRepository__validate_xml_patient_id_path(errors)
        self.assertIsNone(result)
        self.assertEqual(1, len(errors))
        self.assertTrue(any("No patient ID field found" in error for error in errors))

    def test_validate_xml_patient_id_path_present(self):
        errors = []
        result = self.condition_repository._ConditionXMLRepository__validate_xml_patient_id_path(errors)
        self.assertEqual("patient.@id", result)
        self.assertEqual(0, len(errors))

    @patchfs
    def test_parse_xml_diagnosis_datetime_valid(self, fake_fs):
        from persistence.xml_util import parse_xml_file
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        file_content = parse_xml_file(dir_entry)
        validation_errors = []
        result = self.condition_repository._ConditionXMLRepository__parse_xml_diagnosis_datetime(
            file_content, validation_errors
        )
        self.assertIsNotNone(result)
        self.assertEqual(datetime(2007, 10, 16), result)
        self.assertEqual(0, len(validation_errors))

    @patchfs
    def test_parse_xml_diagnosis_datetime_invalid(self, fake_fs):
        from persistence.xml_util import parse_xml_file
        invalid_date_sample = '<STS>' \
                             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                             '<diagnosis>C509</diagnosis>' \
                             '<diagnosis_date>not-a-date</diagnosis_date>' \
                             '</diagnosisMaterial>' \
                             '</STS>'
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=invalid_date_sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        file_content = parse_xml_file(dir_entry)
        validation_errors = []
        self.condition_repository._ConditionXMLRepository__parse_xml_diagnosis_datetime(
            file_content, validation_errors
        )
        self.assertEqual(1, len(validation_errors))

    @patchfs
    def test_parse_xml_diagnosis_datetime_missing_field(self, fake_fs):
        from persistence.xml_util import parse_xml_file
        no_date_sample = '<STS>' \
                        '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                        '<diagnosis>C509</diagnosis>' \
                        '</diagnosisMaterial>' \
                        '</STS>'
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=no_date_sample))
        dir_entry = list(os.scandir(self.dir_path))[0]
        file_content = parse_xml_file(dir_entry)
        validation_errors = []
        result = self.condition_repository._ConditionXMLRepository__parse_xml_diagnosis_datetime(
            file_content, validation_errors
        )
        self.assertIsNone(result)
        self.assertEqual(0, len(validation_errors))

    def test_validate_xml_diagnosis_valid(self):
        validation_errors = []
        self.condition_repository._ConditionXMLRepository__validate_xml_diagnosis(
            "C50.9", "patient_123", validation_errors
        )
        self.assertEqual(0, len(validation_errors))

    def test_validate_xml_diagnosis_empty(self):
        validation_errors = []
        self.condition_repository._ConditionXMLRepository__validate_xml_diagnosis(
            "", "patient_123", validation_errors
        )
        self.assertEqual(1, len(validation_errors))
        self.assertTrue(any("No correct diagnosis has been found" in str(exc) for exc in validation_errors))

    def test_validate_xml_diagnosis_none(self):
        validation_errors = []
        self.condition_repository._ConditionXMLRepository__validate_xml_diagnosis(
            None, "patient_123", validation_errors
        )
        self.assertEqual(1, len(validation_errors))


if __name__ == '__main__':
    unittest.main()
