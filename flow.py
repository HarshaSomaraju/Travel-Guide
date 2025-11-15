"""
Flow creation for the Travel Guide system
"""

from pocketflow import Flow
from nodes import (
    CalculateBudget,
    GetUserRequest,
    ParseRequest,
    DecideNeedInfo,
    AskClarification,
    GetUserClarification,
    ResearchDestination,
    GatherTravelDetails,
    PlanDailyItinerary,
    CombineFinalPlan
)


def create_travel_guide_flow():
    """
    Create and return the travel planning flow
    
    Flow structure:
    1. Get user request
    2. Parse the request
    3. Decision: Need more info?
       - Yes: Ask clarification -> Get answers -> Loop back to decision
       - No: Continue to research
    4. Research destination
    5. Gather travel details
    6. Plan daily itineraries
    7. Combine into final guide
    """
    
    # Create all nodes
    get_request = GetUserRequest()
    parse_request = ParseRequest()
    decide = DecideNeedInfo()
    ask_clarification = AskClarification()
    get_clarification = GetUserClarification()
    research = ResearchDestination()
    gather_details = GatherTravelDetails()
    plan_days = PlanDailyItinerary()
    combine_plan = CombineFinalPlan()
    calculate_budget = CalculateBudget()
    # Connect nodes in sequence
    get_request >> parse_request >> decide
    
    # Branching: clarification loop or proceed
    decide - "clarify" >> ask_clarification
    ask_clarification >> get_clarification
    get_clarification - "decide" >> decide  # Loop back
    
    decide - "proceed" >> research
    
    # Main planning pipeline
    research >> gather_details >> plan_days >> calculate_budget >> combine_plan
    
    # Create and return the flow
    return Flow(start=get_request)


if __name__ == "__main__":
    # Test flow creation
    flow = create_travel_guide_flow()
    print("Travel guide flow created successfully!")
    print(f"Starting node: {flow.start}")
