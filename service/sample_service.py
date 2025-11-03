from persistence.sample_repository import SampleRepository


class SampleService:
    def __init__(self, sample_repo: SampleRepository):
        self._sample_repo = sample_repo

    def get_all(self):
        yield from self._sample_repo.get_all()

    def update_mappings(self) -> None:
        self._sample_repo.update_mappings()

    def smoke_validate(self, validate_all: bool = False) ->  list[str]:
        old_dir_path = self._sample_repo._dir_path
        old_sample_parsing_map = getattr(self._sample_repo, '_sample_parsing_map', None)
        old_type_to_collection_map = getattr(self._sample_repo, '_type_to_collection_map', None)
        old_storage_temp_map = getattr(self._sample_repo, '_storage_temp_map', None)
        old_material_type_map = getattr(self._sample_repo, '_material_type_map', None)
        old_separator = getattr(self._sample_repo, '_separator', None)
        
        try:
            self._sample_repo.update_mappings()
            
            result = self._sample_repo.smoke_validate(validate_all)
            
            return result
        finally:
            self._sample_repo._dir_path = old_dir_path
            if old_sample_parsing_map is not None:
                self._sample_repo._sample_parsing_map = old_sample_parsing_map
            if old_type_to_collection_map is not None:
                self._sample_repo._type_to_collection_map = old_type_to_collection_map
            if old_storage_temp_map is not None:
                self._sample_repo._storage_temp_map = old_storage_temp_map
            if old_material_type_map is not None:
                self._sample_repo._material_type_map = old_material_type_map
            if old_separator is not None:
                self._sample_repo._separator = old_separator
