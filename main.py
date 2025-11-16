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
    # Initialize shared store
    shared = {
        "user_request": "",
        "trip_info": {
            "destination": "",
            "trip_type": "",
            "duration_days": None,
            "travelers": None,
            "budget": "",
            "travel_style": "",
            "interests": [],
            "start_date": "",
        },
        "missing_info": [],
        "clarification_questions": [],
        "clarification_round": 0,
        "max_clarification_rounds": 2,
        "destination_info": {},
        "accommodations": [],
        "transportation": {},
        "activities": [],
        "restaurants": [],
        "daily_plans": [],
        "final_travel_guide": ""
    }

    # Create and run the flow
    travel_flow = create_travel_guide_flow()
    travel_flow.run(shared)

    # Display the final travel guide
    print("\n" + "="*80)
    print("YOUR PERSONALIZED TRAVEL GUIDE")
    print("="*80 + "\n")
    print(shared["final_travel_guide"])

    save_trip(shared)

if __name__ == "__main__":
    main()
