# Synthetic Care Pathway Simulator

A multi-agent system that simulates realistic patient care pathways by orchestrating specialized healthcare agents using CrewAI and Synthea HL7 messages.

## Project Overview

This system decomposes healthcare simulation into modular agents—each mimicking a real-world healthcare function:
- **Data Ingestion**: Parses HL7 messages for structured patient data
- **Diagnostics**: Analyzes patient data for evidence-based diagnostic assessments
- **Treatment Planning**: Develops personalized treatment plans
- **Care Coordination**: Manages transitions between care phases
- **Outcome Evaluation**: Monitors and analyzes treatment results

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/benbarnard-OMI/healthcare-sim.git
   cd healthcare-sim
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY="your-api-key-here"  # Linux/macOS
   set OPENAI_API_KEY=your-api-key-here       # Windows
   ```

## Usage

### Command Line Simulation

Run the simulation with default parameters:
```
python simulate.py
```

Command line options:
```
python simulate.py --help

options:
  -h, --help            show this help message and exit
  --input INPUT, -i INPUT
                        Path to HL7 message file
  --output OUTPUT, -o OUTPUT
                        Path to save results
  --api-key API_KEY, -k API_KEY
                        OpenAI API key
  --verbose, -v         Enable verbose output
  --scenario SCENARIO, -s SCENARIO
                        Sample scenario name. Options: chest_pain, diabetes, pediatric, surgical, stroke
```

Example with specific scenario:
```
python simulate.py --scenario diabetes --output results.txt
```

### Interactive Dashboard

Launch the interactive web dashboard:
```
streamlit run dashboard.py
```

The dashboard allows you to:
- Select pre-defined patient scenarios
- Input custom HL7 messages
- Visualize simulation results
- Analyze care pathways interactively

### Running Unit Tests

To run the unit tests for the project, use the following command:
```
pytest
```

This will discover and run all the tests in the `tests` directory.

### Contributing

We welcome contributions to the project! To contribute, please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch for your feature or bugfix.
3. Make your changes and commit them with clear and descriptive commit messages.
4. Push your changes to your forked repository.
5. Create a pull request to the main repository.

Please ensure that your code follows the project's coding standards and includes appropriate tests.

## Project Components

### 1. Agent Configuration

Agents are defined in `config/agents.yaml` with specialized roles:
- **HL7 Data Ingestion Specialist**: Validates and structures HL7 messages
- **Clinical Diagnostics Analyst**: Generates evidence-based diagnostic assessments
- **Treatment Planning Specialist**: Creates personalized treatment plans
- **Patient Care Coordinator**: Orchestrates care transitions and scheduling
- **Clinical Outcomes Analyst**: Evaluates treatment effectiveness

### 2. Task Configuration

Tasks representing the healthcare workflow are defined in `config/tasks.yaml`:
- **Ingest HL7 Data**: Parse and validate patient messages
- **Analyze Diagnostics**: Identify probable conditions
- **Create Treatment Plan**: Develop personalized interventions
- **Coordinate Care**: Schedule and manage transitions
- **Evaluate Outcomes**: Monitor treatment effectiveness

### 3. Healthcare Tools

Custom tools located in `tools/healthcare_tools.py` enhance agent capabilities:
- **Clinical Guidelines Tool**: Provides evidence-based treatment protocols
- **Medication Interaction Tool**: Checks for drug interactions and contraindications
- **Appointment Scheduler Tool**: Manages patient appointments and resources

### 4. Sample Data

Pre-defined clinical scenarios in `sample_data/sample_messages.py`:
- Chest pain patient
- Diabetic patient with complications
- Pediatric patient with respiratory infection
- Surgical patient for hip replacement
- Emergency patient with stroke symptoms

## Architecture

The system uses a hierarchical process model where:
1. The Care Coordinator acts as the manager agent
2. The manager orchestrates specialized agents for each step
3. Agents collaborate through delegation and information exchange
4. Results are compiled into a comprehensive care pathway simulation

## Example Output

The simulation produces a detailed report that includes:
- Patient demographics and clinical markers
- Diagnostic reasoning with probability rankings
- Personalized treatment plans
- Coordinated care schedule
- Outcome projections and effectiveness metrics

## Customization

- Add new agents in `config/agents.yaml`
- Define additional tasks in `config/tasks.yaml`
- Create custom healthcare tools by extending `healthcare_tools.py`
- Add new patient scenarios in `sample_data/sample_messages.py`

## License

[MIT License](LICENSE)

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI)
- [HL7apy](https://github.com/crs4/hl7apy)
- [Synthea](https://github.com/synthetichealth/synthea)
