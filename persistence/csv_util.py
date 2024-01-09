

def check_sample_map_format(sample_parsing_map: dict):
    """Check if sample_details is available in sample parsing map"""
    if sample_parsing_map.get("sample_details") is None:
        raise WrongSampleMapException


class WrongSampleMapException(Exception):
    """Raised when the sample map being read has a wrong format"""
    pass
