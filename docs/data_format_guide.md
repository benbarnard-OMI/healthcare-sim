# HL7 Data Format Guide

This document provides comprehensive guidance on HL7 data formats, storage requirements, and the relationship between Synthea, HL7, and FHIR data formats.

## Overview

The Healthcare Simulation project is designed to work with **HL7 v2.x messages** for realistic healthcare workflow simulation. This document clarifies data format requirements, storage guidelines, and addresses questions about Synthea and FHIR data conversion.

## Data Format Requirements

### Primary Format: HL7 v2.x Messages

The system is optimized for **HL7 v2.x** messages, which are the standard for real-time healthcare communications:

- **Message Structure**: Pipe-delimited segments (MSH, PID, PV1, DG1, OBX, PR1, etc.)
- **Field Separators**: Standard HL7 separators (`|^~\&`)
- **Encoding**: UTF-8 text format
- **Version Support**: Primarily HL7 v2.5.x, with backward compatibility

### Required Segments

For effective simulation, HL7 messages should include:

1. **MSH (Message Header)** - Required
   - Message type and control information
   - Timestamp and processing instructions

2. **PID (Patient Identification)** - Required  
   - Patient demographics and identifiers
   - Name, DOB, gender, address, phone

3. **PV1 (Patient Visit)** - Recommended
   - Admission information and location
   - Attending physician and hospital service

4. **DG1 (Diagnosis)** - Optional but valuable
   - ICD-10 diagnosis codes and descriptions
   - Diagnosis dates and types

5. **OBX (Observation Result)** - Optional but valuable
   - Lab values, vital signs, clinical observations
   - LOINC codes for standardized observations

6. **PR1 (Procedures)** - Optional
   - Surgical and medical procedures
   - Procedure codes and dates

### Example HL7 Message Structure

```hl7
MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000
DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A
OBX|1|NM|8867-4^HEART RATE^LN||88|/min|60-100|N|||F
OBX|2|NM|8480-6^SYSTOLIC BP^LN||142|mmHg|90-130|H|||F
```

## Data Storage Guidelines

### Scenario Storage Options

#### Option 1: YAML Configuration Files (Recommended)
Store patient scenarios in structured YAML files for easy management:

```yaml
# config/scenarios.yaml
scenarios:
  chest_pain:
    name: "Chest Pain Patient"
    description: "Standard patient admission with chest pain"
    category: "cardiology"
    severity: "moderate"
    hl7_message: |
      MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
      PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
      # ... additional segments
```

**Advantages:**
- Human-readable and editable
- Version control friendly
- Structured metadata support
- Easy validation and templating

#### Option 2: Individual HL7 Files
Store each scenario as a separate `.hl7` text file:

```
data/
├── scenarios/
│   ├── chest_pain.hl7
│   ├── diabetes.hl7
│   ├── pediatric.hl7
│   └── surgical.hl7
```

**Advantages:**
- Standard healthcare file format
- Compatible with HL7 tools
- Easy to share and validate

#### Option 3: Database Storage (Advanced)
For large-scale deployments, consider database storage:

```sql
CREATE TABLE patient_scenarios (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200),
    description TEXT,
    category VARCHAR(50),
    severity VARCHAR(20),
    hl7_message TEXT,
    metadata JSON,
    created_at TIMESTAMP
);
```

### Directory Structure

Recommended project structure for HL7 data:

```
healthcare-sim/
├── config/
│   ├── scenarios.yaml          # Patient scenario definitions
│   ├── agents.yaml            # Agent configurations
│   └── tasks.yaml             # Task configurations
├── data/
│   ├── scenarios/             # Individual HL7 files (optional)
│   ├── templates/             # HL7 message templates
│   └── validation/            # Validation schemas
├── sample_data/
│   └── sample_messages.py     # Legacy Python scenarios (backward compatibility)
└── docs/
    └── data_format_guide.md   # This document
```

## Synthea and FHIR Data Format

### The Synthea Question

**Question**: "The project refers to Synthea, but their datasets are provided in FHIR, not HL7. Should we remove the reference or add FHIR conversion?"

**Answer**: We recommend **keeping the Synthea reference** and providing **FHIR-to-HL7 conversion guidance**. Here's why:

### Why Keep Synthea

1. **Realistic Data**: Synthea generates highly realistic synthetic patient data
2. **Rich Datasets**: Comprehensive patient histories with realistic clinical progressions  
3. **Open Source**: Free, well-documented, and widely used in healthcare simulation
4. **Clinical Accuracy**: Evidence-based disease models and treatment pathways

### FHIR to HL7 Conversion Options

#### Option 1: Microsoft FHIR Converter (Recommended)
Use the Microsoft FHIR Converter for automated conversion:

```bash
# Install the converter
npm install -g @microsoft/fhir-converter

# Convert FHIR to HL7
fhir-converter -t hl7v2 -i patient.json -o patient.hl7
```

**Advantages:**
- Microsoft-supported open source tool
- Handles complex FHIR resources
- Configurable mapping templates
- Active development and community

#### Option 2: HAPI FHIR Library
For programmatic conversion in Java applications:

```java
// Example FHIR to HL7 conversion
FhirContext ctx = FhirContext.forR4();
IParser parser = ctx.newJsonParser();
Patient patient = parser.parseResource(Patient.class, fhirJson);

// Convert to HL7 PID segment
PID pid = new PID();
pid.getPatientName().addFamilyName(patient.getNameFirstRep().getFamily());
```

#### Option 3: Custom Python Conversion
For Python-based workflows:

```python
# Example FHIR to HL7 conversion script
import json
from datetime import datetime

def convert_fhir_to_hl7(fhir_patient):
    """Convert FHIR Patient resource to HL7 PID segment."""
    name = fhir_patient.get('name', [{}])[0]
    family = name.get('family', '')
    given = name.get('given', [''])[0]
    
    birth_date = fhir_patient.get('birthDate', '').replace('-', '')
    gender = fhir_patient.get('gender', 'U')[0].upper()
    
    pid_segment = f"PID|1||{fhir_patient.get('id', '')}|||{family}^{given}||{birth_date}|{gender}"
    return pid_segment
```

### Integration Workflow

Recommended workflow for using Synthea data:

1. **Generate FHIR Data**: Use Synthea to create realistic patient datasets
2. **Convert to HL7**: Use Microsoft FHIR Converter or custom scripts
3. **Validate HL7**: Ensure messages meet simulation requirements
4. **Store Scenarios**: Save in YAML configuration or individual files
5. **Simulate**: Use converted HL7 messages in healthcare simulation

### Example Conversion Pipeline

```bash
#!/bin/bash
# Synthea to Healthcare Simulation Pipeline

# Step 1: Generate synthetic patients with Synthea
java -jar synthea-with-dependencies.jar -p 10 Massachusetts Boston

# Step 2: Convert FHIR to HL7 using Microsoft converter
for file in output/fhir/*.json; do
    fhir-converter -t hl7v2 -i "$file" -o "output/hl7/$(basename "$file" .json).hl7"
done

# Step 3: Process and format for simulation
python scripts/format_for_simulation.py output/hl7/ config/scenarios.yaml

echo "Conversion complete. Scenarios ready for simulation."
```

## Best Practices

### Data Quality

1. **Validate HL7 Structure**: Ensure proper segment formatting and field separators
2. **Include Required Fields**: Patient ID, name, demographics are essential
3. **Use Standard Codes**: ICD-10 for diagnoses, LOINC for observations
4. **Realistic Values**: Lab values and vital signs should be clinically appropriate

### Performance Considerations

1. **Message Size**: Keep individual messages under 100KB for optimal performance
2. **Batch Processing**: For large datasets, process scenarios in batches
3. **Caching**: Cache parsed HL7 messages to improve simulation startup time
4. **Validation**: Pre-validate messages before simulation to catch errors early

### Security and Privacy

1. **Synthetic Data Only**: Never use real patient data in simulations
2. **Data Anonymization**: Even synthetic data should not contain real identifiers
3. **Access Control**: Limit access to scenario data to authorized users
4. **Audit Logging**: Log access to patient scenarios for compliance

## Troubleshooting

### Common HL7 Issues

1. **Invalid Field Separators**: Ensure proper use of `|^~\&` characters
2. **Missing Required Segments**: Include MSH and PID at minimum
3. **Encoding Problems**: Use UTF-8 encoding for all text
4. **Date Format Issues**: Use YYYYMMDD or YYYYMMDDHHMMSS format

### FHIR Conversion Issues

1. **Resource Mapping**: Not all FHIR resources have direct HL7 equivalents
2. **Version Compatibility**: Ensure FHIR version matches converter capabilities
3. **Complex Relationships**: May need custom mapping for complex patient relationships
4. **Missing Data**: Some FHIR fields may not convert to HL7

## Resources and References

### Official Documentation
- [HL7 v2.x Standard](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [Synthea Documentation](https://github.com/synthetichealth/synthea/wiki)

### Tools and Libraries
- [Microsoft FHIR Converter](https://github.com/microsoft/FHIR-Converter)
- [HAPI FHIR Library](https://hapifhir.io/)
- [HL7apy Python Library](https://hl7apy.org/)
- [Synthea Synthetic Patient Generator](https://synthea.mitre.org/)

### Healthcare Standards
- [ICD-10-CM Diagnosis Codes](https://www.cdc.gov/nchs/icd/icd10cm.htm)
- [LOINC Observation Codes](https://loinc.org/)
- [SNOMED CT Clinical Terms](https://www.snomed.org/)

## Conclusion

The Healthcare Simulation project supports HL7 v2.x messages as the primary data format while acknowledging the value of Synthea's FHIR data. By providing clear conversion guidance and multiple storage options, users can leverage both realistic synthetic data and the HL7 format optimized for healthcare workflow simulation.

For questions or additional guidance, please refer to the project documentation or contact the development team.