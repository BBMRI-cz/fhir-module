import logging
import os
from typing import Generator

import pandas as pd

from model.sample import Sample
from persistence.sample_repository import SampleRepository
from util.custom_logger import setup_logger

from persistence.csv_util import check_sample_map_format, WrongSampleMapException

setup_logger()
logger = logging.getLogger()


class SampleCsvRepository(SampleRepository):
    """Class for handling persistence in Csv files"""

    def __init__(self, records_path: str, sample_parsing_map: dict, separator: str,
                 type_to_collection_map: dict = None):
        self._dir_path = records_path
        self._sample_parsing_map = sample_parsing_map
        self._separator = separator
        logger.debug(f"Loaded the following sample parsing map {sample_parsing_map}")
        self._type_to_collection_map = type_to_collection_map

    def get_all(self) -> Generator[Sample, None, None]:
        dir_entry: os.DirEntry
        for dir_entry in os.scandir(self._dir_path):
            if dir_entry.name.endswith(".csv"):
                yield from self.__extract_sample_from_csv_file(dir_entry)

    def __extract_sample_from_csv_file(self, dir_entry: os.DirEntry) -> Sample:
        file_content = pd.read_csv(dir_entry, sep=self._separator, dtype=str)
        try:
            check_sample_map_format(self._sample_parsing_map)
            for _, row in file_content.iterrows():
                sample = Sample(identifier=row[self._sample_parsing_map.get("sample_details").get("id")],
                                donor_id=row[self._sample_parsing_map.get("donor_id")],
                                material_type=row[self._sample_parsing_map.get("sample_details").get("material_type")],
                                diagnosis=self.__extract_first_diagnosis(self, row[self._sample_parsing_map
                                                                         .get("sample_details").get("diagnosis")]))
                if self._type_to_collection_map is not None:
                    sample.sample_collection_id = self._type_to_collection_map.get(sample.diagnosis)
                yield sample
        except WrongSampleMapException:
            logger.info("Given Sample map has a bad format, cannot parse the file")
            pass
        except TypeError as err:
            logger.info(err)
            pass

    @staticmethod
    def __extract_first_diagnosis(self, diagnosis_str: str):
        """Extracts only the first diagnosis, if the file has multiple diagnosis"""
        if ',' in diagnosis_str:
            return diagnosis_str.split(',')[0].strip()
        else:
            return diagnosis_str.strip()
