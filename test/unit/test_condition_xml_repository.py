import unittest

from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_xml_repository import ConditionXMLRepository


class TestConditionXMLRepository(unittest.TestCase):
    sample = '<STS>' \
             '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
             '<diagnosis>C509</diagnosis>' \
             '</diagnosisMaterial>' \
             '</STS>'

    wrong_diagnosis = '<STS>' \
                      '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
                      '<diagnosis>C394</diagnosis>' \
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

    @patchfs
    def test_get_all_from_one_file_with_one_condition(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.sample))
        for condition in ConditionXMLRepository().get_all():
            self.assertIsInstance(condition, Condition)
            self.assertEqual("C509", condition.icd_10_code)

    @patchfs
    def test_get_all_from_one_file_with_two_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        conditions = list(ConditionXMLRepository().get_all())
        self.assertEqual(2, len(conditions))

    @patchfs
    def test_get_all_from_two_files_with_three_conditions(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        fake_fs.create_file(self.dir_path + "mock_file2.xml", contents=self.content
                            .format(sample=self.sample))
        conditions = list(ConditionXMLRepository().get_all())
        self.assertEqual(3, len(conditions))

    @patchfs
    def test_get_all_with_wrong_icd_10_string_skips(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content
                            .format(sample=self.samples))
        fake_fs.create_file(self.dir_path + "mock_file2.xml", contents=self.content
                            .format(sample=self.wrong_diagnosis))
        conditions = list(ConditionXMLRepository().get_all())
        self.assertEqual(2, len(conditions))


if __name__ == '__main__':
    unittest.main()
