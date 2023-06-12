import unittest

from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository


class TestXMLRepo(unittest.TestCase):
    sample_donor_repository = SampleDonorXMLFilesRepository()

    def test_get_all(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == '__main__':
    unittest.main()
