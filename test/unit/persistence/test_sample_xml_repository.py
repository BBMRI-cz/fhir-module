import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.sample import Sample
from persistence.sample_xml_repository import SampleXMLRepository
from util.config import PARSING_MAP


class TestSampleXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<diagnosis>C509</diagnosis>' \
             '</diagnosisMaterial>' \
             '</STS>'

    wrong_diagnosis = '<STS>' \
                      '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                      '<diagnosis>wrong</diagnosis>' \
                      '</diagnosisMaterial>' \
                      '</STS>'

    samples = '<STS>' \
              '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
              '<materialType>S</materialType>' \
              '<diagnosis>C508</diagnosis>' \
              '</diagnosisMaterial>' \
              '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136043" year="2032">' \
              '<materialType>T</materialType>' \
              '<diagnosis>C501</diagnosis>' \
              '</diagnosisMaterial>' \
              '</STS>'
    both_collections = '<STS>' \
                       '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                       '<materialType>S</materialType>' \
                       '<diagnosis>C508</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136043" year="2032">' \
                       '<materialType>T</materialType>' \
                       '<diagnosis>C501</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '</STS>' \
                       '<LTS>' \
                       '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136045" year="2032">' \
                       '<materialType>S</materialType>' \
                       '<diagnosis>C508</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '<diagnosisMaterial number="136044" sampleId="&amp;:2032:136045" year="2032">' \
                       '<materialType>T</materialType>' \
                       '<diagnosis>C501</diagnosis>' \
                       '</diagnosisMaterial>' \
                       '</LTS>'

    content = '<patient id="9999">{sample}</patient>'

    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path,
                                                     sample_parsing_map=PARSING_MAP['sample_map'])
        yield  # run test

    @patchfs
    def test_get_all_one_sample_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        self.assertEqual(1, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertEqual("&:2032:136043", sample.identifier)

    @patchfs
    def test_get_all_two_samples_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        self.assertEqual(2, sum(1 for _ in self.sample_repository.get_all()))
        for sample in self.sample_repository.get_all():
            self.assertIsInstance(sample, Sample)
            self.assertEqual("&:2032:136043", sample.identifier)

    @patchfs
    def test_with_wrong_parsing_map(self, fake_fs):
        wrong_map = {
            "id": ".",
            "donor_id": "wrong_string"
        }
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path, sample_parsing_map=wrong_map)
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))
        wrong_map = {}
        self.sample_repository = SampleXMLRepository(records_path=self.dir_path, sample_parsing_map=wrong_map)
        self.assertEqual(0, sum(1 for _ in self.sample_repository.get_all()))

    @patchfs
    def test_get_all_four_samples_from_two_collections_ok(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.both_collections))
        self.assertEqual(4, sum(1 for _ in self.sample_repository.get_all()))
