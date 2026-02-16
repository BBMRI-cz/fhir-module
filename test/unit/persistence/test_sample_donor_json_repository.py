import json
import os
import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from miabis_model import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_json_repository import SampleDonorJsonRepository
from util.config import PARSING_MAP_CSV


class TestDonorJsonRepo(unittest.TestCase):
    one_sample_correct = [{
        "PatientId": "1",
        "SpecimenId": "10",
        "DateOfDiagnosis": "2020-11-20T00:00:00",
        "Diagnosis": "N880",
        "DiagnosisAgeDonor": 47,
        "DonorAge": "1990-09-09",
        "SamplingDate": "2020-11-19T00:00:00",
        "SampleType": "tumor-tissue-ffpe",
        "Sex": "M",
        "StorageTemperature": "temperatureRoom"
    }]

    parsing_map = {
        "donor_map": {
            "id": "PatientId",
            "gender": "Sex",
            "birthDate": "DonorAge"
        }}
    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.donor_repository = SampleDonorJsonRepository(records_path=self.dir_path,
                                                          donor_parsing_map=self.parsing_map['donor_map'])

    @patchfs
    def test_get_all_ok(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1", donor.identifier)
            self.assertEqual(Gender.MALE, donor.gender)

    @patchfs
    def test_get_all_with_one_wrongly_formatted_file(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1", donor.identifier)

    @patchfs
    def test_get_all_does_not_return_duplicate_patients(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        fake_fs.create_file(self.dir_path + "mock_file_duplicate.json", contents=content)
        counter = 0
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("1", donor.identifier)
            counter += 1
        self.assertEqual(1, counter)

    @patchfs
    def test_get_all_with_empty_repository_throws_no_errors(self, fake_fs):
        fake_fs.create_dir(self.dir_path)
        counter = 0
        for _ in self.donor_repository.get_all():
            counter += 1
        self.assertEqual(0, counter)

    @patchfs
    def test_file_with_no_permissions_trows_no_error(self, fake_fs):
        content = json.dumps(self.one_sample_correct)
        fake_fs.create_file(self.dir_path + "mock_file.json", contents=content)
        # set permission to no access
        os.chmod(self.dir_path + "mock_file.json", 0o000)
        self.assertEqual(0, sum(1 for _ in self.donor_repository.get_all()))
