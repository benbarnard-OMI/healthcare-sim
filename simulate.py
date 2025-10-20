import os
import sys
import json
import argparse
import random
from dotenv import load_dotenv
from crew import HealthcareSimulationCrew
from llm_config import create_llm_config, get_available_backends, LLMBackend
from datetime import datetime
from sample_data.sample_messages import SAMPLE_MESSAGES
from scenario_loader import get_scenario_loader, get_message, list_scenarios
import logging

# Load environment variables from .env file
load_dotenv()
from typing import Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_result(result: Any, output_file: Optional[str] = None) -> str:
    """Format and optionally save the simulation results."""
    output = "\n" + "="*60 + "\n"
    output += "SYNTHETIC CARE PATHWAY SIMULATION RESULTS\n"
    output += "="*60 + "\n"
    output += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    # Format the result content
    if hasattr(result, 'raw'):
        output += result.raw
    else:
        output += str(result)
    
    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Results saved to: {output_file}")
    
    return output

def main() -> None:
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description='Synthetic Care Pathway Simulator')
    parser.add_argument('--input', '-i', type=str, help='Path to HL7 message file')
    parser.add_argument('--output', '-o', type=str, help='Path to save results')
    parser.add_argument('--api-key', '-k', type=str, help='API key for the LLM service')
    parser.add_argument('--backend', '-b', type=str, choices=get_available_backends(), 
                       default='openai', help=f'LLM backend to use. Options: {", ".join(get_available_backends())}')
    parser.add_argument('--model', '-m', type=str, help='Model name to use (e.g., gpt-4, llama2, openai/gpt-4)')
    parser.add_argument('--base-url', type=str, help='Base URL for the LLM API')
    parser.add_argument('--temperature', '-t', type=float, default=0.7, help='Temperature for LLM responses (default: 0.7)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--scenario', '-s', type=str, help=f'Sample scenario name. Options: {", ".join(list_scenarios())}')
    parser.add_argument('--random-scenario', action='store_true', help='Randomly select a scenario from available options')
    parser.add_argument('--test-connection', action='store_true', help='Test LLM connection and exit')
    parser.add_argument('--generate-synthea', action='store_true', help='Generate new Synthea scenarios before simulation')
    parser.add_argument('--num-patients', type=int, default=20, help='Number of Synthea patients to generate')
    parser.add_argument('--age-min', type=int, default=0, help='Minimum age for Synthea patients')
    parser.add_argument('--age-max', type=int, default=100, help='Maximum age for Synthea patients')
    parser.add_argument('--state', type=str, default='Massachusetts', help='US state for Synthea demographics')
    parser.add_argument('--city', type=str, default='Boston', help='City for Synthea demographics')
    parser.add_argument('--synthea-seed', type=int, help='Random seed for Synthea generation')
    args = parser.parse_args()
    
    # Create LLM configuration
    try:
        llm_config = create_llm_config(
            backend=args.backend,
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url,
            temperature=args.temperature
        )
        logger.info(f"Using LLM backend: {llm_config}")
        
    except Exception as e:
        logger.error(f"Failed to configure LLM backend: {str(e)}")
        sys.exit(1)
    
    # Test connection if requested
    if args.test_connection:
        from llm_config import test_connection
        if test_connection(llm_config):
            print(f"✅ Connection to {args.backend} successful!")
            sys.exit(0)
        else:
            print(f"❌ Connection to {args.backend} failed!")
            sys.exit(1)
    
    # Initialize the simulation crew with LLM configuration
    sim_crew = HealthcareSimulationCrew(llm_config=llm_config)
    
    # Generate Synthea scenarios if requested
    if args.generate_synthea:
        try:
            logger.info("Generating Synthea scenarios...")
            scenario_loader = get_scenario_loader()
            synthea_result = scenario_loader.generate_synthea_scenarios(
                num_patients=args.num_patients,
                age_min=args.age_min,
                age_max=args.age_max,
                state=args.state,
                city=args.city,
                seed=args.synthea_seed
            )
            logger.info(f"Generated {synthea_result['scenarios_created']} Synthea scenarios")
            
            # If no specific scenario is requested, use the first generated one
            if not args.scenario and synthea_result['scenario_ids']:
                args.scenario = synthea_result['scenario_ids'][0]
                logger.info(f"Using generated scenario: {args.scenario}")
        except Exception as e:
            logger.error(f"Failed to generate Synthea scenarios: {e}")
            if not args.scenario:
                logger.warning("Falling back to default scenario")
    
    # Handle random scenario selection
    if args.random_scenario:
        available_scenarios = list_scenarios()
        if available_scenarios:
            args.scenario = random.choice(available_scenarios)
            logger.info(f"Randomly selected scenario: {args.scenario}")
        else:
            logger.warning("No scenarios available for random selection")
    
    # Prepare the HL7 message
    hl7_message = None
    
    # Process input sources with priority: file > scenario > default
    if args.input:
        try:
            with open(args.input, 'r') as f:
                hl7_message = f.read()
            logger.info(f"Using HL7 message from: {args.input}")
        except Exception as e:
            logger.error(f"Error reading input file: {str(e)}")
    
    if not hl7_message and args.scenario:
        hl7_message = get_message(args.scenario)
        logger.info(f"Using sample scenario: {args.scenario}")
    
    if not hl7_message:
        # Try to get message using new scenario loader
        loader = get_scenario_loader()
        try:
            # Set fallback module for backward compatibility
            import sample_data.sample_messages as sample_messages
            loader.fallback_module = sample_messages
        except ImportError:
            pass
        
        # Use random scenario if no specific scenario provided
        available_scenarios = list_scenarios()
        if available_scenarios:
            default_scenario = random.choice(available_scenarios)
            logger.info(f"Using random default scenario: {default_scenario}")
        else:
            default_scenario = "chest_pain"
            logger.info("Using fallback chest pain scenario")
        
        hl7_message = loader.get_hl7_message(default_scenario)
    
    # Run the simulation with the HL7 message
    try:
        logger.info("Starting care pathway simulation...")
        
        # Kick off the simulation
        result = sim_crew.crew().kickoff(inputs={
            "hl7_message": hl7_message
        })
        
        # Format and display results
        formatted_result = format_result(result, args.output)
        print(formatted_result)
        
    except Exception as e:
        logger.error(f"Simulation failed: {str(e)}")
        if args.verbose:
            import traceback
            logger.error("Detailed error information:")
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()
