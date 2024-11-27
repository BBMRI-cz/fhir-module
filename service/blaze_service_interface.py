import abc


class BlazeServiceInterface(abc.ABC):

    @abc.abstractmethod
    def sync(self):
        """Start the sync between the repositories and Blaze"""
        pass

    @abc.abstractmethod
    def delete_everything(self):
        """delete all records from the blaze service"""
        pass

    def run_scheduler(self):
        """schedule to run sync periodically"""
        pass