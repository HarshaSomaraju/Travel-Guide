import json
import os

def save_trip(shared):
    try:
        os.makedirs("trips", exist_ok=True)
        with open(f"trips/{shared['trip_info']['destination']}.json", "w") as f:
            json.dump(shared, f)
    except Exception as e:
        print(f"Error saving trip: {e}")

def load_trip(destination):
    try:
        with open(f"trips/{destination}.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"No trip found for destination: {destination}")
        return None