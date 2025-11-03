
class WrongParsingMapException(Exception):
    """Raised when provided Parsing map does not provide necessary keys(attributes)"""
    def __init__(self, data: dict = None):
        if data:
            self.concept = data.get("concept")
            self.error_message = data.get("error_message")
            super().__init__(f"Wrong parsing map for {self.concept}: {self.error_message}")
        else:
            self.concept = None
            self.error_message = None
            super().__init__()
