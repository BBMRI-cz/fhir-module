import os
from typing import List

import xmltodict as xmltodict

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    _dir_path = os.getenv("DIR_PATH", "/mock_dir/")

    def get_all(self) -> List[SampleDonor]:
        for dirEntry in os.scandir(self._dir_path):
            yield self.parse_xml_file(dirEntry)

    def parse_xml_file(self, dir_entry: os.DirEntry):
        with open(dir_entry) as xml_file:
            file_content = xmltodict.parse(xml_file.read())
            return SampleDonor(file_content.get("patient", {}).get("@id", {}))
