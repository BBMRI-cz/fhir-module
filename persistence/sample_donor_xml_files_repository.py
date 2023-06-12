import os
from pyexpat import ExpatError
from typing import List

import xmltodict as xmltodict

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    _dir_path = "/Users/radovan.tomasik/Repositories/fhir-module/test/xml_data"

    def get_all(self) -> List[SampleDonor]:
        for dirEntry in os.scandir(self._dir_path):
            yield from self.parse_xml_file(dirEntry)

    def parse_xml_file(self, dir_entry: os.DirEntry):
        with open(dir_entry) as xml_file:
            file_content = xmltodict.parse(xml_file.read())
            yield SampleDonor(file_content.get("patient", {}).get("@id", {}))
