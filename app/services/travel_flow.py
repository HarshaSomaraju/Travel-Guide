"""
Travel flow service - runs PocketFlow with pause/resume support for API
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flow import create_travel_guide_flow
from app.core.events import EventType


# Thread pool for running sync flow code
executor = ThreadPoolExecutor(max_workers=4)


class FlowRunner:
    """Manages running and resuming the travel flow"""
    
    def __init__(self, session):
        self.session = session
        self.shared = session.shared
        self.flow = None
    
    def run(self):
        """Run the flow until it completes or pauses"""
        try:
            emitter = self.session.emitter
            
            # Set API mode
            self.shared["api_mode"] = True
            self.shared["flow_status"] = "processing"
            
            # Emit start event
            emitter.thinking("Starting to plan your trip...")
            
            # Create and run the flow
            self.flow = create_travel_guide_flow()
            self.flow.run(self.shared)
            
            # Check if flow paused or completed
            if self.shared.get("flow_status") == "waiting_input":
                self.session.status = "waiting_input"
            else:
                # Flow completed normally
                self.shared["flow_status"] = "complete"
                self.session.status = "complete"
                
                final_plan = self.shared.get("final_travel_guide", "")
                if final_plan and not self.shared.get("plan_emitted"):
                    emitter.plan(final_plan, is_final=True)
                    self.shared["plan_emitted"] = True
                
                emitter.complete("Your travel plan is ready!")
            
        except Exception as e:
            self.session.emitter.error(f"Error: {str(e)}")
            self.session.status = "error"
            self.shared["flow_status"] = "error"
            raise
    
    def resume(self, user_input: str):
        """Resume the flow with user input"""
        try:
            emitter = self.session.emitter
            
            # Set the pending input
            self.shared["pending_input"] = user_input
            self.shared["flow_status"] = "processing"
            
            # Add to conversation history
            self.shared["conversation_history"].append(f"User: {user_input}")
            
            emitter.thinking("Processing your response...")
            
            # Re-run the flow - it will continue from where it left off
            # because the shared state is preserved
            self.flow = create_travel_guide_flow()
            self.flow.run(self.shared)
            
            # Check status after run
            if self.shared.get("flow_status") == "waiting_input":
                self.session.status = "waiting_input"
            else:
                self.shared["flow_status"] = "complete"
                self.session.status = "complete"
                
                final_plan = self.shared.get("final_travel_guide", "")
                if final_plan and not self.shared.get("plan_emitted"):
                    emitter.plan(final_plan, is_final=True)
                    self.shared["plan_emitted"] = True
                
                emitter.complete("Your travel plan is ready!")
                
        except Exception as e:
            self.session.emitter.error(f"Error: {str(e)}")
            self.session.status = "error"
            raise


def run_flow_sync(session, user_message: str = None):
    """
    Run or resume the travel flow synchronously.
    Called from thread pool executor.
    """
    runner = FlowRunner(session)
    
    if session.status == "waiting_input" and user_message:
        # Resume with user input
        runner.resume(user_message)
    else:
        # Initial run - set the first message as pending input
        if user_message:
            session.shared["pending_input"] = user_message
            session.shared["conversation_history"].append(f"User: {user_message}")
        runner.run()


async def run_travel_flow_async(session, user_message: str = None):
    """
    Run the travel flow in a background thread.
    This allows the FastAPI endpoint to return immediately.
    """
    loop = asyncio.get_event_loop()
    
    # Run sync flow in thread pool
    await loop.run_in_executor(executor, run_flow_sync, session, user_message)
