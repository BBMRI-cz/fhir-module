"""Module for handling sample donor persistence"""
import abc
import os
from typing import Callable, Generator
import logging

from model.interface.sample_donor_interface import SampleDonorInterface
from exception.wrong_parsing_map import WrongParsingMapException
from util.custom_logger import setup_logger
from util.config import get_records_dir_path, get_parsing_map, MAX_VALIDATION_FILES

setup_logger()
logger = logging.getLogger()

class SampleDonorRepository(abc.ABC):
    """Class for handling a repository of Sample donors"""

    def __init__(self, records_path: str):
        self._dir_path = records_path

    @abc.abstractmethod
    def get_all(self) -> Generator[SampleDonorInterface, None, None]:
        """Fetches all SampleDonors in repository"""

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
        
        if 'donor_map' not in parsing_map:
            logger.error("'donor_map' key not found in parsing map. Cannot proceed without valid configuration.")
            raise WrongParsingMapException({
                "concept": "donor_map",
                "error_message": "'donor_map' key is missing from the parsing map"
            })
        
        self._donor_parsing_map = parsing_map['donor_map']

    @abc.abstractmethod
    def _get_supported_extensions(self) -> tuple[str, Callable]:
        """Return a dictionary mapping file extensions to parser methods."""

    def smoke_validate(self, validate_all: bool = False) -> list[str]:
        all_errors: list[str] = []
        
        ext, validation_method = self._get_supported_extensions()
        
        with os.scandir(self._dir_path) as entries:
            if validate_all:
                files_to_validate = []
                count = 0
                for entry in entries:
                    files_to_validate.append(entry)
                    count += 1
                    if count >= MAX_VALIDATION_FILES:
                        break
            else:
                files_to_validate = [next(entries, None)]
        
        if not files_to_validate or files_to_validate[0] is None:
            error_message = f"No files found in directory {self._dir_path}"
            return [error_message]
        
        for file_entry in files_to_validate:
            if file_entry and file_entry.name.lower().endswith(ext):
                try:
                    errors = validation_method(file_entry)
                    all_errors.extend(errors)
                except Exception as e:
                    all_errors.append(f"Error validating file {file_entry.name}: {str(e)}")
        
        return all_errors
