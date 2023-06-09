class SampleDonor:
    def __init__(self, identifier: str):
        if not isinstance(identifier, str):
            raise TypeError("Identifier must be string")
        self._identifier = identifier

    @property
    def identifier(self):
        return self._identifier
