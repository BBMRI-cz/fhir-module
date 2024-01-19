from exception.wrong_sample_format import WrongSampleMapException


def check_sample_map_format(sample_parsing_map: dict):
    """Check if sample_details is available in sample parsing map"""
    if sample_parsing_map.get("sample_details") is None:
        raise WrongSampleMapException("Sample parsing map cannot be empty")
