"""
AI Travel Guide - Main Entry Point

This travel planning system helps users plan trips from local day outings 
to international multi-week adventures by:
1. Gathering user requirements
2. Asking clarification questions when needed
3. Researching destination information
4. Creating detailed day-by-day itineraries
"""

from dotenv import load_dotenv
from flow import create_travel_guide_flow

from storage import save_trip

# Load environment variables from .env file
load_dotenv()

def main():
    """
    Main function to run the travel guide flow
    """
    # Initialize shared store with dynamic structure
    shared = {
        # Conversation tracking for dynamic question flow
        "conversation_history": [],
        
        # Trip info - populated dynamically by LLM
        "trip_info": {},
        
        # Clarification tracking
        "clarification_round": 0,
        "max_clarification_rounds": 5,
        
        # Research results
        "destination_info": {},
        "accommodations": [],
        "transportation": {},
        "activities": [],
        "restaurants": [],
        
        # Planning outputs
        "daily_plans": [],
        "final_travel_guide": "",
        "plan_revision_count": 0,
    }

    # Create and run the flow
    travel_flow = create_travel_guide_flow()
    travel_flow.run(shared)

    # Final guide is already displayed by EvaluatePlan node
    save_trip(shared)

if __name__ == "__main__":
    main()
