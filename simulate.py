import os
import sys
import json
import argparse
from crew import HealthcareSimulationCrew
from datetime import datetime
from sample_data.sample_messages import SAMPLE_MESSAGES, list_scenarios, get_message
import logging
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
    parser.add_argument('--api-key', '-k', type=str, help='OpenAI API key')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    parser.add_argument('--scenario', '-s', type=str, help=f'Sample scenario name. Options: {", ".join(list_scenarios())}')
    args = parser.parse_args()
    
    # Initialize the simulation crew
    sim_crew = HealthcareSimulationCrew()
    
    # Set OpenAI API key
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        logger.error("OpenAI API key not found. Please set it using the --api-key argument or the OPENAI_API_KEY environment variable.")
        sys.exit(1)
    os.environ["OPENAI_API_KEY"] = api_key
    
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
        hl7_message = SAMPLE_MESSAGES["chest_pain"]  # Default scenario
        logger.info("Using default chest pain scenario")
    
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
