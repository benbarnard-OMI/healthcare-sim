# Healthcare Simulation Examples

This document provides practical examples of using the healthcare simulation system with different LLM backends.

## Quick Start Examples

### 1. OpenAI (Default)
```bash
# Set API key
export OPENAI_API_KEY="your-openai-key"

# Run simulation with default settings
python simulate.py --scenario diabetes

# Use specific model
python simulate.py --backend openai --model gpt-3.5-turbo --scenario chest_pain
```

### 2. Ollama (Local/Remote)

**Local Ollama Setup:**
```bash
# First, install and start Ollama
# Visit: https://ollama.ai

# Pull the medical-specific model
ollama pull alibayram/medgemma:4b

# Run simulation with local Ollama
python simulate.py --backend ollama --model alibayram/medgemma:4b --scenario pediatric

# Test connection
python simulate.py --backend ollama --test-connection
```

**Remote Ollama Server Setup:**
```bash
# Using the remote Ollama server at 100.101.241.121
python simulate.py --backend ollama \
  --base-url http://100.101.241.121:11434/v1 \
  --model alibayram/medgemma:4b \
  --scenario chest_pain

# Test connection to remote server
python simulate.py --backend ollama \
  --base-url http://100.101.241.121:11434/v1 \
  --model alibayram/medgemma:4b \
  --test-connection

# Run with Synthea-generated scenarios
python simulate.py --backend ollama \
  --base-url http://100.101.241.121:11434/v1 \
  --model alibayram/medgemma:4b \
  --generate-synthea --num-patients 5
```

**Using Environment Scripts:**
```bash
# Unix/macOS - Set up environment and run
source setup_ollama_env.sh
python simulate.py --scenario diabetes

# Windows - Set up environment and run
setup_ollama_env.bat
python simulate.py --scenario diabetes
```

### 3. Openrouter
```bash
# Set API key
export OPENROUTER_API_KEY="your-openrouter-key"

# Run with Claude
python simulate.py --backend openrouter --model anthropic/claude-3-opus --scenario surgical

# Run with different OpenAI model via Openrouter
python simulate.py --backend openrouter --model openai/gpt-4 --scenario stroke
```

## Dashboard Usage

### Starting the Dashboard
```bash
streamlit run dashboard.py
```

### Using Different Backends
1. **Select Backend**: Choose from the dropdown (OpenAI, Ollama, Openrouter)
2. **Enter Credentials**: API key field adapts based on backend selection
3. **Test Connection**: Use the "Test Connection" button to verify setup
4. **Configure Model**: Optionally specify a custom model name
5. **Run Simulation**: Select scenario and click "Run Simulation"

## Environment Configuration

### Option 1: Environment Variables
```bash
# Backend selection
export LLM_BACKEND="ollama"

# Ollama configuration
export OLLAMA_MODEL="llama2"
export OLLAMA_BASE_URL="http://localhost:11434/v1"

# Run without additional parameters
python simulate.py --scenario diabetes
```

### Option 2: Configuration File
Create a `.env` file:
```
LLM_BACKEND=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key
OPENROUTER_MODEL=anthropic/claude-3-sonnet
LLM_TEMPERATURE=0.8
```

## Advanced Usage

### Custom API Endpoints
```bash
# Custom OpenAI-compatible endpoint
python simulate.py \
  --backend openai \
  --base-url "https://your-custom-endpoint.com/v1" \
  --api-key "your-key" \
  --model "custom-model"
```

### Batch Processing
```bash
# Process multiple scenarios
for scenario in chest_pain diabetes pediatric surgical stroke; do
  echo "Processing $scenario with Ollama..."
  python simulate.py \
    --backend ollama \
    --model llama2 \
    --scenario $scenario \
    --output "results_${scenario}_ollama.txt"
done
```

### Model Comparison
```bash
# Compare results across backends
python simulate.py --backend openai --model gpt-4 --scenario diabetes --output gpt4_diabetes.txt
python simulate.py --backend ollama --model llama2 --scenario diabetes --output llama2_diabetes.txt
python simulate.py --backend openrouter --model anthropic/claude-3-opus --scenario diabetes --output claude_diabetes.txt
```

## Troubleshooting

### Connection Issues

**Ollama Connection Failed:**
```bash
# Check if Ollama is running
ollama serve

# Verify model is available
ollama list

# Test with curl
curl http://localhost:11434/v1/models
```

**OpenAI API Issues:**
```bash
# Test API key
curl -H "Authorization: Bearer $OPENAI_API_KEY" https://api.openai.com/v1/models

# Check quota
python simulate.py --backend openai --test-connection
```

**Openrouter Issues:**
```bash
# Verify API key format (should start with sk-or-v1-)
echo $OPENROUTER_API_KEY

# Test connection
python simulate.py --backend openrouter --test-connection
```

### Performance Optimization

**Ollama:**
- Use GPU acceleration: `ollama run llama2 --gpu`
- Increase context length: Set `OLLAMA_NUM_CTX=4096`
- Use smaller models for faster responses: `codellama:7b`

**OpenAI:**
- Use `gpt-3.5-turbo` for faster, cheaper responses
- Adjust temperature for consistency: `--temperature 0.3`

**Openrouter:**
- Choose models based on task complexity
- Monitor usage with Openrouter dashboard
- Use cheaper models for development: `openai/gpt-3.5-turbo`

## Model Recommendations

### By Use Case

**Development/Testing:**
- Ollama: `llama2:7b`, `codellama:7b`
- OpenAI: `gpt-3.5-turbo`
- Openrouter: `openai/gpt-3.5-turbo`

**Production Quality:**
- Ollama: `llama2:13b`, `mixtral:8x7b`
- OpenAI: `gpt-4`, `gpt-4-turbo`
- Openrouter: `anthropic/claude-3-opus`, `openai/gpt-4`

**Healthcare-Specific:**
- Medical reasoning: `gpt-4`, `anthropic/claude-3-opus`
- Code generation: `codellama`, `openai/gpt-4`
- Data analysis: `mixtral:8x7b`, `anthropic/claude-3-sonnet`

## Cost Considerations

### Approximate Costs (as of 2024)
- **Ollama**: Free (local compute costs)
- **OpenAI GPT-3.5**: ~$0.001-0.002 per 1K tokens
- **OpenAI GPT-4**: ~$0.03-0.06 per 1K tokens
- **Openrouter**: Varies by model, often 10-30% cheaper

### Cost Optimization Tips
1. Use Ollama for development and testing
2. Start with smaller models and scale up
3. Implement response caching for repeated queries
4. Monitor token usage with verbose logging
5. Use Openrouter for cost-effective access to premium models

## Integration Examples

### Custom Healthcare Tools
```python
from llm_config import create_llm_config
from crew import HealthcareSimulationCrew

# Create custom configuration
llm_config = create_llm_config(
    backend="ollama",
    model="medllama2:13b",  # Hypothetical medical model
    temperature=0.3,
    max_tokens=2000
)

# Initialize crew with custom config
crew = HealthcareSimulationCrew(llm_config=llm_config)
```

### Multi-Backend Comparison
```python
backends = ['openai', 'ollama', 'openrouter']
results = {}

for backend in backends:
    config = create_llm_config(backend=backend)
    crew = HealthcareSimulationCrew(llm_config=config)
    result = crew.crew().kickoff(inputs={"hl7_message": message})
    results[backend] = result
```

## Best Practices

1. **Start Local**: Use Ollama for development to avoid API costs
2. **Test Connections**: Always verify backend connectivity before production
3. **Monitor Performance**: Track response quality and latency
4. **Fallback Strategy**: Implement multiple backends for reliability
5. **Security**: Never commit API keys to version control
6. **Documentation**: Keep track of which models work best for your use cases

## Getting Help

- **Ollama**: https://ollama.ai/docs
- **OpenAI**: https://platform.openai.com/docs
- **Openrouter**: https://openrouter.ai/docs
- **Healthcare Simulation Issues**: Create an issue in this repository