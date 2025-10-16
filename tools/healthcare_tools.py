from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from hl7_validator import HL7Validator, ValidationLevel, validate_hl7_message
    from fhir_to_hl7_converter import FHIRToHL7Converter
    HL7_FHIR_AVAILABLE = True
except ImportError as e:
    print(f"HL7/FHIR modules not available: {e}")
    HL7_FHIR_AVAILABLE = False


class ClinicalGuidelinesInput(BaseModel):
    """Input schema for clinical guidelines tool."""
    condition: str = Field(..., description="The medical condition to get guidelines for")


class MedicationInteractionInput(BaseModel):
    """Input schema for medication interaction tool.""" 
    medications: str = Field(..., description="Comma-separated list of medications to check")


class AppointmentSchedulerInput(BaseModel):
    """Input schema for appointment scheduler tool."""
    appointment_type: str = Field(..., description="Type of appointment (e.g., follow-up, imaging)")
    duration_minutes: int = Field(default=30, description="Duration of appointment in minutes")
    preferred_date: Optional[str] = Field(default=None, description="Preferred date for appointment (YYYY-MM-DD)")
    patient_priority: str = Field(default="routine", description="Priority level (urgent, high, routine, low)")


class HL7ValidationInput(BaseModel):
    """Input schema for HL7 validation tool."""
    hl7_message: str = Field(..., description="The HL7 message to validate")
    validation_level: str = Field(default="standard", description="Validation level: basic, standard, strict, compliance")


class FHIRGenerationInput(BaseModel):
    """Input schema for FHIR generation tool."""
    patient_data: Dict[str, Any] = Field(..., description="Patient data to generate FHIR from")
    output_format: str = Field(default="bundle", description="Output format: bundle, individual_resources, json")
    generate_hl7: bool = Field(default=False, description="Whether to also generate HL7 message from FHIR")


class ClinicalGuidelinesTool(BaseTool):
    """Tool that provides access to clinical guidelines."""
    name: str = "Clinical Guidelines Search"
    description: str = "Search for evidence-based clinical guidelines for specific conditions"
    args_schema: type[BaseModel] = ClinicalGuidelinesInput

    def _run(self, condition: str) -> str:
        """
        Get evidence-based clinical guidelines for a specific condition.
        Args:
            condition: The medical condition to get guidelines for
        Returns:
            String containing clinical guidelines for the condition
        """
        # Comprehensive evidence-based guidelines database
        guidelines_db = {
            "chest pain": """
                CHEST PAIN CLINICAL GUIDELINES (AHA/ACC 2021):
                1. Assessment: Evaluate vital signs, conduct ECG within 10 minutes of arrival
                2. Risk Stratification: Use HEART score for risk assessment (0-3: low risk, 4-6: moderate, 7-10: high)
                3. Diagnostics: Serial troponin at 0 and 3 hours; consider high-sensitivity troponin
                4. Imaging: Consider chest X-ray and CT coronary angiography for intermediate risk
                5. Treatment: Aspirin 325mg immediately for suspected ACS, dual antiplatelet if STEMI
                6. Disposition: High-risk patients require admission; low-risk with negative workup may be discharged
                7. Follow-up: Stress testing within 72 hours for low-risk patients
            """,
            "hypertension": """
                HYPERTENSION CLINICAL GUIDELINES (AHA/ACC 2017):
                1. Diagnosis: BP ≥130/80 mm Hg on two separate visits, use proper technique
                2. Classification: Stage 1 (130-139/80-89), Stage 2 (≥140/90), Crisis (≥180/120)
                3. Non-pharmacological: DASH diet, <2300mg sodium, weight loss if BMI >25, exercise 90-150min/week
                4. Pharmacological first-line: ACE inhibitors, ARBs, CCBs, or thiazide diuretics
                5. Target BP: <130/80 mm Hg for most adults, <130/80 for diabetes/CKD
                6. Follow-up: Every 3-6 months until BP controlled, then every 6-12 months
                7. Monitoring: Home BP monitoring, assess for target organ damage
            """,
            "diabetes mellitus": """
                DIABETES MELLITUS CLINICAL GUIDELINES (ADA 2024):
                1. Screening: Every 3 years in adults ≥35, or earlier with risk factors (BMI ≥25, family history)
                2. Diagnosis: HbA1c ≥6.5%, FPG ≥126 mg/dL, or 2-hr PG ≥200 mg/dL during OGTT, or random glucose ≥200 with symptoms
                3. Management: Target HbA1c <7% for most adults, individualized based on life expectancy/comorbidities
                4. Pharmacotherapy: Metformin as first-line therapy, add SGLT2i/GLP-1 RA for CV/renal protection
                5. Monitoring: HbA1c every 3-6 months, annual lipid panel, microalbumin, dilated eye exam
                6. Complications screening: Diabetic retinopathy, nephropathy, neuropathy, cardiovascular disease
                7. Blood pressure target: <130/80 mmHg, lipid management with statin therapy
            """,
            "bronchiolitis": """
                BRONCHIOLITIS CLINICAL GUIDELINES (AAP 2014):
                1. Definition: Viral lower respiratory tract infection in children <24 months
                2. Diagnosis: Clinical diagnosis based on history and physical exam
                3. Assessment: Evaluate for hypoxia (SpO2 <90%), dehydration, apnea in infants <6 months
                4. Treatment: Supportive care only - adequate hydration, nasal suctioning
                5. NOT recommended: Antibiotics, bronchodilators, corticosteroids, chest physiotherapy
                6. Hospitalization criteria: SpO2 <90%, poor feeding, dehydration, apnea, age <3 months with fever
                7. Discharge criteria: SpO2 >90% on room air, adequate oral intake, respiratory distress improved
            """,
            "hip replacement": """
                HIP REPLACEMENT CLINICAL GUIDELINES (AAOS 2019):
                1. Indications: Severe hip arthritis with functional limitation despite conservative treatment
                2. Preoperative: Optimize medical conditions, DVT prophylaxis, antibiotic prophylaxis
                3. Surgical approach: Anterior, posterior, or lateral approach based on surgeon preference
                4. Postoperative: Early mobilization within 24 hours, DVT prophylaxis for 10-35 days
                5. Rehabilitation: Physical therapy starting day 1, weight bearing as tolerated
                6. Complications monitoring: Infection, dislocation, DVT/PE, leg length discrepancy
                7. Follow-up: 2 weeks, 6 weeks, 3 months, then annually with radiographs
            """,
            "stroke": """
                ACUTE STROKE CLINICAL GUIDELINES (AHA/ASA 2019):
                1. Recognition: Use FAST or BE-FAST assessment tools
                2. Emergency care: Door-to-needle time <60 minutes for tPA, door-to-groin <90 minutes for thrombectomy
                3. Imaging: Non-contrast CT immediately, consider CT angiography for large vessel occlusion
                4. Treatment: IV tPA within 4.5 hours if eligible, mechanical thrombectomy up to 24 hours in select cases
                5. Blood pressure: Permissive hypertension unless >185/110 and tPA candidate
                6. Secondary prevention: Antiplatelet therapy, statin, BP control, diabetes management
                7. Rehabilitation: Early mobilization, swallow evaluation, occupational/physical/speech therapy
            """,
            "pneumonia": """
                PNEUMONIA CLINICAL GUIDELINES (IDSA/ATS 2019):
                1. Classification: Community-acquired (CAP), hospital-acquired (HAP), ventilator-associated (VAP)
                2. Severity assessment: Use CURB-65 or PSI score for CAP
                3. Diagnostic workup: Chest X-ray, consider CT if complicated; blood cultures if severe
                4. Treatment CAP: Amoxicillin or doxycycline for outpatient; azithromycin + ceftriaxone for inpatient
                5. Duration: 5-7 days for most CAP cases, longer if complications or slow response
                6. Monitoring: Clinical improvement expected within 48-72 hours
                7. Prevention: Pneumococcal and influenza vaccination per CDC guidelines
            """,
            "heart failure": """
                HEART FAILURE CLINICAL GUIDELINES (AHA/ACC/HFSA 2022):
                1. Classification: Stage A-D, NYHA Class I-IV functional assessment
                2. Diagnosis: BNP >100 pg/mL or NT-proBNP >300 pg/mL, echocardiogram for EF assessment
                3. HFrEF treatment: ACE-I/ARB/ARNI, beta-blocker, MRA, SGLT2i (quadruple therapy)
                4. HFpEF treatment: Diuretics for volume overload, treat comorbidities, SGLT2i if diabetes
                5. Monitoring: Daily weights, sodium restriction <3g/day, fluid restriction if hyponatremic
                6. Device therapy: ICD for primary prevention if EF ≤35%, CRT if QRS ≥150ms
                7. Follow-up: Within 7-14 days of discharge, then every 3-6 months when stable
            """,
            "asthma": """
                ASTHMA CLINICAL GUIDELINES (GINA 2023):
                1. Diagnosis: Variable respiratory symptoms + variable airflow limitation (FEV1 <80% predicted)
                2. Assessment: Symptom control (ACT/ACQ), risk factors for exacerbations
                3. Step therapy: Step 1-5 based on control, always include ICS except mild intermittent
                4. Preferred controller: ICS-formoterol as reliever and controller therapy
                5. Exacerbation treatment: High-dose SABA, systemic corticosteroids, oxygen if needed
                6. Monitoring: Peak flow monitoring, inhaler technique assessment, trigger avoidance
                7. Follow-up: Every 3-6 months, adjust therapy based on control and future risk
            """,
            "copd": """
                COPD CLINICAL GUIDELINES (GOLD 2023):
                1. Diagnosis: Persistent respiratory symptoms + airflow limitation (post-BD FEV1/FVC <0.70)
                2. Severity: GOLD 1-4 based on FEV1, symptom assessment with mMRC or CAT
                3. Pharmacotherapy: Bronchodilator as foundation, escalate based on symptoms/exacerbations
                4. LABA/LAMA combination for Group B, Triple therapy (ICS/LABA/LAMA) for frequent exacerbators
                5. Non-pharmacological: Smoking cessation, pulmonary rehabilitation, vaccinations
                6. Oxygen therapy: Long-term oxygen if PaO2 ≤55 mmHg or ≤59 mmHg with cor pulmonale
                7. Follow-up: Regular assessment of symptoms, exacerbation frequency, and inhaler technique
            """
        }

        # Enhanced search with fuzzy matching and aliases
        condition_lower = condition.lower().strip()
        
        # Direct match
        if condition_lower in guidelines_db:
            return guidelines_db[condition_lower]
        
        # Partial matching with priority scoring
        matches = []
        for key, guidelines in guidelines_db.items():
            score = 0
            key_words = key.split()
            condition_words = condition_lower.split()
            
            # Exact substring match gets highest score
            if condition_lower in key or key in condition_lower:
                score += 10
            
            # Word-by-word matching
            for word in condition_words:
                if word in key:
                    score += 5
            
            # Individual word matches
            for cond_word in condition_words:
                for key_word in key_words:
                    if cond_word == key_word:
                        score += 3
                    elif cond_word in key_word or key_word in cond_word:
                        score += 1
            
            if score > 0:
                matches.append((score, key, guidelines))
        
        # Return the best match if we have one
        if matches:
            matches.sort(reverse=True, key=lambda x: x[0])
            best_match = matches[0]
            return f"CLOSEST MATCH FOR '{condition}' -> {best_match[1].upper()}:\n{best_match[2]}"
        
        # Common aliases and alternative names
        aliases = {
            "mi": "chest pain",
            "myocardial infarction": "chest pain", 
            "heart attack": "chest pain",
            "acute coronary syndrome": "chest pain",
            "acs": "chest pain",
            "diabetes": "diabetes mellitus",
            "dm": "diabetes mellitus",
            "type 2 diabetes": "diabetes mellitus",
            "t2dm": "diabetes mellitus",
            "high blood pressure": "hypertension",
            "htn": "hypertension",
            "rsv": "bronchiolitis",
            "respiratory syncytial virus": "bronchiolitis",
            "total hip replacement": "hip replacement",
            "thr": "hip replacement",
            "total hip arthroplasty": "hip replacement",
            "tha": "hip replacement",
            "cva": "stroke",
            "cerebrovascular accident": "stroke",
            "acute stroke": "stroke",
            "pneumonia": "pneumonia",
            "cap": "pneumonia",
            "community acquired pneumonia": "pneumonia",
            "chf": "heart failure",
            "congestive heart failure": "heart failure",
            "cardiac failure": "heart failure",
            "chronic obstructive pulmonary disease": "copd"
        }
        
        if condition_lower in aliases:
            matched_condition = aliases[condition_lower]
            return f"MATCHED ALIAS '{condition}' -> {matched_condition.upper()}:\n{guidelines_db[matched_condition]}"
        
        return f"""No specific guidelines found for '{condition}'. 

Available conditions: {', '.join(sorted(guidelines_db.keys()))}

Recommend consulting latest medical literature or professional guidelines from:
- American Heart Association (AHA)
- American College of Cardiology (ACC) 
- American Diabetes Association (ADA)
- Infectious Diseases Society of America (IDSA)
- American Academy of Pediatrics (AAP)"""


class MedicationInteractionTool(BaseTool):
    """Tool for checking medication interactions."""
    name: str = "Medication Interaction Checker"
    description: str = "Check for potential interactions between multiple medications"
    args_schema: type[BaseModel] = MedicationInteractionInput

    def _run(self, medications: str) -> str:
        """
        Check for potential interactions between multiple medications.
        Args:
            medications: Comma-separated list of medications to check
        Returns:
            String describing potential interactions with severity levels
        """
        if not medications or not medications.strip():
            return "No medications provided for interaction checking."
        
        # Parse and normalize medication names
        med_list = []
        for med in medications.split(","):
            med_clean = med.strip().lower()
            if med_clean:
                # Handle common abbreviations and brand names
                med_normalized = self._normalize_drug_name(med_clean)
                med_list.append(med_normalized)
        
        if len(med_list) < 2:
            return "At least two medications required for interaction checking."
        
        # Comprehensive interaction database with severity levels
        known_interactions = {
            # SEVERE INTERACTIONS - Avoid combination
            ("aspirin", "warfarin"): {
                "severity": "SEVERE", 
                "description": "Major bleeding risk. Concurrent use significantly increases bleeding risk.",
                "recommendation": "Avoid combination. If necessary, monitor INR closely and consider PPI for GI protection."
            },
            ("amiodarone", "simvastatin"): {
                "severity": "SEVERE",
                "description": "Increased risk of myopathy/rhabdomyolysis. Amiodarone inhibits CYP3A4.",
                "recommendation": "Limit simvastatin to 20mg daily or use alternative statin (atorvastatin, rosuvastatin)."
            },
            ("fluoxetine", "tramadol"): {
                "severity": "SEVERE",
                "description": "Increased risk of serotonin syndrome. Both affect serotonin.",
                "recommendation": "Avoid combination. Use alternative analgesic or antidepressant."
            },
            ("warfarin", "fluconazole"): {
                "severity": "SEVERE",
                "description": "Fluconazole significantly increases warfarin effect via CYP2C9 inhibition.",
                "recommendation": "Reduce warfarin dose by 25-50%. Monitor INR every 2-3 days."
            },
            ("digoxin", "amiodarone"): {
                "severity": "SEVERE", 
                "description": "Amiodarone increases digoxin levels by 50-100%.",
                "recommendation": "Reduce digoxin dose by 50%. Monitor digoxin levels closely."
            },
            ("lithium", "lisinopril"): {
                "severity": "SEVERE",
                "description": "ACE inhibitors increase lithium levels and toxicity risk.",
                "recommendation": "Monitor lithium levels weekly initially, then monthly. Consider alternative BP medication."
            },
            ("metformin", "furosemide"): {
                "severity": "SEVERE",
                "description": "Loop diuretics can cause dehydration increasing metformin toxicity risk.",
                "recommendation": "Monitor renal function closely. Hold metformin if dehydrated."
            },
            
            # MODERATE INTERACTIONS - Monitor closely
            ("lisinopril", "potassium"): {
                "severity": "MODERATE",
                "description": "ACE inhibitors can cause hyperkalemia when combined with potassium supplements.",
                "recommendation": "Monitor potassium levels every 1-2 weeks initially. Target K+ 3.5-5.0 mEq/L."
            },
            ("ciprofloxacin", "theophylline"): {
                "severity": "MODERATE", 
                "description": "Ciprofloxacin inhibits theophylline metabolism, increasing levels.",
                "recommendation": "Reduce theophylline dose by 50%. Monitor levels and clinical response."
            },
            ("atorvastatin", "amlodipine"): {
                "severity": "MODERATE",
                "description": "Amlodipine moderately increases atorvastatin exposure.",
                "recommendation": "Consider atorvastatin dose reduction if myopathy symptoms occur."
            },
            ("metoprolol", "verapamil"): {
                "severity": "MODERATE",
                "description": "Both drugs depress AV conduction; additive effects on heart rate/BP.",
                "recommendation": "Monitor heart rate and blood pressure closely. Consider dose adjustments."
            },
            ("omeprazole", "clopidogrel"): {
                "severity": "MODERATE",
                "description": "PPI may reduce clopidogrel effectiveness via CYP2C19 inhibition.",
                "recommendation": "Use pantoprazole instead, or separate dosing by 12+ hours."
            },
            ("aspirin", "ibuprofen"): {
                "severity": "MODERATE",
                "description": "NSAIDs may interfere with aspirin's cardioprotective effects.",
                "recommendation": "Take aspirin 2+ hours before ibuprofen, or use acetaminophen instead."
            },
            ("levothyroxine", "calcium"): {
                "severity": "MODERATE",
                "description": "Calcium reduces levothyroxine absorption by forming insoluble complexes.",
                "recommendation": "Separate administration by at least 4 hours."
            },
            ("levothyroxine", "iron"): {
                "severity": "MODERATE",
                "description": "Iron reduces levothyroxine absorption.",
                "recommendation": "Separate administration by at least 4 hours."
            },
            
            # MILD INTERACTIONS - Monitor or separate dosing
            ("metformin", "nifedipine"): {
                "severity": "MINOR",
                "description": "Nifedipine may slightly increase metformin absorption.",
                "recommendation": "Monitor blood glucose. Usually not clinically significant."
            },
            ("aspirin", "acetaminophen"): {
                "severity": "MINOR",
                "description": "Generally safe combination for most patients.",
                "recommendation": "Monitor for excessive analgesic use. Consider GI protection if high-dose aspirin."
            },
            ("lisinopril", "metformin"): {
                "severity": "MINOR",
                "description": "Generally safe combination. Monitor renal function.",
                "recommendation": "Check creatinine annually. Hold metformin if acute kidney injury."
            }
        }
        
        # Additional interaction patterns for drug classes
        interactions = []
        severity_counts = {"SEVERE": 0, "MODERATE": 0, "MINOR": 0}
        
        # Check all medication pairs
        for i, med1 in enumerate(med_list):
            for med2 in med_list[i+1:]:
                interaction = self._check_drug_pair(med1, med2, known_interactions)
                if interaction:
                    interactions.append(interaction)
                    severity_counts[interaction["severity"]] += 1
        
        # Format results
        if not interactions:
            return f"No known interactions found between: {', '.join([med.title() for med in med_list])}"
        
        result = "MEDICATION INTERACTION ANALYSIS:\n"
        result += f"Medications: {', '.join([med.title() for med in med_list])}\n\n"
        
        # Summary
        total_interactions = len(interactions)
        result += f"SUMMARY: {total_interactions} interaction(s) detected\n"
        if severity_counts["SEVERE"] > 0:
            result += f"⚠️  SEVERE: {severity_counts['SEVERE']} (requires immediate attention)\n"
        if severity_counts["MODERATE"] > 0:
            result += f"⚠️  MODERATE: {severity_counts['MODERATE']} (monitor closely)\n"
        if severity_counts["MINOR"] > 0:
            result += f"ℹ️  MINOR: {severity_counts['MINOR']} (awareness needed)\n"
        result += "\n"
        
        # Detailed interactions
        result += "DETAILED INTERACTIONS:\n"
        for i, interaction in enumerate(interactions, 1):
            result += f"{i}. {interaction['drugs']} [{interaction['severity']}]\n"
            result += f"   Description: {interaction['description']}\n"
            result += f"   Recommendation: {interaction['recommendation']}\n\n"
        
        # General recommendations
        if severity_counts["SEVERE"] > 0:
            result += "🚨 URGENT: Severe interactions detected. Consider alternative medications or intensive monitoring.\n"
        
        result += "\nAlways consult with pharmacist or prescriber before making medication changes."
        
        return result
    
    def _normalize_drug_name(self, drug_name: str) -> str:
        """Normalize drug names to handle common variations and brand names."""
        # Common brand name to generic mappings
        brand_to_generic = {
            # Cardiovascular
            "lipitor": "atorvastatin",
            "zocor": "simvastatin", 
            "prinivil": "lisinopril",
            "zestril": "lisinopril",
            "norvasc": "amlodipine",
            "lopressor": "metoprolol",
            "toprol": "metoprolol",
            "cordarone": "amiodarone",
            "pacerone": "amiodarone",
            "lanoxin": "digoxin",
            "coumadin": "warfarin",
            "jantoven": "warfarin",
            "plavix": "clopidogrel",
            
            # Endocrine
            "glucophage": "metformin",
            "synthroid": "levothyroxine",
            "levoxyl": "levothyroxine",
            
            # Psychiatric
            "prozac": "fluoxetine",
            "lithobid": "lithium",
            
            # Antibiotics/Antifungals
            "cipro": "ciprofloxacin",
            "diflucan": "fluconazole",
            
            # Pain/Anti-inflammatory
            "tylenol": "acetaminophen",
            "advil": "ibuprofen",
            "motrin": "ibuprofen",
            "ultram": "tramadol",
            
            # GI
            "prilosec": "omeprazole",
            "lasix": "furosemide",
            
            # Respiratory
            "theo-dur": "theophylline"
        }
        
        drug_normalized = drug_name.strip().lower()
        
        # Remove common dosage information
        drug_normalized = drug_normalized.split()[0]  # Take first word
        
        # Check for brand name mapping
        if drug_normalized in brand_to_generic:
            return brand_to_generic[drug_normalized]
        
        return drug_normalized
    
    def _check_drug_pair(self, drug1: str, drug2: str, interactions_db: dict) -> dict:
        """Check a specific drug pair for interactions."""
        # Try both orders
        if (drug1, drug2) in interactions_db:
            interaction = interactions_db[(drug1, drug2)]
            return {
                "drugs": f"{drug1.title()} + {drug2.title()}",
                "severity": interaction["severity"],
                "description": interaction["description"],
                "recommendation": interaction["recommendation"]
            }
        elif (drug2, drug1) in interactions_db:
            interaction = interactions_db[(drug2, drug1)]
            return {
                "drugs": f"{drug1.title()} + {drug2.title()}",
                "severity": interaction["severity"],
                "description": interaction["description"],
                "recommendation": interaction["recommendation"]
            }
        
        return None


class AppointmentSchedulerTool(BaseTool):
    """Tool for scheduling patient appointments."""
    name: str = "Appointment Scheduler"
    description: str = "Schedule patient appointments for various medical services"
    args_schema: type[BaseModel] = AppointmentSchedulerInput

    def _run(
        self, 
        appointment_type: str, 
        duration_minutes: int = 30,
        preferred_date: Optional[str] = None,
        patient_priority: str = "routine"
    ) -> str:
        """
        Schedule a patient appointment with enhanced resource management.
        Args:
            appointment_type: Type of appointment (e.g., follow-up, imaging, specialist)
            duration_minutes: Duration of appointment in minutes
            preferred_date: Preferred date for appointment (YYYY-MM-DD)
            patient_priority: Priority level (urgent, high, routine, low)
        Returns:
            String with detailed appointment information
        """
        # Enhanced appointment type configurations
        appointment_types = {
            "follow-up": {
                "providers": ["Dr. Smith (Internal Medicine)", "Dr. Johnson (Family Medicine)", "Dr. Brown (Internal Medicine)"],
                "lead_time_days": 7,
                "max_duration": 60,
                "time_slots": ["09:00", "09:30", "10:00", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "15:30", "16:00"],
                "location": "Primary Care Clinic"
            },
            "imaging": {
                "providers": ["Radiology Dept - CT Scanner", "Radiology Dept - MRI Suite", "Radiology Dept - X-Ray"],
                "lead_time_days": 5,
                "max_duration": 120,
                "time_slots": ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"],
                "location": "Diagnostic Imaging Center"
            },
            "lab": {
                "providers": ["Lab Services - Station A", "Lab Services - Station B"],
                "lead_time_days": 2,
                "max_duration": 30,
                "time_slots": ["07:00", "07:30", "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00"],
                "location": "Laboratory Services"
            },
            "specialist": {
                "providers": ["Dr. Patel (Cardiology)", "Dr. Chen (Endocrinology)", "Dr. Rodriguez (Pulmonology)", "Dr. Kim (Neurology)"],
                "lead_time_days": 14,
                "max_duration": 90,
                "time_slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"],
                "location": "Specialty Care Center"
            },
            "physical therapy": {
                "providers": ["PT Department - Room 1", "PT Department - Room 2", "PT Department - Pool Therapy"],
                "lead_time_days": 3,
                "max_duration": 60,
                "time_slots": ["08:00", "09:00", "10:00", "11:00", "13:00", "14:00", "15:00", "16:00"],
                "location": "Rehabilitation Services"
            },
            "surgery": {
                "providers": ["OR Suite 1", "OR Suite 2", "OR Suite 3"],
                "lead_time_days": 21,
                "max_duration": 240,
                "time_slots": ["07:00", "09:00", "13:00"],
                "location": "Operating Room Complex"
            },
            "emergency": {
                "providers": ["Emergency Department"],
                "lead_time_days": 0,
                "max_duration": 120,
                "time_slots": ["24/7"],
                "location": "Emergency Department"
            },
            "telemedicine": {
                "providers": ["Virtual Care Platform A", "Virtual Care Platform B"],
                "lead_time_days": 3,
                "max_duration": 45,
                "time_slots": ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00", "18:00"],
                "location": "Virtual/Remote"
            }
        }
        
        # Priority adjustments
        priority_adjustments = {
            "urgent": {"lead_time_multiplier": 0.1, "priority_score": 10},
            "high": {"lead_time_multiplier": 0.3, "priority_score": 7},
            "routine": {"lead_time_multiplier": 1.0, "priority_score": 5},
            "low": {"lead_time_multiplier": 1.5, "priority_score": 2}
        }
        
        # Find matching appointment type (enhanced matching)
        matched_type = self._find_appointment_type(appointment_type.lower(), appointment_types)
        
        if not matched_type:
            available_types = ", ".join(sorted(appointment_types.keys()))
            return f"""
            APPOINTMENT SCHEDULING FAILED
            Reason: Unknown appointment type '{appointment_type}'
            Available types: {available_types}
            Please specify one of the available appointment types.
            """
        
        apt_info = appointment_types[matched_type]
        priority_info = priority_adjustments.get(patient_priority.lower(), priority_adjustments["routine"])
        
        # Validate duration
        if duration_minutes > apt_info["max_duration"]:
            return f"""
            APPOINTMENT SCHEDULING FAILED
            Reason: Requested duration ({duration_minutes} min) exceeds maximum for {matched_type} ({apt_info['max_duration']} min)
            Please reduce duration or split into multiple appointments.
            """
        
        # Calculate appointment date with priority adjustments
        base_lead_time = int(apt_info["lead_time_days"] * priority_info["lead_time_multiplier"])
        
        # Handle date calculation
        if preferred_date:
            try:
                preferred_dt = datetime.strptime(preferred_date, "%Y-%m-%d")
                earliest_date = datetime.now() + timedelta(days=base_lead_time)
                start_date = max(preferred_dt, earliest_date)
            except ValueError:
                start_date = datetime.now() + timedelta(days=base_lead_time)
        else:
            start_date = datetime.now() + timedelta(days=base_lead_time)
        
        # Find available slot considering business days and holidays
        apt_date, apt_time, provider = self._find_available_slot(
            start_date, apt_info, duration_minutes, patient_priority
        )
        
        # Generate confirmation number
        confirmation_num = f"APT{apt_date.strftime('%y%m%d')}{hash(f'{matched_type}{provider}') % 10000:04d}"
        
        # Determine if reminder/prep instructions needed
        prep_instructions = self._get_prep_instructions(matched_type)
        reminder_info = self._get_reminder_schedule(matched_type, apt_date)
        
        return f"""
        ✅ APPOINTMENT SUCCESSFULLY SCHEDULED
        
        📋 APPOINTMENT DETAILS:
        Type: {matched_type.title()}
        Provider/Resource: {provider}
        Date: {apt_date.strftime('%A, %B %d, %Y')}
        Time: {apt_time}
        Duration: {duration_minutes} minutes
        Location: {apt_info['location']}
        Priority: {patient_priority.title()}
        Confirmation #: {confirmation_num}
        
        📍 ARRIVAL INFORMATION:
        • Please arrive 15 minutes early for registration
        • Bring valid ID and insurance card
        • Bring current medication list
        
        {prep_instructions}
        
        📅 REMINDERS:
        {reminder_info}
        
        📞 CONTACT INFORMATION:
        • To reschedule: Call (555) 123-4567
        • Emergency cancellation: Available 24/7
        • Patient portal: Available for non-urgent changes
        
        ❗ CANCELLATION POLICY:
        Please provide at least 24 hours notice for cancellations to avoid fees.
        """
    
    def _find_appointment_type(self, search_term: str, apt_types: dict) -> Optional[str]:
        """Enhanced appointment type matching with aliases."""
        # Direct match
        if search_term in apt_types:
            return search_term
        
        # Common aliases
        aliases = {
            "followup": "follow-up",
            "follow up": "follow-up", 
            "checkup": "follow-up",
            "check-up": "follow-up",
            "routine": "follow-up",
            "ct": "imaging",
            "mri": "imaging", 
            "xray": "imaging",
            "x-ray": "imaging",
            "ultrasound": "imaging",
            "scan": "imaging",
            "radiology": "imaging",
            "bloodwork": "lab",
            "blood work": "lab",
            "blood test": "lab",
            "laboratory": "lab",
            "cardiology": "specialist",
            "neurology": "specialist",
            "endocrinology": "specialist",
            "pulmonology": "specialist",
            "pt": "physical therapy",
            "rehab": "physical therapy",
            "rehabilitation": "physical therapy",
            "operation": "surgery",
            "procedure": "surgery",
            "or": "surgery",
            "urgent": "emergency",
            "er": "emergency",
            "emergency room": "emergency",
            "virtual": "telemedicine",
            "telehealth": "telemedicine",
            "video": "telemedicine",
            "remote": "telemedicine"
        }
        
        if search_term in aliases:
            return aliases[search_term]
        
        # Partial matching
        for apt_type in apt_types:
            if search_term in apt_type or apt_type in search_term:
                return apt_type
        
        return None
    
    def _find_available_slot(self, start_date: datetime, apt_info: dict, duration: int, priority: str) -> tuple:
        """Find an available appointment slot considering business hours and conflicts."""
        current_date = start_date
        max_search_days = 30  # Limit search to prevent infinite loops
        
        for day_offset in range(max_search_days):
            check_date = current_date + timedelta(days=day_offset)
            
            # Skip weekends for most appointment types
            if check_date.weekday() >= 5 and apt_info.get('location') != 'Emergency Department':
                continue
            
            # Skip holidays (basic implementation)
            if self._is_holiday(check_date):
                continue
            
            # Try to find available time slot
            available_slots = apt_info.get("time_slots", ["09:00"])
            
            # For 24/7 services
            if "24/7" in available_slots:
                provider = apt_info["providers"][0]
                return check_date, "Available 24/7", provider
            
            # Try each time slot
            for time_slot in available_slots:
                if self._is_slot_available(check_date, time_slot, duration, apt_info):
                    # Select provider (simple round-robin based on date)
                    provider_idx = (check_date.day + day_offset) % len(apt_info["providers"])
                    provider = apt_info["providers"][provider_idx]
                    return check_date, time_slot, provider
        
        # If no slot found in reasonable time, return best effort
        fallback_date = start_date + timedelta(days=7)
        fallback_time = apt_info["time_slots"][0] if apt_info["time_slots"] else "09:00"
        fallback_provider = apt_info["providers"][0]
        
        return fallback_date, f"{fallback_time} (Next Available)", fallback_provider
    
    def _is_holiday(self, date: datetime) -> bool:
        """Check if date is a major holiday (basic implementation)."""
        # Simple holiday checking - could be expanded
        month, day = date.month, date.day
        
        # Major US holidays
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day  
            (12, 25), # Christmas Day
        ]
        
        return (month, day) in holidays
    
    def _is_slot_available(self, date: datetime, time_slot: str, duration: int, apt_info: dict) -> bool:
        """Check if a specific time slot is available (simulated availability)."""
        # Simulate some realistic availability patterns
        # In real implementation, this would check actual calendar systems
        
        day_of_week = date.weekday()
        hour = int(time_slot.split(':')[0])
        
        # More availability in mid-week
        if day_of_week in [1, 2, 3]:  # Tue, Wed, Thu
            availability_rate = 0.8
        else:
            availability_rate = 0.6
        
        # Less availability during lunch hours and early morning
        if hour < 8 or (12 <= hour <= 13):
            availability_rate *= 0.7
        
        # Use date and time as seed for consistent results
        import random
        random.seed(date.day * 100 + hour)
        
        return random.random() < availability_rate
    
    def _get_prep_instructions(self, apt_type: str) -> str:
        """Get preparation instructions for specific appointment types."""
        prep_instructions = {
            "imaging": """
        🔍 IMAGING PREPARATION:
        • Fast for 4 hours if contrast study
        • Remove all metal objects before scan
        • Inform staff of any implants or devices
        • Wear comfortable, loose-fitting clothes""",
            
            "lab": """
        🩸 LABORATORY PREPARATION:
        • Fast for 8-12 hours if lipid panel or glucose test
        • Stay hydrated (water only if fasting)
        • Continue regular medications unless instructed otherwise
        • Bring list of current medications""",
            
            "surgery": """
        🏥 SURGICAL PREPARATION:
        • No food or drink after midnight before surgery
        • Remove nail polish, jewelry, and contact lenses
        • Arrange transportation home
        • Complete pre-operative clearance as directed
        • Follow specific surgeon instructions""",
            
            "specialist": """
        👨‍⚕️ SPECIALIST VISIT PREPARATION:
        • Bring relevant medical records and test results
        • Prepare list of current symptoms and questions
        • Bring current medication list with doses
        • Note any allergies or previous reactions""",
            
            "telemedicine": """
        💻 VIRTUAL VISIT PREPARATION:
        • Test your device and internet connection
        • Find a quiet, private space with good lighting
        • Have your medications and medical records nearby
        • Download required app or software in advance"""
        }
        
        return prep_instructions.get(apt_type, "")
    
    def _get_reminder_schedule(self, apt_type: str, apt_date: datetime) -> str:
        """Generate reminder schedule based on appointment type."""
        days_until = (apt_date - datetime.now()).days
        
        reminders = []
        
        if days_until >= 7:
            reminders.append("• 1 week before: Preparation instructions sent")
        if days_until >= 3:
            reminders.append("• 3 days before: Confirmation call/text")
        if days_until >= 1:
            reminders.append("• 1 day before: Final reminder with directions")
        
        reminders.append("• Morning of: Check-in text with any updates")
        
        return "\n".join(reminders) if reminders else "• Day of appointment: Check-in reminder"


class HL7ValidationTool(BaseTool):
    """Tool for validating HL7 messages with comprehensive error reporting."""
    name: str = "HL7 Message Validator"
    description: str = "Validate HL7 v2.x messages for format compliance, data integrity, and business rules"
    args_schema: type[BaseModel] = HL7ValidationInput

    def _run(self, hl7_message: str, validation_level: str = "standard") -> str:
        """
        Validate an HL7 message with comprehensive error reporting.
        Args:
            hl7_message: The HL7 message to validate
            validation_level: Validation level (basic, standard, strict, compliance)
        Returns:
            String containing detailed validation results
        """
        if not HL7_FHIR_AVAILABLE:
            return "HL7 validation tools are not available. Please ensure hl7_validator module is installed."
        
        if not hl7_message or not hl7_message.strip():
            return "ERROR: Empty or null HL7 message provided for validation."
        
        try:
            # Map validation level string to enum
            level_map = {
                "basic": ValidationLevel.BASIC,
                "standard": ValidationLevel.STANDARD,
                "strict": ValidationLevel.STRICT,
                "compliance": ValidationLevel.COMPLIANCE
            }
            
            validation_level_enum = level_map.get(validation_level.lower(), ValidationLevel.STANDARD)
            
            # Perform validation
            result = validate_hl7_message(hl7_message, validation_level_enum)
            
            # Format results
            output = self._format_validation_results(result)
            return output
            
        except Exception as e:
            return f"HL7 validation failed with error: {str(e)}"
    
    def _format_validation_results(self, result: Dict[str, Any]) -> str:
        """Format validation results into readable string."""
        output = []
        
        # Header
        status_emoji = {
            "VALID": "✅",
            "WARNING": "⚠️",
            "ERROR": "❌",
            "CRITICAL": "🚨"
        }
        
        status = result.get('status', 'UNKNOWN')
        emoji = status_emoji.get(status, "❓")
        
        output.append(f"{emoji} HL7 MESSAGE VALIDATION RESULTS")
        output.append("=" * 50)
        output.append(f"Status: {status}")
        output.append(f"Total Issues: {result.get('total_issues', 0)}")
        output.append(f"Validation Level: {result.get('validation_level', 'Unknown')}")
        output.append("")
        
        # Severity counts
        severity_counts = result.get('severity_counts', {})
        if severity_counts:
            output.append("ISSUE BREAKDOWN:")
            for severity, count in severity_counts.items():
                if count > 0:
                    output.append(f"  {severity}: {count}")
            output.append("")
        
        # Issues details
        issues = result.get('issues', [])
        if issues:
            output.append("DETAILED ISSUES:")
            output.append("-" * 30)
            
            for i, issue in enumerate(issues, 1):
                severity = issue.get('severity', 'UNKNOWN')
                segment = issue.get('segment_type', 'UNKNOWN')
                field = issue.get('field_number', 'N/A')
                message = issue.get('message', 'No message')
                details = issue.get('details', 'No details')
                suggested_fix = issue.get('suggested_fix', 'No suggestion')
                
                output.append(f"{i}. [{severity}] {segment}")
                if field != 'N/A':
                    output.append(f"   Field: {field}")
                output.append(f"   Message: {message}")
                output.append(f"   Details: {details}")
                if suggested_fix and suggested_fix != 'No suggestion':
                    output.append(f"   Fix: {suggested_fix}")
                output.append("")
        else:
            output.append("✅ No validation issues found!")
            output.append("")
        
        # Summary
        if result.get('needs_attention', False):
            output.append("⚠️  ATTENTION REQUIRED:")
            output.append("This message has critical errors or issues that need to be addressed.")
        elif result.get('is_valid', False):
            output.append("✅ VALIDATION PASSED:")
            output.append("This HL7 message is valid and ready for use.")
        else:
            output.append("❌ VALIDATION FAILED:")
            output.append("This HL7 message has errors that prevent proper processing.")
        
        return "\n".join(output)


class FHIRGenerationTool(BaseTool):
    """Tool for generating FHIR R4 resources directly from patient data."""
    name: str = "FHIR Message Generator"
    description: str = "Generate FHIR R4 resources directly from patient data, with optional HL7 conversion"
    args_schema: type[BaseModel] = FHIRGenerationInput

    def _run(self, patient_data: Dict[str, Any], output_format: str = "bundle", generate_hl7: bool = False) -> str:
        """
        Generate FHIR resources from patient data.
        Args:
            patient_data: Patient data dictionary containing demographics, conditions, observations, etc.
            output_format: Output format (bundle, individual_resources, json)
            generate_hl7: Whether to also generate HL7 message from FHIR
        Returns:
            String containing FHIR resources and optionally HL7 message
        """
        if not HL7_FHIR_AVAILABLE:
            return "FHIR generation tools are not available. Please ensure required modules are installed."
        
        if not patient_data:
            return "ERROR: No patient data provided for FHIR generation."
        
        try:
            # Generate FHIR resources
            fhir_resources = self._generate_fhir_resources(patient_data)
            
            if not fhir_resources:
                return "ERROR: Failed to generate FHIR resources from patient data."
            
            # Create FHIR Bundle
            bundle = self._create_fhir_bundle(fhir_resources)
            
            # Optionally generate HL7 from FHIR
            hl7_message = None
            if generate_hl7:
                hl7_message = self._generate_hl7_from_fhir(bundle)
            
            # Format output based on requested format
            if output_format.lower() == "bundle":
                return self._format_bundle_output(bundle, hl7_message)
            elif output_format.lower() == "individual_resources":
                return self._format_individual_resources_output(fhir_resources, hl7_message)
            elif output_format.lower() == "json":
                return self._format_json_output(fhir_resources, bundle, hl7_message)
            else:
                return self._format_summary_output(fhir_resources, bundle, hl7_message)
                
        except Exception as e:
            return f"FHIR generation failed with error: {str(e)}"
    
    def _generate_fhir_resources(self, patient_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate FHIR resources from patient data."""
        resources = []
        
        # Create Patient resource
        patient_resource = self._create_patient_resource(patient_data)
        resources.append(patient_resource)
        
        # Create Encounter resource if visit data exists
        if patient_data.get('visit_info'):
            encounter_resource = self._create_encounter_resource(patient_data, patient_resource)
            if encounter_resource:
                resources.append(encounter_resource)
        
        # Create Condition resources from diagnoses
        if patient_data.get('diagnoses'):
            condition_resources = self._create_condition_resources(patient_data, patient_resource)
            resources.extend(condition_resources)
        
        # Create Observation resources from observations
        if patient_data.get('observations'):
            encounter_ref = None
            if patient_data.get('visit_info'):
                encounter_ref = next((r for r in resources if r['resourceType'] == 'Encounter'), None)
            observation_resources = self._create_observation_resources(patient_data, patient_resource, encounter_ref)
            resources.extend(observation_resources)
        
        # Create Procedure resources from procedures
        if patient_data.get('procedures'):
            encounter_ref = None
            if patient_data.get('visit_info'):
                encounter_ref = next((r for r in resources if r['resourceType'] == 'Encounter'), None)
            procedure_resources = self._create_procedure_resources(patient_data, patient_resource, encounter_ref)
            resources.extend(procedure_resources)
        
        return resources
    
    def _create_patient_resource(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create FHIR Patient resource."""
        import uuid
        
        patient_id = patient_data.get('id', str(uuid.uuid4()))
        
        # Build name
        name = {
            'use': 'official',
            'family': patient_data.get('family_name', 'Unknown'),
            'given': [patient_data.get('given_name', 'Unknown')]
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
            'gender': patient_data.get('gender', 'unknown'),
            'telecom': telecom,
            'address': address
        }
        
        if patient_data.get('birth_date'):
            patient_resource['birthDate'] = patient_data['birth_date']
        
        return patient_resource
    
    def _create_encounter_resource(self, patient_data: Dict[str, Any], patient_resource: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create FHIR Encounter resource."""
        import uuid
        
        visit_info = patient_data.get('visit_info', {})
        if not visit_info:
            return None
        
        encounter_id = str(uuid.uuid4())
        
        encounter_resource = {
            'resourceType': 'Encounter',
            'id': encounter_id,
            'status': 'finished',
            'class': {
                'system': 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
                'code': visit_info.get('patient_class', 'inpatient'),
                'display': visit_info.get('patient_class', 'inpatient').title()
            },
            'subject': {
                'reference': f"Patient/{patient_resource['id']}"
            }
        }
        
        if visit_info.get('assigned_patient_location'):
            encounter_resource['location'] = [{
                'location': {
                    'display': visit_info['assigned_patient_location']
                }
            }]
        
        if visit_info.get('admit_date_time'):
            encounter_resource['period'] = {
                'start': visit_info['admit_date_time']
            }
        
        return encounter_resource
    
    def _create_condition_resources(self, patient_data: Dict[str, Any], patient_resource: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create FHIR Condition resources from diagnoses."""
        import uuid
        
        conditions = []
        diagnoses = patient_data.get('diagnoses', [])
        
        for diagnosis in diagnoses:
            condition_id = str(uuid.uuid4())
            
            # Build code
            code_data = None
            if diagnosis.get('code'):
                code_data = {
                    'coding': [{
                        'system': 'http://hl7.org/fhir/sid/icd-10-cm',
                        'code': diagnosis['code'],
                        'display': diagnosis.get('description', diagnosis['code'])
                    }]
                }
            
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
            
            if diagnosis.get('date'):
                condition_resource['onsetDateTime'] = diagnosis['date']
            
            conditions.append(condition_resource)
        
        return conditions
    
    def _create_observation_resources(self, patient_data: Dict[str, Any], patient_resource: Dict[str, Any], encounter_resource: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create FHIR Observation resources from observations."""
        import uuid
        
        observations = []
        obs_data = patient_data.get('observations', [])
        
        for obs in obs_data:
            observation_id = str(uuid.uuid4())
            
            # Build code
            code_data = None
            if obs.get('observation_identifier'):
                code_data = {
                    'coding': [{
                        'system': 'http://loinc.org',
                        'code': obs['observation_identifier'],
                        'display': obs.get('observation_description', obs['observation_identifier'])
                    }]
                }
            
            # Build value
            value_data = None
            if obs.get('observation_value'):
                value = obs['observation_value']
                value_type = obs.get('value_type', 'ST')
                
                if value_type in ['NM', 'SN']:  # Numeric
                    try:
                        numeric_value = float(value)
                        value_data = {
                            'valueQuantity': {
                                'value': numeric_value,
                                'unit': obs.get('units', '')
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
            
            # Build reference range
            reference_range = None
            if obs.get('reference_range'):
                range_parts = obs['reference_range'].split('-')
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
            
            observations.append(observation_resource)
        
        return observations
    
    def _create_procedure_resources(self, patient_data: Dict[str, Any], patient_resource: Dict[str, Any], encounter_resource: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create FHIR Procedure resources from procedures."""
        import uuid
        
        procedures = []
        proc_data = patient_data.get('procedures', [])
        
        for proc in proc_data:
            procedure_id = str(uuid.uuid4())
            
            # Build code
            code_data = None
            if proc.get('procedure_code'):
                code_data = {
                    'coding': [{
                        'system': 'http://www.ama-assn.org/go/cpt',
                        'code': proc['procedure_code'],
                        'display': proc.get('procedure_description', proc['procedure_code'])
                    }]
                }
            
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
            
            if proc.get('procedure_date_time'):
                procedure_resource['performedDateTime'] = proc['procedure_date_time']
            
            if proc.get('surgeon_name'):
                procedure_resource['performer'] = [{
                    'actor': {
                        'display': proc['surgeon_name']
                    }
                }]
            
            procedures.append(procedure_resource)
        
        return procedures
    
    def _create_fhir_bundle(self, resources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create FHIR Bundle containing all resources."""
        import uuid
        
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
    
    def _generate_hl7_from_fhir(self, bundle: Dict[str, Any]) -> Optional[str]:
        """Generate HL7 message from FHIR Bundle using existing converter."""
        try:
            converter = FHIRToHL7Converter()
            hl7_messages = converter.convert_bundle_to_hl7(bundle)
            return hl7_messages[0] if hl7_messages else None
        except Exception as e:
            print(f"HL7 generation from FHIR failed: {e}")
            return None
    
    def _format_bundle_output(self, bundle: Dict[str, Any], hl7_message: Optional[str]) -> str:
        """Format output as FHIR Bundle with optional HL7."""
        import json
        
        output = []
        output.append("🎯 FHIR BUNDLE GENERATED")
        output.append("=" * 40)
        output.append(json.dumps(bundle, indent=2))
        
        if hl7_message:
            output.append("\n\n🔗 CORRESPONDING HL7 MESSAGE:")
            output.append("=" * 40)
            output.append(hl7_message)
        
        return "\n".join(output)
    
    def _format_individual_resources_output(self, resources: List[Dict[str, Any]], hl7_message: Optional[str]) -> str:
        """Format output as individual FHIR resources."""
        import json
        
        output = []
        output.append("🎯 FHIR RESOURCES GENERATED")
        output.append("=" * 40)
        
        for resource in resources:
            output.append(f"\n=== {resource['resourceType']} ===")
            output.append(json.dumps(resource, indent=2))
        
        if hl7_message:
            output.append("\n\n🔗 CORRESPONDING HL7 MESSAGE:")
            output.append("=" * 40)
            output.append(hl7_message)
        
        return "\n".join(output)
    
    def _format_json_output(self, resources: List[Dict[str, Any]], bundle: Dict[str, Any], hl7_message: Optional[str]) -> str:
        """Format output as JSON."""
        import json
        
        result = {
            'success': True,
            'fhir_resources': resources,
            'bundle': bundle,
            'hl7_message': hl7_message
        }
        
        return json.dumps(result, indent=2)
    
    def _format_summary_output(self, resources: List[Dict[str, Any]], bundle: Dict[str, Any], hl7_message: Optional[str]) -> str:
        """Format output as summary."""
        output = []
        
        output.append("🎯 FHIR GENERATION RESULTS")
        output.append("=" * 40)
        output.append(f"Status: SUCCESS")
        output.append(f"Resources Generated: {len(resources)}")
        output.append(f"Bundle ID: {bundle.get('id', 'Unknown')}")
        
        # Resource breakdown
        resource_types = {}
        for resource in resources:
            resource_type = resource.get('resourceType', 'Unknown')
            resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
        
        if resource_types:
            output.append("\nRESOURCE BREAKDOWN:")
            for resource_type, count in resource_types.items():
                output.append(f"  {resource_type}: {count}")
        
        if hl7_message:
            output.append(f"\n🔗 HL7 MESSAGE GENERATED: {len(hl7_message)} characters")
            output.append("First 200 characters:")
            output.append(hl7_message[:200] + "..." if len(hl7_message) > 200 else hl7_message)
        else:
            output.append("\nℹ️  No HL7 message generated (generate_hl7=False)")
        
        return "\n".join(output)


class HealthcareTools:
    """Custom tools for healthcare simulation agents - backward compatibility wrapper"""
    
    @staticmethod
    def clinical_guidelines_tool() -> ClinicalGuidelinesTool:
        """Creates a tool that provides access to clinical guidelines."""
        return ClinicalGuidelinesTool()
    
    @staticmethod
    def medication_interaction_tool() -> MedicationInteractionTool:
        """Creates a tool for checking medication interactions."""
        return MedicationInteractionTool()
    
    @staticmethod  
    def appointment_scheduler_tool() -> AppointmentSchedulerTool:
        """Creates a tool for scheduling patient appointments."""
        return AppointmentSchedulerTool()
    
    @staticmethod
    def hl7_validation_tool() -> HL7ValidationTool:
        """Creates a tool for validating HL7 messages."""
        return HL7ValidationTool()
    
    @staticmethod
    def fhir_generation_tool() -> FHIRGenerationTool:
        """Creates a tool for generating FHIR resources from patient data."""
        return FHIRGenerationTool()