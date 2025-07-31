# Tool Extension Guide

This guide focuses specifically on extending the healthcare simulation system with new tools that provide specialized capabilities for healthcare agents.

## Understanding Healthcare Tools

Tools in the healthcare simulation system are reusable components that provide specialized functionality to agents. They represent:

- **Clinical Knowledge**: Access to medical guidelines, protocols, and evidence
- **Calculation Engines**: Risk scores, dosing calculations, diagnostic algorithms
- **Data Access**: Laboratory systems, imaging results, patient records
- **Decision Support**: Clinical decision trees, workflow automation
- **External Services**: Scheduling systems, pharmacy interfaces, equipment management

## Current Tool Architecture

The system currently includes these core tools:

1. **Clinical Guidelines Tool** - Evidence-based treatment protocols
2. **Medication Interaction Tool** - Drug interaction and contraindication checking
3. **Appointment Scheduler Tool** - Patient appointment management

## Step-by-Step Tool Creation

### Step 1: Define Your Tool's Purpose

Before creating a tool, clearly define:

- **Clinical Function**: What healthcare task does this tool support?
- **User Agents**: Which healthcare professionals would use this tool?
- **Input Requirements**: What data does the tool need to function?
- **Output Format**: What information should the tool return?
- **Integration Points**: How does this connect to existing healthcare systems?

### Step 2: Design the Tool Interface

Create input and output schemas using Pydantic:

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Example: Laboratory Results Tool
class LabTestType(str, Enum):
    """Standard laboratory test types."""
    COMPLETE_BLOOD_COUNT = "cbc"
    COMPREHENSIVE_METABOLIC_PANEL = "cmp"
    LIPID_PANEL = "lipid"
    LIVER_FUNCTION = "lft"
    THYROID_FUNCTION = "tft"
    HEMOGLOBIN_A1C = "hba1c"
    URINALYSIS = "ua"
    BLOOD_CULTURE = "blood_culture"
    TROPONIN = "troponin"
    BNP = "bnp"

class LabOrderInput(BaseModel):
    """Input schema for laboratory ordering tool."""
    patient_id: str = Field(..., description="Patient identifier")
    test_types: List[LabTestType] = Field(..., description="Types of lab tests to order")
    urgency: str = Field(default="routine", description="Order urgency: stat, urgent, routine")
    clinical_indication: str = Field(..., description="Clinical reason for ordering tests")
    patient_age: int = Field(..., description="Patient age in years")
    patient_sex: str = Field(..., description="Patient sex: M/F")
    current_medications: Optional[List[str]] = Field(default=None, description="Current medications")

class LabResult(BaseModel):
    """Individual lab result structure."""
    test_name: str
    value: str
    unit: str
    reference_range: str
    status: str  # normal, high, low, critical
    timestamp: datetime

class LabOrderOutput(BaseModel):
    """Output schema for lab orders."""
    order_id: str
    patient_id: str
    ordered_tests: List[str]
    urgency: str
    estimated_completion: datetime
    special_instructions: List[str]
    cost_estimate: Optional[float]

# Example: Risk Calculation Tool
class CardiacRiskInput(BaseModel):
    """Input for cardiac risk calculation."""
    age: int = Field(..., ge=20, le=120, description="Patient age")
    sex: str = Field(..., regex="^[MF]$", description="Patient sex (M/F)")
    total_cholesterol: float = Field(..., gt=0, description="Total cholesterol mg/dL")
    hdl_cholesterol: float = Field(..., gt=0, description="HDL cholesterol mg/dL")
    systolic_bp: int = Field(..., ge=70, le=250, description="Systolic BP mmHg")
    smoker: bool = Field(..., description="Current smoker status")
    diabetes: bool = Field(..., description="Diabetes mellitus present")
    family_history: bool = Field(default=False, description="Family history of CAD")

class RiskScore(BaseModel):
    """Risk score output."""
    score_value: float
    risk_percentage: float
    risk_category: str  # low, moderate, high
    recommendations: List[str]
    calculation_method: str

# Example: Imaging Protocol Tool
class ImagingStudyType(str, Enum):
    """Types of imaging studies."""
    CHEST_XRAY = "chest_xray"
    CT_HEAD = "ct_head"
    CT_CHEST = "ct_chest"
    CT_ABDOMEN = "ct_abdomen"
    MRI_BRAIN = "mri_brain"
    ULTRASOUND_ABDOMEN = "us_abdomen"
    ECHO = "echocardiogram"
    NUCLEAR_STRESS = "nuclear_stress"

class ImagingOrderInput(BaseModel):
    """Input for imaging order tool."""
    patient_id: str = Field(..., description="Patient identifier")
    study_type: ImagingStudyType = Field(..., description="Type of imaging study")
    clinical_indication: str = Field(..., description="Clinical reason for study")
    urgency: str = Field(default="routine", description="Study urgency")
    contrast_needed: Optional[bool] = Field(default=None, description="Contrast required")
    patient_weight: Optional[float] = Field(default=None, description="Patient weight in kg")
    allergies: Optional[List[str]] = Field(default=None, description="Known allergies")
    kidney_function: Optional[float] = Field(default=None, description="Creatinine level")
```

### Step 3: Implement the Tool Class

Create your tool by inheriting from `crewai.tools.BaseTool`:

```python
from crewai.tools import BaseTool
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

class LabOrderTool(BaseTool):
    """Tool for ordering laboratory tests with clinical decision support."""
    
    name: str = "Laboratory Order Tool"
    description: str = """Order laboratory tests based on clinical indications with 
    appropriate test selection, timing, and clinical decision support"""
    args_schema: type[BaseModel] = LabOrderInput

    def _run(self, patient_id: str, test_types: List[LabTestType], 
             urgency: str = "routine", clinical_indication: str = "",
             patient_age: int = 0, patient_sex: str = "",
             current_medications: Optional[List[str]] = None) -> str:
        """
        Order laboratory tests with clinical decision support.
        
        Args:
            patient_id: Patient identifier
            test_types: List of test types to order
            urgency: Order priority (stat, urgent, routine)
            clinical_indication: Clinical reason for tests
            patient_age: Patient age
            patient_sex: Patient sex
            current_medications: Current medications list
            
        Returns:
            JSON string containing lab order details and recommendations
        """
        
        # Generate order ID
        order_id = f"LAB{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Process each test type
        ordered_tests = []
        special_instructions = []
        estimated_completion = self._calculate_completion_time(test_types, urgency)
        
        for test_type in test_types:
            test_info = self._get_test_information(test_type)
            ordered_tests.append(test_info['name'])
            
            # Add special instructions based on test and patient factors
            instructions = self._get_special_instructions(
                test_type, patient_age, patient_sex, current_medications
            )
            special_instructions.extend(instructions)
        
        # Clinical decision support
        recommendations = self._provide_clinical_recommendations(
            test_types, clinical_indication, patient_age, patient_sex
        )
        
        # Cost estimation
        cost_estimate = self._estimate_cost(test_types, urgency)
        
        # Create output
        order_output = LabOrderOutput(
            order_id=order_id,
            patient_id=patient_id,
            ordered_tests=ordered_tests,
            urgency=urgency,
            estimated_completion=estimated_completion,
            special_instructions=list(set(special_instructions)),  # Remove duplicates
            cost_estimate=cost_estimate
        )
        
        # Format comprehensive output
        result = f"""
        LABORATORY ORDER PLACED:
        Order ID: {order_output.order_id}
        Patient ID: {order_output.patient_id}
        Clinical Indication: {clinical_indication}
        
        TESTS ORDERED:
        {self._format_test_list(ordered_tests)}
        
        ORDER DETAILS:
        - Urgency: {urgency}
        - Estimated Completion: {estimated_completion.strftime('%Y-%m-%d %H:%M')}
        - Estimated Cost: ${cost_estimate:.2f}
        
        SPECIAL INSTRUCTIONS:
        {chr(10).join(f"- {instruction}" for instruction in special_instructions)}
        
        CLINICAL RECOMMENDATIONS:
        {chr(10).join(f"- {rec}" for rec in recommendations)}
        
        ORDER STATUS: Submitted to Laboratory
        """
        
        return result.strip()
    
    def _get_test_information(self, test_type: LabTestType) -> Dict[str, Any]:
        """Get detailed information about a specific test."""
        test_database = {
            LabTestType.COMPLETE_BLOOD_COUNT: {
                'name': 'Complete Blood Count with Differential',
                'components': ['WBC', 'RBC', 'Hemoglobin', 'Hematocrit', 'Platelets'],
                'fasting_required': False,
                'typical_turnaround': 2  # hours
            },
            LabTestType.COMPREHENSIVE_METABOLIC_PANEL: {
                'name': 'Comprehensive Metabolic Panel',
                'components': ['Glucose', 'Sodium', 'Potassium', 'Chloride', 'BUN', 'Creatinine'],
                'fasting_required': True,
                'typical_turnaround': 4
            },
            LabTestType.HEMOGLOBIN_A1C: {
                'name': 'Hemoglobin A1c',
                'components': ['HbA1c'],
                'fasting_required': False,
                'typical_turnaround': 6
            }
            # Add more tests as needed
        }
        return test_database.get(test_type, {'name': str(test_type), 'components': []})
    
    def _calculate_completion_time(self, test_types: List[LabTestType], urgency: str) -> datetime:
        """Calculate estimated completion time based on tests and urgency."""
        base_times = {'stat': 1, 'urgent': 4, 'routine': 24}  # hours
        base_time = base_times.get(urgency, 24)
        
        # Adjust for complex tests
        complex_tests = [LabTestType.BLOOD_CULTURE, LabTestType.THYROID_FUNCTION]
        if any(test in complex_tests for test in test_types):
            base_time *= 2
        
        return datetime.now() + timedelta(hours=base_time)
    
    def _get_special_instructions(self, test_type: LabTestType, age: int, 
                                sex: str, medications: List[str] = None) -> List[str]:
        """Generate special instructions based on test and patient factors."""
        instructions = []
        medications = medications or []
        
        # Fasting requirements
        fasting_tests = [LabTestType.COMPREHENSIVE_METABOLIC_PANEL, LabTestType.LIPID_PANEL]
        if test_type in fasting_tests:
            instructions.append("Patient should fast 8-12 hours before collection")
        
        # Age-specific considerations
        if age < 18 and test_type == LabTestType.COMPLETE_BLOOD_COUNT:
            instructions.append("Use pediatric collection tubes")
        
        # Medication interactions
        if 'warfarin' in [med.lower() for med in medications]:
            instructions.append("Note: Patient on anticoagulation - consider bleeding risk")
        
        return instructions
    
    def _provide_clinical_recommendations(self, test_types: List[LabTestType], 
                                        indication: str, age: int, sex: str) -> List[str]:
        """Provide clinical recommendations based on ordered tests."""
        recommendations = []
        
        # Diabetes monitoring
        if LabTestType.HEMOGLOBIN_A1C in test_types:
            recommendations.append("Consider repeating HbA1c in 3 months to assess treatment response")
        
        # Cardiac risk assessment
        if LabTestType.LIPID_PANEL in test_types and age > 40:
            recommendations.append("Consider cardiac risk stratification if lipid abnormalities found")
        
        # Kidney function monitoring
        if LabTestType.COMPREHENSIVE_METABOLIC_PANEL in test_types:
            recommendations.append("Monitor kidney function if creatinine elevated")
        
        return recommendations
    
    def _estimate_cost(self, test_types: List[LabTestType], urgency: str) -> float:
        """Estimate cost for ordered tests."""
        base_costs = {
            LabTestType.COMPLETE_BLOOD_COUNT: 25.00,
            LabTestType.COMPREHENSIVE_METABOLIC_PANEL: 35.00,
            LabTestType.LIPID_PANEL: 30.00,
            LabTestType.HEMOGLOBIN_A1C: 40.00,
            LabTestType.THYROID_FUNCTION: 60.00
        }
        
        total_cost = sum(base_costs.get(test, 50.00) for test in test_types)
        
        # Urgency multiplier
        if urgency == 'stat':
            total_cost *= 1.5
        elif urgency == 'urgent':
            total_cost *= 1.2
        
        return total_cost
    
    def _format_test_list(self, tests: List[str]) -> str:
        """Format test list for output."""
        return '\n'.join(f"  • {test}" for test in tests)

class CardiacRiskCalculatorTool(BaseTool):
    """Tool for calculating cardiac risk scores."""
    
    name: str = "Cardiac Risk Calculator"
    description: str = """Calculate 10-year cardiovascular risk using validated risk calculators 
    like Framingham or ASCVD Risk Estimator"""
    args_schema: type[BaseModel] = CardiacRiskInput

    def _run(self, age: int, sex: str, total_cholesterol: float, hdl_cholesterol: float,
             systolic_bp: int, smoker: bool, diabetes: bool, family_history: bool = False) -> str:
        """
        Calculate cardiac risk score and provide recommendations.
        
        Returns detailed risk assessment with recommendations.
        """
        
        # Simplified Framingham Risk Score calculation
        # (In practice, use validated algorithms)
        risk_score = self._calculate_framingham_score(
            age, sex, total_cholesterol, hdl_cholesterol, 
            systolic_bp, smoker, diabetes
        )
        
        # Convert to 10-year risk percentage
        risk_percentage = self._score_to_percentage(risk_score, sex)
        
        # Categorize risk
        risk_category = self._categorize_risk(risk_percentage)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            risk_category, risk_percentage, age, smoker, diabetes
        )
        
        result = f"""
        CARDIAC RISK ASSESSMENT:
        
        Patient Profile:
        - Age: {age} years
        - Sex: {sex}
        - Total Cholesterol: {total_cholesterol} mg/dL
        - HDL Cholesterol: {hdl_cholesterol} mg/dL
        - Systolic BP: {systolic_bp} mmHg
        - Smoker: {'Yes' if smoker else 'No'}
        - Diabetes: {'Yes' if diabetes else 'No'}
        - Family History: {'Yes' if family_history else 'No'}
        
        RISK CALCULATION:
        - Framingham Risk Score: {risk_score}
        - 10-Year CV Risk: {risk_percentage:.1f}%
        - Risk Category: {risk_category.upper()}
        
        CLINICAL RECOMMENDATIONS:
        {chr(10).join(f"- {rec}" for rec in recommendations)}
        
        FOLLOW-UP:
        - Reassess risk annually or when risk factors change
        - Consider additional risk factors not captured in this calculator
        - Use clinical judgment for intermediate risk patients
        """
        
        return result.strip()
    
    def _calculate_framingham_score(self, age: int, sex: str, total_chol: float,
                                  hdl_chol: float, systolic_bp: int, 
                                  smoker: bool, diabetes: bool) -> int:
        """Calculate Framingham risk score (simplified version)."""
        score = 0
        
        # Age points
        if sex == 'M':
            if age >= 70: score += 11
            elif age >= 60: score += 8
            elif age >= 50: score += 5
            elif age >= 40: score += 2
        else:  # Female
            if age >= 70: score += 12
            elif age >= 60: score += 9
            elif age >= 50: score += 6
            elif age >= 40: score += 3
        
        # Cholesterol points
        if total_chol >= 280: score += 3
        elif total_chol >= 240: score += 2
        elif total_chol >= 200: score += 1
        
        # HDL points (protective)
        if hdl_chol >= 60: score -= 2
        elif hdl_chol < 35: score += 2
        elif hdl_chol < 45: score += 1
        
        # Blood pressure points
        if systolic_bp >= 160: score += 3
        elif systolic_bp >= 140: score += 2
        elif systolic_bp >= 130: score += 1
        
        # Smoking points
        if smoker: score += 4
        
        # Diabetes points
        if diabetes: score += 3
        
        return max(0, score)  # Don't allow negative scores
    
    def _score_to_percentage(self, score: int, sex: str) -> float:
        """Convert risk score to 10-year risk percentage."""
        # Simplified conversion tables
        male_conversion = {
            0: 2, 1: 2, 2: 3, 3: 3, 4: 4, 5: 5,
            6: 6, 7: 7, 8: 8, 9: 10, 10: 12, 11: 14,
            12: 17, 13: 20, 14: 24, 15: 27, 16: 32
        }
        
        female_conversion = {
            0: 1, 1: 1, 2: 2, 3: 2, 4: 2, 5: 3,
            6: 3, 7: 4, 8: 4, 9: 5, 10: 6, 11: 7,
            12: 8, 13: 9, 14: 11, 15: 13, 16: 15
        }
        
        conversion_table = male_conversion if sex == 'M' else female_conversion
        return conversion_table.get(min(score, 16), 35)  # Cap at 35%
    
    def _categorize_risk(self, risk_percentage: float) -> str:
        """Categorize risk level."""
        if risk_percentage < 5:
            return "low"
        elif risk_percentage < 10:
            return "moderate"
        elif risk_percentage < 20:
            return "high"
        else:
            return "very high"
    
    def _generate_recommendations(self, risk_category: str, risk_percentage: float,
                                age: int, smoker: bool, diabetes: bool) -> List[str]:
        """Generate clinical recommendations based on risk."""
        recommendations = []
        
        # Universal recommendations
        recommendations.append("Lifestyle modifications: diet, exercise, weight management")
        
        # Risk-specific recommendations
        if risk_category in ['moderate', 'high', 'very high']:
            recommendations.append("Consider statin therapy per ACC/AHA guidelines")
            recommendations.append("Blood pressure control to <130/80 mmHg")
        
        if risk_category in ['high', 'very high']:
            recommendations.append("Aspirin 81mg daily if bleeding risk acceptable")
            recommendations.append("Intensive lifestyle counseling")
        
        # Specific factor recommendations
        if smoker:
            recommendations.append("URGENT: Smoking cessation counseling and pharmacotherapy")
        
        if diabetes:
            recommendations.append("Optimize diabetes control (HbA1c <7%)")
            recommendations.append("Consider GLP-1 agonist or SGLT2 inhibitor for CV benefit")
        
        # Follow-up recommendations
        if risk_category == 'moderate':
            recommendations.append("Consider coronary calcium score for risk reclassification")
        
        return recommendations

class ImagingProtocolTool(BaseTool):
    """Tool for imaging study protocols and ordering."""
    
    name: str = "Imaging Protocol Tool"
    description: str = """Provide appropriate imaging protocols, contrast decisions, 
    and ordering guidance based on clinical indications"""
    args_schema: type[BaseModel] = ImagingOrderInput

    def _run(self, patient_id: str, study_type: ImagingStudyType, 
             clinical_indication: str, urgency: str = "routine",
             contrast_needed: Optional[bool] = None, patient_weight: Optional[float] = None,
             allergies: Optional[List[str]] = None, kidney_function: Optional[float] = None) -> str:
        """
        Generate imaging protocol and ordering recommendations.
        
        Returns comprehensive imaging guidance including protocols, safety checks, and scheduling.
        """
        
        # Get study protocol
        protocol = self._get_imaging_protocol(study_type, clinical_indication)
        
        # Determine contrast requirements
        contrast_decision = self._determine_contrast_need(
            study_type, clinical_indication, contrast_needed, 
            allergies, kidney_function
        )
        
        # Safety screening
        safety_checks = self._perform_safety_screening(
            study_type, patient_weight, allergies, kidney_function, contrast_decision['use_contrast']
        )
        
        # Scheduling considerations
        scheduling = self._get_scheduling_guidance(study_type, urgency, contrast_decision['use_contrast'])
        
        # Cost and authorization
        cost_info = self._get_cost_and_authorization_info(study_type, contrast_decision['use_contrast'])
        
        result = f"""
        IMAGING ORDER: {protocol['study_name']}
        Order ID: IMG{datetime.now().strftime('%Y%m%d%H%M%S')}
        Patient ID: {patient_id}
        Clinical Indication: {clinical_indication}
        
        STUDY PROTOCOL:
        {protocol['description']}
        
        TECHNIQUE:
        {chr(10).join(f"- {item}" for item in protocol['technique'])}
        
        CONTRAST DECISION:
        - Contrast Needed: {'Yes' if contrast_decision['use_contrast'] else 'No'}
        - Rationale: {contrast_decision['rationale']}
        {f"- Contrast Type: {contrast_decision.get('contrast_type', 'N/A')}" if contrast_decision['use_contrast'] else ''}
        
        SAFETY SCREENING:
        {chr(10).join(f"- {check}" for check in safety_checks)}
        
        SCHEDULING INFORMATION:
        - Priority: {urgency}
        - Estimated Duration: {scheduling['duration']} minutes
        - Preparation Required: {scheduling['preparation']}
        - Scheduling Notes: {scheduling['notes']}
        
        COST AND AUTHORIZATION:
        - Estimated Cost: ${cost_info['cost']:.2f}
        - Authorization: {cost_info['authorization_status']}
        - CPT Code: {cost_info['cpt_code']}
        
        CLINICAL NOTES:
        {chr(10).join(f"- {note}" for note in protocol.get('clinical_notes', []))}
        """
        
        return result.strip()
    
    def _get_imaging_protocol(self, study_type: ImagingStudyType, indication: str) -> Dict[str, Any]:
        """Get imaging protocol details."""
        protocols = {
            ImagingStudyType.CHEST_XRAY: {
                'study_name': 'Chest X-ray',
                'description': 'Two-view chest radiography (PA and lateral)',
                'technique': [
                    'Upright PA and lateral views preferred',
                    'Portable AP if patient unable to stand',
                    'Inspiratory hold for optimal lung expansion',
                    'Include costophrenic angles and apices'
                ],
                'clinical_notes': [
                    'Evaluate for pneumothorax, pneumonia, CHF, masses',
                    'Compare to prior studies when available'
                ]
            },
            ImagingStudyType.CT_CHEST: {
                'study_name': 'CT Chest',
                'description': 'High-resolution CT of the chest',
                'technique': [
                    'Helical acquisition from lung apices to bases',
                    'Thin-section (1-2mm) reconstruction',
                    'Both mediastinal and lung window images',
                    'IV contrast per clinical indication'
                ],
                'clinical_notes': [
                    'Superior to chest X-ray for lung nodules',
                    'Excellent for mediastinal evaluation',
                    'Consider pulmonary embolism protocol if indicated'
                ]
            }
            # Add more protocols as needed
        }
        
        return protocols.get(study_type, {
            'study_name': str(study_type),
            'description': f'Standard {study_type} protocol',
            'technique': ['Standard technique per departmental protocol'],
            'clinical_notes': []
        })
    
    def _determine_contrast_need(self, study_type: ImagingStudyType, indication: str,
                               contrast_requested: Optional[bool], allergies: Optional[List[str]],
                               kidney_function: Optional[float]) -> Dict[str, Any]:
        """Determine if contrast is needed and safe."""
        
        # Default contrast requirements by study type
        contrast_requirements = {
            ImagingStudyType.CT_CHEST: {
                'default': False,
                'indications_requiring': ['pulmonary embolism', 'mediastinal mass', 'aortic dissection'],
                'contrast_type': 'iodinated'
            },
            ImagingStudyType.CT_ABDOMEN: {
                'default': True,
                'indications_not_requiring': ['kidney stones', 'appendicitis (sometimes)'],
                'contrast_type': 'iodinated'
            }
        }
        
        study_contrast = contrast_requirements.get(study_type, {'default': False})
        
        # Determine if contrast is needed
        use_contrast = contrast_requested
        if use_contrast is None:
            use_contrast = study_contrast['default']
            
            # Check specific indications
            if 'indications_requiring' in study_contrast:
                for req_indication in study_contrast['indications_requiring']:
                    if req_indication.lower() in indication.lower():
                        use_contrast = True
                        break
        
        # Safety check for contrast
        contraindications = []
        if allergies:
            if any('iodine' in allergy.lower() or 'contrast' in allergy.lower() for allergy in allergies):
                contraindications.append('Previous contrast allergy')
        
        if kidney_function and kidney_function > 1.5:
            contraindications.append('Impaired kidney function (Cr > 1.5)')
        
        # Generate rationale
        if contraindications and use_contrast:
            rationale = f"Contrast indicated but contraindicated due to: {', '.join(contraindications)}"
            use_contrast = False
        elif use_contrast:
            rationale = "Contrast indicated for optimal diagnostic accuracy"
        else:
            rationale = "Non-contrast study appropriate for this indication"
        
        return {
            'use_contrast': use_contrast,
            'rationale': rationale,
            'contrast_type': study_contrast.get('contrast_type', ''),
            'contraindications': contraindications
        }
    
    def _perform_safety_screening(self, study_type: ImagingStudyType, weight: Optional[float],
                                allergies: Optional[List[str]], kidney_function: Optional[float],
                                use_contrast: bool) -> List[str]:
        """Perform safety screening checks."""
        checks = []
        
        # General safety checks
        checks.append("Patient identity verified")
        checks.append("Clinical indication confirmed")
        
        # Weight-based checks
        if weight and weight > 150:  # kg
            checks.append("Patient weight exceeds table limit - verify equipment capacity")
        
        # Contrast-specific checks
        if use_contrast:
            checks.append("Contrast allergy history reviewed")
            checks.append("Kidney function assessed")
            if kidney_function and kidney_function > 1.5:
                checks.append("ALERT: Elevated creatinine - consider nephrology consultation")
            checks.append("IV access verified")
            checks.append("Emergency medications available")
        
        # Study-specific checks
        if 'CT' in str(study_type):
            checks.append("Pregnancy screening completed for females of childbearing age")
            checks.append("Previous studies reviewed for comparison")
        
        return checks
    
    def _get_scheduling_guidance(self, study_type: ImagingStudyType, urgency: str, 
                               use_contrast: bool) -> Dict[str, str]:
        """Get scheduling guidance."""
        
        # Base durations (minutes)
        durations = {
            ImagingStudyType.CHEST_XRAY: 15,
            ImagingStudyType.CT_HEAD: 20,
            ImagingStudyType.CT_CHEST: 30,
            ImagingStudyType.CT_ABDOMEN: 35,
            ImagingStudyType.MRI_BRAIN: 45,
            ImagingStudyType.ECHO: 60
        }
        
        duration = durations.get(study_type, 30)
        if use_contrast:
            duration += 15  # Additional time for contrast
        
        # Preparation requirements
        preparation = "No special preparation required"
        if study_type == ImagingStudyType.CT_ABDOMEN and use_contrast:
            preparation = "NPO 4 hours prior if using oral contrast"
        elif 'MRI' in str(study_type):
            preparation = "Remove all metallic objects, MRI safety screening required"
        
        # Scheduling notes
        notes = "Schedule per departmental availability"
        if urgency == 'stat':
            notes = "Immediate scheduling required - contact radiology directly"
        elif urgency == 'urgent':
            notes = "Schedule within 24 hours"
        
        return {
            'duration': str(duration),
            'preparation': preparation,
            'notes': notes
        }
    
    def _get_cost_and_authorization_info(self, study_type: ImagingStudyType, 
                                       use_contrast: bool) -> Dict[str, Any]:
        """Get cost and authorization information."""
        
        # Base costs (simplified)
        base_costs = {
            ImagingStudyType.CHEST_XRAY: 150,
            ImagingStudyType.CT_HEAD: 800,
            ImagingStudyType.CT_CHEST: 1200,
            ImagingStudyType.CT_ABDOMEN: 1400,
            ImagingStudyType.MRI_BRAIN: 2500,
            ImagingStudyType.ECHO: 800
        }
        
        cost = base_costs.get(study_type, 1000)
        if use_contrast:
            cost += 300  # Additional cost for contrast
        
        # CPT codes (simplified)
        cpt_codes = {
            ImagingStudyType.CHEST_XRAY: '71020',
            ImagingStudyType.CT_CHEST: '71260' if use_contrast else '71250',
            ImagingStudyType.CT_ABDOMEN: '74177' if use_contrast else '74176'
        }
        
        # Authorization requirements
        high_cost_studies = [ImagingStudyType.MRI_BRAIN, ImagingStudyType.CT_ABDOMEN]
        auth_required = study_type in high_cost_studies
        
        return {
            'cost': cost,
            'cpt_code': cpt_codes.get(study_type, '00000'),
            'authorization_status': 'Prior authorization required' if auth_required else 'No authorization required'
        }
```

### Step 4: Register Your Tools

Add your tools to the `HealthcareTools` class:

```python
# In tools/healthcare_tools.py

class HealthcareTools:
    """Collection of healthcare-specific tools for agents."""
    
    def __init__(self):
        # Existing tools
        self.clinical_guidelines = ClinicalGuidelinesTool()
        self.medication_interaction_checker = MedicationInteractionTool()
        self.appointment_scheduler = AppointmentSchedulerTool()
        
        # New tools
        self.lab_order_tool = LabOrderTool()
        self.cardiac_risk_calculator = CardiacRiskCalculatorTool()
        self.imaging_protocol_tool = ImagingProtocolTool()

    def get_all_tools(self) -> List[BaseTool]:
        """Return all available healthcare tools."""
        return [
            self.clinical_guidelines,
            self.medication_interaction_checker,
            self.appointment_scheduler,
            self.lab_order_tool,
            self.cardiac_risk_calculator,
            self.imaging_protocol_tool,
        ]
    
    def get_tools_by_specialty(self, specialty: str) -> List[BaseTool]:
        """Get tools appropriate for a specific medical specialty."""
        specialty_mappings = {
            'emergency': [
                self.clinical_guidelines,
                self.lab_order_tool,
                self.imaging_protocol_tool
            ],
            'cardiology': [
                self.clinical_guidelines,
                self.cardiac_risk_calculator,
                self.lab_order_tool,
                self.imaging_protocol_tool
            ],
            'pharmacy': [
                self.medication_interaction_checker,
                self.clinical_guidelines
            ],
            'radiology': [
                self.imaging_protocol_tool
            ]
        }
        
        return specialty_mappings.get(specialty.lower(), self.get_all_tools())
```

### Step 5: Assign Tools to Agents

Update agent configurations to use your new tools:

```python
# In crew.py

@agent
def emergency_physician(self) -> Agent:
    return Agent(
        config=self.agents_config['emergency_physician'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            self.healthcare_tools.lab_order_tool,
            self.healthcare_tools.imaging_protocol_tool,
        ],
        llm=self.llm_config.llm,
        verbose=True
    )

@agent
def cardiologist(self) -> Agent:
    return Agent(
        config=self.agents_config['cardiologist'],
        tools=[
            self.healthcare_tools.clinical_guidelines,
            self.healthcare_tools.cardiac_risk_calculator,
            self.healthcare_tools.lab_order_tool,
        ],
        llm=self.llm_config.llm,
        verbose=True
    )
```

## Advanced Tool Features

### External API Integration

```python
import httpx
import asyncio

class EHRIntegrationTool(BaseTool):
    """Tool for integrating with Electronic Health Records."""
    
    name: str = "EHR Integration Tool"
    description: str = "Access patient data from Electronic Health Record system"
    
    def __init__(self, api_base_url: str, api_key: str):
        super().__init__()
        self.api_base_url = api_base_url
        self.api_key = api_key
        self.client = httpx.Client(
            base_url=api_base_url,
            headers={'Authorization': f'Bearer {api_key}'}
        )
    
    def _run(self, patient_id: str, data_type: str) -> str:
        """Retrieve patient data from EHR system."""
        try:
            response = self.client.get(f'/patients/{patient_id}/{data_type}')
            response.raise_for_status()
            
            data = response.json()
            return self._format_ehr_data(data, data_type)
            
        except httpx.HTTPError as e:
            return f"Error accessing EHR: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"
    
    def _format_ehr_data(self, data: dict, data_type: str) -> str:
        """Format EHR data for agent consumption."""
        if data_type == 'medications':
            return self._format_medications(data)
        elif data_type == 'allergies':
            return self._format_allergies(data)
        elif data_type == 'vitals':
            return self._format_vitals(data)
        else:
            return json.dumps(data, indent=2)
    
    def __del__(self):
        """Clean up HTTP client."""
        if hasattr(self, 'client'):
            self.client.close()
```

### Caching and Performance Optimization

```python
from functools import lru_cache
import hashlib
import pickle
from datetime import datetime, timedelta

class CachedHealthcareTool(BaseTool):
    """Base class for tools with caching capabilities."""
    
    def __init__(self, cache_duration_hours: int = 24):
        super().__init__()
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self._cache = {}
    
    def _get_cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        content = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached data is still valid."""
        return datetime.now() - timestamp < self.cache_duration
    
    def _get_cached_result(self, cache_key: str) -> Optional[str]:
        """Get cached result if valid."""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if self._is_cache_valid(timestamp):
                return result
            else:
                del self._cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: str) -> None:
        """Cache the result."""
        self._cache[cache_key] = (result, datetime.now())
    
    def _run_with_cache(self, *args, **kwargs) -> str:
        """Execute with caching support."""
        cache_key = self._get_cache_key(*args, **kwargs)
        
        # Try to get cached result
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return f"{cached_result}\n\n[Note: Result from cache]"
        
        # Execute and cache result
        result = self._execute(*args, **kwargs)
        self._cache_result(cache_key, result)
        
        return result
    
    def _execute(self, *args, **kwargs) -> str:
        """Override this method in subclasses."""
        raise NotImplementedError
```

### Tool Configuration and Customization

```python
class ConfigurableGuidelinesTool(ClinicalGuidelinesTool):
    """Configurable version of clinical guidelines tool."""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__()
        self.config = config or {}
        self.guideline_version = self.config.get('guideline_version', '2024')
        self.evidence_level_threshold = self.config.get('evidence_threshold', 'B')
        self.include_experimental = self.config.get('include_experimental', False)
    
    def _run(self, condition: str) -> str:
        """Get guidelines with configuration applied."""
        guidelines = super()._run(condition)
        
        # Apply configuration filters
        if not self.include_experimental:
            guidelines = self._filter_experimental(guidelines)
        
        guidelines = self._filter_by_evidence_level(guidelines)
        
        return f"""
        CLINICAL GUIDELINES ({self.guideline_version}):
        Evidence Level Threshold: {self.evidence_level_threshold}
        
        {guidelines}
        
        Configuration Notes:
        - Guideline Version: {self.guideline_version}
        - Evidence Threshold: {self.evidence_level_threshold}
        - Experimental Treatments: {'Included' if self.include_experimental else 'Excluded'}
        """
```

## Tool Testing and Validation

### Unit Testing Tools

```python
import pytest
from unittest.mock import Mock, patch

class TestLabOrderTool:
    
    def setup_method(self):
        self.tool = LabOrderTool()
    
    def test_basic_lab_order(self):
        """Test basic lab ordering functionality."""
        result = self.tool._run(
            patient_id="12345",
            test_types=[LabTestType.COMPLETE_BLOOD_COUNT],
            urgency="routine",
            clinical_indication="routine checkup",
            patient_age=45,
            patient_sex="M"
        )
        
        assert "LABORATORY ORDER PLACED" in result
        assert "Complete Blood Count" in result
        assert "12345" in result
    
    def test_stat_order_timing(self):
        """Test stat order completion time."""
        result = self.tool._run(
            patient_id="12345",
            test_types=[LabTestType.COMPLETE_BLOOD_COUNT],
            urgency="stat",
            clinical_indication="acute illness",
            patient_age=45,
            patient_sex="M"
        )
        
        # Check that completion time is within stat timeframe
        assert "stat" in result.lower()
        # Additional timing validation logic
    
    def test_medication_interaction_warnings(self):
        """Test medication interaction warnings."""
        result = self.tool._run(
            patient_id="12345",
            test_types=[LabTestType.COMPREHENSIVE_METABOLIC_PANEL],
            urgency="routine",
            clinical_indication="monitoring",
            patient_age=65,
            patient_sex="F",
            current_medications=["warfarin", "metformin"]
        )
        
        assert "anticoagulation" in result.lower()
    
    def test_invalid_input_handling(self):
        """Test handling of invalid inputs."""
        with pytest.raises(ValueError):
            self.tool._run(
                patient_id="",  # Invalid empty patient ID
                test_types=[],  # Invalid empty test list
                urgency="invalid_urgency",
                clinical_indication="test",
                patient_age=-5,  # Invalid age
                patient_sex="X"  # Invalid sex
            )

class TestCardiacRiskCalculator:
    
    def setup_method(self):
        self.tool = CardiacRiskCalculatorTool()
    
    def test_low_risk_patient(self):
        """Test low-risk patient calculation."""
        result = self.tool._run(
            age=35, sex="F", total_cholesterol=180, hdl_cholesterol=55,
            systolic_bp=115, smoker=False, diabetes=False
        )
        
        assert "low" in result.lower()
        assert "lifestyle modifications" in result.lower()
    
    def test_high_risk_patient(self):
        """Test high-risk patient calculation."""
        result = self.tool._run(
            age=65, sex="M", total_cholesterol=280, hdl_cholesterol=35,
            systolic_bp=165, smoker=True, diabetes=True
        )
        
        assert "high" in result.lower()
        assert "statin therapy" in result.lower()
        assert "smoking cessation" in result.lower()
    
    def test_boundary_conditions(self):
        """Test boundary conditions."""
        # Test minimum age
        result = self.tool._run(
            age=20, sex="M", total_cholesterol=150, hdl_cholesterol=45,
            systolic_bp=120, smoker=False, diabetes=False
        )
        assert "CARDIAC RISK ASSESSMENT" in result
        
        # Test maximum values
        result = self.tool._run(
            age=120, sex="F", total_cholesterol=400, hdl_cholesterol=100,
            systolic_bp=250, smoker=True, diabetes=True
        )
        assert "very high" in result.lower()
```

### Integration Testing

```python
def test_tool_integration_with_agents():
    """Test how tools integrate with agents."""
    crew = HealthcareSimulationCrew()
    
    # Create agent with multiple tools
    agent = Agent(
        role="Emergency Physician",
        goal="Provide comprehensive emergency care",
        tools=[
            crew.healthcare_tools.lab_order_tool,
            crew.healthcare_tools.imaging_protocol_tool,
            crew.healthcare_tools.clinical_guidelines
        ],
        llm=crew.llm_config.llm
    )
    
    # Test agent can access all tools
    assert len(agent.tools) == 3
    tool_names = [tool.name for tool in agent.tools]
    assert "Laboratory Order Tool" in tool_names
    assert "Imaging Protocol Tool" in tool_names
    assert "Clinical Guidelines Search" in tool_names

def test_tool_performance():
    """Test tool performance and response times."""
    tool = LabOrderTool()
    
    import time
    start_time = time.time()
    
    result = tool._run(
        patient_id="12345",
        test_types=[LabTestType.COMPLETE_BLOOD_COUNT, LabTestType.COMPREHENSIVE_METABOLIC_PANEL],
        urgency="routine",
        clinical_indication="annual physical",
        patient_age=45,
        patient_sex="M"
    )
    
    execution_time = time.time() - start_time
    
    assert execution_time < 5.0  # Should complete within 5 seconds
    assert len(result) > 100  # Should provide substantial output
```

### Clinical Validation

```python
def validate_clinical_accuracy(tool_output: str, expected_elements: List[str]) -> bool:
    """Validate tool output for clinical accuracy."""
    
    # Check for required clinical elements
    for element in expected_elements:
        if element.lower() not in tool_output.lower():
            return False
    
    # Check for contraindicated recommendations
    contraindications = [
        'double dose', 'exceed maximum', 'contraindicated combination'
    ]
    
    for contraindication in contraindications:
        if contraindication in tool_output.lower():
            return False
    
    return True

def test_guidelines_compliance():
    """Test tool compliance with clinical guidelines."""
    tool = ClinicalGuidelinesTool()
    
    # Test chest pain guidelines
    result = tool._run("chest pain")
    
    # Should include evidence-based elements
    required_elements = ['ecg', 'troponin', 'aspirin', 'heart score']
    assert validate_clinical_accuracy(result, required_elements)
    
    # Should not include contraindicated recommendations
    assert 'contraindicated' not in result.lower()
```

## Best Practices for Tool Extension

### 1. Clinical Accuracy and Safety
- Base tool logic on current clinical guidelines and evidence
- Include appropriate safety checks and contraindication screening
- Validate outputs against professional standards
- Provide clear rationale for recommendations

### 2. User Experience
- Design intuitive input schemas with clear field descriptions
- Provide comprehensive, well-formatted outputs
- Include relevant clinical context and recommendations
- Handle edge cases gracefully with informative messages

### 3. Performance and Reliability
- Implement appropriate caching for expensive operations
- Include proper error handling and fallback mechanisms
- Optimize for common use cases while supporting edge cases
- Monitor tool performance and usage patterns

### 4. Integration and Compatibility
- Design tools to work seamlessly with existing agents and workflows
- Follow consistent naming and output format conventions
- Provide configuration options for different use cases
- Support both individual and batch operations when appropriate

## Common Pitfalls to Avoid

1. **Overly Complex Inputs**: Keep input schemas simple and focused
2. **Poor Error Handling**: Always handle exceptions gracefully
3. **Inconsistent Outputs**: Maintain consistent format and terminology
4. **Missing Validation**: Validate inputs and provide meaningful feedback
5. **Performance Issues**: Consider caching and optimization for slow operations
6. **Clinical Inaccuracy**: Always validate against current medical standards

## Conclusion

Healthcare tools are critical components that provide specialized functionality to agents in the simulation system. Focus on clinical accuracy, user experience, and seamless integration when developing new tools. Always validate against current healthcare standards and consider real-world constraints and safety requirements.