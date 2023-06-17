import unittest

from model.gender import Gender
from model.sample_donor import SampleDonor


class TestSampleDonor(unittest.TestCase):
    def test_sample_donor_init(self):
        patient = SampleDonor("testId")
        self.assertIsInstance(patient, SampleDonor)

    def test_sample_donor_id_must_be_str(self):
        with self.assertRaises(TypeError):
            SampleDonor(37)

    def test_get_sample_donor_id(self):
        self.assertEqual(SampleDonor("test").identifier, "test")

    def test_sample_donor_to_fhir_identifier(self):
        donor = SampleDonor("unique_org_id")
        self.assertEqual(donor.to_fhir().identifier[0].value, donor.identifier)

    def test_set_donor_gender(self):
        donor = SampleDonor("unique_org_id")
        donor.gender = Gender.MALE
        self.assertEqual("male", donor.gender.name.lower())
        donor.gender = Gender.FEMALE
        self.assertEqual("female", donor.gender.name.lower())


if __name__ == '__main__':
    unittest.main()
