import json
import json
import logging
import os
from json import JSONDecodeError
from typing import Callable, Generator

from dateutil import parser as date_parser
from dateutil.parser import ParserError
from miabis_model.storage_temperature import parse_storage_temp_from_code as miabis_parse_storage_temp_from_code

from exception.no_diagnosis_found_for_sample import NoDiagnosisFoundForSampleException
from exception.wrong_sample_format import WrongSampleMapException
from exception.value_mapping_record_does_not_exist import ValueMappingRecordDoesNotExistError
from model.interface.sample_interface import SampleInterface
from model.miabis.sample_miabis import SampleMiabis
from model.sample import Sample
from persistence.csv_util import check_sample_map_format
from persistence.sample_repository import SampleRepository
from util.custom_logger import setup_logger
from util.enums_util import parse_storage_temp_from_code as module_parse_storage_temp_from_code
from util.sample_util import extract_all_diagnosis

setup_logger()
logger = logging.getLogger()


class SampleJsonRepository(SampleRepository):
    """Class for handling persistence in Csv files"""

    def __init__(self, records_path: str, sample_parsing_map: dict,
                 type_to_collection_map: dict = None, storage_temp_map: dict = None, material_type_map: dict = None,
                 miabis_on_fhir_model: bool = False, standardized: bool = True):
        super().__init__(records_path)
        self._sample_parsing_map = sample_parsing_map
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map
        self._storage_temp_map = storage_temp_map
        self._material_type_map = material_type_map
        self._miabis_on_fhir_model = miabis_on_fhir_model
        self.standardized = standardized

    def get_all(self) -> Generator[SampleInterface, None, None]:
        with os.scandir(self._dir_path) as entries:
            for dir_entry in entries:
                if dir_entry.name.lower().endswith(".json"):
                    yield from self.__extract_sample_from_json_file(dir_entry)

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        super().update_mappings()

    def _get_supported_extensions(self) -> tuple[str, Callable]:
        return ".json", self.__validate_sample_from_json_file

    def __extract_sample_from_json_file(self, dir_entry: os.DirEntry) -> SampleInterface:
        try:
            with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
                try:
                    check_sample_map_format(self._sample_parsing_map)
                    samples_json = json.load(json_file)
                except WrongSampleMapException:
                    logger.info("Given Sample map has a bad format, cannot parse the file")
                    return
                except JSONDecodeError:
                    logger.error("Biobank file does not have a correct JSON format. Exiting...")
                    return
                for sample_json in samples_json:
                    try:
                        sample = self.__build_sample(sample_json)
                        yield sample
                    except (ValueError, TypeError, KeyError) as err:
                        logger.info(f"{err} Skipping....")
        except OSError as e:
            logger.debug(f"Error while opening file {dir_entry.name}: {e}")
            logger.info(f"Error while opening file {dir_entry.name} [Skipping...]")
            return

    def __validate_sample_from_json_file(self, dir_entry: os.DirEntry) -> list[str]:
        errors = []
        try:
            with open(dir_entry, "r", encoding="utf-8-sig") as json_file:
                try:
                    check_sample_map_format(self._sample_parsing_map)
                    samples_json = json.load(json_file)

                # Sample map must be correct
                except WrongSampleMapException:
                    errors.append(f"File {dir_entry.name} - Given Sample map has a bad format, cannot parse the file")
                    return errors
                
                # Format must be correct
                except JSONDecodeError:
                    errors.append(f"File {dir_entry.name} - does not have a correct JSON format. Exiting...")
                    return errors
            
                sample_index = 0  # Start from 0 for JSON array index
                for sample_json in samples_json:
                    try:
                        _ = self.__build_sample(sample_json, is_validation=True)
                    except ExceptionGroup as eg:
                        for exc in eg.exceptions:
                            errors.append(f"File {dir_entry.name} - Sample (index {sample_index}): {exc}")
                    except (ValueError, TypeError, KeyError) as err:
                        errors.append(f"File {dir_entry.name} - Sample (index {sample_index}): {err}")
                    finally:
                        sample_index += 1

        except OSError as e:
            errors.append(f"Error while opening file {dir_entry.name}: {e}")
            return errors
    
        return errors

    def __extract_json_material_type(self, data: dict, validation_errors: list | None):
        """Extract and validate material type from JSON data."""
        material_type = data.get(self._sample_parsing_map.get("sample_details").get("material_type"), None)
        
        if not self.standardized or self._miabis_on_fhir_model:
            if material_type is not None and self._material_type_map is not None:
                material_type = self._material_type_map.get(material_type)
            if material_type is None and validation_errors is not None:
                validation_errors.append(
                    ValueMappingRecordDoesNotExistError(
                        f"Value mapping for material type {material_type} does not exist."
                    )
                )
        
        return material_type

    def __extract_json_diagnoses(self, data: dict, identifier: str, validation_errors: list | None) -> list[str]:
        """Extract and validate diagnoses from JSON data."""
        diagnosis_string = data.get(
            self._sample_parsing_map.get("sample_details").get("diagnosis")
        )
        
        diagnoses = []
        if diagnosis_string is not None:
            diagnoses = extract_all_diagnosis(diagnosis_string)
        
        if not diagnoses:
            exception = NoDiagnosisFoundForSampleException(
                f"No correct diagnosis has been found for sample with id {identifier}."
            )
            if validation_errors is not None:
                validation_errors.append(exception)
            else:
                raise ValueError(exception)
        
        return diagnoses

    def __extract_json_storage_temperature(self, data: dict, validation_errors: list | None):
        """Extract and validate storage temperature from JSON data."""
        storage_temperature_value = data.get(
            self._sample_parsing_map.get("sample_details").get("storage_temperature")
        )
        storage_temperature = None
        
        if storage_temperature_value is not None and self._storage_temp_map is not None:
            if self._miabis_on_fhir_model:
                storage_temperature = miabis_parse_storage_temp_from_code(
                    self._storage_temp_map, storage_temperature_value
                )
            else:
                storage_temperature = module_parse_storage_temp_from_code(
                    self._storage_temp_map, storage_temperature_value
                )
            
            if storage_temperature is None and validation_errors is not None:
                validation_errors.append(
                    ValueMappingRecordDoesNotExistError(
                        f"Value mapping for storage temperature {storage_temperature_value} does not exist."
                    )
                )
        
        return storage_temperature

    def __parse_json_collection_datetime(self, data: dict, identifier: str, validation_errors: list | None):
        """Parse the optional collection datetime field from JSON."""
        collection_datetime = data.get(
            self._sample_parsing_map.get("sample_details").get("collection_date"), None
        )
        
        if collection_datetime is not None:
            try:
                collection_datetime = date_parser.parse(collection_datetime)
                collection_datetime = collection_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                exception = ParserError(
                    f"Error parsing date for sample with identifier {identifier} "
                    f"while parsing collection datetime with value {collection_datetime}. "
                    f"Please make sure the date is in a valid format."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise exception
        
        return collection_datetime

    def __parse_json_diagnosis_datetime(self, data: dict, identifier: str, validation_errors: list | None):
        """Parse the optional diagnosis datetime field from JSON."""
        diagnosis_datetime = data.get(
            self._sample_parsing_map.get("sample_details").get("diagnosis_date"), None
        )
        
        if diagnosis_datetime is not None:
            try:
                diagnosis_datetime = date_parser.parse(diagnosis_datetime)
                diagnosis_datetime = diagnosis_datetime.replace(hour=0, minute=0, second=0)
            except ParserError:
                exception = ParserError(
                    f"Error parsing date for sample with identifier {identifier} "
                    f"while parsing diagnosis datetime with value {diagnosis_datetime}. "
                    f"Please make sure the date is in a valid format."
                )
                if validation_errors is not None:
                    validation_errors.append(exception)
                else:
                    raise exception
        
        return diagnosis_datetime

    def __extract_json_sample_collection_id(self, data: dict) -> str | None:
        """Extract sample collection ID from JSON data."""
        sample_collection_id = None
        if self._type_to_collection_map is not None:
            attribute_to_collection = self._sample_parsing_map.get("sample_details").get("collection")
            if attribute_to_collection in data.keys():
                sample_collection_id = self._type_to_collection_map.get(
                    data.get(attribute_to_collection)
                )
            else:
                sample_collection_id = self._type_to_collection_map.get("default")
        return sample_collection_id

    def __create_json_sample_object(self, identifier: str, donor_id: str, diagnoses: list[str],
                                     material_type, storage_temperature, collection_datetime,
                                     diagnosis_datetime, sample_collection_id: str | None) -> SampleInterface:
        """Create the appropriate Sample or SampleMiabis object."""
        if self._miabis_on_fhir_model:
            diagnoses_with_observed_datetime = []
            for diagnosis in diagnoses:
                diagnoses_with_observed_datetime.append((diagnosis, diagnosis_datetime))
            
            return SampleMiabis(
                identifier=identifier,
                donor_id=donor_id,
                diagnoses_with_observed_datetime=diagnoses_with_observed_datetime,
                material_type=material_type,
                sample_collection_id=sample_collection_id,
                collected_datetime=collection_datetime,
                storage_temperature=storage_temperature
            )
        else:
            return Sample(
                identifier=identifier,
                donor_id=donor_id,
                material_type=material_type,
                diagnoses=diagnoses,
                sample_collection_id=sample_collection_id,
                collected_datetime=collection_datetime,
                storage_temperature=storage_temperature
            )

    def __build_sample(self, data: dict, is_validation: bool = False) -> SampleInterface:
        validation_errors = [] if is_validation else None
        
        # Extract mandatory fields
        identifier = str(data.get(self._sample_parsing_map.get("sample_details").get("id")))
        donor_id = str(data.get(self._sample_parsing_map.get("donor_id")))
        
        # Extract optional fields with validation
        material_type = self.__extract_json_material_type(data, validation_errors)
        diagnoses = self.__extract_json_diagnoses(data, identifier, validation_errors)
        storage_temperature = self.__extract_json_storage_temperature(data, validation_errors)
        
        # Parse datetime fields
        collection_datetime = self.__parse_json_collection_datetime(data, identifier, validation_errors)
        diagnosis_datetime = self.__parse_json_diagnosis_datetime(data, identifier, validation_errors)
        
        # If in validation mode and there are errors, raise them all together
        if is_validation and validation_errors:
            raise ExceptionGroup("Validation errors", validation_errors)
        
        # Extract sample collection ID
        sample_collection_id = self.__extract_json_sample_collection_id(data)
        
        # Create and return the appropriate sample object
        return self.__create_json_sample_object(
            identifier, donor_id, diagnoses, material_type, storage_temperature,
            collection_datetime, diagnosis_datetime, sample_collection_id
        )
