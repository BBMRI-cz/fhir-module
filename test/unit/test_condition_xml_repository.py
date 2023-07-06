import unittest

from pyfakefs.fake_filesystem_unittest import patchfs

from model.condition import Condition
from persistence.condition_xml_repository import ConditionXMLRepository


class TestConditionXMLRepository(unittest.TestCase):
    samples = '<STS>' \
              '<diagnosisMaterial number="136043" sampleId="&amp;:2032:136043" year="2032">' \
              '<diagnosis>C509</diagnosis>' \
              '</diagnosisMaterial>' \
                '</STS>'

    content = '<patient xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
              'xmlns="http://www.bbmri.cz/schemas/biobank/data" xsi:noNamespaceSchemaLocation="exportNIS.xsd" ' \
              'id="9999">{sample}</patient>'.format(sample=samples)

    dir_path = "/mock_dir/"

    @patchfs
    def test_get_all(self, fake_fs):
        fake_fs.create_file(self.dir_path + "mock_file.xml", contents=self.content)
        for condition in ConditionXMLRepository().get_all():
            self.assertIsInstance(condition, Condition)
            self.assertEqual("C509", condition.icd_10_code)


if __name__ == '__main__':
    unittest.main()
