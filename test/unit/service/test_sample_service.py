import unittest
from typing import List

from model.sample import Sample
from persistence.sample_repository import SampleRepository
from service.sample_service import SampleService


class SampleRepoStub(SampleRepository):
    samples = [Sample("fakeId", "fakePatientId"),
               Sample("fakeId2", "fakePatientId2")]

    def get_all(self) -> List[Sample]:
        yield from self.samples


class TestSampleService(unittest.TestCase):

    def test_get_all(self):
        sample_service = SampleService(SampleRepoStub())
        self.assertEqual(2, sum(1 for _ in sample_service.get_all()))
