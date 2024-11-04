from miabis_model import Collection, CollectionOrganization, Gender

from model.interface.collection_interface import CollectionInterface


class CollectionMiabis(CollectionOrganization, CollectionInterface):
    def __init__(self, identifier: str, name: str, managing_biobank_id: str,
                 contact_name: str, contact_surname: str,
                 contact_email: str,
                 country: str,
                 alias: str = None,
                 url: str = None,
                 description: str = None,
                 dataset_type: str = None,
                 sample_source: str = None,
                 sample_collection_setting: str = None, collection_design: list[str] = None,
                 use_and_access_conditions: list[str] = None,
                 publications: list[str] = None,
                 material_types: list[str] = None):
        super().__init__(identifier=identifier, name=name, managing_biobank_id=managing_biobank_id,
                         contact_name=contact_name, contact_surname=contact_surname, contact_email=contact_email,
                         country=country, alias=alias, url=url, description=description, dataset_type=dataset_type,
                         sample_source=sample_source, sample_collection_setting=sample_collection_setting,
                         collection_design=collection_design, use_and_access_conditions=use_and_access_conditions,
                         publications=publications)
        self._collection = Collection(identifier=identifier, name=name, managing_collection_org_id=identifier,
                                      genders=[Gender.UNKNOWN], material_types=material_types)

    @property
    def collection(self):
        return self._collection
