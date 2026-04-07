"""
Main Execution Entry Point for Child Safety Guardian AI.

This file is the "control center" that starts and manages the entire 
child safety audit workflow. Think of it as the master switch that:
1. Sets up the audit request
2. Runs the AI workflow
3. Displays the final child safety report
"""

# Standard library imports for basic Python functionality
import uuid      # Generates unique IDs (like session tracking numbers)
import json      # Handles JSON data formatting (converts Python dicts to readable text)
import logging   # Records what happens during execution (like a flight recorder)
from pprint import pprint  # Pretty-prints data structures (unused here, but available)


# Load environment variables from .env file
# This reads API keys, database credentials, etc. without hardcoding them
from dotenv import load_dotenv
load_dotenv(override=True)  # override=True means .env values take priority over system variables

# Fail early with a clear message if the audit pipeline is not configured.
from backend.src.config import validate_audit_environment
validate_audit_environment()

# Import the main workflow graph (the "brain" of your child safety system)
from backend.src.graph.workflow import app

# Configure logging - sets up the "flight recorder" for your application
logging.basicConfig(
    level=logging.INFO,        # INFO = show important events (DEBUG would show everything)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'  
    # Format: timestamp - logger_name - severity - message
)
logger = logging.getLogger("child-safety-guardian-runner")  # Creates a named logger for this module


def run_cli_simulation():
    """
    Simulates a Video Child Safety Audit request.
    
    This function orchestrates the entire audit process:
    - Creates a unique session ID
    - Prepares the video URL and metadata
    - Runs it through the AI workflow
    - Displays the child safety audit results
    """
    
    # ========== STEP 1: GENERATE SESSION ID ==========
    session_id = str(uuid.uuid4())
    logger.info(f"Starting Audit Session: {session_id}")

    # ========== STEP 2: DEFINE INITIAL STATE ==========
    initial_inputs = {
        # The YouTube video to audit
        "video_url": "https://www.youtube.com/watch?v=xGhIVEyxayg",
        
        # Shortened video ID for easier tracking
        "video_id": f"vid_{session_id[:8]}",
        
        # Empty list that will store child safety violations found
        "compliance_results": [],
        
        # Empty list for any errors during processing
        "errors": []
    }

    # ========== DISPLAY SECTION: INPUT SUMMARY ==========
    print("\n--- 1. Input Payload: INITIALIZING WORKFLOW ---")
    print(f"  {json.dumps(initial_inputs, indent=2)}")

    # ========== STEP 3: EXECUTE GRAPH ==========
    try:
        final_state = app.invoke(initial_inputs)
        
        print("\n--- 2. WORKFLOW EXECUTION COMPLETE ---")
        
        # ========== STEP 4: OUTPUT RESULTS ==========
        print("\n=== CHILD SAFETY AUDIT REPORT ===")
        
        print(f"Video ID:    {final_state.get('video_id')}")
        print(f"Status:      {final_state.get('final_status')}")
        
        # ========== VIOLATIONS SECTION ==========
        print("\n[ VIOLATIONS DETECTED ]")
        
        results = final_state.get('compliance_results', [])
        
        if results:
            for issue in results:
                print(f"- [{issue.get('severity')}] {issue.get('category')}: {issue.get('description')}")
        else:
            print("No violations found.")

        # ========== POLICIES CHECKED SECTION ==========
        print("\n[ POLICIES CHECKED ]")
        retrieved_policies = final_state.get('retrieved_policies', [])
        if retrieved_policies:
            for i, policy in enumerate(retrieved_policies, 1):
                print(f"\n--- Policy Excerpt {i} ---")
                print(policy[:200] + "..." if len(policy) > 200 else policy)
        else:
            print("No policies retrieved.")

        # ========== SUMMARY SECTION ==========
        print("\n[ FINAL SUMMARY ]")
        print(final_state.get('final_report'))

    except Exception as e:
        logger.error(f"Workflow Execution Failed: {str(e)}")
        raise e


# ========== PROGRAM ENTRY POINT ==========
if __name__ == "__main__":
    run_cli_simulation()



'''
Ingestion:  (YouTube -> Azure)

Indexing:  (Speech-to-Text + OCR)

Retrieval:  (Found the child safety policy rules)

Reasoning:  (Applied rules to the specific content in the video)

You are done. Your pipeline is fully operational.
'''
