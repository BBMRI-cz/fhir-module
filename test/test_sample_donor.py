import unittest

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


if __name__ == '__main__':
    unittest.main()
