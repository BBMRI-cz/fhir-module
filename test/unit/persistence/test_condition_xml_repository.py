import unittest
from datetime import datetime

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_xml_repository import ConditionXMLRepository
from util.config import PARSING_MAP


class TestConditionXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<diagnosis>C509</diagnosis>'\
             '<diagnosis_date>2007-10-16</diagnosis_date>'\
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

    dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.condition_repository = ConditionXMLRepository(records_path=self.dir_path,
                                                           condition_parsing_map=PARSING_MAP['condition_map'])
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
                            .format(sample=self.sample))
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(3, len(conditions))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        fake_fs.create_file(self.dir_path + "mock_file2.xml", contents=self.content
                            .format(sample=self.wrong_diagnosis))
        conditions = list(self.condition_repository.get_all())
        self.assertEqual(2, len(conditions))


if __name__ == '__main__':
    unittest.main()
