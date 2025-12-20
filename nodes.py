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
        return "default"


class ParseRequest(Node):
    """Parse user request to extract structured information"""

    def prep(self, shared):
        return shared["user_request"]

    def exec(self, user_request):
        prompt = f"""
Parse this travel request and extract key information. Return as YAML:

User Request: "{user_request}"

Extract these fields (use null if not mentioned):
```yaml
destination: <destination name or null>
trip_type: <local/domestic/international or null>
duration_days: <number of days or null>
travelers: <number of travelers or null>
budget: <budget amount/range or null>
travel_style: <luxury/mid-range/budget/backpacker or null>
interests: <list of interests like culture, food, adventure, etc. or []>
start_date: <date if mentioned or null>
```

Output only the YAML block.
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        parsed = yaml.safe_load(yaml_str)

        return parsed

    def post(self, shared, prep_res, exec_res):
        # Update trip_info with parsed data
        for key, value in exec_res.items():
            if value is not None and value != [] and value != "":
                shared["trip_info"][key] = value

        # Identify missing critical information
        missing = []
        critical_fields = [
            "destination",
            "duration_days",
            "travelers",
            "budget",
            "travel_style",
        ]

        for field in critical_fields:
            if not shared["trip_info"].get(field):
                missing.append(field)

        shared["missing_info"] = missing

        print(f"\n[PARSED] Trip info: {shared['trip_info']}")
        print(f"[MISSING] Need clarification on: {missing}")

        return "default"


class DecideNeedInfo(Node):
    """Agent node to decide if clarification is needed"""

    def prep(self, shared):
        return {
            "missing_info": shared["missing_info"],
            "clarification_round": shared["clarification_round"],
            "max_rounds": shared["max_clarification_rounds"],
            "trip_info": shared["trip_info"],
        }

    def exec(self, data):
        missing = data["missing_info"]
        round_num = data["clarification_round"]
        max_rounds = data["max_rounds"]

        # If no missing info or exceeded max rounds, proceed
        if not missing or round_num >= max_rounds:
            return "proceed"

        # Otherwise, ask for clarification
        return "clarify"

    def post(self, shared, prep_res, exec_res):
        print(f"\n[DECISION] Action: {exec_res}")
        return exec_res


class AskClarification(Node):
    """Generate and ask clarification questions"""

    def prep(self, shared):
        return {
            "missing_info": shared["missing_info"],
            "trip_info": shared["trip_info"],
        }

    def exec(self, data):
        missing = data["missing_info"]
        trip_info = data["trip_info"]

        prompt = f"""
Generate friendly clarification questions for a travel planner.

Current trip info: {trip_info}
Missing information: {missing}

Create 2-3 specific, conversational questions to gather the missing details.
Make them natural and helpful.

Return as YAML:
```yaml
questions:
  - <question 1>
  - <question 2>
  - <question 3 if needed>
```
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        parsed = yaml.safe_load(yaml_str)

        return parsed["questions"]

    def post(self, shared, prep_res, exec_res):
        shared["clarification_questions"] = exec_res
        shared["clarification_round"] += 1

        print("\n" + "-" * 80)
        print("I need a bit more information:")
        for i, question in enumerate(exec_res, 1):
            print(f"{i}. {question}")
        print("-" * 80)

        return "default"


class GetUserClarification(Node):
    """Get user's answers to clarification questions"""

    def prep(self, shared):
        return shared["clarification_questions"]

    def exec(self, questions):
        print("\nPlease answer the questions (all in one response):")
        user_response = input("Your answers: ")
        return user_response

    def post(self, shared, prep_res, exec_res):
        # Parse user response to update trip_info
        questions_str = "\n".join(prep_res)

        prompt = f"""
The user was asked these clarification questions:
{questions_str}

User's response: "{exec_res}"

Update the trip information based on the response. Return as YAML:
```yaml
destination: <value or null>
duration_days: <value or null>
travelers: <value or null>
budget: <value or null>
travel_style: <value or null>
interests: <list or []>
start_date: <value or null>
```
"""
        response = call_llm(prompt)
        yaml_str = extract_yaml_str(response)
        parsed = yaml.safe_load(yaml_str)

        # Update trip_info
        for key, value in parsed.items():
            if value is not None and value != [] and value != "":
                shared["trip_info"][key] = value

        # Re-evaluate missing info
        missing = []
        critical_fields = [
            "destination",
            "duration_days",
            "travelers",
            "budget",
            "travel_style",
        ]
        for field in critical_fields:
            if not shared["trip_info"].get(field):
                missing.append(field)

        shared["missing_info"] = missing

        print(f"\n[UPDATED] Trip info: {shared['trip_info']}")

        return "decide"


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
2. Day-by-Day Itinerary (detailed)
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
        print("\n[COMPLETE] Travel guide generated!")
        return "default"
