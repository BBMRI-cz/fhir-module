import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.gender import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_csv_repository import SampleDonorCsvRepository
from util.config import PARSING_MAP_CSV


class TestDonorCsvRepo(unittest.TestCase):
    header = "sample_ID;patient_pseudonym;sex;birth_year;date_of_diagnosis;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples \n"

    content = "34;1113;f;1939;2100-10-22;M329;49;2007-10-22;serum;-20;1"

    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.donor_repository = SampleDonorCsvRepository(records_path=self.dir_path,
                                                         donor_parsing_map=PARSING_MAP_CSV['donor_map'],
                                                         separator=";")

    @patchfs
    def test_get_all_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.content)
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1113", donor.identifier)
            self.assertEqual(Gender.FEMALE, donor.gender)

    @patchfs
    def test_get_all_with_one_wrongly_formatted_file(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.content)
        fake_fs.create_file(self.dir_path + "mock_wrong_file.csv", contents="badly_formated_csv")
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1113", donor.identifier)

    @patchfs
    def test_get_all_does_not_return_duplicate_patients(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.content)
        fake_fs.create_file(self.dir_path + "mock_file_duplicate.csv", contents=self.header + self.content)
        counter = 0
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1113", donor.identifier)
            counter += 1
        self.assertEqual(1, counter)

    @patchfs
    def test_get_all_with_empty_repository_throws_no_errors(self, fake_fs):
        fake_fs.create_dir(self.dir_path)
        counter = 0
        for _ in self.donor_repository.get_all():
            counter += 1
        self.assertEqual(0, counter)
