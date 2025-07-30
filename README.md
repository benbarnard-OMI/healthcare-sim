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

3. Set up your LLM backend:

   ### OpenAI (Default)
   ```bash
   export OPENAI_API_KEY="your-api-key-here"  # Linux/macOS
   set OPENAI_API_KEY=your-api-key-here       # Windows
   ```

   ### Ollama (Local)
   1. Install Ollama from https://ollama.ai
   2. Pull a model: `ollama pull llama2`
   3. Start Ollama: `ollama serve`
   4. Set environment variable (optional):
   ```bash
   export OLLAMA_MODEL="llama2"
   export OLLAMA_BASE_URL="http://localhost:11434/v1"
   ```

   ### Openrouter
   ```bash
   export OPENROUTER_API_KEY="your-api-key-here"  # Get from https://openrouter.ai
   export OPENROUTER_MODEL="openai/gpt-4"         # Choose your preferred model
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
                        API key for the LLM service
  --backend BACKEND, -b BACKEND
                        LLM backend to use (openai, ollama, openrouter)
  --model MODEL, -m MODEL
                        Model name to use (e.g., gpt-4, llama2, openai/gpt-4)
  --base-url BASE_URL   Base URL for the LLM API
  --temperature TEMPERATURE, -t TEMPERATURE
                        Temperature for LLM responses (default: 0.7)
  --verbose, -v         Enable verbose output
  --scenario SCENARIO, -s SCENARIO
                        Sample scenario name. Options: chest_pain, diabetes, pediatric, surgical, stroke
  --test-connection     Test LLM connection and exit
```

Example with different backends:
```bash
# OpenAI
python simulate.py --backend openai --api-key your-openai-key --scenario diabetes

# Ollama (local)
python simulate.py --backend ollama --model llama2 --scenario diabetes

# Openrouter
python simulate.py --backend openrouter --api-key your-openrouter-key --model openai/gpt-4 --scenario diabetes

# Test connection
python simulate.py --backend ollama --test-connection
```

### Interactive Dashboard

Launch the interactive web dashboard:
```
streamlit run dashboard.py
```

The dashboard allows you to:
- **Select LLM backend**: Choose between OpenAI, Ollama, or Openrouter
- **Configure settings**: Set API keys, models, and parameters
- **Test connections**: Verify your LLM backend is working
- **Select or input** HL7 patient messages
- **Run simulations** of patient care pathways
- **View detailed results** of multi-agent simulations
- **Analyze outcomes** across different perspectives

## LLM Backend Support

### OpenAI
- **Models**: gpt-4, gpt-3.5-turbo, and other OpenAI models
- **Setup**: Requires OpenAI API key
- **Use case**: High-quality responses with broad model selection

### Ollama (Local)
- **Models**: llama2, codellama, mistral, and other open-source models
- **Setup**: Install Ollama locally, no API key required
- **Use case**: Privacy-focused, offline operation, cost-effective

### Openrouter
- **Models**: Access to various providers (OpenAI, Anthropic, etc.)
- **Setup**: Requires Openrouter API key
- **Use case**: Model diversity, competitive pricing, unified API

## Environment Variables

You can configure the system using environment variables:

```bash
# Backend selection
export LLM_BACKEND="ollama"  # openai, ollama, openrouter

# API Keys
export OPENAI_API_KEY="your-openai-key"
export OPENROUTER_API_KEY="your-openrouter-key"
export OLLAMA_API_KEY="optional-ollama-key"

# Models
export OPENAI_MODEL="gpt-4"
export OPENROUTER_MODEL="openai/gpt-4"
export OLLAMA_MODEL="llama2"

# API Endpoints
export OPENAI_BASE_URL="https://api.openai.com/v1"
export OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
export OLLAMA_BASE_URL="http://localhost:11434/v1"

# General settings
export LLM_TEMPERATURE="0.7"
export LLM_MAX_TOKENS="2000"
```

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
