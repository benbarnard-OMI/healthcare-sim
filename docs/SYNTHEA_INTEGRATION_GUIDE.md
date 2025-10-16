# Synthea Integration Guide

This guide provides comprehensive instructions for using Synthea-generated synthetic patient data with the Healthcare Simulation system.

## Overview

Synthea is a synthetic patient data generator that creates highly realistic patient datasets with:
- **Realistic Demographics**: Age-appropriate patient populations
- **Clinical Accuracy**: Evidence-based disease models and treatment pathways
- **Comprehensive Data**: Complete patient histories with realistic clinical progressions
- **Open Source**: Free, well-documented, and widely used in healthcare simulation

## Installation and Setup

### Prerequisites

1. **Java Runtime Environment (JRE) 8 or higher**
   ```bash
   # Check Java version
   java -version
   
   # Install Java if needed (Ubuntu/Debian)
   sudo apt-get install openjdk-11-jre
   
   # Install Java if needed (macOS)
   brew install openjdk@11
   ```

2. **Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Initial Setup

1. **Clone the repository** (if not already done):
   ```bash
   git clone https://github.com/benbarnard-OMI/healthcare-sim.git
   cd healthcare-sim
   ```

2. **Verify installation**:
   ```bash
   python test_synthea_integration.py
   ```

## Quick Start

### Basic Usage

1. **Generate Synthea scenarios and run simulation**:
   ```bash
   python simulate.py --generate-synthea --num-patients 20 --backend openai --api-key your-key
   ```

2. **Use existing Synthea scenarios**:
   ```bash
   python simulate.py --scenario synthea_20240101_120000_1 --backend openai
   ```

### Advanced Usage

1. **Generate diverse patient populations**:
   ```bash
   # Pediatric patients
   python simulate.py --generate-synthea --num-patients 30 --age-min 0 --age-max 18
   
   # Elderly patients
   python simulate.py --generate-synthea --num-patients 25 --age-min 65 --age-max 100
   
   # Specific demographics
   python simulate.py --generate-synthea --num-patients 50 --state California --city Los Angeles
   ```

2. **Run integration demo**:
   ```bash
   python synthea_integration_demo.py --num-patients 50 --llm-backend openai --api-key your-key
   ```

## Components

### 1. Synthea Generator (`synthea_generator.py`)

Generates realistic synthetic patient data using Synthea.

**Key Features:**
- Downloads Synthea JAR automatically
- Generates patients with specified demographics
- Supports age ranges, geographic locations
- Produces FHIR R4 format data

**Usage:**
```python
from synthea_generator import SyntheaGenerator

# Initialize generator
generator = SyntheaGenerator(output_dir="synthea_output")

# Generate patients
result = generator.generate_patients(
    num_patients=20,
    state="Massachusetts",
    city="Boston",
    age_min=0,
    age_max=100,
    seed=12345
)

# Load generated patients
patients = generator.get_fhir_patients(result["generation_id"])
```

### 2. FHIR to HL7 Converter (`fhir_to_hl7_converter.py`)

Converts Synthea's FHIR R4 data to HL7 v2.x messages.

**Key Features:**
- Comprehensive FHIR resource support
- Realistic HL7 v2.x message generation
- Medical code mappings (LOINC, ICD-10, SNOMED)
- Vital signs and lab values generation

**Usage:**
```python
from fhir_to_hl7_converter import FHIRToHL7Converter

# Initialize converter
converter = FHIRToHL7Converter()

# Convert patient
hl7_message = converter.convert_patient_to_hl7(fhir_patient)

# Convert bundle of patients
hl7_messages = converter.convert_bundle_to_hl7(fhir_bundle)
```

### 3. Synthea Scenario Loader (`synthea_scenario_loader.py`)

Manages Synthea-generated scenarios for the simulation system.

**Key Features:**
- Dynamic scenario generation
- Clinical categorization
- Scenario metadata management
- Integration with existing scenario system

**Usage:**
```python
from synthea_scenario_loader import SyntheaScenarioLoader

# Initialize loader
loader = SyntheaScenarioLoader()

# Generate scenarios
result = loader.generate_synthea_scenarios(
    num_patients=20,
    age_min=0,
    age_max=100,
    state="Massachusetts",
    city="Boston"
)

# Get scenario
scenario = loader.get_scenario("synthea_20240101_120000_1")
hl7_message = loader.get_hl7_message("synthea_20240101_120000_1")
```

## Configuration

### Scenario Configuration

Synthea scenarios are automatically integrated into the existing scenario system. They appear alongside built-in scenarios and can be used interchangeably.

**Scenario Structure:**
```yaml
scenarios:
  synthea_20240101_120000_1:
    name: "John Smith - 45y/o Male with diabetes_type2"
    description: "Synthea-generated patient: John Smith - 45y/o Male with diabetes_type2"
    category: "endocrinology"
    severity: "high"
    tags: ["synthea", "generated", "endocrinology"]
    metadata:
      generation_id: "20240101_120000"
      patient_id: "patient_1"
      age_group: "adult"
      gender: "male"
      primary_condition: "diabetes_type2"
      expected_duration: "3-5_days"
      synthea_generated: true
    hl7_message: |
      MSH|^~\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
      PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19780315|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
      # ... additional segments
```

### LLM Configuration

Synthea scenarios work with all supported LLM backends:

**OpenAI:**
```bash
export OPENAI_API_KEY="your-api-key"
python simulate.py --generate-synthea --backend openai
```

**Ollama (Local):**
```bash
ollama serve
python simulate.py --generate-synthea --backend ollama --model llama2
```

**Openrouter:**
```bash
export OPENROUTER_API_KEY="your-api-key"
python simulate.py --generate-synthea --backend openrouter --model openai/gpt-4
```

## Data Quality and Realism

### Clinical Accuracy

Synthea-generated data provides:
- **Realistic Demographics**: Age-appropriate patient characteristics
- **Evidence-Based Conditions**: Medically accurate disease models
- **Realistic Progression**: Natural disease and treatment pathways
- **Comprehensive Histories**: Complete patient medical records

### Data Validation

The system includes comprehensive validation:
- **HL7 Structure Validation**: Ensures proper message format
- **Clinical Data Validation**: Validates medical codes and values
- **Demographic Validation**: Ensures realistic patient characteristics
- **Temporal Validation**: Validates dates and timelines

### Quality Metrics

Monitor data quality with:
```python
# Check generation results
result = generator.generate_patients(num_patients=50)
print(f"Generated {result['fhir_files']} patients")
print(f"Generation ID: {result['generation_id']}")

# Validate scenarios
loader = SyntheaScenarioLoader()
scenarios = loader.list_scenarios()
print(f"Available scenarios: {len(scenarios)}")
```

## Best Practices

### 1. Patient Population Design

**Diverse Age Groups:**
```python
# Generate balanced population
age_ranges = [(0, 5), (6, 17), (18, 35), (36, 55), (56, 75), (76, 100)]
for min_age, max_age in age_ranges:
    generator.generate_patients(
        num_patients=10,
        age_min=min_age,
        age_max=max_age
    )
```

**Geographic Diversity:**
```python
# Generate patients from different locations
locations = [
    ("Massachusetts", "Boston"),
    ("California", "Los Angeles"),
    ("Texas", "Houston"),
    ("Florida", "Miami")
]

for state, city in locations:
    generator.generate_patients(
        num_patients=25,
        state=state,
        city=city
    )
```

### 2. Scenario Management

**Organize by Clinical Category:**
```python
# Generate scenarios by specialty
specialties = {
    "cardiology": {"age_min": 40, "age_max": 80},
    "pediatrics": {"age_min": 0, "age_max": 18},
    "geriatrics": {"age_min": 65, "age_max": 100}
}

for specialty, params in specialties.items():
    loader.generate_synthea_scenarios(
        num_patients=20,
        **params
    )
```

**Use Reproducible Seeds:**
```python
# Use seeds for reproducible results
generator.generate_patients(
    num_patients=100,
    seed=12345  # Same seed = same patients
)
```

### 3. Performance Optimization

**Batch Processing:**
```python
# Generate large datasets in batches
batch_size = 50
total_patients = 500

for i in range(0, total_patients, batch_size):
    generator.generate_patients(
        num_patients=min(batch_size, total_patients - i),
        seed=12345 + i
    )
```

**Caching:**
```python
# Cache generated scenarios
loader = SyntheaScenarioLoader()
scenarios = loader.list_scenarios()  # Cached after first load
```

## Troubleshooting

### Common Issues

**1. Java Not Found**
```
Error: Java not found
Solution: Install Java Runtime Environment 8 or higher
```

**2. Synthea Download Fails**
```
Error: Failed to download Synthea JAR
Solution: Check internet connection and try again
```

**3. FHIR Conversion Errors**
```
Error: FHIR to HL7 conversion failed
Solution: Check FHIR data structure and try again
```

**4. Memory Issues**
```
Error: Out of memory during generation
Solution: Reduce batch size or increase Java heap size
```

### Debug Mode

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Run with verbose output
python simulate.py --generate-synthea --verbose
```

### Validation

Test integration:
```bash
# Run comprehensive tests
python test_synthea_integration.py

# Test specific components
python test_synthea_integration.py --test synthea_generator
python test_synthea_integration.py --test fhir_converter
```

## Advanced Features

### Custom Patient Generation

**Specific Conditions:**
```python
# Generate patients with specific conditions
generator = SyntheaGenerator()

# Use Synthea's condition-specific generation
# (Requires custom Synthea configuration)
```

**Custom Demographics:**
```python
# Generate patients with specific characteristics
generator.generate_patients(
    num_patients=100,
    state="Massachusetts",
    city="Boston",
    age_min=30,
    age_max=50,
    seed=12345
)
```

### Integration with External Systems

**Export to External Systems:**
```python
# Export scenarios for external use
loader.export_all_synthea_scenarios("export_directory/")

# Export specific scenario
loader.export_scenario("synthea_20240101_120000_1", "patient.hl7")
```

**API Integration:**
```python
# Use with external APIs
scenario = loader.get_scenario("synthea_20240101_120000_1")
hl7_message = scenario["hl7_message"]

# Send to external system
import requests
response = requests.post("https://api.example.com/hl7", data=hl7_message)
```

## Performance Considerations

### Generation Speed

- **Small Batches**: 10-20 patients per generation for faster results
- **Large Batches**: 100+ patients for comprehensive datasets
- **Parallel Processing**: Generate multiple batches simultaneously

### Memory Usage

- **Java Heap**: Increase with `-Xmx` flag if needed
- **Python Memory**: Monitor with memory profilers
- **Disk Space**: Synthea data can be large (1GB+ for 1000 patients)

### Storage

- **Local Storage**: Default location is `synthea_output/`
- **Cloud Storage**: Can be configured for cloud deployment
- **Cleanup**: Regular cleanup of old generations recommended

## Contributing

### Adding New Features

1. **Fork the repository**
2. **Create feature branch**
3. **Implement changes**
4. **Add tests**
5. **Submit pull request**

### Testing

```bash
# Run all tests
python test_synthea_integration.py

# Run specific tests
python test_synthea_integration.py --test synthea_generator
```

### Documentation

- Update this guide for new features
- Add examples for new functionality
- Document configuration changes

## Support

### Getting Help

1. **Check this guide** for common issues
2. **Run tests** to verify installation
3. **Check logs** for detailed error messages
4. **Open an issue** on GitHub for bugs
5. **Start a discussion** for questions

### Resources

- [Synthea Documentation](https://github.com/synthetichealth/synthea/wiki)
- [HL7 v2.x Standard](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=185)
- [FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [CrewAI Documentation](https://docs.crewai.com/)

## License

This integration follows the same MIT license as the main project. Synthea is also open source and free to use.