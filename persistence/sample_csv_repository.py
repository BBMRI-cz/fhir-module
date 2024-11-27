import csv
import logging
import os
import re
from typing import Generator

from dateutil.parser import ParserError

from exception.wrong_sample_format import WrongSampleMapException
from model.interface.sample_interface import SampleInterface
from model.sample import Sample
from model.miabis.sample_miabis import SampleMiabis
from persistence.sample_repository import SampleRepository
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code as module_parse_storage_temp_from_code
from miabis_model.storage_temperature import parse_storage_temp_from_code as miabis_parse_storage_temp_from_code

from persistence.csv_util import check_sample_map_format

from dateutil import parser as date_parser

from util.sample_util import diagnosis_with_period, extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class SampleCsvRepository(SampleRepository):
    """Class for handling persistence in Csv files"""

    def __init__(self, records_path: str, sample_parsing_map: dict, separator: str,
                 type_to_collection_map: dict = None, storage_temp_map: dict = None, material_type_map: dict = None,
                 miabis_on_fhir_model: bool = False):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        self._separator = separator
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map
        self._material_type_map = material_type_map
        self._miabis_on_fhir_model = miabis_on_fhir_model
        self._fields_dict = {}

    def get_all(self) -> Generator[SampleInterface, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.lower().endswith(".csv"):
                yield from self.__extract_sample_from_csv_file(dir_entry)

    def __extract_sample_from_csv_file(self, dir_entry: os.DirEntry) -> SampleInterface:
        with open(dir_entry, "r") as file_content:
            reader = csv.reader(file_content, delimiter=self._separator)
            self._fields_dict = {}
            fields = next(reader)
            for i, field in enumerate(fields):
                self._fields_dict[field] = i
            try:
                check_sample_map_format(self._sample_parsing_map)
            except WrongSampleMapException:
                logger.info("Given Sample map has a bad format, cannot parse the file")
                return
            for row in reader:
                try:
                    sample = self.__build_sample(row)
                    yield sample
                except ParserError as err:
                    logger.warning(f"{err}. Skipping .....")
                    continue
                except TypeError as err:
                    logger.info(f"{err} Skipping....")
                    continue
                except ValueError as err:
                    logger.info(f"{err} Skipping....")
                    continue

    def __build_sample(self, data: list[str]) -> SampleInterface:
        identifier = data[self._fields_dict[self._sample_parsing_map.get("sample_details").get("id")]]
        donor_id = data[self._fields_dict[self._sample_parsing_map.get("donor_id")]]
        material_type = None
        material_type_field = self._fields_dict.get(
            self._sample_parsing_map.get("sample_details").get("material_type"))
        if material_type_field is not None and self._material_type_map is not None:
            material_type = self._material_type_map.get(data[material_type_field])
        diagnosis_field = self._fields_dict.get(self._sample_parsing_map.
                                                get("sample_details")
                                                .get("diagnosis"))
        diagnoses = []
        if diagnosis_field is not None:
            diagnoses = extract_all_diagnosis(data[diagnosis_field])
        if not diagnoses:
            raise ValueError(f"No correct diagnosis has been found for sample with id {identifier}.")
        storage_temperature = None
        storage_temp_field = self._fields_dict.get(self._sample_parsing_map
                                                   .get("sample_details")
                                                   .get("storage_temperature"))
        if storage_temp_field is not None and self._storage_temp_map is not None:
            if self._miabis_on_fhir_model:
                storage_temperature = miabis_parse_storage_temp_from_code(self._storage_temp_map,
                                                                          data[storage_temp_field])
            else:
                storage_temperature = module_parse_storage_temp_from_code(self._storage_temp_map,
                                                                          data[storage_temp_field])

        collection_datetime = None
        collection_date_field = self._fields_dict.get(self._sample_parsing_map
                                                      .get("sample_details")
                                                      .get("collection_date"))
        if collection_date_field is not None:
            try:
                collection_datetime = date_parser.parse(data[collection_date_field])
                collection_datetime = collection_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                raise ParserError(
                    f"Error parsing date for sample with identifier {identifier} "
                    f"while parsing collection datetime with value {data[collection_date_field]}. "
                    f"Please make sure the date is in a valid format.")
        diagnosis_datetime = None
        diagnosis_datetime_field = self._fields_dict.get(self._sample_parsing_map
                                                         .get("sample_details")
                                                         .get("diagnosis_date"))
        if diagnosis_datetime_field is not None:
            try:
                diagnosis_datetime = date_parser.parse(data[diagnosis_datetime_field])
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                raise ParserError(
                    f"Error parsing date for sample with identifier {identifier} "
                    f"while parsing diagnosis datetime with value {data[diagnosis_datetime_field]}. "
                    f"Please make sure the date is in a valid format."
                )
        sample_collection_id = None
        if self._type_to_collection_map is not None:
            sample_collection_id = None
            attribute_to_collection = self._sample_parsing_map.get("sample_details").get("collection")
            if attribute_to_collection in self._fields_dict:
                sample_collection_id = self._type_to_collection_map.get(
                    data[self._fields_dict[attribute_to_collection]])
        if self._miabis_on_fhir_model:
            diagnoses_with_observed_datetime = []
            for diagnosis in diagnoses:
                diagnoses_with_observed_datetime.append((diagnosis, diagnosis_datetime))
            sample = SampleMiabis(identifier=identifier, donor_id=donor_id,
                                  diagnoses_with_observed_datetime=diagnoses_with_observed_datetime,
                                  material_type=material_type,
                                  sample_collection_id=sample_collection_id,
                                  collected_datetime=collection_datetime,
                                  storage_temperature=storage_temperature)
        else:
            sample = Sample(identifier=identifier, donor_id=donor_id, material_type=material_type, diagnoses=diagnoses,
                            sample_collection_id=sample_collection_id, collected_datetime=collection_datetime,
                            storage_temperature=storage_temperature)
        return sample
