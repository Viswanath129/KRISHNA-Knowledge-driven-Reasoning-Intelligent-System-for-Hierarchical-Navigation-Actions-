import json
import re
from pydantic import BaseModel, Field

class PlanSchema(BaseModel):
    plan_steps: list[str] = Field(description="List of steps to complete the goal.")
    analysis: str = Field(description="Why this plan was chosen.")


def split_compound_goal(goal):
    """Split compound goals into steps, handling complex sentences."""
    # Normalize separators
    # "open notepad and write about krishna and save it as krishna.txt, 
    #  then open calculator, calc 5+5 and open youtube play latest telugu song 
    #  at 50% sound at max resolution"
    
    # First, split on major separators: "then", ",", ";", "after that"
    major_parts = re.split(
        r'\s*(?:,\s*then\s+|,\s*after\s+that\s+|;\s*then\s+|;\s+then\s+|,\s+then\s+|then\s+|;\s+)',
        goal, flags=re.IGNORECASE
    )
    
    all_steps = []
    for part in major_parts:
        part = part.strip()
        if not part:
            continue
        
        # Within each major part, split on "and" but be smart about it
        # Don't split "write and save" or "search and open" — those are one action
        # DO split "open notepad and open calculator" — those are separate actions
        
        # Check if this part has multiple distinct actions with "and"
        # NOTE: 'save' excluded — "write about X and save as Y" is ONE action
        sub_parts = re.split(r'\s+and\s+(?=(?:open|launch|start|play|calc|list|show|create|search|send|set|write|read|get|run|execute|visit|browse|go|close|press|type|what|find|make|check|take|kill|minimize|maximize|switch|lock|download|empty|zip|unzip|rename|copy|move|delete|snap)\s)', part, flags=re.IGNORECASE)
        
        for sp in sub_parts:
            sp = sp.strip()
            if sp and len(sp) > 2:
                all_steps.append(sp)
    
    # If no splitting happened, return original as single step
    return all_steps if len(all_steps) > 0 else [goal]


class Navigator:
    def __init__(self, intelligence_gateway, ethics_engine=None):
        self.intelligence = intelligence_gateway
        self.ethics_engine = ethics_engine
        self.priority_queue = []
        self.current_plan = []

    def set_goal(self, goal):
        print(f"[Navigator] Processing goal: {goal}")
        
        # --- Ethics Gate ---
        if self.ethics_engine:
            ethics_verdict = self.ethics_engine.evaluate_goal(goal)
            if not ethics_verdict.get("approved"):
                print(f"[Navigator] 🚫 GOAL REJECTED: {ethics_verdict.get('reason')}")
                print(f"[Navigator] Principle violated: {ethics_verdict.get('principle')}")
                self.priority_queue.append(
                    f"[ETHICS BLOCK] Goal refused: {ethics_verdict.get('reason')}. "
                    f"Dharma principle: {ethics_verdict.get('principle')}."
                )
                return

        # Split compound goals into steps (instant)
        steps = split_compound_goal(goal)
        if len(steps) > 1:
            print(f"[Navigator] ⚡ Compound goal — {len(steps)} steps:")
            for i, s in enumerate(steps, 1):
                print(f"[Navigator]   Step {i}: {s}")
        else:
            print(f"[Navigator] ⚡ Single goal — fast mode")
        
        self.current_plan = steps
        self.priority_queue.extend(self.current_plan)

    def get_next_step(self):
        if self.priority_queue:
            return self.priority_queue.pop(0)
        return None

    def handle_error(self, error):
        print(f"[Navigator] Handling error: {error}")
        self.priority_queue.insert(0, f"Recover from failure: {error}")
