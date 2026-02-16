
class NonexistentAttributeParsingMapException(Exception):
    """Raised when name/value pair is present in the parsing map, but the value itself is missing in the record file."""
    pass
