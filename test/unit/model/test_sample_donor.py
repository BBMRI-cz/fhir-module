import datetime
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

    def test_get_gender(self):
        donor = SampleDonor("unique_org_id")
        self.assertEqual(None, donor.gender)

    def test_set_wrong_gender(self):
        donor = SampleDonor("unique_org_id")
        with self.assertRaises(TypeError):
            donor.gender = "tree"

    def test_get_fhir_gender(self):
        donor = SampleDonor("unique_org_id")
        self.assertEqual(None, donor.to_fhir().gender)
        donor.gender = Gender.MALE
        self.assertEqual("male", donor.to_fhir().gender)
        donor.gender = Gender.UNKNOWN
        self.assertEqual("unknown", donor.to_fhir().gender)

    def test_assign_birth_date_full_date_ok(self):
        donor = SampleDonor("unique_org_id")
        donor.date_of_birth = datetime.datetime(year=2022, month=10, day=20)
        self.assertEqual("2022-10-20T00:00:00", donor.date_of_birth.isoformat())

    def test_assign_birth_date_from_string_no_day_ok(self):
        donor = SampleDonor("unique_org_id")
        donor.date_of_birth = datetime.datetime.strptime("2022-10", '%Y-%m')
        self.assertEqual("2022-10-01T00:00:00", donor.date_of_birth.isoformat())
        self.assertEqual("2022-10-01", donor.to_fhir().birthDate.date.isoformat())

    def test_assign_birth_date_from_string_just_year_ok(self):
        donor = SampleDonor("unique_org_id")
        donor.date_of_birth = datetime.datetime.strptime("2022", '%Y')
        self.assertEqual("2022-01-01T00:00:00", donor.date_of_birth.isoformat())


if __name__ == '__main__':
    unittest.main()
