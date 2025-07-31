# Scenario Extension Guide

This guide explains how to create and add new patient scenarios to the Healthcare Simulation system. It covers both YAML-based configuration and programmatic approaches.

## Quick Start

### Adding a Simple Scenario

1. Open `config/scenarios.yaml`
2. Add your scenario under the `scenarios` section:

```yaml
scenarios:
  my_new_scenario:
    name: "My New Patient Scenario"
    description: "Description of the clinical case"
    category: "general_medicine"
    severity: "moderate"
    tags: ["example", "custom"]
    metadata:
      age_group: "adult"
      gender: "female"
      primary_condition: "example_condition"
      expected_duration: "2-3_hours"
    hl7_message: |
      MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
      PID|1|98765|98765^^^SIMULATOR^MR~9999^^^SIMULATOR^SB|1111111111^^^USSSA^SS|DOE^JANE^F||19801225|F|||456 ELM ST^^CHICAGO^IL^60601||312-555-0123|||F|NON|98765|987-65-4321
      # Add more HL7 segments as needed
```

3. Test your scenario:
```bash
python simulate.py --scenario my_new_scenario
```

## Scenario Structure

### Core Fields

Every scenario must include these fields:

- **name**: Human-readable scenario name
- **description**: Detailed description of the clinical case
- **category**: Medical specialty category
- **severity**: Clinical severity level
- **hl7_message**: Complete HL7 v2.x message

### Optional Fields

- **tags**: List of keywords for scenario organization
- **metadata**: Additional structured information
- **expected_findings**: List of expected clinical findings
- **clinical_pathways**: List of relevant clinical pathways

### Metadata Structure

```yaml
metadata:
  age_group: "adult"           # infant, pediatric, adolescent, adult, elderly
  gender: "female"             # male, female, other, unknown
  primary_condition: "diabetes" # Primary medical condition
  expected_duration: "2-4_hours" # Expected simulation duration
```

## Advanced Scenario Creation

### Complex Multi-Condition Scenario

```yaml
scenarios:
  complex_cardiac_case:
    name: "Complex Cardiac Patient with Comorbidities"
    description: "Elderly patient with acute MI, diabetes, and renal insufficiency"
    category: "cardiology"
    severity: "critical"
    tags: ["cardiac", "emergency", "multi_condition", "elderly"]
    metadata:
      age_group: "elderly"
      gender: "male"
      primary_condition: "acute_myocardial_infarction"
      expected_duration: "6-12_hours"
      comorbidities: ["diabetes_type2", "chronic_kidney_disease", "hypertension"]
      risk_factors: ["smoking", "family_history", "obesity"]
    hl7_message: |
      MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240301080000||ADT^A01|789123|P|2.5.1
      PID|1|56789|56789^^^SIMULATOR^MR~7777^^^SIMULATOR^SB|3333333333^^^USSSA^SS|JOHNSON^ROBERT^M||19451015|M|||789 CARDIAC BLVD^^HOUSTON^TX^77001||713-555-7890|||M|NON|56789|345-67-8901
      PV1|1|E|CCU^301^01||||30101^CARDIO^SARAH^MD|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240301080000
      DG1|1|ICD-10-CM|I21.9|ACUTE MYOCARDIAL INFARCTION, UNSPECIFIED|20240301080000|A
      DG1|2|ICD-10-CM|E11.9|TYPE 2 DIABETES MELLITUS|20240301080000|A
      DG1|3|ICD-10-CM|N18.3|CHRONIC KIDNEY DISEASE, STAGE 3|20240301080000|A
      OBX|1|NM|8867-4^HEART RATE^LN||110|/min|60-100|H|||F
      OBX|2|NM|8480-6^SYSTOLIC BP^LN||88|mmHg|90-130|L|||F
      OBX|3|NM|8462-4^DIASTOLIC BP^LN||52|mmHg|60-80|L|||F
      OBX|4|NM|2160-0^CREATININE^LN||2.1|mg/dL|0.6-1.2|H|||F
      OBX|5|NM|33747-0^TROPONIN I^LN||8.5|ng/mL|0.0-0.4|H|||F
      OBX|6|NM|2345-7^GLUCOSE^LN||280|mg/dL|70-110|H|||F
    expected_findings:
      - elevated_troponin
      - hypotension
      - hyperglycemia
      - acute_kidney_injury
      - st_elevation_changes
    clinical_pathways:
      - stemi_protocol
      - cardiac_catheterization
      - intensive_care_monitoring
      - diabetes_management
      - renal_function_monitoring
```

### Pediatric Scenario with Age-Specific Considerations

```yaml
scenarios:
  pediatric_asthma_exacerbation:
    name: "Pediatric Asthma Exacerbation"
    description: "8-year-old child with acute asthma exacerbation requiring hospitalization"
    category: "pediatrics"
    severity: "moderate"
    tags: ["pediatric", "respiratory", "asthma", "emergency"]
    metadata:
      age_group: "pediatric"
      gender: "male"
      primary_condition: "asthma_exacerbation"
      expected_duration: "1-2_days"
      age_months: 96  # 8 years
      weight_kg: 28
      allergies: ["dust_mites", "pollen", "pet_dander"]
    hl7_message: |
      MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240415160000||ADT^A01|456123|P|2.5.1
      PID|1|11111|11111^^^SIMULATOR^MR~4444^^^SIMULATOR^SB|2222222222^^^USSSA^SS|MILLER^ALEX^J||20160415|M|||123 PEDIATRIC WAY^^DENVER^CO^80202||303-555-1111|||M|NON|11111|111-22-3333
      PV1|1|I|PEDS^201^02||||20202^PEDS^MARIA^MD|||PEDIATRICS||||||ADM|A0|||||||||||||||||||||||||20240415160000
      DG1|1|ICD-10-CM|J45.9|ASTHMA, UNSPECIFIED|20240415160000|A
      OBX|1|NM|8867-4^HEART RATE^LN||125|/min|70-120|H|||F
      OBX|2|NM|9279-1^RESPIRATORY RATE^LN||28|/min|15-25|H|||F
      OBX|3|NM|2708-6^OXYGEN SATURATION^LN||91|%|95-100|L|||F
      OBX|4|NM|8310-5^BODY TEMPERATURE^LN||37.2|C|36.5-37.5|N|||F
      OBX|5|ST|PEAK_FLOW^PEAK FLOW^L||180|L/min|200-250|L|||F
    expected_findings:
      - wheezing
      - increased_work_of_breathing
      - hypoxemia
      - decreased_peak_flow
    clinical_pathways:
      - pediatric_asthma_protocol
      - bronchodilator_therapy
      - corticosteroid_treatment
      - oxygen_therapy
      - discharge_planning_with_action_plan
```

## HL7 Message Construction

### Required Segments

#### MSH (Message Header)
```hl7
MSH|^~\&|SENDING_APP|SENDING_FACILITY|RECEIVING_APP|RECEIVING_FACILITY|TIMESTAMP||MESSAGE_TYPE|CONTROL_ID|PROCESSING_ID|VERSION
```

#### PID (Patient Identification)
```hl7
PID|SET_ID|PATIENT_ID|PATIENT_ID_LIST|ALT_PATIENT_ID|PATIENT_NAME|MOTHER_NAME|DATE_OF_BIRTH|SEX|PATIENT_ALIAS|RACE|PATIENT_ADDRESS|COUNTRY|PHONE_HOME|PHONE_BUSINESS|PRIMARY_LANGUAGE|MARITAL_STATUS|RELIGION|PATIENT_ACCOUNT|SSN|DRIVER_LICENSE
```

### Common Optional Segments

#### PV1 (Patient Visit)
```hl7
PV1|SET_ID|PATIENT_CLASS|ASSIGNED_PATIENT_LOCATION|ADMISSION_TYPE|PREADMIT_NUMBER|PRIOR_PATIENT_LOCATION|ATTENDING_DOCTOR|REFERRING_DOCTOR|CONSULTING_DOCTOR|HOSPITAL_SERVICE|TEMPORARY_LOCATION|PREADMIT_TEST_INDICATOR|RE_ADMISSION_INDICATOR|ADMIT_SOURCE|AMBULATORY_STATUS|VIP_INDICATOR|ADMITTING_DOCTOR|PATIENT_TYPE|VISIT_NUMBER|FINANCIAL_CLASS|CHARGE_PRICE_INDICATOR|COURTESY_CODE|CREDIT_RATING|CONTRACT_CODE|CONTRACT_EFFECTIVE_DATE|CONTRACT_AMOUNT|CONTRACT_PERIOD|INTEREST_CODE|TRANSFER_TO_BAD_DEBT_CODE|TRANSFER_TO_BAD_DEBT_DATE|BAD_DEBT_AGENCY_CODE|BAD_DEBT_TRANSFER_AMOUNT|BAD_DEBT_RECOVERY_AMOUNT|DELETE_ACCOUNT_INDICATOR|DELETE_ACCOUNT_DATE|DISCHARGE_DISPOSITION|DISCHARGED_TO_LOCATION|DIET_TYPE|SERVICING_FACILITY|BED_STATUS|ACCOUNT_STATUS|PENDING_LOCATION|PRIOR_TEMPORARY_LOCATION|ADMIT_DATE_TIME|DISCHARGE_DATE_TIME
```

#### DG1 (Diagnosis)
```hl7
DG1|SET_ID|DIAGNOSIS_CODING_METHOD|DIAGNOSIS_CODE|DIAGNOSIS_DESCRIPTION|DIAGNOSIS_DATE_TIME|DIAGNOSIS_TYPE|MAJOR_DIAGNOSTIC_CATEGORY|DIAGNOSTIC_RELATED_GROUP|DRG_APPROVAL_INDICATOR|DRG_GROUPER_REVIEW_CODE|OUTLIER_TYPE|OUTLIER_DAYS|OUTLIER_COST|GROUPER_VERSION_AND_TYPE|DIAGNOSIS_PRIORITY|DIAGNOSING_CLINICIAN|DIAGNOSIS_CLASSIFICATION|CONFIDENTIAL_INDICATOR
```

#### OBX (Observation Result)
```hl7
OBX|SET_ID|VALUE_TYPE|OBSERVATION_IDENTIFIER|OBSERVATION_SUB_ID|OBSERVATION_VALUE|UNITS|REFERENCES_RANGE|ABNORMAL_FLAGS|PROBABILITY|NATURE_OF_ABNORMAL_TEST|OBSERVATION_RESULT_STATUS|EFFECTIVE_DATE_OF_REFERENCE_RANGE|USER_DEFINED_ACCESS_CHECKS|DATE_TIME_OF_OBSERVATION|PRODUCER_ID|RESPONSIBLE_OBSERVER|OBSERVATION_METHOD
```

### HL7 Message Templates

#### Basic Adult Patient Template
```hl7
MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|YYYYMMDDHHMMSS||ADT^A01|CONTROL_ID|P|2.5.1
PID|1|PATIENT_ID|PATIENT_ID^^^SIMULATOR^MR~MRN^^^SIMULATOR^SB|SSN^^^USSSA^SS|LAST^FIRST^MIDDLE||YYYYMMDD|GENDER|||ADDRESS^^CITY^STATE^ZIP||PHONE|||GENDER|NON|PATIENT_ID|SSN
PV1|1|I|UNIT^ROOM^BED||||DOCTOR_ID^DOCTOR_LAST^DOCTOR_FIRST^TITLE|||SPECIALTY||||||ADM|A0|||||||||||||||||||||||||YYYYMMDDHHMMSS
DG1|1|ICD-10-CM|CODE|DESCRIPTION|YYYYMMDDHHMMSS|A
OBX|1|NM|CODE^NAME^LN||VALUE|UNITS|REFERENCE_RANGE|FLAG|||F
```

#### Pediatric Patient Template
```hl7
MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|YYYYMMDDHHMMSS||ADT^A01|CONTROL_ID|P|2.5.1
PID|1|PATIENT_ID|PATIENT_ID^^^SIMULATOR^MR~MRN^^^SIMULATOR^SB|SSN^^^USSSA^SS|LAST^FIRST^MIDDLE||YYYYMMDD|GENDER|||ADDRESS^^CITY^STATE^ZIP||PHONE|||GENDER|NON|PATIENT_ID|SSN
PV1|1|I|PEDS^ROOM^BED||||DOCTOR_ID^DOCTOR_LAST^DOCTOR_FIRST^MD|||PEDIATRICS||||||ADM|A0|||||||||||||||||||||||||YYYYMMDDHHMMSS
DG1|1|ICD-10-CM|CODE|DESCRIPTION|YYYYMMDDHHMMSS|A
OBX|1|NM|CODE^NAME^LN||VALUE|UNITS|PEDIATRIC_REFERENCE_RANGE|FLAG|||F
```

## Programmatic Scenario Creation

### Using the Scenario Loader API

```python
from scenario_loader import get_scenario_loader
from datetime import datetime

# Get the scenario loader
loader = get_scenario_loader()

# Create a new scenario programmatically
def create_hypertension_scenario():
    return {
        'name': 'Hypertensive Crisis Patient',
        'description': 'Patient presenting with severe hypertension requiring immediate intervention',
        'category': 'cardiology',
        'severity': 'critical',
        'tags': ['hypertension', 'emergency', 'cardiovascular'],
        'metadata': {
            'age_group': 'adult',
            'gender': 'female',
            'primary_condition': 'hypertensive_crisis',
            'expected_duration': '4-8_hours'
        },
        'hl7_message': generate_hypertension_hl7(),
        'expected_findings': [
            'severe_hypertension',
            'end_organ_damage_risk',
            'cardiovascular_stress'
        ],
        'clinical_pathways': [
            'hypertensive_emergency_protocol',
            'blood_pressure_management',
            'cardiovascular_monitoring'
        ]
    }

def generate_hypertension_hl7():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"""MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|{timestamp}||ADT^A01|HT001|P|2.5.1
PID|1|HT001|HT001^^^SIMULATOR^MR~8888^^^SIMULATOR^SB|4444444444^^^USSSA^SS|GARCIA^MARIA^L||19751203|F|||890 PRESSURE ST^^PHOENIX^AZ^85001||602-555-4567|||F|NON|HT001|444-55-6666
PV1|1|E|ER^101^01||||10101^EMERGENCY^JOHN^MD|||EMERGENCY||||||ADM|A0|||||||||||||||||||||||||{timestamp}
DG1|1|ICD-10-CM|I16.9|HYPERTENSIVE CRISIS, UNSPECIFIED|{timestamp}|A
OBX|1|NM|8480-6^SYSTOLIC BP^LN||210|mmHg|90-130|HH|||F
OBX|2|NM|8462-4^DIASTOLIC BP^LN||125|mmHg|60-80|HH|||F
OBX|3|NM|8867-4^HEART RATE^LN||105|/min|60-100|H|||F
OBX|4|ST|SYMPTOMS^SYMPTOMS^L||SEVERE HEADACHE, BLURRED VISION, CHEST PAIN||||F"""

# Add the scenario
try:
    scenario_data = create_hypertension_scenario()
    # This would typically be added to the YAML file or loaded dynamically
    print("Scenario created successfully")
except Exception as e:
    print(f"Error creating scenario: {e}")
```

### Dynamic Scenario Loading

```python
# Load scenario at runtime
loader = get_scenario_loader()

# Add scenario dynamically (for testing or temporary scenarios)
temp_scenario = {
    'name': 'Test Scenario',
    'description': 'Temporary test scenario',
    'category': 'general_medicine',
    'severity': 'low',
    'hl7_message': 'MSH|...\nPID|...\n'
}

# This would be handled by the crew system
from crew import HealthcareSimulationCrew
crew = HealthcareSimulationCrew()

# The crew can use the scenario directly
result = crew.crew().kickoff(inputs={
    'hl7_message': temp_scenario['hl7_message']
})
```

## Validation and Testing

### Scenario Validation

The system automatically validates scenarios for:

- **Required fields**: Name, description, category, severity, hl7_message
- **Field format**: Proper YAML structure and data types
- **HL7 structure**: Valid message format with required segments
- **Category values**: Must match predefined categories
- **Severity levels**: Must be low, moderate, high, or critical

### Testing Your Scenario

1. **Basic validation**:
```bash
python validate_scenarios.py config/scenarios.yaml
```

2. **Test simulation**:
```bash
python simulate.py --scenario your_scenario_name --verbose
```

3. **Dry run**:
```bash
python simulate.py --scenario your_scenario_name --test-connection
```

### Common Validation Errors

1. **Missing MSH segment**: Every HL7 message must start with MSH
2. **Missing PID segment**: Patient identification is required
3. **Invalid field separators**: Use `|^~\&` consistently
4. **Incorrect date formats**: Use YYYYMMDD or YYYYMMDDHHMMSS
5. **Invalid category**: Must be one of the predefined categories

## Best Practices

### Clinical Accuracy

1. **Realistic vital signs**: Use age-appropriate normal ranges
2. **Appropriate ICD-10 codes**: Use current, specific diagnosis codes
3. **LOINC codes for labs**: Use standard observation identifiers
4. **Logical progression**: Ensure findings match the clinical scenario

### Data Quality

1. **Complete demographics**: Include essential patient information
2. **Consistent identifiers**: Use unique, consistent patient IDs
3. **Proper encoding**: Use UTF-8 for all text data
4. **Validation**: Always validate HL7 messages before deployment

### Organization

1. **Descriptive names**: Use clear, searchable scenario names
2. **Appropriate tags**: Tag scenarios for easy filtering
3. **Version control**: Track scenario changes with git
4. **Documentation**: Include clear descriptions and expected outcomes

## Troubleshooting

### Common Issues

1. **YAML parsing errors**: Check indentation and special characters
2. **HL7 validation failures**: Verify segment structure and field separators
3. **Scenario not found**: Check spelling and file location
4. **Simulation failures**: Review logs for specific error messages

### Debug Tools

```python
# Debug scenario loading
from scenario_loader import get_scenario_loader
loader = get_scenario_loader()

# Check if scenario exists
scenarios = loader.list_scenarios()
print("Available scenarios:", scenarios)

# Get scenario details
scenario_info = loader.get_scenario_info('your_scenario')
print("Scenario info:", scenario_info)

# Validate HL7 message
hl7_message = loader.get_hl7_message('your_scenario')
if hl7_message:
    print("HL7 message loaded successfully")
    print("Message length:", len(hl7_message))
else:
    print("Failed to load HL7 message")
```

## Resources

- [HL7 v2.x Standard Documentation](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
- [ICD-10-CM Diagnosis Codes](https://www.cdc.gov/nchs/icd/icd10cm.htm)
- [LOINC Laboratory Codes](https://loinc.org/)
- [YAML Specification](https://yaml.org/spec/1.2/spec.html)
- [Healthcare Simulation Documentation](docs/README.md)

For additional help or questions, please refer to the project documentation or contact the development team.