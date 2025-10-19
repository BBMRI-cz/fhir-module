# Test Data Generator - Summary

## What Was Created

A flexible test data generation system has been created in the `test/generator/` folder with the following components:

### Core Files

1. **`generate_test_data.py`** - Main generator script

   - Generates CSV, JSON, or XML test files
   - Creates timestamped output folders: `generated_test_data_{file_type}_{timestamp}`
   - Supports flexible schema-based configuration
   - Command-line interface for easy use

2. **`schema.json`** - Configuration schema

   - Defines data structure for all three file formats (CSV, JSON, XML)
   - Supports various field types (sequential, random_int, choice, dates, etc.)
   - References external data files for realistic values
   - Extensible and customizable

3. **`README.md`** - Comprehensive documentation
   - Usage instructions
   - Schema configuration guide
   - Field type reference
   - Examples and tips

### Reference Data Files

- **`diagnoses.json`** - Diagnosis codes (e.g., C446, C490, C445)
- **`storage_temps.json`** - Storage temperature codes
- **`material_types.json`** - Sample/material type codes

## Quick Start

### Basic Usage

```bash
# Generate CSV files
python generate_test_data.py --file-type csv --num-files 5 --records-per-file 100

# Generate JSON files
python generate_test_data.py --file-type json --num-files 3 --records-per-file 50

# Generate XML files (each file = 1 patient with multiple samples)
python generate_test_data.py --file-type xml --num-files 10 --records-per-file 1
```

**Note:** For XML files, each file contains exactly **one patient** with multiple samples. The `--records-per-file` parameter is ignored for XML files.

### What Happens

1. Script reads `schema.json` and reference data files
2. Creates a new folder: `generated_test_data_{type}_{timestamp}/`
3. Generates the specified number of files with random but realistic data
4. Data values are pulled from reference files or generated based on schema rules

## Features

### Supported Field Types

- **Sequential**: Auto-incrementing numbers (resets for each file)
- **Sequential Global**: Auto-incrementing numbers (persists across all files)
- **Random Integers**: Within specified ranges
- **Random Dates/Times**: With custom formatting
- **Choice**: Random selection from predefined options
- **From File**: Random values from reference JSON files
- **Constants**: Fixed values
- **Copy Field**: Reference other fields in the same record
- **Format String**: Template strings using other field values

### Output Format

Generated files are placed in timestamped folders:

```
test/generator/
  ├── generated_test_data_csv_20251019_143025/
  │   ├── test_data_1.csv
  │   ├── test_data_2.csv
  │   └── ...
  ├── generated_test_data_json_20251019_143045/
  │   ├── test_data_1.json
  │   ├── test_data_2.json
  │   └── ...
  └── generated_test_data_xml_20251019_143105/
      ├── test_data_1.xml
      ├── test_data_2.xml
      └── ...
```

## Examples of Generated Data

### CSV

```csv
sample_ID;patient_pseudonym;sex;birth_year;date_of_diagnosis;diagnosis;donor_age;sampling_date;sampling_type;storage_temperature
1;8224;m;1972;02.03.2019;C445;75;04.02.2015;g-dna;temperatureRoom
2;6146;other;1940;28.03.2019;C446;90;08.10.2018;liquid-other;temperatureLN
```

### JSON

```json
[
  {
    "PatientId": "1",
    "SpecimenId": "10",
    "DateOfDiagnosis": "2013-10-27T12:09:12",
    "Diagnosis": "C446",
    "DonorAge": "1995-07",
    "SamplingDate": "2020-07-15T06:13:14",
    "SampleType": "blood-serum",
    "Sex": "other",
    "StorageTemperature": "-20"
  }
]
```

### XML

Each XML file contains **exactly one patient** with multiple samples:

```xml
<patient biobank="MOU" consent="true" id="1" month="--06" sex="female" year="1998">
  <LTS>
    <tissue year="2029" number="125" sampleId="BBM:2029:125:1">
      <samplesNo>6</samplesNo>
      <availableSamplesNo>6</availableSamplesNo>
      <materialType>11</materialType>
      <diagnosis>C445</diagnosis>
      ...
    </tissue>
    <tissue year="2030" number="126" sampleId="BBM:2030:126:1">
      <samplesNo>3</samplesNo>
      <availableSamplesNo>3</availableSamplesNo>
      <materialType>4</materialType>
      <diagnosis>C490</diagnosis>
      ...
    </tissue>
  </LTS>
</patient>
```

This structure matches the expected XML format where one file = one patient/donor with multiple sample records.

## Customization

### Modify Schema

Edit `schema.json` to change field structure, data types, or add new fields.

### Add Reference Data

Create new JSON files with reference data and reference them in the schema:

```json
{
  "field_name": {
    "type": "from_file",
    "file": "your_reference_data.json"
  }
}
```

### Custom Date Formats

Use Python's strftime format codes:

- `%Y-%m-%d` → 2025-10-19
- `%d.%m.%Y` → 19.10.2025
- `%Y-%m-%dT%H:%M:%S` → 2025-10-19T14:30:45

## Command-Line Options

| Option               | Required | Description                                                                                    |
| -------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| `--file-type`        | Yes      | Type of files: `csv`, `json`, or `xml`                                                         |
| `--num-files`        | Yes      | Number of files to generate                                                                    |
| `--records-per-file` | Yes      | Number of records per file (ignored for XML - each XML file always contains exactly 1 patient) |
| `--schema`           | No       | Custom schema file path (default: `schema.json`)                                               |

## Use Cases

1. **Testing Data Import**: Generate large datasets to test import performance
2. **UI Testing**: Create varied test data for frontend development
3. **Integration Testing**: Generate data matching production schemas
4. **Load Testing**: Create large volumes of data for stress testing
5. **Development**: Quick sample data for local development

## Notes

- Sequential fields reset for each file (each file starts from the beginning)
- Random data ensures variety within specified constraints
- Timestamps in folder names prevent overwriting previous generations
- All dates and values are randomly generated but follow realistic patterns
- **XML format**: Each XML file contains exactly **one patient** with multiple samples (1-5 tissue samples by default)
- This XML structure matches the expected format: one file = one patient/donor with multiple sample records

## Troubleshooting

- Ensure you're in the `test/generator/` directory or provide full paths
- Check that reference JSON files exist and contain valid arrays
- Verify schema.json has valid JSON syntax
- For date fields, ensure format strings match Python's strftime format
- On Windows, avoid Unicode characters in output (handled in the script)

## Future Enhancements

Possible additions:

- Support for nested JSON objects
- More complex XML schemas
- Database direct import
- Data validation rules
- Custom generators for specific data types
- Multi-threaded generation for large datasets
- Progress bars for long-running generations
