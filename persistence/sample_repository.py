"""Module for handling Sample persistence."""
import abc
import os
from typing import Callable, Generator
import logging

from model.interface.sample_interface import SampleInterface
from exception.wrong_parsing_map import WrongParsingMapException
from util.custom_logger import setup_logger
from util.config import get_records_dir_path, get_parsing_map, get_type_to_collection_map, get_storage_temp_map, get_material_type_map, get_miabis_storage_temp_map, get_miabis_material_type_map, MAX_VALIDATION_FILES

setup_logger()
logger = logging.getLogger()

class SampleRepository:
    """Class for interacting with Sample storage"""

    def __init__(self, records_path: str):
        self._dir_path = records_path

    @abc.abstractmethod
    def get_all(self) -> Generator[SampleInterface, None, None]:
        """Get all conditions."""

    def update_mappings(self) -> None:
        """Update the mappings for the repository."""
        self._dir_path = get_records_dir_path()
        
        parsing_map = get_parsing_map()
        if not parsing_map:
            logger.error("Failed to load parsing map file. Cannot proceed without valid configuration.")
            raise WrongParsingMapException({
                "concept": "parsing_map",
                "error_message": "Parsing map file not found or could not be loaded"
            })
        
        if 'sample_map' not in parsing_map:
            logger.error("'sample_map' key not found in parsing map. Cannot proceed without valid configuration.")
            raise WrongParsingMapException({
                "concept": "sample_map",
                "error_message": "'sample_map' key is missing from the parsing map"
            })
        
        self._sample_parsing_map = parsing_map['sample_map']
        self._type_to_collection_map = get_type_to_collection_map()

        if self._miabis_on_fhir_model:
            self._storage_temp_map = get_miabis_storage_temp_map()
            self._material_type_map = get_miabis_material_type_map()
        else:
            self._storage_temp_map = get_storage_temp_map()
            self._material_type_map = get_material_type_map()

    @abc.abstractmethod
    def _get_supported_extensions(self) -> tuple[str, Callable]:
        """Return a dictionary mapping file extensions to parser methods."""

    def smoke_validate(self, validate_all: bool = False) -> list[str]:
        all_errors: list[str] = []
        
        ext, validation_method = self._get_supported_extensions()
        files_to_validate = []
        max_files = MAX_VALIDATION_FILES if validate_all else 1
        
        with os.scandir(self._dir_path) as entries:
            for entry in entries:
                if entry.name.lower().endswith(ext):
                    files_to_validate.append(entry)
                    if len(files_to_validate) >= max_files:
                        break
        
        if not files_to_validate:
            error_message = f"No {ext} files found in directory {self._dir_path}"
            return [error_message]
        
        for file_entry in files_to_validate:
            try:
                errors = validation_method(file_entry)
                all_errors.extend(errors)
            except Exception as e:
                all_errors.append(f"Error validating file {file_entry.name}: {str(e)}")
        
        return all_errors

