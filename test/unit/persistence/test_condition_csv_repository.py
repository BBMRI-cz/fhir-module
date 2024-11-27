import datetime
import unittest
import pytest
import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_csv_repository import ConditionCsvRepository
from persistence.condition_xml_repository import ConditionXMLRepository
from util.config import PARSING_MAP_CSV


class TestConditionCsvRepository(unittest.TestCase):
    header = "sample_ID;patient_pseudonym;sex;birth_year;diagnosis_date;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples\n"

    wrong_diagnosis = "32;1111;f;1945;2007-10-16;wrong;85;2100-01-16;blood-serum;-20;0"

    one_sample = "33;1111;m;1947;2007-10-16;M058;85;2100-01-16;serum;-20;0"

    sample_multiple_diagnosis = "33;1111;m;1947;2007-10-16;M058,C51,C50;85;2100-01-16;serum;-20;0"

    samples = "34;1112;f;1958;2100-10-16;M060;85;2007-10-30;serum;-20;0\n35;1113;m;1959;2100-10-22;M329;49;2007-10-22;serum;-20;1"

    dir_path = "/mock/dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.condition_repository = ConditionCsvRepository(records_path=self.dir_path,
                                                           condition_parsing_map=PARSING_MAP_CSV['condition_map'],
                                                           separator=";")
        yield  # run test

    @patchfs
    def test_get_all_from_one_file_with_one_condition(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        for condition in self.condition_repository.get_all():
            self.assertIsInstance(condition, Condition)
            self.assertEqual("M05.8", condition.icd_10_code)
            self.assertEqual(datetime.datetime(year=2007, month=10, day=16), condition.diagnosis_datetime)

    @patchfs
    def test_get_all_from_two_files_with_three_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        fake_fs.create_file(self.dir_path + "mock_file2.csv", contents=self.header + self.one_sample)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(3, len(conditions))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        fake_fs.create_file(self.dir_path + "mock_file2.csv", contents=self.header + self.wrong_diagnosis)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_get_all_with_multiple_diagnosis_from_one_sample(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.sample_multiple_diagnosis)
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(3, len(conditions))
        self.assertEqual("M05.8", conditions[0].icd_10_code)


if __name__ == '__main__':
    unittest.main()
