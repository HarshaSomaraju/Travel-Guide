"""
Test script for Travel Guide API
Demonstrates the full conversation flow with SSE streaming
"""
import requests
import sseclient
import json
import threading
import time

BASE_URL = "http://localhost:8000"


def stream_events(session_id, stop_event):
    """Stream SSE events in a background thread"""
    print("\n📡 Starting event stream...\n")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/chat/{session_id}/stream",
            stream=True,
            headers={"Accept": "text/event-stream"}
        )
        
        client = sseclient.SSEClient(response)
        
        for event in client.events():
            if stop_event.is_set():
                break
            
            # Handle the data - could be JSON string, Python dict string, or dict
            try:
                if isinstance(event.data, dict):
                    data = event.data
                elif isinstance(event.data, str):
                    # Try JSON first
                    try:
                        data = json.loads(event.data)
                    except json.JSONDecodeError:
                        # Try Python literal (single quotes)
                        import ast
                        data = ast.literal_eval(event.data)
                else:
                    print(f"⚠️ Unknown data type: {type(event.data)}")
                    continue
            except Exception as e:
                print(f"⚠️ Parse error: {e}")
                continue
            
            # Handle nested format {"event": ..., "data": {...}}
            if "data" in data and isinstance(data["data"], dict):
                event_type = data.get("event", data["data"].get("type", "unknown"))
                content = data["data"].get("content", "")
            else:
                event_type = data.get("type", "unknown")
                content = data.get("content", "")
            
            # Format output based on event type
            if event_type == "thinking":
                print(f"🤔 {content}")
            elif event_type == "searching":
                print(f"🔍 {content}")
            elif event_type == "progress":
                print(f"✅ {content}")
            elif event_type == "question":
                print(f"\n❓ QUESTIONS:\n{content}\n")
            elif event_type == "plan":
                print(f"\n📋 TRAVEL PLAN:\n{'='*60}\n{content}\n{'='*60}")
            elif event_type == "complete":
                print(f"\n🎉 {content}")
                stop_event.set()
            elif event_type == "error":
                print(f"❌ Error: {content}")
                stop_event.set()
            else:
                print(f"[{event_type}] {content[:100] if content else 'no content'}")
                
    except Exception as e:
        print(f"Stream error: {e}")


def send_message(session_id, message):
    """Send a message to the API"""
    payload = {"message": message}
    if session_id:
        payload["session_id"] = session_id
    
    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    return response.json()


def check_session_status(session_id):
    """Check the current session status"""
    response = requests.get(f"{BASE_URL}/api/chat/{session_id}")
    return response.json()


def main():
    print("=" * 60)
    print("🌍 TRAVEL GUIDE API TEST")
    print("=" * 60)
    
    # Step 1: Start a new conversation
    print("\n📤 Sending initial request...")
    initial_message = "I want to visit Paris for 5 days with a $2000 budget"
    
    result = send_message(None, initial_message)
    session_id = result["session_id"]
    print(f"✅ Session created: {session_id}")
    print(f"   Status: {result['status']}")
    
    # Step 2: Start streaming events
    stop_event = threading.Event()
    stream_thread = threading.Thread(
        target=stream_events, 
        args=(session_id, stop_event)
    )
    stream_thread.start()
    
    # Step 3: Interactive loop
    print("\n" + "-" * 60)
    print("💬 INTERACTIVE MODE")
    print("   Type your responses when prompted")
    print("   Type 'quit' to exit")
    print("   Type 'status' to check session status")
    print("-" * 60)
    
    try:
        while not stop_event.is_set():
            time.sleep(1)  # Small delay to let events stream
            
            # Check if we need input
            status = check_session_status(session_id)
            
            if status.get("status") == "waiting_input":
                user_input = input("\n✏️  Your response: ").strip()
                
                if user_input.lower() == "quit":
                    stop_event.set()
                    break
                elif user_input.lower() == "status":
                    print(f"Session status: {status}")
                    continue
                elif user_input:
                    print(f"\n📤 Sending: {user_input}")
                    send_message(session_id, user_input)
                    
            elif status.get("status") == "complete":
                print("\n✅ Conversation complete!")
                stop_event.set()
                break
                
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
        stop_event.set()
    
    stream_thread.join(timeout=2)
    print("\n🏁 Test finished!")


if __name__ == "__main__":
    main()
