import streamlit as st
import os
import json
import re
from datetime import datetime, timedelta
from crew import HealthcareSimulationCrew
from llm_config import create_llm_config, get_available_backends, LLMBackend
from sample_data.sample_messages import SAMPLE_MESSAGES, list_scenarios, get_message
import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions for parsing simulation results
def parse_diagnostic_results(result_text: str) -> Dict[str, Any]:
    """Parse diagnostic assessment from simulation results."""
    diagnostics = {
        'diagnoses': [],
        'confidence_scores': {},
        'supporting_evidence': [],
        'recommended_tests': [],
        'risk_factors': []
    }
    
    # Extract diagnoses and confidence scores using regex patterns
    diagnosis_patterns = [
        r'(?:diagnosis|condition|probable|likely).*?:?\s*([A-Za-z\s,]+)(?:\s*[-–]\s*(\d+\.?\d*)%?|\s*confidence:\s*(\d+\.?\d*)%?)?',
        r'(\d+\.?\d*)%?\s*(?:confidence|probability|likelihood).*?([A-Za-z\s,]+)',
        r'([A-Za-z\s,]+).*?(\d+\.?\d*)%?\s*(?:confidence|probability|likelihood)'
    ]
    
    # Extract structured information from text
    lines = result_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identify sections
        if any(keyword in line.lower() for keyword in ['diagnosis', 'diagnostic', 'condition']):
            current_section = 'diagnoses'
        elif any(keyword in line.lower() for keyword in ['evidence', 'support', 'finding']):
            current_section = 'evidence'
        elif any(keyword in line.lower() for keyword in ['test', 'investigation', 'recommend']):
            current_section = 'tests'
        elif any(keyword in line.lower() for keyword in ['risk', 'factor']):
            current_section = 'risks'
        
        # Extract confidence scores
        confidence_match = re.search(r'(\d+\.?\d*)%?\s*(?:confidence|probability|likelihood)', line.lower())
        if confidence_match:
            score = float(confidence_match.group(1))
            if score > 1:  # Assume percentage
                score = score / 100
            # Try to find the associated diagnosis
            diag_text = re.sub(r'\d+\.?\d*%?\s*(?:confidence|probability|likelihood)', '', line, flags=re.IGNORECASE).strip()
            if diag_text:
                diagnostics['confidence_scores'][diag_text] = score
        
        # Extract bullet points or numbered items
        if re.match(r'^[\s]*[-*•]\s*', line) or re.match(r'^[\s]*\d+\.?\s*', line):
            clean_line = re.sub(r'^[\s]*[-*•\d.]\s*', '', line).strip()
            if current_section == 'diagnoses':
                diagnostics['diagnoses'].append(clean_line)
            elif current_section == 'evidence':
                diagnostics['supporting_evidence'].append(clean_line)
            elif current_section == 'tests':
                diagnostics['recommended_tests'].append(clean_line)
            elif current_section == 'risks':
                diagnostics['risk_factors'].append(clean_line)
    
    # If no structured diagnoses found, try to extract from general text
    if not diagnostics['diagnoses']:
        common_conditions = [
            'acute coronary syndrome', 'myocardial infarction', 'heart attack',
            'hypertension', 'diabetes', 'stroke', 'pneumonia', 'bronchitis',
            'chest pain', 'angina', 'heart failure', 'arrhythmia'
        ]
        
        for condition in common_conditions:
            if condition.lower() in result_text.lower():
                diagnostics['diagnoses'].append(condition.title())
    
    return diagnostics

def parse_treatment_plan(result_text: str) -> Dict[str, Any]:
    """Parse treatment plan from simulation results."""
    treatment = {
        'medications': [],
        'therapies': [],
        'lifestyle_modifications': [],
        'follow_up_schedule': [],
        'precautions': []
    }
    
    lines = result_text.split('\n')
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Identify sections
        if any(keyword in line.lower() for keyword in ['medication', 'drug', 'prescription']):
            current_section = 'medications'
        elif any(keyword in line.lower() for keyword in ['therapy', 'treatment', 'procedure']):
            current_section = 'therapies'
        elif any(keyword in line.lower() for keyword in ['lifestyle', 'diet', 'exercise', 'modification']):
            current_section = 'lifestyle'
        elif any(keyword in line.lower() for keyword in ['follow-up', 'followup', 'appointment', 'schedule']):
            current_section = 'follow_up'
        elif any(keyword in line.lower() for keyword in ['precaution', 'warning', 'contraindication']):
            current_section = 'precautions'
        
        # Extract structured items
        if re.match(r'^[\s]*[-*•]\s*', line) or re.match(r'^[\s]*\d+\.?\s*', line):
            clean_line = re.sub(r'^[\s]*[-*•\d.]\s*', '', line).strip()
            if current_section == 'medications':
                treatment['medications'].append(clean_line)
            elif current_section == 'therapies':
                treatment['therapies'].append(clean_line)
            elif current_section == 'lifestyle':
                treatment['lifestyle_modifications'].append(clean_line)
            elif current_section == 'follow_up':
                treatment['follow_up_schedule'].append(clean_line)
            elif current_section == 'precautions':
                treatment['precautions'].append(clean_line)
    
    return treatment

def extract_care_timeline_events(result_text: str, patient_info: Dict = None) -> List[Dict[str, Any]]:
    """Extract timeline events from simulation results."""
    events = []
    
    # Add initial assessment
    events.append({
        'date': datetime.now().strftime('%Y-%m-%d'),
        'time': '08:00',
        'event_type': 'Assessment',
        'title': 'Initial Patient Assessment',
        'description': 'Patient admitted and initial assessment completed',
        'status': 'completed'
    })
    
    # Extract scheduled appointments and procedures from text
    lines = result_text.split('\n')
    for line in lines:
        line = line.strip().lower()
        if not line:
            continue
            
        # Look for appointment/procedure mentions
        if any(keyword in line for keyword in ['appointment', 'schedule', 'follow-up', 'procedure', 'test']):
            # Try to extract date/time information
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}-\d{2}-\d{2})', line)
            time_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[ap]m)?)', line)
            
            event_date = date_match.group(1) if date_match else (datetime.now() + timedelta(days=len(events))).strftime('%Y-%m-%d')
            event_time = time_match.group(1) if time_match else f"{9 + len(events)}:00"
            
            # Determine event type and title
            if 'follow-up' in line:
                event_type = 'Follow-up'
                title = 'Follow-up Appointment'
            elif 'test' in line or 'lab' in line:
                event_type = 'Test'
                title = 'Laboratory Tests'
            elif 'procedure' in line:
                event_type = 'Procedure'
                title = 'Medical Procedure'
            else:
                event_type = 'Appointment'
                title = 'Medical Appointment'
            
            events.append({
                'date': event_date,
                'time': event_time,
                'event_type': event_type,
                'title': title,
                'description': line.title(),
                'status': 'scheduled'
            })
    
    # Add some default follow-up events if none were found
    if len(events) == 1:  # Only initial assessment
        base_date = datetime.now()
        events.extend([
            {
                'date': (base_date + timedelta(days=3)).strftime('%Y-%m-%d'),
                'time': '10:00',
                'event_type': 'Test',
                'title': 'Laboratory Follow-up',
                'description': 'Follow-up laboratory tests',
                'status': 'scheduled'
            },
            {
                'date': (base_date + timedelta(days=7)).strftime('%Y-%m-%d'),
                'time': '14:00',
                'event_type': 'Follow-up',
                'title': 'Clinical Follow-up',
                'description': 'Follow-up appointment with primary care physician',
                'status': 'scheduled'
            },
            {
                'date': (base_date + timedelta(days=30)).strftime('%Y-%m-%d'),
                'time': '09:00',
                'event_type': 'Assessment',
                'title': 'Treatment Assessment',
                'description': 'Assess treatment effectiveness and adjust plan if needed',
                'status': 'scheduled'
            }
        ])
    
    return sorted(events, key=lambda x: f"{x['date']} {x['time']}")

def create_diagnostic_confidence_chart(diagnostics: Dict[str, Any]) -> go.Figure:
    """Create a confidence score chart for diagnoses."""
    if not diagnostics['confidence_scores'] and diagnostics['diagnoses']:
        # Create mock confidence scores if none exist
        confidence_scores = {}
        for i, diagnosis in enumerate(diagnostics['diagnoses'][:5]):  # Top 5
            confidence_scores[diagnosis] = max(0.3, 0.9 - (i * 0.15))  # Decreasing confidence
        diagnostics['confidence_scores'] = confidence_scores
    
    if not diagnostics['confidence_scores']:
        # Default sample data
        diagnostics['confidence_scores'] = {
            'Acute Coronary Syndrome': 0.82,
            'Musculoskeletal Pain': 0.45,
            'GERD': 0.38,
            'Anxiety': 0.25
        }
    
    # Prepare data
    diagnoses = list(diagnostics['confidence_scores'].keys())
    scores = list(diagnostics['confidence_scores'].values())
    
    # Create horizontal bar chart
    fig = go.Figure(data=[
        go.Bar(
            y=diagnoses,
            x=scores,
            orientation='h',
            marker=dict(
                color=scores,
                colorscale='RdYlGn',
                colorbar=dict(title="Confidence"),
                line=dict(color='rgba(50,50,50,0.8)', width=1)
            ),
            text=[f"{score:.1%}" for score in scores],
            textposition='auto'
        )
    ])
    
    fig.update_layout(
        title="Diagnostic Confidence Scores",
        xaxis_title="Confidence Level",
        yaxis_title="Diagnosis",
        height=max(300, len(diagnoses) * 50),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_timeline_chart(events: List[Dict[str, Any]]) -> go.Figure:
    """Create an interactive timeline chart."""
    if not events:
        return go.Figure()
    
    # Convert events to timeline format
    dates = []
    titles = []
    descriptions = []
    colors = []
    statuses = []
    
    color_map = {
        'Assessment': '#1f77b4',
        'Test': '#ff7f0e',
        'Procedure': '#2ca02c',
        'Follow-up': '#d62728',
        'Appointment': '#9467bd'
    }
    
    for event in events:
        event_datetime = datetime.strptime(f"{event['date']} {event['time']}", '%Y-%m-%d %H:%M')
        dates.append(event_datetime)
        titles.append(event['title'])
        descriptions.append(event['description'])
        colors.append(color_map.get(event['event_type'], '#7f7f7f'))
        statuses.append(event['status'])
    
    fig = go.Figure()
    
    # Add timeline points
    for i, (date, title, desc, color, status) in enumerate(zip(dates, titles, descriptions, colors, statuses)):
        marker_symbol = 'circle' if status == 'completed' else 'diamond'
        marker_size = 12 if status == 'completed' else 10
        
        fig.add_trace(go.Scatter(
            x=[date],
            y=[i],
            mode='markers+text',
            marker=dict(
                color=color,
                size=marker_size,
                symbol=marker_symbol,
                line=dict(width=2, color='white')
            ),
            text=title,
            textposition='middle right',
            textfont=dict(size=10),
            hovertemplate=f"<b>{title}</b><br>{desc}<br>%{{x}}<br>Status: {status}<extra></extra>",
            showlegend=False,
            name=title
        ))
    
    # Add connecting line
    fig.add_trace(go.Scatter(
        x=dates,
        y=list(range(len(dates))),
        mode='lines',
        line=dict(color='lightblue', width=2, dash='dash'),
        showlegend=False,
        hoverinfo='skip'
    ))
    
    fig.update_layout(
        title="Patient Care Timeline",
        xaxis_title="Date",
        yaxis=dict(
            showticklabels=False,
            showgrid=False,
            zeroline=False
        ),
        height=max(400, len(events) * 60),
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='closest'
    )
    
    return fig

# Page configuration
st.set_page_config(
    page_title="Care Pathway Simulator Dashboard",
    page_icon="🏥",
    layout="wide",
)

# Header
st.title("🏥 Synthetic Care Pathway Simulator")
st.markdown("### Interactive Dashboard for Healthcare Simulation")

# Sidebar configuration
st.sidebar.header("Configuration")

# LLM Backend selection
available_backends = get_available_backends()
selected_backend = st.sidebar.selectbox(
    "LLM Backend",
    options=available_backends,
    index=0,
    help="Choose the LLM backend to use for the simulation"
)

# API Key input (conditional based on backend)
api_key = None
if selected_backend == "openai":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
elif selected_backend == "openrouter":
    api_key = st.sidebar.text_input("Openrouter API Key", type="password", 
                                   help="Get your API key from https://openrouter.ai")
elif selected_backend == "ollama":
    api_key = st.sidebar.text_input("Ollama API Key (optional)", type="password",
                                   help="Leave empty for local Ollama instance")

# Model selection
model_help = {
    "openai": "e.g., gpt-4, gpt-3.5-turbo",
    "openrouter": "e.g., openai/gpt-4, anthropic/claude-3-opus",
    "ollama": "e.g., llama2, codellama, mistral"
}

model = st.sidebar.text_input(
    "Model Name (optional)", 
    help=f"Model to use. Examples: {model_help.get(selected_backend, '')}"
)

# Base URL (for advanced users)
with st.sidebar.expander("Advanced Settings"):
    base_url = st.sidebar.text_input(
        "Base URL (optional)",
        help="Custom API endpoint URL"
    )
    
    temperature = st.sidebar.slider(
        "Temperature",
        min_value=0.0,
        max_value=2.0,
        value=0.7,
        step=0.1,
        help="Controls randomness in responses"
    )

# Scenario selection
scenario_options = list_scenarios()
selected_scenario = st.sidebar.selectbox(
    "Select Patient Scenario", 
    options=scenario_options,
    index=0
)

# Custom HL7 message input
custom_hl7 = st.sidebar.text_area(
    "Or enter custom HL7 message",
    height=150,
    help="Paste a custom HL7 message here to override the selected scenario"
)

# Test connection button
test_connection_button = st.sidebar.button("Test Connection", help="Test connection to the selected LLM backend")

# Run simulation button
run_button = st.sidebar.button("Run Simulation", type="primary")

# Demo mode button (for testing without API key)
demo_button = st.sidebar.button("Run Demo", help="Test dashboard features with mock data")

# Initialize session state for storing results
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None
if "patient_info" not in st.session_state:
    st.session_state.patient_info = None
if "simulation_timestamp" not in st.session_state:
    st.session_state.simulation_timestamp = None

# Function to create mock simulation results for demo
def create_mock_simulation_results(scenario: str) -> str:
    """Create realistic mock simulation results for demo purposes."""
    mock_results = f"""
    HEALTHCARE SIMULATION REPORT - Patient Care Pathway Analysis
    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    Scenario: {scenario.title()}
    
    === DATA INGESTION RESULTS ===
    Patient ID: {scenario.upper()}_001
    Message validation: PASSED
    Data extraction: SUCCESS
    Quality score: 95%
    
    === DIAGNOSTIC ASSESSMENT ===
    Primary Analysis:
    - Acute Coronary Syndrome: 82% confidence
      Supporting evidence: Elevated troponin levels, characteristic chest pain, ECG changes
    - Musculoskeletal Pain: 45% confidence  
      Supporting evidence: Pain pattern, patient history
    - Gastroesophageal Reflux: 38% confidence
      Supporting evidence: Temporal pattern, symptom description
    - Anxiety Disorder: 25% confidence
      Supporting evidence: Patient presentation, stress factors
      
    Risk Factors Identified:
    - Hypertension (systolic BP 142 mmHg)
    - Family history of cardiovascular disease
    - Age-related risk factors
    - Elevated cholesterol levels
    
    Recommended Additional Tests:
    - Serial cardiac enzymes q6h x 3
    - Echocardiogram
    - Stress testing if appropriate
    - Lipid panel
    
    === TREATMENT PLAN ===
    Immediate Interventions:
    - Aspirin 325mg immediately, then 81mg daily
    - Atorvastatin 40mg daily at bedtime
    - Metoprolol 25mg twice daily
    - Nitroglycerin SL PRN chest pain
    
    Therapies and Procedures:
    - Cardiac catheterization within 24 hours if indicated
    - Continuous cardiac monitoring x 24 hours
    - Physical therapy consultation
    
    Lifestyle Modifications:
    - Heart-healthy diet (Mediterranean style preferred)
    - Smoking cessation counseling if applicable
    - Exercise program (cardiac rehabilitation)
    - Weight management (target BMI 18.5-24.9)
    - Stress reduction techniques
    
    Follow-up Schedule:
    - Cardiology appointment in 1-2 weeks
    - Primary care follow-up in 3-5 days
    - Laboratory work in 6-8 weeks
    - Repeat echocardiogram in 3 months
    
    Precautions and Warnings:
    - Monitor for bleeding with anticoagulation
    - Watch for signs of heart failure
    - Avoid NSAIDs due to cardiovascular risk
    - Emergency return precautions provided
    
    === CARE COORDINATION ===
    Appointments Scheduled:
    - Cardiology consultation: Next Tuesday 10:00 AM
    - Laboratory draw: Friday 8:00 AM  
    - Physical therapy evaluation: Next Wednesday 2:00 PM
    - Primary care follow-up: One week from discharge
    
    Care Transitions:
    - Telemetry monitoring for 24 hours
    - Step-down to medical floor if stable
    - Discharge planning initiated
    - Home health services arranged
    
    === OUTCOME EVALUATION ===
    Expected Outcomes:
    - Symptom resolution within 24-48 hours
    - Stable cardiac enzymes by 12 hours
    - Safe discharge within 2-3 days
    - 30-day readmission risk: LOW (8%)
    
    Monitoring Parameters:
    - Vital signs q4h
    - Daily weights
    - I/O monitoring
    - Pain assessment q2h
    
    Quality Metrics:
    - Door-to-balloon time: N/A (no intervention needed)
    - Length of stay: Projected 2 days
    - Patient satisfaction: Target >90%
    - Medication adherence: High priority
    """
    return mock_results

# Function to run the simulation
def run_simulation() -> None:
    # Validate API key for backends that require it
    if selected_backend in ["openai", "openrouter"] and not api_key:
        st.error(f"Please enter your {selected_backend.title()} API key in the sidebar")
        return
    
    # Display a spinner during simulation
    with st.spinner("Running care pathway simulation..."):
        try:
            # Create LLM configuration
            llm_config = create_llm_config(
                backend=selected_backend,
                api_key=api_key,
                model=model if model else None,
                base_url=base_url if base_url else None,
                temperature=temperature
            )
            
            # Initialize the simulation crew with LLM configuration
            sim_crew = HealthcareSimulationCrew(llm_config=llm_config)
            
        except Exception as e:
            st.error(f"Failed to configure LLM backend: {str(e)}")
            return
        
        # Get the HL7 message (custom or from selected scenario)
        hl7_message = custom_hl7 if custom_hl7.strip() else get_message(selected_scenario)
        
        try:
            # Run the simulation
            result = sim_crew.crew().kickoff(inputs={"hl7_message": hl7_message})
            
            # Store results in session state
            st.session_state.simulation_results = result
            st.session_state.simulation_timestamp = datetime.now()
            
            # Access structured patient information
            retrieved_patient_info = sim_crew.patient_data.get('patient_info')
            validation_issues = sim_crew.validation_issues

            if retrieved_patient_info:
                st.session_state.patient_info = retrieved_patient_info
            else:
                st.session_state.patient_info = None
                st.warning("Could not retrieve structured patient information after simulation.")

            if validation_issues:
                st.warning("HL7 Message Validation Issues:")
                for issue in validation_issues:
                    st.warning(f"- {issue.get('error_type', 'Error')}: {issue.get('message', 'Unknown issue')}")
                
        except Exception as e:
            st.error(f"Simulation failed: {str(e)}")
            st.session_state.simulation_results = None

# Test connection if button clicked
if test_connection_button:
    if selected_backend in ["openai", "openrouter"] and not api_key:
        st.sidebar.error(f"Please enter your {selected_backend.title()} API key first")
    else:
        try:
            from llm_config import test_connection
            llm_config = create_llm_config(
                backend=selected_backend,
                api_key=api_key,
                model=model if model else None,
                base_url=base_url if base_url else None,
                temperature=temperature
            )
            
            with st.spinner("Testing connection..."):
                if test_connection(llm_config):
                    st.sidebar.success(f"✅ Connection to {selected_backend} successful!")
                else:
                    st.sidebar.error(f"❌ Connection to {selected_backend} failed!")
        except Exception as e:
            st.sidebar.error(f"Connection test failed: {str(e)}")

# Run simulation if button clicked
if run_button:
    run_simulation()

# Run demo simulation if button clicked
if demo_button:
    st.success("Running demo simulation with mock data...")
    
    # Create mock results
    mock_result_text = create_mock_simulation_results(selected_scenario)
    
    # Create a mock result object that mimics the actual simulation result
    class MockResult:
        def __init__(self, text):
            self.raw = text
    
    # Store mock results in session state
    st.session_state.simulation_results = MockResult(mock_result_text)
    st.session_state.simulation_timestamp = datetime.now()
    
    # Create mock patient info
    scenario_patients = {
        'chest_pain': {
            'id': 'CHEST_PAIN_001',
            'name': 'SMITH^JOHN^M',
            'dob': '1965-03-12',
            'gender': 'M',
            'address': '123 MAIN ST, BOSTON, MA 02115'
        },
        'diabetes': {
            'id': 'DIABETES_001', 
            'name': 'JOHNSON^EMILY^F',
            'dob': '1958-07-24',
            'gender': 'F',
            'address': '456 OAK DR, CHICAGO, IL 60601'
        },
        'pediatric': {
            'id': 'PEDIATRIC_001',
            'name': 'WILLIAMS^EMMA^F', 
            'dob': '2021-05-02',
            'gender': 'F',
            'address': '789 PINE ST, SEATTLE, WA 98101'
        },
        'surgical': {
            'id': 'SURGICAL_001',
            'name': 'BROWN^ROBERT^M',
            'dob': '1948-06-15', 
            'gender': 'M',
            'address': '101 CEDAR LN, DENVER, CO 80201'
        },
        'stroke': {
            'id': 'STROKE_001',
            'name': 'DAVIS^PATRICIA^F',
            'dob': '1952-08-30',
            'gender': 'F', 
            'address': '222 MAPLE AVE, MIAMI, FL 33101'
        }
    }
    
    st.session_state.patient_info = scenario_patients.get(selected_scenario, scenario_patients['chest_pain'])
    
    # Rerun to refresh the display
    st.rerun()

# Display results if available
if st.session_state.simulation_results:
    # Success message
    st.success("Simulation completed successfully!")
    
    # Show timestamp
    st.write(f"Simulation ran at: {st.session_state.simulation_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create tabs for different sections of the results
    tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Diagnostics", "Treatment Plan", "Care Timeline"])
    
    with tab1:
        st.header("Patient Overview")
        
        # Display patient info if available
        if st.session_state.patient_info:
            patient_info = st.session_state.patient_info
            
            # Display key patient demographics
            st.subheader("Patient Demographics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Patient ID", patient_info.get("id", "N/A"))
                st.metric("Name", patient_info.get("name", "N/A"))
            with col2:
                st.metric("DOB", patient_info.get("dob", "N/A"))
                st.metric("Gender", patient_info.get("gender", "N/A"))
            with col3:
                st.metric("Address", patient_info.get("address", "N/A"))
                st.metric("Status", "Active") # Assuming 'Active' or derive if available
        else:
            st.info("Patient demographics not available.")
        
        # Display full results in an expander
        with st.expander("Full Simulation Results", expanded=True):
            if hasattr(st.session_state.simulation_results, 'raw'):
                st.text_area("", st.session_state.simulation_results.raw, height=300)
            else:
                st.text_area("", str(st.session_state.simulation_results), height=300)
    
    with tab2:
        st.header("Diagnostic Assessment")
        
        if st.session_state.simulation_results:
            # Parse diagnostic results from simulation
            result_text = ""
            if hasattr(st.session_state.simulation_results, 'raw'):
                result_text = st.session_state.simulation_results.raw
            else:
                result_text = str(st.session_state.simulation_results)
            
            diagnostics = parse_diagnostic_results(result_text)
            
            # Display diagnostic information
            if diagnostics['diagnoses']:
                st.subheader("Identified Conditions")
                for i, diagnosis in enumerate(diagnostics['diagnoses'][:5], 1):
                    confidence = diagnostics['confidence_scores'].get(diagnosis, 0.5)
                    st.write(f"{i}. **{diagnosis}** (Confidence: {confidence:.1%})")
            
            # Display confidence chart
            if diagnostics['confidence_scores']:
                st.subheader("Diagnostic Confidence")
                fig = create_diagnostic_confidence_chart(diagnostics)
                st.plotly_chart(fig, use_container_width=True)
            
            # Display supporting evidence
            if diagnostics['supporting_evidence']:
                st.subheader("Supporting Evidence")
                for evidence in diagnostics['supporting_evidence'][:5]:
                    st.write(f"• {evidence}")
            
            # Display recommended tests
            if diagnostics['recommended_tests']:
                st.subheader("Recommended Additional Tests")
                for test in diagnostics['recommended_tests'][:5]:
                    st.write(f"• {test}")
            
            # Display risk factors
            if diagnostics['risk_factors']:
                st.subheader("Risk Factors")
                for risk in diagnostics['risk_factors'][:5]:
                    st.write(f"• {risk}")
                    
        else:
            st.info("Run a simulation to see diagnostic assessment results.")
            
            # Show example of what would be displayed
            st.markdown("""
            #### Example Diagnostic Assessment
            
            This tab will display:
            
            - **Identified Conditions**: Ranked list of probable diagnoses
            - **Confidence Scores**: Interactive chart showing diagnostic confidence
            - **Supporting Evidence**: Clinical findings supporting each diagnosis  
            - **Recommended Tests**: Additional investigations suggested
            - **Risk Factors**: Patient-specific risk factors identified
            """)
    
    with tab3:
        st.header("Treatment Plan")
        
        if st.session_state.simulation_results:
            # Parse treatment plan from simulation
            result_text = ""
            if hasattr(st.session_state.simulation_results, 'raw'):
                result_text = st.session_state.simulation_results.raw
            else:
                result_text = str(st.session_state.simulation_results)
            
            treatment = parse_treatment_plan(result_text)
            
            # Create columns for better layout
            col1, col2 = st.columns(2)
            
            with col1:
                # Display medications
                if treatment['medications']:
                    st.subheader("💊 Medications")
                    for med in treatment['medications'][:5]:
                        st.write(f"• {med}")
                else:
                    st.subheader("💊 Medications")
                    st.write("No specific medications mentioned in results.")
                
                # Display lifestyle modifications
                if treatment['lifestyle_modifications']:
                    st.subheader("🥗 Lifestyle Modifications")
                    for mod in treatment['lifestyle_modifications'][:5]:
                        st.write(f"• {mod}")
                else:
                    st.subheader("🥗 Lifestyle Modifications")
                    st.write("No specific lifestyle modifications mentioned.")
            
            with col2:
                # Display therapies
                if treatment['therapies']:
                    st.subheader("🏥 Therapies & Procedures")
                    for therapy in treatment['therapies'][:5]:
                        st.write(f"• {therapy}")
                else:
                    st.subheader("🏥 Therapies & Procedures")
                    st.write("No specific therapies mentioned in results.")
                
                # Display follow-up schedule
                if treatment['follow_up_schedule']:
                    st.subheader("📅 Follow-up Schedule")  
                    for followup in treatment['follow_up_schedule'][:5]:
                        st.write(f"• {followup}")
                else:
                    st.subheader("📅 Follow-up Schedule")
                    st.write("No specific follow-up schedule mentioned.")
            
            # Display precautions (full width)
            if treatment['precautions']:
                st.subheader("⚠️ Precautions & Warnings")
                for precaution in treatment['precautions'][:5]:
                    st.warning(f"• {precaution}")
                    
        else:
            st.info("Run a simulation to see treatment plan results.")
            
            # Show example of what would be displayed  
            st.markdown("""
            #### Example Treatment Plan
            
            This tab will display:
            
            - **💊 Medications**: Prescribed medications with dosing
            - **🏥 Therapies**: Treatment procedures and therapies
            - **🥗 Lifestyle**: Diet, exercise, and lifestyle changes
            - **📅 Follow-up**: Appointment and monitoring schedule
            - **⚠️ Precautions**: Important warnings and contraindications
            """)
    
    with tab4:
        st.header("Care Timeline")
        
        if st.session_state.simulation_results:
            # Parse timeline events from simulation
            result_text = ""
            if hasattr(st.session_state.simulation_results, 'raw'):
                result_text = st.session_state.simulation_results.raw
            else:
                result_text = str(st.session_state.simulation_results)
            
            events = extract_care_timeline_events(result_text, st.session_state.patient_info)
            
            # Display interactive timeline
            if events:
                st.subheader("Interactive Care Timeline")
                timeline_fig = create_timeline_chart(events)
                st.plotly_chart(timeline_fig, use_container_width=True)
                
                # Display events in a table format
                st.subheader("Scheduled Events")
                
                # Convert events to DataFrame for better display
                events_df = pd.DataFrame(events)
                events_df['DateTime'] = events_df['date'] + ' ' + events_df['time']
                
                # Format for display
                display_df = events_df[['DateTime', 'event_type', 'title', 'status']].copy()
                display_df.columns = ['Date & Time', 'Type', 'Event', 'Status']
                
                # Color code by status
                def highlight_status(row):
                    if row['Status'] == 'completed':
                        return ['background-color: #d4edda'] * len(row)
                    elif row['Status'] == 'scheduled':
                        return ['background-color: #fff3cd'] * len(row)
                    else:
                        return [''] * len(row)
                
                st.dataframe(
                    display_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_events = len(events)
                    st.metric("Total Events", total_events)
                
                with col2:
                    completed_events = len([e for e in events if e['status'] == 'completed'])
                    st.metric("Completed", completed_events)
                
                with col3:
                    scheduled_events = len([e for e in events if e['status'] == 'scheduled'])
                    st.metric("Scheduled", scheduled_events)
                
                with col4:
                    # Calculate next event
                    next_events = [e for e in events if e['status'] == 'scheduled']
                    if next_events:
                        next_date = min(next_events, key=lambda x: f"{x['date']} {x['time']}")
                        days_until = (datetime.strptime(next_date['date'], '%Y-%m-%d') - datetime.now()).days
                        st.metric("Next Event", f"{days_until} days")
                    else:
                        st.metric("Next Event", "None")
                        
        else:
            st.info("Run a simulation to see the patient care timeline.")
            
            # Show example of what would be displayed
            st.markdown("""
            #### Interactive Care Timeline
            
            This tab will display:
            
            - **📊 Timeline Visualization**: Interactive chart showing care journey
            - **📅 Event Schedule**: Table of all scheduled appointments and procedures  
            - **📈 Progress Metrics**: Summary of completed vs scheduled events
            - **🔔 Next Events**: Upcoming appointments and their timing
            
            The timeline will show:
            - Initial assessment and admission
            - Diagnostic tests and procedures
            - Treatment interventions
            - Follow-up appointments
            - Outcome evaluations
            """)

else:
    # Instructions when no simulation has been run yet
    st.info("Configure the simulation in the sidebar and click 'Run Simulation' to start")
    
    # Show example of what the dashboard will display
    st.markdown("""
    ### Dashboard Overview
    
    This interactive dashboard allows you to:
    
    1. **Select or input** an HL7 patient message
    2. **Run a simulation** of the patient's care pathway
    3. **View detailed results** of the multi-agent simulation
    4. **Analyze the outcomes** across different perspectives
    
    The simulation uses a hierarchical crew of specialized healthcare agents:
    
    - **Data Ingestion Agent**: Parses and validates HL7 messages
    - **Diagnostics Agent**: Analyzes patient data for probable diagnoses  
    - **Treatment Planner**: Develops evidence-based treatment plans
    - **Care Coordinator**: Manages the overall patient journey
    - **Outcome Evaluator**: Monitors and analyzes simulated outcomes
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Synthetic Care Pathway Simulator v1.0")
st.sidebar.caption("Built with CrewAI + Streamlit")
