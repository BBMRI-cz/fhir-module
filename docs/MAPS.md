# Maps

Usually, biobanks have their own naming conventions, be it for material types, storage temperatures, etc. These Maps, which are json files, tell FHIR-module how to map these internal naming conventions into standardized values.

They are essential part of the transformation process. Without them, the transformation into FHIR based profiles would not work.

### Parsing map

Parsing map tells FHIR-module which standardized attribute name (used in source code) corresponds to attributes in the provided records.

For example, in the [default_json_parsing_map](/util/default_csv_map.json), the standardized attribude for patient(donor) ID corresponds to an attribute called "patient pseudonym" in the records file.

In order to create your own parsing map, you need to keep the keys in the json same, and change the values for these keys to the actuall attribute names used in record files.

For parsing_map_for xml files, see [default_parsing_map](/util/default_map.json)

### Material Type map

The Material Type Map is a JSON file used by the FHIR module to translate material type values found in record files into [standardized values](https://simplifier.net/bbmri.de/samplematerialtype).

When the FHIR module processes a record file, it looks up the material type provided in the record and maps it to the corresponding standardized value using this map.

For example, in the [default_material_type_map](/util/default_material_type_map.json), the material type used by biobank "S" gets mapped into standardized value "serum".

In order to create your own Material Type map, the keys need to correspond to standardized values , and the values for these keys are actual values used in record files.

### Storage Temperature map
The Storage Temperature Map is a JSON file used by the FHIR module to convert storage temperature values from record files into [standardized values](https://simplifier.net/bbmri.de/storagetemperature).

When the FHIR module processes a record file, it uses this map to translate the original storage temperature information into the corresponding standardized format.

For example, in the [default_storage_temperature_map](/util/default_storage_temp_map.json), the storage temperature value used by biobanks "TEMPERATURE_2_TO_10" gets mapped into standardized value "temperature2to10".

In order to create your own Storage Temperature map, the keys need to correspond to standardized values , and the values for these keys are actual values used in record files.

### Type to Collection map
The Type to Collection Map is a JSON file used by the FHIR module to translate values of the "collection" attribute (as defined in the parsing map) into standardized Collection IDs provided by the BBMRI-ERIC Directory.

When processing data, the FHIR module uses this map to match incoming "collection" values to their corresponding identifiers in the BBMRI-ERIC Directory. This ensures that references to sample collections are accurate and consistent with the BBMRI ERIC Directory.

For example, in the [default_parsing_map](/util/default_map.json) we can see that the attribute that tells us to which collection the sample belongs to is "materialType". Then, in the [default_type_to_collection_map](/util/default_type_to_collection_map.json), we have the actual values of the material types as keys, and the values are Collection IDs (from BBMRI-ERIC Directory), to which these samples with these material types correspond to.

### Sample collections
Sample Collections is a JSON file that contains a list of collections registered in the BBMRI-ERIC Directory. Unlike the mapping files, this is not a map—it is a straightforward list of available collections.

This file is used to upload the collections into the BLAZE FHIR store. Doing so enables each sample to reference the collection it belongs to.

When working with the BBMRI.de specification, only two fields are required for each collection:
- identifier: The unique ID of the collection (as defined by BBMRI-ERIC)
- name: A human-readable name for the collection

For example, see [default_sample_collection](/util/default_sample_collection.json)

### Biobank

The Biobank file is a JSON file similar in structure to the Sample Collections file, but it contains only a single biobank entry.

This file is specifically used when working with the MIABIS_on_FHIR representation. In this context, the biobank serves as a required parent resource for sample collections, since collections cannot exist independently of a biobank in the MIABIS model.

The Biobank file enables the upload of this biobank into the BLAZE FHIR store, ensuring that the sample collections can be correctly linked and represented in compliance with MIABIS specifications.

For example, see [default_biobank](/util/default_biobank.json)




