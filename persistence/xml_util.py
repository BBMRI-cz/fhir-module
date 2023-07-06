"""Module containing utility functions for handling XML files"""
import os
from collections import OrderedDict
from pyexpat import ExpatError
from typing import Any

import xmltodict


def parse_xml_file(dir_entry: os.DirEntry) -> OrderedDict[str, Any]:
    """Parse a Sample donor from an XML file"""
    with open(dir_entry, encoding="UTF-8") as xml_file:
        try:
            file_content = xmltodict.parse(xml_file.read())
            return file_content
        except ExpatError:
            raise WrongXMLFormatError


class WrongXMLFormatError(Exception):
    """Raised when the XML file being read has wrong format"""
    pass
