import streamlit as st
import os
import json
from datetime import datetime
from crew import HealthcareSimulationCrew
from sample_data.sample_messages import SAMPLE_MESSAGES, list_scenarios, get_message
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# API Key input
api_key = st.sidebar.text_input("OpenAI API Key", type="password")
if api_key:
    os.environ["OPENAI_API_KEY"] = api_key

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

# Run simulation button
run_button = st.sidebar.button("Run Simulation", type="primary")

# Initialize session state for storing results
if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None
if "patient_info" not in st.session_state:
    st.session_state.patient_info = None
if "simulation_timestamp" not in st.session_state:
    st.session_state.simulation_timestamp = None

# Function to run the simulation
def run_simulation() -> None:
    if not api_key:
        st.error("Please enter your OpenAI API key in the sidebar")
        return
    
    # Display a spinner during simulation
    with st.spinner("Running care pathway simulation..."):
        # Initialize the simulation crew
        sim_crew = HealthcareSimulationCrew()
        
        # Get the HL7 message (custom or from selected scenario)
        hl7_message = custom_hl7 if custom_hl7.strip() else get_message(selected_scenario)
        
        try:
            # Run the simulation
            result = sim_crew.crew().kickoff(inputs={"hl7_message": hl7_message})
            
            # Store results in session state
            st.session_state.simulation_results = result
            st.session_state.simulation_timestamp = datetime.now()
            
            # Try to extract patient info from the result
            try:
                if hasattr(result, 'raw'):
                    # Look for patient demographics in the results
                    patient_info = {}
                    raw_text = result.raw
                    
                    # Very basic extraction - would be more robust in production
                    if "PATIENT DEMOGRAPHICS" in raw_text:
                        demo_section = raw_text.split("PATIENT DEMOGRAPHICS")[1].split("\n\n")[0]
                        lines = demo_section.strip().split("\n")
                        for line in lines:
                            if ":" in line:
                                key, value = line.split(":", 1)
                                patient_info[key.strip()] = value.strip()
                    
                    st.session_state.patient_info = patient_info
            except Exception as e:
                st.warning(f"Could not parse patient demographics: {str(e)}")
                
        except Exception as e:
            st.error(f"Simulation failed: {str(e)}")
            st.session_state.simulation_results = None

# Run simulation if button clicked
if run_button:
    run_simulation()

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
            cols = st.columns(4)
            patient_info = st.session_state.patient_info
            
            with cols[0]:
                st.metric("Patient ID", patient_info.get("Patient ID", "N/A"))
            with cols[1]:
                st.metric("Age", patient_info.get("Age", "N/A"))
            with cols[2]:
                st.metric("Gender", patient_info.get("Gender", "N/A"))
            with cols[3]:
                st.metric("Status", patient_info.get("Status", "Active"))
        
        # Display full results in an expander
        with st.expander("Full Simulation Results", expanded=True):
            if hasattr(st.session_state.simulation_results, 'raw'):
                st.text_area("", st.session_state.simulation_results.raw, height=300)
            else:
                st.text_area("", str(st.session_state.simulation_results), height=300)
    
    with tab2:
        st.header("Diagnostic Assessment")
        st.info("This tab would display parsed diagnostic information from the simulation results.")
        
        # In a real implementation, we would parse and present the diagnostic information
        st.markdown("""
        #### Sample Visualization
        
        If integrated with a full backend system, this tab would show:
        
        - Ranked list of probable diagnoses with confidence scores
        - Supporting evidence for each diagnosis
        - Relevant lab results and clinical markers
        - Risk stratification analysis
        """)
        
        # Placeholder for a diagnostic chart
        st.markdown("### Diagnostic Confidence")
        chart_data = {
            "Diagnosis": ["Acute Coronary Syndrome", "Musculoskeletal Pain", "GERD", "Anxiety"],
            "Confidence": [0.82, 0.45, 0.38, 0.25]
        }
        st.bar_chart(chart_data, x="Diagnosis", y="Confidence")
    
    with tab3:
        st.header("Treatment Plan")
        st.info("This tab would display the generated treatment plan from the simulation.")
        
        # In a real implementation, we would parse and present the treatment plan
        st.markdown("""
        #### Sample Visualization
        
        A complete implementation would show:
        
        - Medication schedule and doses
        - Therapy appointments
        - Lifestyle modifications
        - Follow-up requirements
        - Potential contraindications
        """)
    
    with tab4:
        st.header("Care Timeline")
        st.info("This tab would show a timeline of the patient's care journey.")
        
        # In a real implementation, we would parse and present the care timeline
        st.markdown("""
        #### Sample Visualization
        
        A complete implementation would show an interactive timeline of:
        
        - Initial assessment
        - Diagnostic tests
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
