from persistence.sample_repository import SampleRepository


class SampleService:
    def __init__(self, sample_repo: SampleRepository):
        self._sample_repo = sample_repo

    def get_all(self):
        yield from self._sample_repo.get_all()
