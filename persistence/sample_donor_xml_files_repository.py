"""Module for handling sample donor persistence in XML files"""
import os
from typing import List

from model.gender import Gender
from model.sample_donor import SampleDonor
from persistence.sample_donor_repository import SampleDonorRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError


class SampleDonorXMLFilesRepository(SampleDonorRepository):
    """Class for handling sample donors stored in XML files"""

    def __init__(self, records_path: str):
        self._dir_path = records_path
        self._ids: set = set()

    def get_all(self) -> List[SampleDonor]:
        for dir_entry in os.scandir(self._dir_path):
            yield from self.__extract_donor_from_xml_file(dir_entry)

    def __extract_donor_from_xml_file(self, dir_entry: os.DirEntry) -> SampleDonor:
        """Extracts SampleDonor from an XML file"""
        try:
            contents = parse_xml_file(dir_entry)
            donor = SampleDonor(contents.get("patient", {}).get("@id", {}))
            donor.gender = Gender[contents.get("patient", {}).get("@sex", {}).upper()]
        except WrongXMLFormatError:
            return
        if donor.identifier not in self._ids:
            self._ids.add(donor.identifier)
            yield donor
