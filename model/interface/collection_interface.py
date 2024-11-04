import abc


class CollectionInterface:
    @property
    @abc.abstractmethod
    def identifier(self):
        """get identifier of collection"""
        pass

    @identifier.setter
    @abc.abstractmethod
    def identifier(self, identifier: str):
        """set identifier"""
        pass
