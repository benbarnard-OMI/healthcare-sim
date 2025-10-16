#!/usr/bin/env python3
"""
HL7 Message Validator

This module provides comprehensive validation for HL7 v2.x messages including:
- Message structure validation
- Field format validation
- Required segment validation
- Data type validation
- Business rule validation
- Compliance checking
"""

import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Validation levels for HL7 messages."""
    BASIC = 1
    STANDARD = 2
    STRICT = 3
    COMPLIANCE = 4

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

@dataclass
class ValidationIssue:
    """Represents a validation issue found in an HL7 message."""
    severity: ValidationSeverity
    segment_type: str
    field_number: Optional[int]
    message: str
    details: str
    suggested_fix: Optional[str] = None

class HL7Validator:
    """Comprehensive HL7 message validator."""
    
    def __init__(self, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.issues: List[ValidationIssue] = []
        
        # HL7 field separators
        self.field_separator = '|'
        self.component_separator = '^'
        self.subcomponent_separator = '&'
        self.repetition_separator = '~'
        self.escape_character = '\\'
        
        # Common LOINC codes for validation
        self.loinc_codes = {
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
        
        # Common ICD-10 codes for validation
        self.icd10_codes = {
            'I10': 'Essential hypertension',
            'E11.9': 'Type 2 diabetes mellitus',
            'R07.9': 'Chest pain, unspecified',
            'I63.9': 'Cerebral infarction',
            'J21.9': 'Acute bronchiolitis'
        }
    
    def validate_message(self, hl7_message: str) -> Dict[str, Any]:
        """
        Validate an HL7 message and return comprehensive results.
        
        Args:
            hl7_message: The HL7 message string to validate
            
        Returns:
            Dictionary containing validation results
        """
        self.issues = []
        
        # Basic message structure validation
        self._validate_message_structure(hl7_message)
        
        # Parse and validate segments
        segments = self._parse_segments(hl7_message)
        for segment in segments:
            self._validate_segment(segment)
        
        # Cross-segment validation
        self._validate_cross_segments(segments)
        
        # Business rule validation
        self._validate_business_rules(segments)
        
        # Generate validation summary
        return self._generate_validation_summary()
    
    def _validate_message_structure(self, message: str) -> None:
        """Validate basic message structure."""
        if not message or not message.strip():
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                segment_type="MESSAGE",
                field_number=None,
                message="Empty or null HL7 message",
                details="The provided HL7 message is empty or contains only whitespace",
                suggested_fix="Provide a valid HL7 message"
            ))
            return
        
        # Check for proper line endings
        lines = message.strip().split('\n')
        if len(lines) < 2:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="MESSAGE",
                field_number=None,
                message="Message too short",
                details="HL7 message must contain at least MSH and one other segment",
                suggested_fix="Ensure message contains MSH segment and at least one data segment"
            ))
        
        # Check for MSH segment
        if not lines[0].startswith('MSH'):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                segment_type="MSH",
                field_number=None,
                message="Missing MSH segment",
                details="HL7 message must start with MSH (Message Header) segment",
                suggested_fix="Add MSH segment at the beginning of the message"
            ))
    
    def _parse_segments(self, message: str) -> List[Dict[str, Any]]:
        """Parse HL7 message into segments."""
        segments = []
        lines = message.strip().split('\n')
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():
                continue
                
            fields = line.split(self.field_separator)
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
    
    def _validate_segment(self, segment: Dict[str, Any]) -> None:
        """Validate individual segment."""
        segment_type = segment['segment_type']
        fields = segment['fields']
        line_num = segment['line_number']
        
        if segment_type == 'MSH':
            self._validate_msh_segment(fields, line_num)
        elif segment_type == 'PID':
            self._validate_pid_segment(fields, line_num)
        elif segment_type == 'PV1':
            self._validate_pv1_segment(fields, line_num)
        elif segment_type == 'DG1':
            self._validate_dg1_segment(fields, line_num)
        elif segment_type == 'OBX':
            self._validate_obx_segment(fields, line_num)
        elif segment_type == 'PR1':
            self._validate_pr1_segment(fields, line_num)
        else:
            # Validate unknown segment types
            self._validate_unknown_segment(segment)
    
    def _validate_msh_segment(self, fields: List[str], line_num: int) -> None:
        """Validate MSH (Message Header) segment."""
        if len(fields) < 12:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="MSH",
                field_number=None,
                message="Insufficient fields in MSH segment",
                details=f"MSH segment has {len(fields)} fields, minimum 12 required",
                suggested_fix="Ensure MSH segment contains all required fields"
            ))
            return
        
        # Field 1: Field Separator (should be '|')
        if fields[1] != self.field_separator:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="MSH",
                field_number=1,
                message="Invalid field separator",
                details=f"Expected '{self.field_separator}', found '{fields[1]}'",
                suggested_fix=f"Change field separator to '{self.field_separator}'"
            ))
        
        # Field 2: Encoding Characters
        if len(fields) > 2 and fields[2]:
            encoding_chars = fields[2]
            if len(encoding_chars) < 4:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    segment_type="MSH",
                    field_number=2,
                    message="Invalid encoding characters",
                    details="Encoding characters must be at least 4 characters",
                    suggested_fix="Provide complete encoding character set"
                ))
        
        # Field 3: Sending Application
        if len(fields) > 3 and not fields[3]:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="MSH",
                field_number=3,
                message="Missing sending application",
                details="Sending application identifier is empty",
                suggested_fix="Provide sending application identifier"
            ))
        
        # Field 4: Sending Facility
        if len(fields) > 4 and not fields[4]:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="MSH",
                field_number=4,
                message="Missing sending facility",
                details="Sending facility identifier is empty",
                suggested_fix="Provide sending facility identifier"
            ))
        
        # Field 7: Date/Time of Message
        if len(fields) > 7 and fields[7]:
            self._validate_datetime(fields[7], "MSH", 7, line_num)
        
        # Field 9: Message Type
        if len(fields) > 9 and fields[9]:
            self._validate_message_type(fields[9], line_num)
        
        # Field 12: Version ID
        if len(fields) > 12 and fields[12]:
            self._validate_version_id(fields[12], line_num)
    
    def _validate_pid_segment(self, fields: List[str], line_num: int) -> None:
        """Validate PID (Patient Identification) segment."""
        if len(fields) < 4:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="PID",
                field_number=None,
                message="Insufficient fields in PID segment",
                details=f"PID segment has {len(fields)} fields, minimum 4 required",
                suggested_fix="Ensure PID segment contains all required fields"
            ))
            return
        
        # Field 3: Patient Identifier List
        if len(fields) > 3 and fields[3]:
            self._validate_patient_identifier(fields[3], line_num)
        
        # Field 5: Patient Name
        if len(fields) > 5 and fields[5]:
            self._validate_patient_name(fields[5], line_num)
        
        # Field 7: Date/Time of Birth
        if len(fields) > 7 and fields[7]:
            self._validate_datetime(fields[7], "PID", 7, line_num)
        
        # Field 8: Administrative Sex
        if len(fields) > 8 and fields[8]:
            self._validate_administrative_sex(fields[8], line_num)
        
        # Field 11: Patient Address
        if len(fields) > 11 and fields[11]:
            self._validate_patient_address(fields[11], line_num)
    
    def _validate_pv1_segment(self, fields: List[str], line_num: int) -> None:
        """Validate PV1 (Patient Visit) segment."""
        if len(fields) < 3:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="PV1",
                field_number=None,
                message="Insufficient fields in PV1 segment",
                details=f"PV1 segment has {len(fields)} fields, minimum 3 required",
                suggested_fix="Ensure PV1 segment contains all required fields"
            ))
            return
        
        # Field 2: Patient Class
        if len(fields) > 2 and fields[2]:
            self._validate_patient_class(fields[2], line_num)
        
        # Field 3: Assigned Patient Location
        if len(fields) > 3 and fields[3]:
            self._validate_patient_location(fields[3], line_num)
    
    def _validate_dg1_segment(self, fields: List[str], line_num: int) -> None:
        """Validate DG1 (Diagnosis) segment."""
        if len(fields) < 5:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="DG1",
                field_number=None,
                message="Insufficient fields in DG1 segment",
                details=f"DG1 segment has {len(fields)} fields, minimum 5 required",
                suggested_fix="Ensure DG1 segment contains all required fields"
            ))
            return
        
        # Field 3: Diagnosis Code
        if len(fields) > 3 and fields[3]:
            self._validate_diagnosis_code(fields[3], line_num)
        
        # Field 4: Diagnosis Description
        if len(fields) > 4 and not fields[4]:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="DG1",
                field_number=4,
                message="Missing diagnosis description",
                details="Diagnosis description is empty",
                suggested_fix="Provide diagnosis description"
            ))
    
    def _validate_obx_segment(self, fields: List[str], line_num: int) -> None:
        """Validate OBX (Observation Result) segment."""
        if len(fields) < 6:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="OBX",
                field_number=None,
                message="Insufficient fields in OBX segment",
                details=f"OBX segment has {len(fields)} fields, minimum 6 required",
                suggested_fix="Ensure OBX segment contains all required fields"
            ))
            return
        
        # Field 3: Observation Identifier
        if len(fields) > 3 and fields[3]:
            self._validate_observation_identifier(fields[3], line_num)
        
        # Field 5: Observation Value
        if len(fields) > 5 and fields[5]:
            self._validate_observation_value(fields[5], line_num)
        
        # Field 6: Units
        if len(fields) > 6 and fields[6]:
            self._validate_units(fields[6], line_num)
    
    def _validate_pr1_segment(self, fields: List[str], line_num: int) -> None:
        """Validate PR1 (Procedure) segment."""
        if len(fields) < 5:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="PR1",
                field_number=None,
                message="Insufficient fields in PR1 segment",
                details=f"PR1 segment has {len(fields)} fields, minimum 5 required",
                suggested_fix="Ensure PR1 segment contains all required fields"
            ))
            return
        
        # Field 4: Procedure Code
        if len(fields) > 4 and fields[4]:
            self._validate_procedure_code(fields[4], line_num)
    
    def _validate_unknown_segment(self, segment: Dict[str, Any]) -> None:
        """Validate unknown segment types."""
        segment_type = segment['segment_type']
        fields = segment['fields']
        
        if len(fields) < 2:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type=segment_type,
                field_number=None,
                message=f"Unknown segment type with insufficient fields",
                details=f"Segment {segment_type} has only {len(fields)} fields",
                suggested_fix="Verify segment type and field count"
            ))
    
    def _validate_datetime(self, datetime_str: str, segment: str, field: int, line_num: int) -> None:
        """Validate datetime format."""
        # Common HL7 datetime formats
        datetime_patterns = [
            r'^\d{14}$',  # YYYYMMDDHHMMSS
            r'^\d{8}$',   # YYYYMMDD
            r'^\d{12}$',  # YYYYMMDDHHMM
            r'^\d{10}$',  # YYYYMMDDHH
        ]
        
        if not any(re.match(pattern, datetime_str) for pattern in datetime_patterns):
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type=segment,
                field_number=field,
                message="Invalid datetime format",
                details=f"Datetime '{datetime_str}' does not match HL7 format",
                suggested_fix="Use YYYYMMDDHHMMSS format"
            ))
    
    def _validate_message_type(self, message_type: str, line_num: int) -> None:
        """Validate message type format."""
        if '^' not in message_type:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="MSH",
                field_number=9,
                message="Invalid message type format",
                details=f"Message type '{message_type}' should contain '^' separator",
                suggested_fix="Use format: MESSAGE_TYPE^TRIGGER_EVENT"
            ))
    
    def _validate_version_id(self, version: str, line_num: int) -> None:
        """Validate HL7 version."""
        valid_versions = ['2.1', '2.2', '2.3', '2.3.1', '2.4', '2.5', '2.5.1', '2.6', '2.7', '2.8', '2.8.1', '2.8.2']
        if version not in valid_versions:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="MSH",
                field_number=12,
                message="Unsupported HL7 version",
                details=f"Version '{version}' may not be supported",
                suggested_fix=f"Use one of: {', '.join(valid_versions)}"
            ))
    
    def _validate_patient_identifier(self, identifier: str, line_num: int) -> None:
        """Validate patient identifier format."""
        if '^' not in identifier:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PID",
                field_number=3,
                message="Invalid patient identifier format",
                details="Patient identifier should contain component separators",
                suggested_fix="Use format: ID^CHECK_DIGIT^CHECK_DIGIT_SCHEME^ASSIGNING_AUTHORITY^ID_TYPE^ASSIGNING_FACILITY"
            ))
    
    def _validate_patient_name(self, name: str, line_num: int) -> None:
        """Validate patient name format."""
        if '^' not in name:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PID",
                field_number=5,
                message="Invalid patient name format",
                details="Patient name should contain component separators",
                suggested_fix="Use format: FAMILY_NAME^GIVEN_NAME^MIDDLE_NAME^SUFFIX^PREFIX"
            ))
    
    def _validate_administrative_sex(self, sex: str, line_num: int) -> None:
        """Validate administrative sex values."""
        valid_values = ['M', 'F', 'O', 'U', 'A', 'N']
        if sex not in valid_values:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PID",
                field_number=8,
                message="Invalid administrative sex",
                details=f"Sex '{sex}' is not a valid HL7 value",
                suggested_fix=f"Use one of: {', '.join(valid_values)}"
            ))
    
    def _validate_patient_address(self, address: str, line_num: int) -> None:
        """Validate patient address format."""
        components = address.split('^')
        if len(components) < 4:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PID",
                field_number=11,
                message="Incomplete patient address",
                details="Address should contain street, city, state, and postal code",
                suggested_fix="Use format: STREET^CITY^STATE^POSTAL_CODE^COUNTRY"
            ))
    
    def _validate_patient_class(self, patient_class: str, line_num: int) -> None:
        """Validate patient class values."""
        valid_values = ['I', 'O', 'P', 'E', 'R', 'B', 'N', 'U']
        if patient_class not in valid_values:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PV1",
                field_number=2,
                message="Invalid patient class",
                details=f"Patient class '{patient_class}' is not valid",
                suggested_fix=f"Use one of: {', '.join(valid_values)}"
            ))
    
    def _validate_patient_location(self, location: str, line_num: int) -> None:
        """Validate patient location format."""
        if '^' not in location:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PV1",
                field_number=3,
                message="Invalid patient location format",
                details="Location should contain component separators",
                suggested_fix="Use format: POINT_OF_CARE^ROOM^BED^FACILITY^LOCATION_STATUS^PERSON_LOCATION_TYPE^BUILDING^FLOOR^LOCATION_DESCRIPTION"
            ))
    
    def _validate_diagnosis_code(self, code: str, line_num: int) -> None:
        """Validate diagnosis code format."""
        if '^' not in code:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="DG1",
                field_number=3,
                message="Invalid diagnosis code format",
                details="Diagnosis code should contain component separators",
                suggested_fix="Use format: IDENTIFIER^TEXT^CODING_SYSTEM"
            ))
        else:
            components = code.split('^')
            if len(components) >= 1 and components[0]:
                # Check if it's a known ICD-10 code
                if components[0] in self.icd10_codes:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        segment_type="DG1",
                        field_number=3,
                        message="Valid ICD-10 code detected",
                        details=f"Code '{components[0]}' corresponds to '{self.icd10_codes[components[0]]}'",
                        suggested_fix=None
                    ))
    
    def _validate_observation_identifier(self, identifier: str, line_num: int) -> None:
        """Validate observation identifier format."""
        if '^' not in identifier:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="OBX",
                field_number=3,
                message="Invalid observation identifier format",
                details="Observation identifier should contain component separators",
                suggested_fix="Use format: IDENTIFIER^TEXT^CODING_SYSTEM"
            ))
        else:
            components = identifier.split('^')
            if len(components) >= 1 and components[0]:
                # Check if it's a known LOINC code
                if components[0] in self.loinc_codes:
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        segment_type="OBX",
                        field_number=3,
                        message="Valid LOINC code detected",
                        details=f"Code '{components[0]}' corresponds to '{self.loinc_codes[components[0]]}'",
                        suggested_fix=None
                    ))
    
    def _validate_observation_value(self, value: str, line_num: int) -> None:
        """Validate observation value."""
        if not value.strip():
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="OBX",
                field_number=5,
                message="Empty observation value",
                details="Observation value is empty",
                suggested_fix="Provide a valid observation value"
            ))
    
    def _validate_units(self, units: str, line_num: int) -> None:
        """Validate units format."""
        if '^' not in units and units:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="OBX",
                field_number=6,
                message="Invalid units format",
                details="Units should contain component separators",
                suggested_fix="Use format: IDENTIFIER^TEXT^CODING_SYSTEM"
            ))
    
    def _validate_procedure_code(self, code: str, line_num: int) -> None:
        """Validate procedure code format."""
        if '^' not in code:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.WARNING,
                segment_type="PR1",
                field_number=4,
                message="Invalid procedure code format",
                details="Procedure code should contain component separators",
                suggested_fix="Use format: IDENTIFIER^TEXT^CODING_SYSTEM"
            ))
    
    def _validate_cross_segments(self, segments: List[Dict[str, Any]]) -> None:
        """Validate relationships between segments."""
        # Check for required segments
        segment_types = [seg['segment_type'] for seg in segments]
        
        if 'MSH' not in segment_types:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                segment_type="MESSAGE",
                field_number=None,
                message="Missing required MSH segment",
                details="Every HL7 message must contain an MSH segment",
                suggested_fix="Add MSH segment to the message"
            ))
        
        if 'PID' not in segment_types:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                segment_type="MESSAGE",
                field_number=None,
                message="Missing required PID segment",
                details="Patient identification segment is required",
                suggested_fix="Add PID segment to the message"
            ))
    
    def _validate_business_rules(self, segments: List[Dict[str, Any]]) -> None:
        """Validate business rules and clinical logic."""
        # Extract patient data for business rule validation
        patient_data = self._extract_patient_data(segments)
        
        # Validate age-related business rules
        if patient_data.get('dob') and patient_data.get('gender'):
            self._validate_age_gender_consistency(patient_data)
        
        # Validate clinical data consistency
        self._validate_clinical_consistency(segments)
    
    def _extract_patient_data(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract patient data from segments for business rule validation."""
        patient_data = {}
        
        for segment in segments:
            if segment['segment_type'] == 'PID':
                fields = segment['fields']
                if len(fields) > 7:
                    patient_data['dob'] = fields[7]
                if len(fields) > 8:
                    patient_data['gender'] = fields[8]
                if len(fields) > 5:
                    patient_data['name'] = fields[5]
        
        return patient_data
    
    def _validate_age_gender_consistency(self, patient_data: Dict[str, Any]) -> None:
        """Validate age and gender consistency."""
        # This is a placeholder for more complex age/gender validation
        pass
    
    def _validate_clinical_consistency(self, segments: List[Dict[str, Any]]) -> None:
        """Validate clinical data consistency."""
        # This is a placeholder for clinical consistency validation
        pass
    
    def _generate_validation_summary(self) -> Dict[str, Any]:
        """Generate validation summary with statistics."""
        severity_counts = {
            ValidationSeverity.INFO: 0,
            ValidationSeverity.WARNING: 0,
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.CRITICAL: 0
        }
        
        for issue in self.issues:
            severity_counts[issue.severity] += 1
        
        total_issues = len(self.issues)
        has_critical = severity_counts[ValidationSeverity.CRITICAL] > 0
        has_errors = severity_counts[ValidationSeverity.ERROR] > 0
        has_warnings = severity_counts[ValidationSeverity.WARNING] > 0
        
        # Determine overall validation status
        if has_critical:
            status = "CRITICAL"
        elif has_errors:
            status = "ERROR"
        elif has_warnings:
            status = "WARNING"
        else:
            status = "VALID"
        
        return {
            'status': status,
            'total_issues': total_issues,
            'severity_counts': {severity.value: count for severity, count in severity_counts.items()},
            'issues': [
                {
                    'severity': issue.severity.value,
                    'segment_type': issue.segment_type,
                    'field_number': issue.field_number,
                    'message': issue.message,
                    'details': issue.details,
                    'suggested_fix': issue.suggested_fix
                }
                for issue in self.issues
            ],
            'validation_level': self.validation_level.value,
            'is_valid': status in ["VALID", "WARNING"],
            'needs_attention': has_critical or has_errors
        }


def validate_hl7_message(hl7_message: str, validation_level: ValidationLevel = ValidationLevel.STANDARD) -> Dict[str, Any]:
    """
    Convenience function to validate an HL7 message.
    
    Args:
        hl7_message: The HL7 message string to validate
        validation_level: The validation level to use
        
    Returns:
        Dictionary containing validation results
    """
    validator = HL7Validator(validation_level)
    return validator.validate_message(hl7_message)


if __name__ == "__main__":
    # Example usage
    sample_message = """MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|20240101120000||ADT^A01|123456|P|2.5.1
PID|1|12345|12345^^^SIMULATOR^MR~2222^^^SIMULATOR^SB|9999999999^^^USSSA^SS|SMITH^JOHN^M||19650312|M|||123 MAIN ST^^BOSTON^MA^02115||555-555-5555|||M|NON|12345|123-45-6789
PV1|1|I|MEDSURG^101^01||||10101^JONES^MARIA^L|||CARDIOLOGY||||||ADM|A0|||||||||||||||||||||||||20240101120000
DG1|1|ICD-10-CM|R07.9|CHEST PAIN, UNSPECIFIED|20240101120000|A
OBX|1|NM|8867-4^HEART RATE^LN||88|/min|60-100|N|||F
OBX|2|NM|8480-6^SYSTOLIC BP^LN||142|mmHg|90-130|H|||F"""
    
    result = validate_hl7_message(sample_message)
    print(f"Validation Status: {result['status']}")
    print(f"Total Issues: {result['total_issues']}")
    print(f"Severity Counts: {result['severity_counts']}")
    
    for issue in result['issues']:
        print(f"- {issue['severity']}: {issue['message']}")