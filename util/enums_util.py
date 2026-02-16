import logging

from model.gender import Gender
from model.storage_temperature import StorageTemperature
from util.custom_logger import setup_logger

setup_logger()
logger = logging.getLogger()


def parse_storage_temp_from_code(storage_temp_map: dict, code: str) -> StorageTemperature | None:
    if code not in storage_temp_map:
        logger.info(f"COULD NOT FING A MATCHING STORAGE TEMPERATURE CODE FOR: {code}!"
                    f" PLEASE UPDATE STORAGE_TEMP_MAP. Using None instead.")
        return None
    storage_temp = storage_temp_map.get(code)
    if storage_temp not in StorageTemperature.list():
        logger.info(f"FOUND A MATCHING STORAGE TEMPERATURE {storage_temp} FOR CODE: {code}"
                    f" BUT IT IS NOT A VALID STORAGE TEMPERATURE! Using None instead.")
        return None
    return StorageTemperature[storage_temp]


def get_gender_from_abbreviation(gender: str) -> Gender:
    match gender.upper():
        case "F":
            return Gender.FEMALE
        case "M":
            return Gender.MALE
        case "O":
            return Gender.OTHER
        case _:
            return Gender.UNKNOWN