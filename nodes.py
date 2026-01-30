"""
Node definitions for the Travel Guide Flow
"""

from pocketflow import Node, BatchNode
from utils import call_llm, search_web, extract_yaml_str, get_place_details
import yaml
from yaml.scanner import ScannerError

class GetUserRequest(Node):
    """Initial node to capture user's travel request"""

    def exec(self, prep_res):
        print("\n" + "=" * 80)
        print("WELCOME TO AI TRAVEL GUIDE")
        print("=" * 80)
        print("\nTell me about your travel plans!")
        print("Examples:")
        print("  - 'I want to visit Paris for 5 days'")
        print("  - 'Plan a weekend trip to the mountains'")
        print("  - 'I need a 2-week itinerary for Japan'")
        print("\n")

        user_input = input("Your travel request: ")
        return user_input

    def post(self, shared, prep_res, exec_res):
        shared["user_request"] = exec_res
        # Add to conversation history for dynamic analysis
        shared["conversation_history"].append(f"Initial request: {exec_res}")
        return "default"


class AnalyzeRequest(Node):
    """Dynamically analyze travel request and generate contextual questions"""

    def prep(self, shared):
        return {
            "conversation_history": shared.get("conversation_history", []),
            "trip_info": shared.get("trip_info", {}),
        }

    def exec(self, data):
        conversation = data["conversation_history"]
        current_info = data["trip_info"]
        
        # Format conversation history for the prompt
        convo_text = "\n".join([f"- {msg}" for msg in conversation]) if conversation else "No conversation yet."
        
        prompt = f"""
You are an expert travel planner analyzing a user's travel request.

CONVERSATION SO FAR:
{convo_text}

INFORMATION GATHERED SO FAR:
{yaml.dump(current_info, default_flow_style=False) if current_info else "None yet."}

TASK:
1. Extract any NEW travel information from the conversation into a structured format
2. Analyze what's known and what's missing or unclear
3. Generate 1-3 SMART, CONTEXTUAL follow-up questions (if needed)
   - Questions should be specific to THIS trip, not generic
   - Ask about things that would genuinely help create a better plan
   - If you have enough info for a good plan, set needs_clarification to false

Return ONLY this YAML:
```yaml
extracted_info:
  destination: <string or null>
  trip_type: <local/domestic/international or null>
  duration_days: <number or null>
  travelers: <number or null>
  budget: <string like "$2000" or "mid-range" or null>
  travel_style: <luxury/mid-range/budget/backpacker or null>
  interests: <list of specific interests or []>
  start_date: <date string or null>
  special_requirements: <any special needs, accessibility, dietary, etc. or null>
  
needs_clarification: <true/false>
reasoning: <brief explanation of what's known and what's missing>
questions:
  - <question 1 if needed>
  - <question 2 if needed>
```
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        parsed = yaml.safe_load(yaml_str)
        return parsed

    def post(self, shared, prep_res, exec_res):
        # Update trip_info with newly extracted data
        extracted = exec_res.get("extracted_info", {})
        for key, value in extracted.items():
            if value is not None and value != [] and value != "":
                shared["trip_info"][key] = value

        # Store analysis results
        shared["needs_clarification"] = exec_res.get("needs_clarification", False)
        shared["dynamic_questions"] = exec_res.get("questions", [])
        shared["analysis_reasoning"] = exec_res.get("reasoning", "")

        print(f"\n[ANALYSIS] Trip info: {shared['trip_info']}")
        print(f"[ANALYSIS] Reasoning: {shared['analysis_reasoning']}")

        return "default"


class DecideNeedInfo(Node):
    """Agent node to decide if clarification is needed based on LLM analysis"""

    def prep(self, shared):
        return {
            "needs_clarification": shared.get("needs_clarification", False),
            "clarification_round": shared.get("clarification_round", 0),
            "max_rounds": shared.get("max_clarification_rounds", 5),
            "has_destination": bool(shared.get("trip_info", {}).get("destination")),
        }

    def exec(self, data):
        round_num = data["clarification_round"]
        max_rounds = data["max_rounds"]

        # Must have at least a destination to proceed
        if not data["has_destination"]:
            return "clarify"

        # If exceeded max rounds, proceed anyway
        if round_num >= max_rounds:
            return "proceed"

        # Use the LLM's judgment
        if data["needs_clarification"]:
            return "clarify"

        return "proceed"

    def post(self, shared, prep_res, exec_res):
        print(f"\n[DECISION] Action: {exec_res}")
        return exec_res


class AskClarification(Node):
    """Display the dynamically generated clarification questions"""

    def prep(self, shared):
        return shared.get("dynamic_questions", [])

    def exec(self, questions):
        # Questions are already generated by AnalyzeRequest
        return questions if questions else ["What destination are you considering?"]

    def post(self, shared, prep_res, exec_res):
        shared["clarification_questions"] = exec_res
        shared["clarification_round"] = shared.get("clarification_round", 0) + 1

        print("\n" + "-" * 80)
        print("I have a few questions to help plan your perfect trip:")
        for i, question in enumerate(exec_res, 1):
            print(f"{i}. {question}")
        print("-" * 80)

        return "default"


class GetUserClarification(Node):
    """Get user's answers to clarification questions and add to conversation history"""

    def prep(self, shared):
        return shared.get("clarification_questions", [])

    def exec(self, questions):
        print("\nYour answers: ", end="")
        user_response = input()
        return user_response

    def post(self, shared, prep_res, exec_res):
        # Add the Q&A to conversation history for AnalyzeRequest to process
        questions_text = " | ".join(prep_res)
        shared["conversation_history"].append(f"Questions asked: {questions_text}")
        shared["conversation_history"].append(f"User answered: {exec_res}")

        print(f"\n[RECORDED] Added response to conversation history")

        # Return to analyze loop for re-analysis
        return "analyze"


class ResearchDestination(BatchNode):
    """Research destination information using web search"""

    def prep(self, shared):
        destination = shared["trip_info"]["destination"]
        interests = shared["trip_info"].get("interests", [])

        # Generate search queries
        queries = [
            f"{destination} travel guide",
            f"{destination} top attractions",
            f"{destination} best time to visit",
        ]

        if interests:
            for interest in interests[:2]:  # Limit to 2 interests
                queries.append(f"{destination} {interest}")

        return queries

    def exec(self, query):
        results = search_web(query)
        return {"query": query, "results": results}

    def post(self, shared, prep_res, exec_res_list):
        shared["destination_info"] = exec_res_list
        print(f"\n[RESEARCH] Completed {len(exec_res_list)} searches")
        return "default"


class GatherTravelDetails(BatchNode):
    """Gather specific travel details (accommodations, transport, activities)"""

    def prep(self, shared):
        destination = shared["trip_info"]["destination"]
        travel_style = shared["trip_info"]["travel_style"]

        categories = [
            f"{destination} {travel_style} hotels accommodations",
            f"{destination} transportation getting around",
            f"{destination} restaurants food recommendations",
            f"{destination} activities things to do",
            f"{destination} safety tips",
            f"{destination} local customs",
            f"{destination} weather forecast"
        ]

        return categories

    def exec(self, query):
        results = search_web(query)
        return {"query": query, "results": results}

    def post(self, shared, prep_res, exec_res_list):
        # Categorize results
        for item in exec_res_list:
            query = item["query"]
            if "hotel" in query or "accommodation" in query:
                shared["accommodations"].append(item)
            elif "transportation" in query:
                shared["transportation"] = item
            elif "restaurant" in query or "food" in query:
                shared["restaurants"].append(item)
            elif "activities" in query or "things to do" in query:
                shared["activities"].append(item)

        print(
            f"\n[DETAILS] Gathered travel details across {len(exec_res_list)} categories"
        )
        return "default"


class IdentifyPlaces(Node):
    """Identify specific places to review from gathered details"""

    def prep(self, shared):
        return {
            "accommodations": shared.get("accommodations", []),
            "restaurants": shared.get("restaurants", []),
            "activities": shared.get("activities", []),
        }

    def exec(self, data):
        # Format text for LLM
        text_content = ""
        for cat, items in data.items():
            text_content += f"\n--- {cat.upper()} ---\n"
            # Use top 3 items from each category to avoid context overflow
            for item in items:
                query_results = item.get("results", [])
                for result in query_results:
                    text_content += f"{result.get('title', '')}: {result.get('snippet', '')}\n"

        prompt = f"""
Identify the top 5 most interesting specific places (hotels, restaurants, attractions) mentioned in this text that are worth checking reviews for.
Return ONLY a YAML list of names.

Text:
{text_content}

```yaml
places:
  - <Place Name 1>
  - <Place Name 2>
```
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        parsed = yaml.safe_load(yaml_str)
        return parsed.get("places", [])

    def post(self, shared, prep_res, exec_res):
        shared["places_to_review"] = exec_res
        print(f"\n[IDENTIFY] Identified {len(exec_res)} places to review")
        return "default"


class GetPlaceReviews(BatchNode):
    """Fetch reviews and details for identified places"""

    def prep(self, shared):
        return shared.get("places_to_review", [])

    def exec(self, place_name):
        # Get structured details (rating, address)
        details = get_place_details(place_name)

        # Get review snippets via web search
        reviews_search = search_web(f"latest reviews of {place_name} positive negative")

        return {
            "name": place_name,
            "details": details[0] if details else {},  # Take top match
            "review_snippets": [r["snippet"] for r in reviews_search[:3]],
        }

    def post(self, shared, prep_res, exec_res_list):
        shared["place_reviews"] = exec_res_list
        print(f"\n[REVIEWS] Fetched reviews for {len(exec_res_list)} places")
        return "default"


class CalculateBudget(Node):
    def prep(self, shared):
        return {
            "budget": shared["trip_info"]["budget"],
            "duration": shared["trip_info"]["duration_days"],
            "travelers": shared["trip_info"]["travelers"],
            "daily_plans": shared["daily_plans"]
        }
    
    def exec(self, data):
        # Use LLM to create budget breakdown
        prompt = f"Create budget breakdown for: {data}"
        return call_llm(prompt)
    
    def post(self, shared, prep_res, exec_res):
        shared["budget_breakdown"] = exec_res

class PlanDailyItinerary(BatchNode):
    """Create detailed daily itineraries"""

    def prep(self, shared):
        duration = shared["trip_info"]["duration_days"]
        return list(range(1, duration + 1))

    def exec(self, day_number):
        # This will be called once per day
        return day_number

    def post(self, shared, prep_res, exec_res_list):
        # Generate plans for all days
        trip_info = shared["trip_info"]
        destination_info = shared["destination_info"]
        place_reviews = shared.get("place_reviews", [])

        prompt = f"""
Create a detailed daily itinerary for a {trip_info['duration_days']}-day trip to {trip_info['destination']}.

Trip Details:
- Travelers: {trip_info['travelers']}
- Budget: {trip_info['budget']}
- Style: {trip_info['travel_style']}
- Interests: {trip_info['interests']}

Research Data Available:
{destination_info[:3]}  # Use first 3 research results

Top Places & Reviews:
{place_reviews}

Create a day-by-day plan. For each day include:
- Morning activities
- Afternoon activities  
- Evening activities
- Restaurant recommendations
- Transportation tips
- Be reasonable with what can be covered on each day

Return as YAML:
strictly follow yaml structure and if there are : or any special characters in the content, escape those characters
```yaml
daily_plans:
  day_1:
    morning: <activities>
    afternoon: <activities>
    evening: <activities>
    meals: <recommendations>
    tips: <helpful tips>
  day_2:
    ...
```
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        try:
            parsed = yaml.safe_load(yaml_str)
        except ScannerError as e:
            error_prompt = f"""While parsing the below yaml I am getting error as {str(e)}.
{yaml_str}

Can you fix the parsing issue correcting the yaml. Return only the yaml and nothing else.
            """
            yaml_str = call_llm(error_prompt)
            parsed = yaml.safe_load(yaml_str)

        shared["daily_plans"] = parsed["daily_plans"]
        print(f"\n[PLANNING] Created {len(parsed['daily_plans'])} daily itineraries")

        return "default"


class CombineFinalPlan(Node):
    """Combine all sections into a comprehensive travel guide"""

    def prep(self, shared):
        return {
            "trip_info": shared["trip_info"],
            "daily_plans": shared["daily_plans"],
            "accommodations": shared["accommodations"],
            "transportation": shared["transportation"],
        }

    def exec(self, data):
        prompt = f"""
Create a comprehensive, well-formatted travel guide.

Trip Information:
{data['trip_info']}

Daily Plans:
{data['daily_plans']}

Additional Info:
- Accommodations: {data['accommodations'][:2] if data['accommodations'] else 'N/A'}
- Transportation: {data['transportation']}

Format as a beautiful travel guide with:
1. Trip Overview
2. Day-by-Day Itinerary (detailed) that is practically possible
3. Accommodation Recommendations
4. Transportation Guide
5. Important Tips
6. Budget Breakdown

Make it engaging, practical, and easy to follow.
"""
        response = call_llm(prompt)
        return response

    def post(self, shared, prep_res, exec_res):
        shared["final_travel_guide"] = exec_res
        shared["plan_revision_count"] = shared.get("plan_revision_count", 0) + 1
        print("\n[COMPLETE] Travel guide generated!")
        return "default"


class EvaluatePlan(Node):
    """Ask user if they're satisfied with the plan or have feedback"""

    def prep(self, shared):
        return {
            "plan": shared.get("final_travel_guide", ""),
            "revision_count": shared.get("plan_revision_count", 1),
        }

    def exec(self, data):
        print("\n" + "=" * 80)
        print("YOUR PERSONALIZED TRAVEL GUIDE")
        print("=" * 80 + "\n")
        print(data["plan"])
        print("\n" + "=" * 80)
        
        if data["revision_count"] >= 5:
            print("\n(Maximum revisions reached)")
            return {"satisfied": True, "feedback": ""}
        
        print("\nAre you satisfied with this plan?")
        print("  - Type 'done' or 'yes' if you're happy with it")
        print("  - Or describe any changes you'd like (e.g., 'add more food spots', 'reduce budget')")
        print()
        
        user_response = input("Your feedback: ").strip()
        
        if user_response.lower() in ["done", "yes", "looks good", "perfect", ""]:
            return {"satisfied": True, "feedback": ""}
        else:
            return {"satisfied": False, "feedback": user_response}

    def post(self, shared, prep_res, exec_res):
        if exec_res["satisfied"]:
            print("\n[FEEDBACK] User is satisfied with the plan!")
            return "done"
        else:
            shared["user_feedback"] = exec_res["feedback"]
            shared["conversation_history"].append(f"User feedback on plan: {exec_res['feedback']}")
            print(f"\n[FEEDBACK] User requested changes: {exec_res['feedback']}")
            return "revise"


class ReplanFromFeedback(Node):
    """Revise the travel plan based on user feedback"""

    def prep(self, shared):
        return {
            "current_plan": shared.get("final_travel_guide", ""),
            "feedback": shared.get("user_feedback", ""),
            "trip_info": shared.get("trip_info", {}),
            "daily_plans": shared.get("daily_plans", {}),
        }

    def exec(self, data):
        prompt = f"""
You are revising a travel plan based on user feedback.

CURRENT PLAN:
{data['current_plan']}

USER'S FEEDBACK:
"{data['feedback']}"

TRIP DETAILS:
{yaml.dump(data['trip_info'], default_flow_style=False)}

TASK:
Revise the travel plan to address the user's feedback. Keep what's working well and modify only what's needed to address their concerns.

Create an updated comprehensive travel guide that incorporates their requested changes.
"""
        response = call_llm(prompt)
        return response

    def post(self, shared, prep_res, exec_res):
        shared["final_travel_guide"] = exec_res
        shared["plan_revision_count"] = shared.get("plan_revision_count", 0) + 1
        print(f"\n[REVISED] Plan updated based on feedback (revision #{shared['plan_revision_count']})")
        return "evaluate"
