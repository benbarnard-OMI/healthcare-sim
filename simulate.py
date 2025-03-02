import os
import json
import argparse
from crew import HealthcareSimulationCrew
from datetime import datetime
from sample_data.sample_messages import SAMPLE_MESSAGES, list_scenarios, get_message

def format_result(result, output_file=None):
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
        print(f"\nResults saved to: {output_file}")
    
    return output

def main():
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
        print("Warning: No OpenAI API key provided. Set with --api-key or OPENAI_API_KEY environment variable.")
        return
    os.environ["OPENAI_API_KEY"] = api_key
    
    # Prepare the HL7 message
    hl7_message = None
    
    # Process input sources with priority: file > scenario > default
    if args.input:
        try:
            with open(args.input, 'r') as f:
                hl7_message = f.read()
            print(f"Using HL7 message from: {args.input}")
        except Exception as e:
            print(f"Error reading input file: {str(e)}")
    
    if not hl7_message and args.scenario:
        hl7_message = get_message(args.scenario)
        print(f"Using sample scenario: {args.scenario}")
    
    if not hl7_message:
        hl7_message = SAMPLE_MESSAGES["chest_pain"]  # Default scenario
        print("Using default chest pain scenario")
    
    # Run the simulation with the HL7 message
    try:
        print("\nStarting care pathway simulation...\n")
        
        # Kick off the simulation
        result = sim_crew.crew().kickoff(inputs={
            "hl7_message": hl7_message
        })
        
        # Format and display results
        formatted_result = format_result(result, args.output)
        print(formatted_result)
        
    except Exception as e:
        print(f"\nSimulation failed: {str(e)}")
        if args.verbose:
            import traceback
            print("\nDetailed error information:")
            traceback.print_exc()

if __name__ == "__main__":
    main()