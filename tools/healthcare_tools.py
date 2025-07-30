from typing import Dict, Any, List, Optional
from crewai.tools import BaseTool
from datetime import datetime, timedelta

class HealthcareTools:
    """Custom tools for healthcare simulation agents"""
    
    @staticmethod
    def clinical_guidelines_tool() -> BaseTool:
        """Creates a tool that provides access to clinical guidelines."""
        
        def get_clinical_guidelines(condition: str) -> str:
            """
            Get evidence-based clinical guidelines for a specific condition.
            Args:
                condition: The medical condition to get guidelines for
            Returns:
                String containing clinical guidelines for the condition
            """
            # Simulated guidelines database (would be replaced with actual guidelines API)
            guidelines_db = {
                "chest pain": """
                    CHEST PAIN CLINICAL GUIDELINES:
                    1. Assessment: Evaluate vital signs, conduct ECG within 10 minutes of arrival
                    2. Risk Stratification: Use HEART score for risk assessment
                    3. Diagnostics: Serial troponin at 0 and 3 hours
                    4. Imaging: Consider chest X-ray and CT coronary angiography for intermediate risk
                    5. Treatment: Aspirin 325mg immediately for suspected ACS
                    6. Disposition: High-risk patients require admission; low-risk with negative workup may be discharged
                """,
                "hypertension": """
                    HYPERTENSION CLINICAL GUIDELINES:
                    1. Diagnosis: BP ≥130/80 mm Hg on two separate visits
                    2. Classification: Stage 1 (130-139/80-89), Stage 2 (≥140/90)
                    3. Non-pharmacological: Diet, exercise, sodium restriction, weight management
                    4. Pharmacological first-line: ACE inhibitors, ARBs, CCBs, or thiazide diuretics
                    5. Target BP: <130/80 mm Hg for most adults
                    6. Follow-up: Every 3-6 months until BP controlled, then every 6-12 months
                """,
                "diabetes mellitus": """
                    DIABETES MELLITUS CLINICAL GUIDELINES:
                    1. Screening: Every 3 years in adults over 45, or earlier with risk factors
                    2. Diagnosis: HbA1c ≥6.5%, FPG ≥126 mg/dL, or 2-hr PG ≥200 mg/dL during OGTT
                    3. Management: Target HbA1c <7%, individualized based on patient factors
                    4. Pharmacotherapy: Metformin as first-line therapy, add additional agents based on comorbidities
                    5. Monitoring: HbA1c every 3-6 months, annual eye and foot examination
                    6. Complications screening: Microalbuminuria, neuropathy, retinopathy, cardiovascular risk
                """
            }
            
            # Case-insensitive search
            condition_lower = condition.lower()
            for key, guidelines in guidelines_db.items():
                if condition_lower in key or key in condition_lower:
                    return guidelines
            
            return f"No specific guidelines found for {condition}. Recommend consulting latest medical literature."
            
        return BaseTool(
            name="Clinical Guidelines Search",
            description="Search for evidence-based clinical guidelines for specific conditions",
            func=get_clinical_guidelines
        )
    
    @staticmethod
    def medication_interaction_tool() -> BaseTool:
        """Creates a tool for checking medication interactions."""
        
        def check_medication_interactions(medications: str) -> str:
            """
            Check for potential interactions between multiple medications.
            Args:
                medications: Comma-separated list of medications to check
            Returns:
                String describing potential interactions
            """
            med_list = [med.strip().lower() for med in medications.split(",")]
            
            # Simulated interaction database (would be replaced with actual drug interaction API)
            known_interactions = {
                ("aspirin", "warfarin"): "High-risk bleeding interaction. Concurrent use may significantly increase bleeding risk.",
                ("lisinopril", "potassium"): "Moderate interaction. May cause hyperkalemia. Monitor potassium levels.",
                ("amiodarone", "simvastatin"): "Severe interaction. Increased risk of myopathy/rhabdomyolysis. Consider dose reduction or alternative.",
                ("fluoxetine", "tramadol"): "Severe interaction. Increased risk of serotonin syndrome. Avoid combination if possible.",
                ("ciprofloxacin", "theophylline"): "Moderate interaction. May increase theophylline levels. Monitor levels and adjust dose.",
            }
            
            interactions = []
            for i, med1 in enumerate(med_list):
                for med2 in med_list[i+1:]:
                    if (med1, med2) in known_interactions:
                        interactions.append(f"{med1.capitalize()} + {med2.capitalize()}: {known_interactions[(med1, med2)]}")
                    elif (med2, med1) in known_interactions:
                        interactions.append(f"{med1.capitalize()} + {med2.capitalize()}: {known_interactions[(med2, med1)]}")
            
            if interactions:
                return "POTENTIAL INTERACTIONS DETECTED:\n" + "\n".join(interactions)
            else:
                return "No known interactions between the provided medications."
                
        return BaseTool(
            name="Medication Interaction Checker",
            description="Check for potential interactions between multiple medications",
            func=check_medication_interactions
        )
    
    @staticmethod
    def appointment_scheduler_tool() -> BaseTool:
        """Creates a tool for scheduling patient appointments."""
        
        def schedule_appointment(
            appointment_type: str, 
            duration_minutes: int = 30,
            preferred_date: Optional[str] = None
        ) -> str:
            """
            Schedule a patient appointment.
            Args:
                appointment_type: Type of appointment (e.g., follow-up, imaging)
                duration_minutes: Duration of appointment in minutes
                preferred_date: Preferred date for appointment (YYYY-MM-DD)
            Returns:
                String with appointment details
            """
            # Start from today or preferred date
            if preferred_date:
                try:
                    start_date = datetime.strptime(preferred_date, "%Y-%m-%d")
                except ValueError:
                    start_date = datetime.now() + timedelta(days=1)
            else:
                start_date = datetime.now() + timedelta(days=1)
            
            # Simulate scheduling logic (would be replaced with actual calendar API)
            appointment_types = {
                "follow-up": {"providers": ["Dr. Smith", "Dr. Johnson"], "lead_time_days": 7},
                "imaging": {"providers": ["Radiology Dept"], "lead_time_days": 5},
                "lab": {"providers": ["Lab Services"], "lead_time_days": 2},
                "specialist": {"providers": ["Dr. Specialist"], "lead_time_days": 14},
                "physical therapy": {"providers": ["PT Department"], "lead_time_days": 3}
            }
            
            # Find the appointment type (case-insensitive partial match)
            matched_type = None
            for apt_type in appointment_types:
                if apt_type in appointment_type.lower():
                    matched_type = apt_type
                    break
            
            if not matched_type:
                return f"Unable to schedule: Unknown appointment type '{appointment_type}'"
            
            # Calculate appointment date and time
            apt_info = appointment_types[matched_type]
            apt_date = start_date + timedelta(days=apt_info["lead_time_days"])
            
            # Format time as business hours (9-5)
            hour = 9 + (apt_date.day % 7)  # Distribute across the day
            if hour > 16:
                hour = 9  # Reset to morning if would be after 4pm
            
            apt_time = f"{hour:02d}:{(apt_date.minute//15)*15:02d}"
            provider = apt_info["providers"][apt_date.day % len(apt_info["providers"])]
            
            return f"""
            APPOINTMENT SCHEDULED
            Type: {appointment_type}
            Provider: {provider}
            Date: {apt_date.strftime('%Y-%m-%d')}
            Time: {apt_time}
            Duration: {duration_minutes} minutes
            Location: Main Hospital Campus
            Instructions: Please arrive 15 minutes early to complete registration.
            """
                
        return BaseTool(
            name="Appointment Scheduler",
            description="Schedule patient appointments for various medical services",
            func=schedule_appointment
        )