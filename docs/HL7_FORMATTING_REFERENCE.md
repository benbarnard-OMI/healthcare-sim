# HL7 v2.5.1 Formatting Reference

This document contains critical HL7 formatting rules for consistent message generation.

## Critical Field Mappings

### PID Segment (Patient Identification)
- **MRN Location**: PID-3 (NOT PID-2)
- **Format**: `PID|1||123456789^^^MAIN_HOSPITAL^MR||DOE^JOHN^M`
- **Patient Name**: PID-5 in format `FAMILY^GIVEN^MIDDLE`

### DG1 Segment (Diagnosis)
- **Coding System**: Use `ICD-10-CM` (NOT `I10`)
- **Format**: `DG1|2||E11.9^Type 2 diabetes mellitus^ICD-10-CM`
- **Structure**: `DG1|set_id||code^description^coding_system`

### ORC Segment (Common Order)
- **Timestamp Location**: ORC-9 (NOT ORC-5)
- **Provider Location**: ORC-12
- **Format**: `ORC|NW|ORD123|||||||20231015101500|||1234567890^SMITH^JANE^MD`
- **Order Control**: Use `NW` for new orders, `SC` for RAS messages

### RXO Segment (Pharmacy Order)
- **NDC Format**: `RXO|00093-0245-56^LISINOPRIL 20MG TAB^NDC|20|mg`
- **Structure**: `RXO|NDC^DRUG^NDC|dose|units`
- **Note**: Omit RXO-3 unless max dose specified
- **Separate Segments**: Use separate RXR and TQ1 segments

### OBX Segment (Observation)
- **WBC/Platelet Units**: Use `10*9/L^10*9/L^UCUM` (NOT `109/L`)
- **Format**: `OBX|...|6690-2^Leukocytes^LN||6.8|10*9/L^10*9/L^UCUM|4.5-11.0|N`
- **BP LOINC Codes**: Use correct LOINC codes for systolic/diastolic BP
- **Diagnoses in OBX-5**: Use CWE (Coded With Exceptions) format for diagnoses

### PV1 Segment (Patient Visit)
- **Provider Location**: PV1-7
- **Format**: `PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||...`

## Message Sequence Requirements

### Complete Clinical Pathway Must Include:
1. **ADT^A01** - Admission with proper PID-3 MRN and DG1 ICD-10-CM coding
2. **ORM^O01** - Lab orders with ORC-9 timestamps
3. **ORU^R01** - Lab results with proper UCUM units (10*9/L)
4. **ORM^O01** - Medication orders with correct RXO field mapping
5. **RAS^O17** - Medication administrations (ORC-1 uses SC)
6. **ADT^A08** - Patient updates
7. **ADT^A03** - Discharge
8. **MDM^T02** - Discharge summary with TXA and diagnoses as CWE in OBX-5
9. **Pharmacy Discharge Message** - Complete pharmacy discharge message

## Segment Termination Rules

- End each segment after last meaningful field
- Avoid trailing empty pipes
- Use proper field separators: `|` for fields, `^` for components

## Data Consistency Requirements

- Valid NDC codes for medications
- Consistent patient data across all messages
- Proper HL7 v2.5.1 structure with correct field positions
- Realistic timestamps showing chronological progression
- Distinct provider IDs for different providers

## Common Mistakes to Avoid

1. ❌ MRN in PID-2 instead of PID-3
2. ❌ Using `I10` instead of `ICD-10-CM` for coding system
3. ❌ Timestamp in ORC-5 instead of ORC-9
4. ❌ Using `109/L` instead of `10*9/L^10*9/L^UCUM` for WBC/platelets
5. ❌ Truncated pharmacy messages
6. ❌ Missing ADT^A03 discharge message
7. ❌ Missing MDM^T02 discharge summary
8. ❌ Trailing empty pipes in segments
