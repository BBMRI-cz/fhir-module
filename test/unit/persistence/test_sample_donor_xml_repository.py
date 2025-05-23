import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.gender import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository
from util.config import PARSING_MAP


class TestDonorXMLRepo(unittest.TestCase):
    content = '<patient xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
              'xmlns="http://www.bbmri.cz/schemas/biobank/data" xsi:noNamespaceSchemaLocation="exportNIS.xsd" ' \
              'id="9999" sex="female"></patient>'
    wrong_format_content ="This is a wrong format for an xml file."
    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.donor_repository = SampleDonorXMLFilesRepository(records_path=self.dir_path,
                                                              donor_parsing_map=PARSING_MAP['donor_map'])
        yield  # run test
    @patchfs
    def test_get_all_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content)
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("9999", donor.identifier)
            self.assertEqual(Gender.FEMALE, donor.gender)

    @patchfs
    def test_get_all_with_one_wrongly_formatted_file(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content)
        fake_fs.create_file(self.dir_path + "mock_wrong_file.xml", contents="<>test</a>")
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("9999", donor.identifier)

    @patchfs
    def test_get_all_does_not_return_duplicate_patients(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content)
        fake_fs.create_file(self.dir_path + "mock_file_duplicate.xml", contents=self.content)
        counter = 0
        for donor in self.donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("9999", donor.identifier)
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
    def test_get_all_with_wrong_file_format_throws_no_errors(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.wrong_format_content)
        counter = 0
        for _ in self.donor_repository.get_all():
            counter += 1
            self.assertEqual(0,counter)
