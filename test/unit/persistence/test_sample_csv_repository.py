import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.sample import Sample
from persistence.sample_csv_repository import SampleCsvRepository
from util.config import PARSING_MAP_CSV


class TestSampleCsvRepository(unittest.TestCase):
    header = "sample_ID;patient_pseudonym;sex;birth_year;date_of_diagnosis;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature;available_number_of_samples \n"

    wrong_diagnosis = "32;1111;f;1945;2007-10-16;wrong;85;2100-01-16;blood-serum;-20;0"

    one_sample = "33;1111;m;1947;2007-10-16;M0580;85;2100-01-16;serum;-20;0"

    samples = "34;1112;f;1958;2100-10-16;M0600;85;2007-10-30;serum;-20;0 \n35;1113;m;1959;2100-10-22;M329;49;2007-10-22;serum;-20;1"

    dir_path = "/mock/dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.sample_repository = SampleCsvRepository(records_path=self.dir_path,
                                                     separator=";",
                                                     sample_parsing_map=PARSING_MAP_CSV['sample_map'])
        yield  # run test

    @patchfs
    def test_get_all_one_sample_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        self.assertEqual(1, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertEqual("33", sample.identifier)

    @patchfs
    def test_get_all_two_samples_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.samples)
        self.assertEqual(2, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, Sample)
            self.assertIn(sample.identifier, ["34", "35"])

    @patchfs
    def test_with_wrong_parsing_map(self, fake_fs):
        wrong_map = {
            "id": ".",
            "donor_id": "wrong_string"
        }
        self.sample_repository = SampleCsvRepository(records_path=self.dir_path, sample_parsing_map=wrong_map, separator=";")
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))
        wrong_map = {}
        self.sample_repository = SampleCsvRepository(records_path=self.dir_path, sample_parsing_map=wrong_map, separator=";")
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_three_samples_from_two_collections_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample + "\n" + self.samples)
        self.assertEqual(3, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_with_wrong_diagnosis_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.wrong_diagnosis)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_three_samples_not_none_diagnosis(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample + "\n" + self.samples)
        self.assertEqual(3, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsNotNone(sample.diagnosis)

    @patchfs
    def test_with_type_to_collection_map_ok(self, fake_fs):
        self.sample_repository = SampleCsvRepository(records_path=self.dir_path,
                                                     separator=";",
                                                     sample_parsing_map=PARSING_MAP_CSV['sample_map'],
                                                     type_to_collection_map={"M0580": "test:collection:id"})
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        self.assertEqual("test:collection:id", next(self.sample_repository.get_all()).sample_collection_id)

    @patchfs
    def test_with_wrong_type_to_collection_map_id_is_none(self, fake_fs):
        self.sample_repository = SampleCsvRepository(records_path=self.dir_path,
                                                     separator=";",
                                                     sample_parsing_map=PARSING_MAP_CSV['sample_map'],
                                                     type_to_collection_map={"not_present": "test:collection:id"})
        fake_fs.create_file(self.dir_path + "mock_file.csv", contents=self.header + self.one_sample)
        self.assertEqual(None, next(self.sample_repository.get_all()).sample_collection_id)
