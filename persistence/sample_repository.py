"""Module for handling Sample persistence."""
import abc
import os
from typing import Callable, Generator

from model.interface.sample_interface import SampleInterface

from util.config import get_records_dir_path, get_parsing_map, get_type_to_collection_map, get_storage_temp_map, get_material_type_map, get_miabis_storage_temp_map, get_miabis_material_type_map


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
        self._sample_parsing_map = get_parsing_map()['sample_map']
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

