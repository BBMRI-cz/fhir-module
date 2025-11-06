import os
import unittest

import pytest
from pyfakefs.fake_filesystem_unittest import patchfs

from persistence.sample_collection_json_repository import SampleCollectionJSONRepository
from util.config import get_sample_collections_path


class TestSampleCollectionRepository(unittest.TestCase):
    collections_json = """
    [
  {
    "identifier": "test:collection:1",
    "name": "Test Collection",
    "acronym": "TC"
  }
]
    """

    @pytest.fixture(autouse=True)
    def run_around_tests(self):
        self.sample_collection_repo = SampleCollectionJSONRepository(collections_json_file_path=get_sample_collections_path())
        yield  # run test

    @patchfs
    def test_get_all_ok(self, fake_fs):
        util_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'util')
        fake_fs.create_file(
            os.path.join(util_dir, 'shared_config.json'),
            contents='{"SAMPLE_COLLECTIONS_PATH": "default_sample_collection.json"}'
        )
        fake_fs.create_file(get_sample_collections_path(), contents=self.collections_json)
        self.assertEqual(1, sum(1 for _ in self.sample_collection_repo.get_all()))
        self.assertEqual("test:collection:1", next(self.sample_collection_repo.get_all()).identifier)
