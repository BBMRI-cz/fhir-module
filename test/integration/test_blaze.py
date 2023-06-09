import unittest

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from service.blaze_service import BlazeService
from service.patient_service import PatientService

from mock import patch


class TestBlazeStore(unittest.TestCase):
    blaze_service = BlazeService(PatientService(SampleDonorRepository()))

    @patch('persistence.sample_donor_repository.SampleDonorRepository.get_all')
    def test_upload_all_patients(self, get_all_mock):
        get_all_mock.return_value = [SampleDonor("newId"), SampleDonor("fakeId")]
        self.assertEqual(200, self.blaze_service.upload_all_patients())


if __name__ == '__main__':
    unittest.main()
