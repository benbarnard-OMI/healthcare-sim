#!/usr/bin/env python3
"""
FHIR to HL7 v2.x Converter for Synthea Data

This module provides comprehensive conversion from FHIR R4 resources to HL7 v2.x messages,
specifically designed to work with Synthea-generated synthetic patient data.

The converter handles:
- Patient demographics and identification
- Medical conditions and diagnoses
- Laboratory results and observations
- Procedures and encounters
- Medications and treatments
"""

import json
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FHIRToHL7Converter:
    """Converts FHIR R4 resources to HL7 v2.x messages."""
    
    def __init__(self):
        """Initialize the converter with medical code mappings."""
        self.loinc_codes = self._load_loinc_codes()
        self.icd10_codes = self._load_icd10_codes()
        self.snomed_codes = self._load_snomed_codes()
        self.medication_codes = self._load_medication_codes()
        
    def _load_loinc_codes(self) -> Dict[str, str]:
        """Load LOINC codes for observations and lab values."""
        return {
            # Vital Signs
            "heart_rate": "8867-4",
            "systolic_bp": "8480-6",
            "diastolic_bp": "8462-4", 
            "temperature": "8310-5",
            "respiratory_rate": "9279-1",
            "oxygen_saturation": "2708-6",
            "height": "8302-2",
            "weight": "29463-7",
            "bmi": "39156-5",
            
            # Laboratory Values
            "glucose": "2345-7",
            "hemoglobin": "718-7",
            "hematocrit": "4544-3",
            "creatinine": "2160-0",
            "hemoglobin_a1c": "4548-4",
            "total_cholesterol": "2093-3",
            "hdl_cholesterol": "2085-9",
            "ldl_cholesterol": "2089-1",
            "triglycerides": "2571-8",
            "white_blood_cells": "770-8",
            "red_blood_cells": "789-8",
            "platelets": "777-3",
            "sodium": "2951-2",
            "potassium": "2823-3",
            "chloride": "2075-0",
            "co2": "2028-9",
            "bun": "3094-0",
            "alt": "1742-6",
            "ast": "1920-8",
            "alkaline_phosphatase": "6768-6",
            "bilirubin_total": "1975-2",
            "albumin": "1751-7",
            "protein_total": "2885-2",
            "calcium": "17861-6",
            "phosphorus": "2777-1",
            "magnesium": "19123-9",
            "iron": "2498-4",
            "ferritin": "2276-4",
            "vitamin_b12": "2132-9",
            "folate": "2284-8",
            "tsh": "3016-3",
            "t4_free": "3024-7",
            "t3_free": "3051-0",
            "psa": "2857-1",
            "troponin_i": "6598-7",
            "troponin_t": "6599-5",
            "ck_mb": "33747-0",
            "bnp": "33762-9",
            "d_dimer": "33762-9",
            "inr": "34714-6",
            "ptt": "33747-0",
            "pt": "5902-2",
            
            # Urinalysis
            "urine_glucose": "25428-4",
            "urine_protein": "25428-4",
            "urine_blood": "25428-4",
            "urine_ketones": "25428-4",
            "urine_ph": "25428-4",
            "urine_specific_gravity": "25428-4",
            
            # Microbiology
            "blood_culture": "600-7",
            "urine_culture": "600-7",
            "stool_culture": "600-7",
            "sputum_culture": "600-7",
            "wound_culture": "600-7"
        }
    
    def _load_icd10_codes(self) -> Dict[str, str]:
        """Load ICD-10-CM codes for diagnoses."""
        return {
            # Cardiovascular
            "hypertension": "I10",
            "essential_hypertension": "I10",
            "myocardial_infarction": "I21.9",
            "angina": "I20.9",
            "chest_pain": "R07.9",
            "heart_failure": "I50.9",
            "atrial_fibrillation": "I48.91",
            "stroke": "I63.9",
            "cerebral_infarction": "I63.9",
            "peripheral_vascular_disease": "I73.9",
            
            # Endocrine
            "diabetes_type1": "E10.9",
            "diabetes_type2": "E11.9",
            "diabetes_with_complications": "E11.9",
            "hyperlipidemia": "E78.5",
            "hypercholesterolemia": "E78.0",
            "hypothyroidism": "E03.9",
            "hyperthyroidism": "E05.9",
            "obesity": "E66.9",
            
            # Respiratory
            "pneumonia": "J18.9",
            "bronchitis": "J40",
            "asthma": "J45.9",
            "copd": "J44.1",
            "respiratory_failure": "J96.9",
            "pneumothorax": "J93.9",
            
            # Gastrointestinal
            "gastroenteritis": "K59.1",
            "peptic_ulcer": "K27.9",
            "gastroesophageal_reflux": "K21.9",
            "inflammatory_bowel_disease": "K50.9",
            "cirrhosis": "K74.60",
            "hepatitis": "K75.9",
            
            # Neurological
            "migraine": "G43.9",
            "epilepsy": "G40.9",
            "parkinsons_disease": "G20",
            "alzheimers_disease": "G30.9",
            "dementia": "F03.90",
            "seizure": "G40.9",
            
            # Musculoskeletal
            "osteoarthritis": "M19.9",
            "rheumatoid_arthritis": "M06.9",
            "fracture": "S72.001A",
            "hip_fracture": "S72.001A",
            "back_pain": "M54.9",
            "fibromyalgia": "M79.3",
            
            # Genitourinary
            "urinary_tract_infection": "N39.0",
            "kidney_disease": "N18.9",
            "chronic_kidney_disease": "N18.6",
            "kidney_stones": "N20.0",
            "prostate_cancer": "C61",
            "breast_cancer": "C50.9",
            
            # Mental Health
            "depression": "F32.9",
            "anxiety": "F41.9",
            "bipolar_disorder": "F31.9",
            "schizophrenia": "F20.9",
            "substance_abuse": "F19.10",
            
            # Infectious Diseases
            "influenza": "J11.1",
            "covid19": "U07.1",
            "sepsis": "A41.9",
            "cellulitis": "L03.90",
            "pneumonia_bacterial": "J15.9",
            
            # Pediatric
            "bronchiolitis": "J21.9",
            "otitis_media": "H66.9",
            "croup": "J05.0",
            "febrile_seizure": "R56.00",
            "asthma_pediatric": "J45.9"
        }
    
    def _load_snomed_codes(self) -> Dict[str, str]:
        """Load SNOMED CT codes for procedures and observations."""
        return {
            # Procedures
            "blood_draw": "182829008",
            "chest_xray": "399208008",
            "ekg": "164930006",
            "ct_scan": "399208008",
            "mri": "399208008",
            "ultrasound": "399208008",
            "surgery": "387713003",
            "suture": "387713003",
            "injection": "182829008",
            "catheterization": "182829008",
            
            # Observations
            "normal": "17621005",
            "abnormal": "263493007",
            "high": "75540009",
            "low": "255214003",
            "positive": "10828004",
            "negative": "260385009",
            "present": "52101004",
            "absent": "2667000"
        }
    
    def _load_medication_codes(self) -> Dict[str, str]:
        """Load medication codes and names."""
        return {
            # Cardiovascular
            "lisinopril": "314076",
            "metoprolol": "1190805",
            "amlodipine": "197361",
            "atorvastatin": "617312",
            "simvastatin": "36567",
            "warfarin": "106009",
            "aspirin": "1191",
            "clopidogrel": "1653963",
            
            # Diabetes
            "metformin": "860975",
            "insulin": "7980",
            "glipizide": "5487",
            "glyburide": "5489",
            "pioglitazone": "613008",
            
            # Respiratory
            "albuterol": "148",
            "prednisone": "7980",
            "fluticasone": "1653963",
            "montelukast": "1653963",
            
            # Pain Management
            "acetaminophen": "161",
            "ibuprofen": "3640",
            "morphine": "7980",
            "oxycodone": "7980",
            "tramadol": "7980",
            
            # Antibiotics
            "amoxicillin": "7980",
            "azithromycin": "7980",
            "ciprofloxacin": "7980",
            "doxycycline": "7980",
            "vancomycin": "7980"
        }
    
    def convert_bundle_to_hl7(self, fhir_bundle: Dict[str, Any]) -> List[str]:
        """
        Convert a FHIR Bundle containing multiple resources to HL7 messages.
        
        Args:
            fhir_bundle: FHIR Bundle resource
            
        Returns:
            List of HL7 v2.x message strings
        """
        hl7_messages = []
        
        # Extract Patient resources
        patients = []
        for entry in fhir_bundle.get("entry", []):
            resource = entry.get("resource", {})
            if resource.get("resourceType") == "Patient":
                patients.append(resource)
        
        # Convert each patient
        for patient in patients:
            try:
                hl7_message = self.convert_patient_to_hl7(patient, fhir_bundle)
                hl7_messages.append(hl7_message)
            except Exception as e:
                logger.error(f"Failed to convert patient {patient.get('id', 'unknown')}: {e}")
        
        return hl7_messages
    
    def convert_patient_to_hl7(self, 
                              fhir_patient: Dict[str, Any],
                              fhir_bundle: Optional[Dict[str, Any]] = None) -> str:
        """
        Convert a FHIR Patient resource to HL7 v2.x message.
        
        Args:
            fhir_patient: FHIR Patient resource
            fhir_bundle: Optional FHIR Bundle containing related resources
            
        Returns:
            HL7 v2.x message string
        """
        # Generate message header
        msh = self._create_msh_segment()
        
        # Generate patient identification
        pid = self._create_pid_segment(fhir_patient)
        
        # Generate patient visit
        pv1 = self._create_pv1_segment(fhir_patient)
        
        # Generate diagnoses from conditions
        dg1_segments = self._create_dg1_segments(fhir_patient, fhir_bundle)
        
        # Generate observations from lab results and vital signs
        obx_segments = self._create_obx_segments(fhir_patient, fhir_bundle)
        
        # Generate procedures
        pr1_segments = self._create_pr1_segments(fhir_patient, fhir_bundle)
        
        # Generate medications
        rxr_segments = self._create_rxr_segments(fhir_patient, fhir_bundle)
        
        # Combine all segments
        segments = [msh, pid, pv1] + dg1_segments + obx_segments + pr1_segments + rxr_segments
        
        return "\n".join(segments)
    
    def _create_msh_segment(self) -> str:
        """Create MSH (Message Header) segment."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        control_id = str(uuid.uuid4()).replace("-", "")[:10]
        
        return f"MSH|^~\\&|SYNTHEA|SYNTHEA|SIMULATOR|SIMULATOR|{timestamp}||ADT^A01|{control_id}|P|2.5.1"
    
    def _create_pid_segment(self, fhir_patient: Dict[str, Any]) -> str:
        """Create PID (Patient Identification) segment."""
        # Extract patient information
        patient_id = fhir_patient.get("id", "UNKNOWN")
        
        # Extract name
        names = fhir_patient.get("name", [])
        if names:
            name = names[0]
            family = name.get("family", "UNKNOWN")
            given = " ".join(name.get("given", ["UNKNOWN"]))
        else:
            family = "UNKNOWN"
            given = "UNKNOWN"
        
        # Extract birth date
        birth_date = fhir_patient.get("birthDate", "")
        if birth_date:
            birth_date = birth_date.replace("-", "")
        
        # Extract gender
        gender = fhir_patient.get("gender", "U").upper()
        
        # Extract address
        addresses = fhir_patient.get("address", [])
        if addresses:
            address = addresses[0]
            street = address.get("line", [""])[0]
            city = address.get("city", "")
            state = address.get("state", "")
            postal_code = address.get("postalCode", "")
            address_str = f"{street}^{city}^{state}^{postal_code}"
        else:
            address_str = "UNKNOWN"
        
        # Extract phone
        telecoms = fhir_patient.get("telecom", [])
        phone = ""
        for telecom in telecoms:
            if telecom.get("system") == "phone":
                phone = telecom.get("value", "")
                break
        
        # Generate SSN (synthetic)
        ssn = f"{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(1000, 9999)}"
        
        # Create PID segment
        return (f"PID|1|{patient_id}|{patient_id}^^^SIMULATOR^MR~{patient_id}^^^SIMULATOR^SB|"
                f"{patient_id}^^^USSSA^SS|{family}^{given}||{birth_date}|{gender}|||"
                f"{address_str}||{phone}|||{gender}|NON|{patient_id}|{ssn}")
    
    def _create_pv1_segment(self, fhir_patient: Dict[str, Any]) -> str:
        """Create PV1 (Patient Visit) segment."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Generate random provider info
        provider_id = str(uuid.uuid4()).replace("-", "")[:5]
        provider_names = ["SMITH", "JOHNSON", "WILLIAMS", "BROWN", "JONES", "GARCIA", "MILLER", "DAVIS"]
        provider_name = f"PROVIDER^{random.choice(provider_names)}"
        
        # Determine patient class based on age
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        if age < 18:
            patient_class = "P"  # Pediatric
        elif age > 65:
            patient_class = "E"  # Emergency
        else:
            patient_class = "I"  # Inpatient
        
        return (f"PV1|1|{patient_class}|MEDSURG^101^01||||{provider_id}^{provider_name}|||"
                f"GENERAL||||||ADM|A0|||||||||||||||||||||||||{timestamp}")
    
    def _create_dg1_segments(self, fhir_patient: Dict[str, Any], fhir_bundle: Optional[Dict[str, Any]]) -> List[str]:
        """Create DG1 (Diagnosis) segments from conditions."""
        segments = []
        
        # Look for Condition resources in the bundle
        if fhir_bundle:
            for entry in fhir_bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Condition":
                    # Extract condition information
                    code = resource.get("code", {})
                    coding = code.get("coding", [])
                    
                    if coding:
                        condition_code = coding[0].get("code", "")
                        condition_display = coding[0].get("display", "")
                        
                        # Map to ICD-10 if needed
                        icd10_code = self._map_to_icd10(condition_code, condition_display)
                        
                        if icd10_code:
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            segments.append(f"DG1|{len(segments) + 1}|ICD-10-CM|{icd10_code}|{condition_display}|{timestamp}|A")
        
        # If no conditions found, generate some based on demographics
        if not segments:
            age = self._calculate_age(fhir_patient.get("birthDate", ""))
            gender = fhir_patient.get("gender", "unknown")
            
            # Generate realistic diagnoses based on demographics
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            if age > 65:
                segments.append(f"DG1|1|ICD-10-CM|{self.icd10_codes['hypertension']}|ESSENTIAL (PRIMARY) HYPERTENSION|{timestamp}|A")
            if age > 50 and random.random() < 0.3:
                segments.append(f"DG1|{len(segments) + 1}|ICD-10-CM|{self.icd10_codes['diabetes_type2']}|TYPE 2 DIABETES MELLITUS WITHOUT COMPLICATIONS|{timestamp}|A")
            if age < 5 and random.random() < 0.4:
                segments.append(f"DG1|{len(segments) + 1}|ICD-10-CM|{self.icd10_codes['bronchiolitis']}|ACUTE BRONCHIOLITIS, UNSPECIFIED|{timestamp}|A")
        
        return segments
    
    def _create_obx_segments(self, fhir_patient: Dict[str, Any], fhir_bundle: Optional[Dict[str, Any]]) -> List[str]:
        """Create OBX (Observation Result) segments from observations."""
        segments = []
        
        # Look for Observation resources in the bundle
        if fhir_bundle:
            for entry in fhir_bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Observation":
                    obx_segment = self._convert_observation_to_obx(resource, len(segments) + 1)
                    if obx_segment:
                        segments.append(obx_segment)
        
        # If no observations found, generate realistic vital signs
        if not segments:
            segments = self._generate_realistic_vitals(fhir_patient)
        
        return segments
    
    def _convert_observation_to_obx(self, observation: Dict[str, Any], set_id: int) -> Optional[str]:
        """Convert a FHIR Observation to OBX segment."""
        try:
            # Extract observation code
            code = observation.get("code", {})
            coding = code.get("coding", [])
            
            if not coding:
                return None
            
            loinc_code = coding[0].get("code", "")
            display_name = coding[0].get("display", "")
            
            # Extract value
            value_quantity = observation.get("valueQuantity", {})
            value = value_quantity.get("value", "")
            unit = value_quantity.get("unit", "")
            
            # Extract reference range
            reference_range = observation.get("referenceRange", [])
            ref_range = ""
            if reference_range:
                low = reference_range[0].get("low", {}).get("value", "")
                high = reference_range[0].get("high", {}).get("value", "")
                if low and high:
                    ref_range = f"{low}-{high}"
            
            # Determine abnormal flag
            abnormal_flag = "N"
            if observation.get("interpretation"):
                interpretation = observation[0].get("coding", [{}])[0].get("code", "")
                if interpretation in ["H", "HH"]:
                    abnormal_flag = "H"
                elif interpretation in ["L", "LL"]:
                    abnormal_flag = "L"
            
            # Create OBX segment
            return (f"OBX|{set_id}|NM|{loinc_code}^{display_name}^LN||{value}|{unit}|{ref_range}|"
                    f"{abnormal_flag}|||F")
                    
        except Exception as e:
            logger.warning(f"Failed to convert observation: {e}")
            return None
    
    def _generate_realistic_vitals(self, fhir_patient: Dict[str, Any]) -> List[str]:
        """Generate realistic vital signs based on patient demographics."""
        segments = []
        age = self._calculate_age(fhir_patient.get("birthDate", ""))
        gender = fhir_patient.get("gender", "unknown")
        
        # Heart rate
        if age < 18:
            hr = random.randint(70, 120)
            ref_range = "70-120"
        else:
            hr = random.randint(60, 100)
            ref_range = "60-100"
        
        segments.append(f"OBX|1|NM|{self.loinc_codes['heart_rate']}^HEART RATE^LN||{hr}|/min|{ref_range}|N|||F")
        
        # Blood pressure
        if age < 18:
            sys_bp = random.randint(80, 110)
            dia_bp = random.randint(50, 70)
            sys_ref = "80-110"
            dia_ref = "50-70"
        else:
            sys_bp = random.randint(110, 140)
            dia_bp = random.randint(70, 90)
            sys_ref = "90-130"
            dia_ref = "60-80"
        
        segments.append(f"OBX|2|NM|{self.loinc_codes['systolic_bp']}^SYSTOLIC BP^LN||{sys_bp}|mmHg|{sys_ref}|N|||F")
        segments.append(f"OBX|3|NM|{self.loinc_codes['diastolic_bp']}^DIASTOLIC BP^LN||{dia_bp}|mmHg|{dia_ref}|N|||F")
        
        # Temperature
        temp = round(random.uniform(36.5, 37.5), 1)
        segments.append(f"OBX|4|NM|{self.loinc_codes['temperature']}^BODY TEMPERATURE^LN||{temp}|C|36.5-37.5|N|||F")
        
        # Respiratory rate
        if age < 18:
            rr = random.randint(20, 30)
            rr_ref = "20-30"
        else:
            rr = random.randint(12, 20)
            rr_ref = "12-20"
        
        segments.append(f"OBX|5|NM|{self.loinc_codes['respiratory_rate']}^RESPIRATORY RATE^LN||{rr}|/min|{rr_ref}|N|||F")
        
        # Oxygen saturation
        spo2 = random.randint(95, 100)
        segments.append(f"OBX|6|NM|{self.loinc_codes['oxygen_saturation']}^OXYGEN SATURATION^LN||{spo2}|%|95-100|N|||F")
        
        # Generate some lab values
        if age > 18:
            # Glucose
            glucose = random.randint(80, 120)
            if age > 50 and random.random() < 0.2:
                glucose = random.randint(140, 200)
            segments.append(f"OBX|7|NM|{self.loinc_codes['glucose']}^GLUCOSE^LN||{glucose}|mg/dL|70-110|N|||F")
            
            # Creatinine
            creatinine = round(random.uniform(0.6, 1.2), 1)
            segments.append(f"OBX|8|NM|{self.loinc_codes['creatinine']}^CREATININE^LN||{creatinine}|mg/dL|0.6-1.2|N|||F")
        
        return segments
    
    def _create_pr1_segments(self, fhir_patient: Dict[str, Any], fhir_bundle: Optional[Dict[str, Any]]) -> List[str]:
        """Create PR1 (Procedures) segments from procedures."""
        segments = []
        
        # Look for Procedure resources in the bundle
        if fhir_bundle:
            for entry in fhir_bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "Procedure":
                    pr1_segment = self._convert_procedure_to_pr1(resource, len(segments) + 1)
                    if pr1_segment:
                        segments.append(pr1_segment)
        
        return segments
    
    def _convert_procedure_to_pr1(self, procedure: Dict[str, Any], set_id: int) -> Optional[str]:
        """Convert a FHIR Procedure to PR1 segment."""
        try:
            # Extract procedure code
            code = procedure.get("code", {})
            coding = code.get("coding", [])
            
            if not coding:
                return None
            
            procedure_code = coding[0].get("code", "")
            procedure_display = coding[0].get("display", "")
            
            # Extract date
            performed_date = procedure.get("performedDateTime", "")
            if performed_date:
                performed_date = performed_date.replace("-", "").replace("T", "").replace(":", "")[:14]
            
            # Generate provider info
            provider_id = str(uuid.uuid4()).replace("-", "")[:5]
            provider_name = f"PROVIDER^{random.choice(['SMITH', 'JOHNSON', 'WILLIAMS'])}"
            
            # Create PR1 segment
            return (f"PR1|{set_id}||{procedure_code}^{procedure_display}^ICD10|{performed_date}|"
                    f"ROUTINE|||01|{provider_id}^{provider_name}")
                    
        except Exception as e:
            logger.warning(f"Failed to convert procedure: {e}")
            return None
    
    def _create_rxr_segments(self, fhir_patient: Dict[str, Any], fhir_bundle: Optional[Dict[str, Any]]) -> List[str]:
        """Create RXR (Pharmacy/Treatment Route) segments from medications."""
        segments = []
        
        # Look for MedicationStatement resources in the bundle
        if fhir_bundle:
            for entry in fhir_bundle.get("entry", []):
                resource = entry.get("resource", {})
                if resource.get("resourceType") == "MedicationStatement":
                    rxr_segment = self._convert_medication_to_rxr(resource, len(segments) + 1)
                    if rxr_segment:
                        segments.append(rxr_segment)
        
        return segments
    
    def _convert_medication_to_rxr(self, medication: Dict[str, Any], set_id: int) -> Optional[str]:
        """Convert a FHIR MedicationStatement to RXR segment."""
        try:
            # Extract medication information
            medication_code = medication.get("medicationCodeableConcept", {})
            coding = medication_code.get("coding", [])
            
            if not coding:
                return None
            
            med_code = coding[0].get("code", "")
            med_display = coding[0].get("display", "")
            
            # Extract dosage
            dosage = medication.get("dosage", [])
            if dosage:
                dose = dosage[0].get("doseQuantity", {})
                dose_value = dose.get("value", "")
                dose_unit = dose.get("unit", "")
            else:
                dose_value = ""
                dose_unit = ""
            
            # Create RXR segment
            return (f"RXR|{set_id}|{med_code}^{med_display}^NDC|{dose_value}|{dose_unit}|"
                    f"ORAL|||F")
                    
        except Exception as e:
            logger.warning(f"Failed to convert medication: {e}")
            return None
    
    def _map_to_icd10(self, code: str, display: str) -> Optional[str]:
        """Map a condition code to ICD-10-CM."""
        # Simple mapping based on common patterns
        display_lower = display.lower()
        
        if "hypertension" in display_lower or "high blood pressure" in display_lower:
            return self.icd10_codes["hypertension"]
        elif "diabetes" in display_lower:
            return self.icd10_codes["diabetes_type2"]
        elif "chest pain" in display_lower:
            return self.icd10_codes["chest_pain"]
        elif "stroke" in display_lower or "cerebral infarction" in display_lower:
            return self.icd10_codes["stroke"]
        elif "pneumonia" in display_lower:
            return self.icd10_codes["pneumonia"]
        elif "asthma" in display_lower:
            return self.icd10_codes["asthma"]
        elif "depression" in display_lower:
            return self.icd10_codes["depression"]
        elif "anxiety" in display_lower:
            return self.icd10_codes["anxiety"]
        
        return None
    
    def _calculate_age(self, birth_date: str) -> int:
        """Calculate age from birth date."""
        if not birth_date:
            return 30  # Default age
        
        try:
            birth = datetime.strptime(birth_date, "%Y-%m-%d")
            today = datetime.now()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except:
            return 30


def main():
    """Main function for command-line usage."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert FHIR data to HL7 v2.x")
    parser.add_argument("--input", "-i", required=True, help="Input FHIR JSON file")
    parser.add_argument("--output", "-o", help="Output HL7 file (default: input.hl7)")
    parser.add_argument("--format", "-f", choices=["single", "bundle"], default="bundle", 
                       help="Input format: single Patient resource or Bundle")
    
    args = parser.parse_args()
    
    # Load FHIR data
    with open(args.input, "r") as f:
        fhir_data = json.load(f)
    
    # Convert to HL7
    converter = FHIRToHL7Converter()
    
    if args.format == "bundle":
        hl7_messages = converter.convert_bundle_to_hl7(fhir_data)
    else:
        hl7_message = converter.convert_patient_to_hl7(fhir_data)
        hl7_messages = [hl7_message]
    
    # Save output
    output_file = args.output or args.input.replace(".json", ".hl7")
    
    if len(hl7_messages) == 1:
        with open(output_file, "w") as f:
            f.write(hl7_messages[0])
        print(f"Converted 1 patient to HL7: {output_file}")
    else:
        # Save multiple messages to separate files
        base_name = output_file.replace(".hl7", "")
        for i, message in enumerate(hl7_messages):
            filename = f"{base_name}_{i+1}.hl7"
            with open(filename, "w") as f:
                f.write(message)
        print(f"Converted {len(hl7_messages)} patients to HL7 files")


if __name__ == "__main__":
    main()