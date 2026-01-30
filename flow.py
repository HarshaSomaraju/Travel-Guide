"""
Flow creation for the Travel Guide system
"""

from pocketflow import Flow
from nodes import (
    CalculateBudget,
    GetUserRequest,
    AnalyzeRequest,
    DecideNeedInfo,
    AskClarification,
    GetUserClarification,
    ResearchDestination,
    GatherTravelDetails,
    PlanDailyItinerary,
    CombineFinalPlan,
    IdentifyPlaces,
    GetPlaceReviews,
    EvaluatePlan,
    ReplanFromFeedback,
)


def create_travel_guide_flow():
    """
    Create and return the travel planning flow

    Flow structure:
    1. Get user request
    2. Analyze the request dynamically (LLM decides what questions to ask)
    3. Decision: Need more info?
       - Yes: Ask dynamic questions -> Get answers -> Loop back to analyze
       - No: Continue to research
    4. Research destination
    5. Gather travel details
    6. Identify places and get reviews
    7. Plan daily itineraries
    8. Combine into final guide
    9. Evaluate: User satisfied?
       - Yes: Done
       - No: Revise based on feedback -> Loop back to evaluate
    """

    # Create all nodes
    get_request = GetUserRequest()
    analyze_request = AnalyzeRequest()
    decide = DecideNeedInfo()
    ask_clarification = AskClarification()
    get_clarification = GetUserClarification()
    research = ResearchDestination()
    gather_details = GatherTravelDetails()
    identify_places = IdentifyPlaces()
    get_reviews = GetPlaceReviews()
    plan_days = PlanDailyItinerary()
    combine_plan = CombineFinalPlan()
    calculate_budget = CalculateBudget()
    evaluate_plan = EvaluatePlan()
    replan = ReplanFromFeedback()

    # Connect nodes in sequence: Get request -> Analyze
    get_request >> analyze_request >> decide

    # Branching: clarification loop or proceed
    decide - "clarify" >> ask_clarification
    ask_clarification >> get_clarification
    get_clarification - "analyze" >> analyze_request  # Loop back to re-analyze

    decide - "proceed" >> research

    # Main planning pipeline
    research >> gather_details >> identify_places >> get_reviews >> plan_days >> calculate_budget >> combine_plan

    # Plan evaluation loop
    combine_plan >> evaluate_plan
    evaluate_plan - "revise" >> replan
    replan - "evaluate" >> evaluate_plan
    # "done" is terminal - no connection needed

    # Create and return the flow
    return Flow(start=get_request)


if __name__ == "__main__":
    # Test flow creation
    flow = create_travel_guide_flow()
    print("Travel guide flow created successfully!")
    print(f"Starting node: {flow.start}")

