"""Module for handling condition persistence"""
import abc
import os
from typing import Callable, Generator
import logging

from model.condition import Condition
from exception.wrong_parsing_map import WrongParsingMapException
from util.custom_logger import setup_logger
from util.config import get_records_dir_path, get_parsing_map

setup_logger()
logger = logging.getLogger()

class ConditionRepository(abc.ABC):
    """Class for handling Condition persistence"""

    def __init__(self, records_path: str):
        self._dir_path = records_path

    @abc.abstractmethod
    def get_all(self) -> Generator[Condition, None, None]:
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
        
        if 'condition_map' not in parsing_map:
            logger.error("'condition_map' key not found in parsing map. Cannot proceed without valid configuration.")
            raise WrongParsingMapException({
                "concept": "condition_map",
                "error_message": "'condition_map' key is missing from the parsing map"
            })
        
        self._condition_parsing_map = parsing_map['condition_map']

    @abc.abstractmethod
    def _get_supported_extensions(self) -> tuple[str, Callable]:
        """Return a dictionary mapping file extensions to parser methods."""
    
    def smoke_validate(self, validate_all: bool = False) -> list[str]:
        all_errors: list[str] = []
        
        ext, validation_method = self._get_supported_extensions()
        
        with os.scandir(self._dir_path) as entries:
            files_to_validate = list(entries) if validate_all else [next(entries, None)]
        
        if not files_to_validate or files_to_validate[0] is None:
            error_message = f"No files found in directory {self._dir_path}"
            return [error_message]
        
        for file_entry in files_to_validate:
            if file_entry and file_entry.name.lower().endswith(ext):
                errors = validation_method(file_entry)
                all_errors.extend(errors)
        
        return all_errors
