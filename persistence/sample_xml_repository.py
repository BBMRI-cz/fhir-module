import logging
import os
from typing import Generator

from dateutil.parser import ParserError
from glom import glom, PathAccessError

from model.interface.sample_interface import SampleInterface
from model.sample import Sample
from model.miabis.sample_miabis import SampleMiabis
from persistence.sample_repository import SampleRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger

from util.enums_util import parse_storage_temp_from_code as module_parse_storage_temp_from_code
from miabis_model.storage_temperature import parse_storage_temp_from_code as miabis_parse_storage_temp_from_code
from dateutil import parser as date_parser

from util.sample_util import diagnosis_with_period, extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class SampleXMLRepository(SampleRepository):
    """Class for handling sample persistence in XML files."""

    def __init__(self, records_path: str, sample_parsing_map: dict, type_to_collection_map: dict = None,
                 storage_temp_map: dict = None, material_type_map: dict = None, miabis_on_fhir_model: bool = False):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map
        self._material_type_map = material_type_map
        self._miabis_on_fhir_model = miabis_on_fhir_model

    def get_all(self) -> Generator[SampleInterface, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_sample_from_xml_file(dir_entry)

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> SampleInterface:
        """Extracts Sample from an XML file"""
        file_content = parse_xml_file(dir_entry)
        for parsing_path in str(self._sample_parsing_map.get("sample")).split(" || "):
            try:
                for xml_sample in flatten_list(glom(file_content, parsing_path)):
                    logger.debug(f"Found a specimen: {xml_sample}")
                    yield self.__build_sample(file_content, xml_sample)
            except ParserError as err:
                logger.warning(f"{err}. Skipping.....")
                continue
            except (TypeError, ValueError, KeyError) as err:
                logger.warning(f"{err}. Skipping")
                continue
            except (WrongXMLFormatError, PathAccessError, TypeError):
                logger.warning("Error reading XML file.")
                return

    def __build_sample(self, file_content, xml_sample) -> SampleInterface:
        # TODO add diagnosis observer datetime to parsing
        # TODO material type will be mapped to a standardized value here, not in the Sample object
        identifier = glom(xml_sample,
                          self._sample_parsing_map.get("sample_details").get("id"))
        donor_id = glom(file_content,
                        self._sample_parsing_map.get("donor_id"))

        material_type = None
        material_type_non_standardized = glom(xml_sample,
                                              self._sample_parsing_map.get("sample_details").get(
                                                  "material_type"),
                                              default=None)
        if self._material_type_map is not None:
            material_type = self._material_type_map.get(material_type_non_standardized)

        diagnoses = []
        diagnoses_unparsed = glom(xml_sample,
                                  self._sample_parsing_map.get("sample_details").get(
                                      "diagnosis"), default=None)
        if diagnoses_unparsed is not None:
            if isinstance(diagnoses_unparsed, list):
                for diagnosis in diagnoses_unparsed:
                    diagnoses.extend(extract_all_diagnosis(diagnosis))
            else:
                diagnoses = extract_all_diagnosis(diagnoses_unparsed)
        if not diagnoses:
            raise ValueError(f"No correct diagnosis found for sample with identifier {identifier}.")
        collected_datetime = None
        collection_datetime_string = glom(xml_sample,
                                          self._sample_parsing_map.get("sample_details").get("collection_date"),
                                          default=None)
        if collection_datetime_string is not None:
            try:
                collected_datetime = date_parser.parse(collection_datetime_string)
                collected_datetime = collected_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                raise ParserError(
                    f"Error parsing date {collection_datetime_string} for sample with identifier {identifier}."
                    f" Please make sure the date is in a valid format.")

        diagnosis_datetime = None
        diagnosis_datetime_string = glom(xml_sample,
                                         self._sample_parsing_map.get("sample_details").get("diagnosis_date"),
                                         default=None)
        if diagnosis_datetime_string is not None:
            try:
                diagnosis_datetime = date_parser.parse(diagnosis_datetime_string)
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                raise ParserError(
                    f"Error parsing date {diagnosis_datetime_string} for sample with identifier {identifier}."
                    f" Please make sure the date is in a valid format."
                )
        sample_collection_id = None
        if self._type_to_collection_map is not None:
            attribute_to_collection = self._sample_parsing_map.get("sample_details").get("collection")
            collection_attribute_value = glom(xml_sample, attribute_to_collection,
                                              default=None)
            if collection_attribute_value is not None:
                sample_collection_id = self._type_to_collection_map.get(collection_attribute_value)
        storage_temperature = None
        if self._storage_temp_map is not None:
            storage_temp_code = glom(xml_sample,
                                     self._sample_parsing_map.get("sample_details").get("storage_temperature"),
                                     default=None)
            if storage_temp_code is not None:
                if self._miabis_on_fhir_model:
                    storage_temperature = miabis_parse_storage_temp_from_code(self._storage_temp_map, storage_temp_code)
                else:
                    storage_temperature = module_parse_storage_temp_from_code(self._storage_temp_map, storage_temp_code)

        if self._miabis_on_fhir_model:
            diagnoses_with_observed_datetime = []
            for diagnosis in diagnoses:
                diagnoses_with_observed_datetime.append((diagnosis_with_period(diagnosis), diagnosis_datetime))
            sample = SampleMiabis(identifier=identifier, donor_id=donor_id, material_type=material_type,
                                  sample_collection_id=sample_collection_id,
                                  collected_datetime=collected_datetime, storage_temperature=storage_temperature,
                                  diagnoses_with_observed_datetime=diagnoses_with_observed_datetime)
        else:
            sample = Sample(identifier=identifier, donor_id=donor_id, material_type=material_type, diagnoses=diagnoses,
                            sample_collection_id=sample_collection_id, collected_datetime=collected_datetime,
                            storage_temperature=storage_temperature)
        return sample

def flatten_list(nested_list):
    return [item for sublist in nested_list for item in
            (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]
