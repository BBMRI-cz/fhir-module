import unittest

from model.sample_donor import SampleDonor
from persistence.sample_donor_xml_files_repository import SampleDonorXMLFilesRepository


class TestXMLRepo(unittest.TestCase):
    sample_donor_repository = SampleDonorXMLFilesRepository()

    def test_get_all(self):
        for donor in self.sample_donor_repository.get_all():
            self.assertIsInstance(donor, SampleDonor)
            self.assertEqual("9999", donor.identifier)


if __name__ == '__main__':
    unittest.main()
