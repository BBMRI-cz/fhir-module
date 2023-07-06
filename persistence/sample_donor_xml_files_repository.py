"""Module for handling sample donor persistence in XML files"""
import os
from typing import List
from pyexpat import ExpatError

import xmltodict

from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    """Class for handling sample donors stored in XML files"""
    def __init__(self):
        self._dir_path = os.getenv("DIR_PATH", "/mock_dir/")
        self._ids: set = set()

    def get_all(self) -> List[SampleDonor]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.parse_xml_file(dir_entry)

    def parse_xml_file(self, dir_entry: os.DirEntry) -> SampleDonor:
        """Parse a Sample donor from an XML file"""
        with open(dir_entry, encoding="UTF-8") as xml_file:
            try:
                file_content = xmltodict.parse(xml_file.read())
                donor = SampleDonor(file_content.get("patient", {}).get("@id", {}))
                if donor.identifier not in self._ids:
                    self._ids.add(donor.identifier)
                    yield donor
            except ExpatError:
                print("Skipping file")
