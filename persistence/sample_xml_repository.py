import logging
import os
from typing import Callable, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError
from glom import glom, PathAccessError
from miabis_model.storage_temperature import parse_storage_temp_from_code as miabis_parse_storage_temp_from_code

from exception.no_diagnosis_found_for_sample import NoDiagnosisFoundForSampleException
from exception.value_mapping_record_does_not_exist import ValueMappingRecordDoesNotExistError
from model.interface.sample_interface import SampleInterface
from model.miabis.sample_miabis import SampleMiabis
from model.sample import Sample
from persistence.sample_repository import SampleRepository
from persistence.xml_util import parse_xml_file, WrongXMLFormatError
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code as module_parse_storage_temp_from_code
from util.sample_util import diagnosis_with_period, extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class SampleXMLRepository(SampleRepository):
    """Class for handling sample persistence in XML files."""

    def __init__(self, records_path: str, sample_parsing_map: dict, type_to_collection_map: dict = None,
                 storage_temp_map: dict = None, material_type_map: dict = None, miabis_on_fhir_model: bool = False):
        super().__init__(records_path)
        self._sample_parsing_map = sample_parsing_map
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map
        self._material_type_map = material_type_map
        self._miabis_on_fhir_model = miabis_on_fhir_model

    def get_all(self) -> Generator[SampleInterface, None, None]:
        dir_entries = list(os.scandir(self._dir_path))
        for dir_entry in dir_entries:
            if dir_entry.name.lower().endswith(".xml"):
                yield from self.__extract_sample_from_xml_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".xml", self.__validate_sample_from_xml_file

    def __extract_sample_from_xml_file(self, dir_entry: os.DirEntry) -> SampleInterface:
        """Extracts Sample from an XML file"""
        try:
            file_content = parse_xml_file(dir_entry)
        except WrongXMLFormatError:
            logger.info(f"Wrong XLM format of file: {dir_entry.name} [Skipping...]")
            return
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
            except (WrongXMLFormatError, PathAccessError):
                logger.warning("Error reading XML file.")
                return

    def __validate_sample_from_xml_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            file_content = parse_xml_file(dir_entry)
        except WrongXMLFormatError:
            return ["Wrong XML format"]

        sample_index = 0  # Start from 0 for XML elements index
        for parsing_path in str(self._sample_parsing_map.get("sample")).split(" || "):
            try:
                for xml_sample in flatten_list(glom(file_content, parsing_path)):
                    _ = self.__build_sample(file_content, xml_sample, is_validation=True)
                    sample_index += 1
            
            except ExceptionGroup as eg:
                for exc in eg.exceptions:
                    errors.append(f"Sample (index {sample_index}): {exc}")
            except (ValueError, TypeError, KeyError) as err:
                errors.append(f"Sample (index {sample_index}): {err}")
            except (WrongXMLFormatError, PathAccessError, TypeError):
                errors.append(f"Sample (index {sample_index}): Error reading XML file.")
                return errors
        return errors

    def __extract_xml_material_type(self, xml_sample, validation_errors: list | None):
        """Extract and validate material type from XML data."""
        material_type = None
        material_type_path = self._sample_parsing_map.get("sample_details").get("material_type")
        
        if material_type_path is not None:
            material_type_non_standardized = glom(xml_sample, material_type_path, default=None)
            
            if self._material_type_map is not None and material_type_non_standardized is not None:
                material_type = self._material_type_map.get(material_type_non_standardized)
                if material_type is None and validation_errors is not None:
                    validation_errors.append(
                        ValueMappingRecordDoesNotExistError(
                            f"Value mapping for material type {material_type_non_standardized} does not exist."
                        )
                    )
        
        return material_type

    def __extract_xml_diagnoses(self, xml_sample, identifier: str, validation_errors: list | None) -> list[str]:
        """Extract and validate diagnoses from XML data."""
        diagnoses = []
        diagnoses_unparsed = glom(
            xml_sample,
            self._sample_parsing_map.get("sample_details").get("diagnosis"),
            default=None
        )
        
        if diagnoses_unparsed is not None:
            if isinstance(diagnoses_unparsed, list):
                for diagnosis in diagnoses_unparsed:
                    diagnoses.extend(extract_all_diagnosis(diagnosis))
            else:
                diagnoses = extract_all_diagnosis(diagnoses_unparsed)
            
            if not diagnoses:
                exception = NoDiagnosisFoundForSampleException(
                    f"No correct diagnosis found for sample with identifier {identifier}."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise ValueError(exception)
        
        return diagnoses

    def __parse_xml_collection_datetime(self, xml_sample, identifier: str, validation_errors: list | None):
        """Parse the optional collection datetime field from XML."""
        collection_datetime_path = self._sample_parsing_map.get("sample_details").get("collection_date")
        
        if collection_datetime_path is None:
            return None
        
        collection_datetime_string = glom(xml_sample, collection_datetime_path, default=None)
        
        if collection_datetime_string is not None:
            try:
                collected_datetime = date_parser.parse(collection_datetime_string)
                return collected_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                exception = ParserError(
                    f"Error parsing date {collection_datetime_string} for sample with identifier {identifier}. "
                    f"Please make sure the date is in a valid format."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise exception
        
        return None

    def __parse_xml_diagnosis_datetime(self, xml_sample, identifier: str, validation_errors: list | None):
        """Parse the optional diagnosis datetime field from XML."""
        diagnosis_datetime_path = self._sample_parsing_map.get("sample_details").get("diagnosis_date")
        
        if diagnosis_datetime_path is None:
            return None
        
        diagnosis_datetime_string = glom(xml_sample, diagnosis_datetime_path, default=None)
        
        if diagnosis_datetime_string is not None:
            try:
                diagnosis_datetime = date_parser.parse(diagnosis_datetime_string)
                return diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                exception = ParserError(
                    f"Error parsing date {diagnosis_datetime_string} for sample with identifier {identifier}. "
                    f"Please make sure the date is in a valid format."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise exception
        
        return None

    def __extract_xml_sample_collection_id(self, xml_sample) -> str | None:
        """Extract sample collection ID from XML data."""
        sample_collection_id = None
        if self._type_to_collection_map is not None:
            attribute_to_collection = self._sample_parsing_map.get("sample_details").get("collection")
            if attribute_to_collection is not None:
                collection_attribute_value = glom(xml_sample, attribute_to_collection, default=None)
                if collection_attribute_value is not None:
                    sample_collection_id = self._type_to_collection_map.get(collection_attribute_value)
        return sample_collection_id

    def __extract_xml_storage_temperature(self, xml_sample, validation_errors: list | None):
        """Extract and validate storage temperature from XML data."""
        if self._storage_temp_map is None:
            return None
        
        storage_temp_path = self._sample_parsing_map.get("sample_details").get("storage_temperature")
        if storage_temp_path is None:
            return None
        
        storage_temp_code = glom(xml_sample, storage_temp_path, default=None)
        if storage_temp_code is None:
            return None
        
        if self._miabis_on_fhir_model:
            storage_temperature = miabis_parse_storage_temp_from_code(
                self._storage_temp_map, storage_temp_code
            )
        else:
            storage_temperature = module_parse_storage_temp_from_code(
                self._storage_temp_map, storage_temp_code
            )
        
        if storage_temperature is None and validation_errors is not None:
            validation_errors.append(
                ValueMappingRecordDoesNotExistError(
                    f"Value mapping for storage temperature {storage_temp_code} does not exist."
                )
            )
        
        return storage_temperature

    def __create_xml_sample_object(self, identifier: str, donor_id: str, diagnoses: list[str],
                                    material_type, storage_temperature, collected_datetime,
                                    diagnosis_datetime, sample_collection_id: str | None) -> SampleInterface:
        """Create the appropriate Sample or SampleMiabis object."""
        if self._miabis_on_fhir_model:
            diagnoses_with_observed_datetime = []
            for diagnosis in diagnoses:
                diagnoses_with_observed_datetime.append((diagnosis_with_period(diagnosis), diagnosis_datetime))
            
            return SampleMiabis(
                identifier=identifier,
                donor_id=donor_id,
                material_type=material_type,
                sample_collection_id=sample_collection_id,
                collected_datetime=collected_datetime,
                storage_temperature=storage_temperature,
                diagnoses_with_observed_datetime=diagnoses_with_observed_datetime
            )
        else:
            return Sample(
                identifier=identifier,
                donor_id=donor_id,
                material_type=material_type,
                diagnoses=diagnoses,
                sample_collection_id=sample_collection_id,
                collected_datetime=collected_datetime,
                storage_temperature=storage_temperature
            )

    def __build_sample(self, file_content, xml_sample, is_validation: bool = False) -> SampleInterface:
        validation_errors = [] if is_validation else None
        
        # Extract mandatory fields
        identifier = glom(xml_sample, self._sample_parsing_map.get("sample_details").get("id"))
        donor_id = glom(file_content, self._sample_parsing_map.get("donor_id"))
        
        # Extract optional fields with validation
        material_type = self.__extract_xml_material_type(xml_sample, validation_errors)
        diagnoses = self.__extract_xml_diagnoses(xml_sample, identifier, validation_errors)
        storage_temperature = self.__extract_xml_storage_temperature(xml_sample, validation_errors)
        
        # Parse datetime fields
        collected_datetime = self.__parse_xml_collection_datetime(xml_sample, identifier, validation_errors)
        diagnosis_datetime = self.__parse_xml_diagnosis_datetime(xml_sample, identifier, validation_errors)
        
        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)
        
        # Extract sample collection ID
        sample_collection_id = self.__extract_xml_sample_collection_id(xml_sample)
        
        # Create and return the appropriate sample object
        return self.__create_xml_sample_object(
            identifier, donor_id, diagnoses, material_type, storage_temperature,
            collected_datetime, diagnosis_datetime, sample_collection_id
        )


def flatten_list(nested_list):
    return [item for sublist in nested_list for item in
            (flatten_list(sublist) if isinstance(sublist, list) else [sublist])]
