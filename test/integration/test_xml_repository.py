import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import TestCase
from model.sample_donor import SampleDonor
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository


class TestXMLRepo(TestCase):
    sample_donor_repository = SampleDonorXMLFilesRepository()
    content = '<patient xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
              'xmlns="http://www.bbmri.cz/schemas/biobank/data" xsi:noNamespaceSchemaLocation="exportNIS.xsd" ' \
              'id="9999"></patient>'

    @classmethod
    def setUpClass(cls) -> None:
        cls._fileParser = None
        cls.setUpClassPyfakefs()
        cls.dir_path = "/mock_dir/"

    @pytest.fixture(autouse=True)
    def runBeforeAndAfterEachTest(self):
        self.fs.create_dir(self.dir_path)
        # Execute test
        yield
        self._fileParser = None
        self.fs.reset()

    def test_get_all(self):
        self.fs.create_file(self.dir_path + "mock_file.xml", contents=self.content)
        for donor in self.sample_donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("9999", donor.identifier)


if __name__ == '__main__':
    unittest.main()
