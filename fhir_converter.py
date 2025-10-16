#!/usr/bin/env python3
"""
HL7 to FHIR Converter

This module provides comprehensive conversion from HL7 v2.x messages to FHIR R4 resources.
It handles various HL7 segments and converts them to appropriate FHIR resources.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class FHIRResourceType(Enum):
    """FHIR resource types supported by the converter."""
    PATIENT = "Patient"
    OBSERVATION = "Observation"
    CONDITION = "Condition"
    PROCEDURE = "Procedure"
    ENCOUNTER = "Encounter"
    MEDICATION_STATEMENT = "MedicationStatement"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    BUNDLE = "Bundle"

@dataclass
class ConversionResult:
    """Result of HL7 to FHIR conversion."""
    success: bool
    fhir_resources: List[Dict[str, Any]]
    bundle: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    warnings: List[str] = None

class HL7ToFHIRConverter:
    """Converts HL7 v2.x messages to FHIR R4 resources."""
    
    def __init__(self):
        """Initialize the converter with code mappings."""
        self.loinc_codes = self._load_loinc_codes()
        self.icd10_codes = self._load_icd10_codes()
        self.snomed_codes = self._load_snomed_codes()
        self.medication_codes = self._load_medication_codes()
        
        # FHIR base URL for references
        self.fhir_base_url = "http://hl7.org/fhir"
        
    def convert_hl7_to_fhir(self, hl7_message: str) -> ConversionResult:
        """
        Convert HL7 message to FHIR resources.
        
        Args:
            hl7_message: The HL7 message string to convert
            
        Returns:
            ConversionResult containing FHIR resources and metadata
        """
        errors = []
        warnings = []
        fhir_resources = []
        
        try:
            # Parse HL7 message
            segments = self._parse_hl7_message(hl7_message)
            
            # Extract patient information
            patient_data = self._extract_patient_data(segments)
            if not patient_data:
                errors.append("No patient data found in HL7 message")
                return ConversionResult(False, [], errors=errors)
            
            # Create Patient resource
            patient_resource = self._create_patient_resource(patient_data)
            fhir_resources.append(patient_resource)
            
            # Create Encounter resource
            encounter_resource = self._create_encounter_resource(segments, patient_resource)
            if encounter_resource:
                fhir_resources.append(encounter_resource)
            
            # Create Condition resources from DG1 segments
            condition_resources = self._create_condition_resources(segments, patient_resource)
            fhir_resources.extend(condition_resources)
            
            # Create Observation resources from OBX segments
            observation_resources = self._create_observation_resources(segments, patient_resource, encounter_resource)
            fhir_resources.extend(observation_resources)
            
            # Create Procedure resources from PR1 segments
            procedure_resources = self._create_procedure_resources(segments, patient_resource, encounter_resource)
            fhir_resources.extend(procedure_resources)
            
            # Create Bundle
            bundle = self._create_bundle(fhir_resources)
            
            return ConversionResult(
                success=True,
                fhir_resources=fhir_resources,
                bundle=bundle,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Conversion failed: {str(e)}")
            logger.error(f"HL7 to FHIR conversion failed: {e}")
            return ConversionResult(False, [], errors=errors)
    
    def _parse_hl7_message(self, hl7_message: str) -> List[Dict[str, Any]]:
        """Parse HL7 message into segments."""
        segments = []
        lines = hl7_message.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            fields = line.split('|')
            if len(fields) < 2:
                continue
                
            segment_type = fields[0]
            segments.append({
                'line_number': line_num,
                'segment_type': segment_type,
                'fields': fields,
                'raw_line': line
            })
        
        return segments
    
    def _extract_patient_data(self, segments: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract patient data from PID segment."""
        for segment in segments:
            if segment['segment_type'] == 'PID':
                fields = segment['fields']
                if len(fields) < 8:
                    continue
                
                # Extract patient identifier
                patient_id = fields[3].split('^')[0] if fields[3] else str(uuid.uuid4())
                
                # Extract name
                name_parts = fields[5].split('^') if len(fields) > 5 and fields[5] else []
                family_name = name_parts[0] if name_parts else "Unknown"
                given_name = name_parts[1] if len(name_parts) > 1 else "Unknown"
                
                # Extract birth date
                birth_date = fields[7] if len(fields) > 7 and fields[7] else None
                if birth_date and len(birth_date) >= 8:
                    # Convert YYYYMMDD to YYYY-MM-DD
                    birth_date = f"{birth_date[:4]}-{birth_date[4:6]}-{birth_date[6:8]}"
                
                # Extract gender
                gender = fields[8] if len(fields) > 8 and fields[8] else "unknown"
                gender_map = {'M': 'male', 'F': 'female', 'O': 'other', 'U': 'unknown'}
                gender = gender_map.get(gender, 'unknown')
                
                # Extract address
                address_data = None
                if len(fields) > 11 and fields[11]:
                    address_parts = fields[11].split('^')
                    if len(address_parts) >= 4:
                        address_data = {
                            'line': [address_parts[0]] if address_parts[0] else [],
                            'city': address_parts[1] if len(address_parts) > 1 else '',
                            'state': address_parts[2] if len(address_parts) > 2 else '',
                            'postalCode': address_parts[3] if len(address_parts) > 3 else '',
                            'country': address_parts[4] if len(address_parts) > 4 else 'US'
                        }
                
                # Extract phone
                phone = None
                if len(fields) > 13 and fields[13]:
                    phone = fields[13]
                
                return {
                    'id': patient_id,
                    'family_name': family_name,
                    'given_name': given_name,
                    'birth_date': birth_date,
                    'gender': gender,
                    'address': address_data,
                    'phone': phone
                }
        
        return None
    
    def _create_patient_resource(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create FHIR Patient resource."""
        patient_id = patient_data['id']
        
        # Build name
        name = {
            'use': 'official',
            'family': patient_data['family_name'],
            'given': [patient_data['given_name']]
        }
        
        # Build identifier
        identifier = {
            'use': 'usual',
            'type': {
                'coding': [{
                    'system': 'http://terminology.hl7.org/CodeSystem/v2-0203',
                    'code': 'MR',
                    'display': 'Medical Record Number'
                }]
            },
            'value': patient_id
        }
        
        # Build telecom
        telecom = []
        if patient_data.get('phone'):
            telecom.append({
                'system': 'phone',
                'value': patient_data['phone'],
                'use': 'home'
            })
        
        # Build address
        address = []
        if patient_data.get('address'):
            address.append(patient_data['address'])
        
        patient_resource = {
            'resourceType': 'Patient',
            'id': patient_id,
            'identifier': [identifier],
            'name': [name],
            'gender': patient_data['gender'],
            'telecom': telecom,
            'address': address
        }
        
        if patient_data.get('birth_date'):
            patient_resource['birthDate'] = patient_data['birth_date']
        
        return patient_resource
    
    def _create_encounter_resource(self, segments: List[Dict[str, Any]], patient_resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create FHIR Encounter resource from PV1 segment."""
        for segment in segments:
            if segment['segment_type'] == 'PV1':
                fields = segment['fields']
                if len(fields) < 4:
                    continue
                
                encounter_id = str(uuid.uuid4())
                
                # Extract patient class
                patient_class = fields[2] if len(fields) > 2 and fields[2] else 'I'
                class_map = {
                    'I': 'inpatient',
                    'O': 'outpatient',
                    'P': 'prenatal',
                    'E': 'emergency',
                    'R': 'recurring patient',
                    'B': 'obstetrics',
                    'N': 'not applicable',
                    'U': 'unknown'
                }
                class_code = class_map.get(patient_class, 'unknown')
                
                # Extract location
                location_data = None
                if len(fields) > 3 and fields[3]:
                    location_parts = fields[3].split('^')
                    if location_parts[0]:
                        location_data = {
                            'display': f"Room {location_parts[1] if len(location_parts) > 1 else 'Unknown'}"
                        }
                
                # Extract admission date
                admit_date = None
                if len(fields) > 44 and fields[44]:
                    admit_date = self._convert_hl7_datetime(fields[44])
                
                encounter_resource = {
                    'resourceType': 'Encounter',
                    'id': encounter_id,
                    'status': 'finished',
                    'class': {
                        'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                        'code': class_code,
                        'display': class_code.title()
                    },
                    'subject': {
                        'reference': f"Patient/{patient_resource['id']}"
                    }
                }
                
                if location_data:
                    encounter_resource['location'] = [{
                        'location': location_data
                    }]
                
                if admit_date:
                    encounter_resource['period'] = {
                        'start': admit_date
                    }
                
                return encounter_resource
        
        return None
    
    def _create_condition_resources(self, segments: List[Dict[str, Any]], patient_resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create FHIR Condition resources from DG1 segments."""
        conditions = []
        
        for segment in segments:
            if segment['segment_type'] == 'DG1':
                fields = segment['fields']
                if len(fields) < 5:
                    continue
                
                condition_id = str(uuid.uuid4())
                
                # Extract diagnosis code
                code_data = None
                if len(fields) > 3 and fields[3]:
                    code_parts = fields[3].split('^')
                    if code_parts[0]:
                        code_data = {
                            'coding': [{
                                'system': 'http://hl7.org/fhir/sid/icd-10-cm',
                                'code': code_parts[0],
                                'display': code_parts[1] if len(code_parts) > 1 else code_parts[0]
                            }]
                        }
                
                # Extract description
                description = fields[4] if len(fields) > 4 and fields[4] else ''
                
                # Extract date
                onset_date = None
                if len(fields) > 5 and fields[5]:
                    onset_date = self._convert_hl7_datetime(fields[5])
                
                condition_resource = {
                    'resourceType': 'Condition',
                    'id': condition_id,
                    'subject': {
                        'reference': f"Patient/{patient_resource['id']}"
                    },
                    'clinicalStatus': {
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/condition-clinical',
                            'code': 'active',
                            'display': 'Active'
                        }]
                    },
                    'verificationStatus': {
                        'coding': [{
                            'system': 'http://terminology.hl7.org/CodeSystem/condition-ver-status',
                            'code': 'confirmed',
                            'display': 'Confirmed'
                        }]
                    }
                }
                
                if code_data:
                    condition_resource['code'] = code_data
                
                if description:
                    condition_resource['code']['text'] = description
                
                if onset_date:
                    condition_resource['onsetDateTime'] = onset_date
                
                conditions.append(condition_resource)
        
        return conditions
    
    def _create_observation_resources(self, segments: List[Dict[str, Any]], patient_resource: Dict[str, Any], encounter_resource: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create FHIR Observation resources from OBX segments."""
        observations = []
        
        for segment in segments:
            if segment['segment_type'] == 'OBX':
                fields = segment['fields']
                if len(fields) < 6:
                    continue
                
                observation_id = str(uuid.uuid4())
                
                # Extract observation identifier
                code_data = None
                if len(fields) > 3 and fields[3]:
                    code_parts = fields[3].split('^')
                    if code_parts[0]:
                        code_data = {
                            'coding': [{
                                'system': 'http://loinc.org',
                                'code': code_parts[0],
                                'display': code_parts[1] if len(code_parts) > 1 else code_parts[0]
                            }]
                        }
                
                # Extract value
                value_data = None
                if len(fields) > 5 and fields[5]:
                    value = fields[5]
                    value_type = fields[2] if len(fields) > 2 and fields[2] else 'ST'
                    
                    if value_type in ['NM', 'SN']:  # Numeric
                        try:
                            numeric_value = float(value)
                            value_data = {
                                'valueQuantity': {
                                    'value': numeric_value,
                                    'unit': fields[6] if len(fields) > 6 and fields[6] else ''
                                }
                            }
                        except ValueError:
                            value_data = {
                                'valueString': value
                            }
                    else:  # String
                        value_data = {
                            'valueString': value
                        }
                
                # Extract reference range
                reference_range = None
                if len(fields) > 7 and fields[7]:
                    range_parts = fields[7].split('-')
                    if len(range_parts) == 2:
                        try:
                            low = float(range_parts[0])
                            high = float(range_parts[1])
                            reference_range = [{
                                'low': {'value': low},
                                'high': {'value': high}
                            }]
                        except ValueError:
                            pass
                
                # Extract abnormal flags
                interpretation = None
                if len(fields) > 8 and fields[8]:
                    flag_map = {
                        'H': 'high',
                        'L': 'low',
                        'N': 'normal',
                        'A': 'abnormal',
                        'HH': 'critically high',
                        'LL': 'critically low'
                    }
                    flag = fields[8]
                    if flag in flag_map:
                        interpretation = [{
                            'coding': [{
                                'system': 'http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation',
                                'code': flag,
                                'display': flag_map[flag]
                            }]
                        }]
                
                observation_resource = {
                    'resourceType': 'Observation',
                    'id': observation_id,
                    'status': 'final',
                    'subject': {
                        'reference': f"Patient/{patient_resource['id']}"
                    }
                }
                
                if encounter_resource:
                    observation_resource['encounter'] = {
                        'reference': f"Encounter/{encounter_resource['id']}"
                    }
                
                if code_data:
                    observation_resource['code'] = code_data
                
                if value_data:
                    observation_resource.update(value_data)
                
                if reference_range:
                    observation_resource['referenceRange'] = reference_range
                
                if interpretation:
                    observation_resource['interpretation'] = interpretation
                
                observations.append(observation_resource)
        
        return observations
    
    def _create_procedure_resources(self, segments: List[Dict[str, Any]], patient_resource: Dict[str, Any], encounter_resource: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create FHIR Procedure resources from PR1 segments."""
        procedures = []
        
        for segment in segments:
            if segment['segment_type'] == 'PR1':
                fields = segment['fields']
                if len(fields) < 5:
                    continue
                
                procedure_id = str(uuid.uuid4())
                
                # Extract procedure code
                code_data = None
                if len(fields) > 3 and fields[3]:
                    code_parts = fields[3].split('^')
                    if code_parts[0]:
                        code_data = {
                            'coding': [{
                                'system': 'http://www.ama-assn.org/go/cpt',
                                'code': code_parts[0],
                                'display': code_parts[1] if len(code_parts) > 1 else code_parts[0]
                            }]
                        }
                
                # Extract procedure date
                performed_date = None
                if len(fields) > 5 and fields[5]:
                    performed_date = self._convert_hl7_datetime(fields[5])
                
                # Extract surgeon
                performer = None
                if len(fields) > 11 and fields[11]:
                    surgeon_parts = fields[11].split('^')
                    if len(surgeon_parts) >= 3:
                        performer = [{
                            'actor': {
                                'display': f"{surgeon_parts[1]} {surgeon_parts[2]}"
                            }
                        }]
                
                procedure_resource = {
                    'resourceType': 'Procedure',
                    'id': procedure_id,
                    'status': 'completed',
                    'subject': {
                        'reference': f"Patient/{patient_resource['id']}"
                    }
                }
                
                if encounter_resource:
                    procedure_resource['encounter'] = {
                        'reference': f"Encounter/{encounter_resource['id']}"
                    }
                
                if code_data:
                    procedure_resource['code'] = code_data
                
                if performed_date:
                    procedure_resource['performedDateTime'] = performed_date
                
                if performer:
                    procedure_resource['performer'] = performer
                
                procedures.append(procedure_resource)
        
        return procedures
    
    def _create_bundle(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create FHIR Bundle containing all resources."""
        bundle_id = str(uuid.uuid4())
        
        entries = []
        for resource in resources:
            entry = {
                'fullUrl': f"urn:uuid:{resource['id']}",
                'resource': resource
            }
            entries.append(entry)
        
        bundle = {
            'resourceType': 'Bundle',
            'id': bundle_id,
            'type': 'collection',
            'timestamp': datetime.now().isoformat(),
            'entry': entries
        }
        
        return bundle
    
    def _convert_hl7_datetime(self, hl7_datetime: str) -> str:
        """Convert HL7 datetime to FHIR datetime format."""
        if not hl7_datetime:
            return None
        
        # Remove any non-numeric characters except decimal point
        clean_datetime = ''.join(c for c in hl7_datetime if c.isdigit() or c == '.')
        
        if len(clean_datetime) >= 8:
            # YYYYMMDD format
            year = clean_datetime[:4]
            month = clean_datetime[4:6]
            day = clean_datetime[6:8]
            
            if len(clean_datetime) >= 10:
                # YYYYMMDDHH format
                hour = clean_datetime[8:10]
                if len(clean_datetime) >= 12:
                    # YYYYMMDDHHMM format
                    minute = clean_datetime[10:12]
                    if len(clean_datetime) >= 14:
                        # YYYYMMDDHHMMSS format
                        second = clean_datetime[12:14]
                        return f"{year}-{month}-{day}T{hour}:{minute}:{second}Z"
                    else:
                        return f"{year}-{month}-{day}T{hour}:{minute}:00Z"
                else:
                    return f"{year}-{month}-{day}T{hour}:00:00Z"
            else:
                return f"{year}-{month}-{day}"
        
        return None
    
    def _load_loinc_codes(self) -> Dict[str, str]:
        """Load LOINC codes for observations."""
        return {
            '8867-4': 'Heart rate',
            '8480-6': 'Systolic blood pressure',
            '8462-4': 'Diastolic blood pressure',
            '8310-5': 'Body temperature',
            '9279-1': 'Respiratory rate',
            '2708-6': 'Oxygen saturation',
            '2345-7': 'Glucose',
            '4548-4': 'Hemoglobin A1c',
            '2160-0': 'Creatinine'
        }
    
    def _load_icd10_codes(self) -> Dict[str, str]:
        """Load ICD-10 codes for conditions."""
        return {
            'I10': 'Essential hypertension',
            'E11.9': 'Type 2 diabetes mellitus',
            'R07.9': 'Chest pain, unspecified',
            'I63.9': 'Cerebral infarction',
            'J21.9': 'Acute bronchiolitis'
        }
    
    def _load_snomed_codes(self) -> Dict[str, str]:
        """Load SNOMED CT codes."""
        return {
            '182829008': 'Blood draw',
            '399208008': 'Chest X-ray',
            '164930006': 'Electrocardiogram'
        }
    
    def _load_medication_codes(self) -> Dict[str, str]:
        """Load medication codes."""
        return {
            '314076': 'Lisinopril',
            '1190805': 'Metoprolol',
            '860975': 'Metformin'
        }


def convert_hl7_to_fhir(hl7_message: str) -> ConversionResult:
    """
    Convenience function to convert HL7 message to FHIR.
    
    Args:
        hl7_message: The HL7 message string to convert
        
    Returns:
        ConversionResult containing FHIR resources and metadata
    """
    converter = HL7ToFHIRConverter()
    return converter.convert_hl7_to_fhir(hl7_message)


if __name__ == "__main__":
    # Example usage
    sample_hl7 = """MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000
DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A
OBX|1|NM|8867-4^HEART RATE^LN||88|/min|60-100|N|||F
OBX|2|NM|8480-6^SYSTOLIC BP^LN||142|mmHg|90-130|H|||F"""
    
    result = convert_hl7_to_fhir(sample_hl7)
    
    if result.success:
        print("Conversion successful!")
        print(f"Generated {len(result.fhir_resources)} FHIR resources")
        print(f"Bundle ID: {result.bundle['id']}")
        
        # Print first resource as example
        if result.fhir_resources:
            print(f"\nFirst resource ({result.fhir_resources[0]['resourceType']}):")
            print(json.dumps(result.fhir_resources[0], indent=2))
    else:
        print("Conversion failed!")
        for error in result.errors:
            print(f"Error: {error}")