import os
from pyexpat import ExpatError
from typing import List

import xmltodict as xmltodict

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository


class SampleDonorXMLFilesRepository(SampleDonorRepository):

    def __init__(self):
        self._dir_path = os.getenv("DIR_PATH", "/mock_dir/")
        self._ids: set = set()

    def get_all(self) -> List[SampleDonor]:
        for dirEntry in os.scandir(self._dir_path):
            yield from self.parse_xml_file(dirEntry)

    def parse_xml_file(self, dir_entry: os.DirEntry):
        with open(dir_entry) as xml_file:
            try:
                file_content = xmltodict.parse(xml_file.read())
                donor = SampleDonor(file_content.get("patient", {}).get("@id", {}))
                if donor.identifier not in self._ids:
                    self._ids.add(donor.identifier)
                    yield donor
            except ExpatError:
                print("Skipping file")
