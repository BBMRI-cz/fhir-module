from enum import Enum


class StorageTemperature(Enum):
    """Enum for expressing storage temperature of a sample:
    2 to 10 degrees Celsius
    -18 to -35 degrees Celsius
    -60 to -85 degrees Celsius
    Gaseous Nitrogen
    Liquid Nitrogen
    Room temperature
    Other storage temperature"""
    TEMPERATURE_2_TO_10 = "temperature2to10"
    TEMPERATURE_MINUS_18_TO_MINUS_35 = "temperature-18to-35"
    TEMPERATURE_MINUS_60_TO_MINUS_85 = "temperature-60to-85"
    TEMPERATURE_GN = "temperatureGN"
    TEMPERATURE_LN = "temperatureLN"
    TEMPERATURE_ROOM = "temperatureRoom"
    TEMPERATURE_OTHER = "temperatureOther"

    @classmethod
    def list(cls):
        """List all possible storage temperature values"""
        return list(map(lambda c: c.name, cls))


