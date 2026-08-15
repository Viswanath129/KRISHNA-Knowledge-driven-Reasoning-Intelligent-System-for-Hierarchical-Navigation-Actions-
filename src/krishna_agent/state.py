import json
import os

class StateManager:
    def __init__(self, db_path=None):
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(project_root, "krishna_memory.json")
        self.db_path = db_path
        self.short_term_memory = []
        self.long_term_storage = {}
        self.context_variables = {}
        self.goal_tracking = {}
        self.ethics_audit_log = []
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    data = json.load(f)
                    self.long_term_storage = data.get("long_term_storage", {})
                    self.context_variables = data.get("context_variables", {})
                    self.goal_tracking = data.get("goal_tracking", {})
                    self.ethics_audit_log = data.get("ethics_audit_log", [])
            except Exception as e:
                print(f"[State] Error loading memory: {e}")

    def _save_state(self):
        data = {
            "long_term_storage": self.long_term_storage,
            "context_variables": self.context_variables,
            "goal_tracking": self.goal_tracking,
            "ethics_audit_log": self.ethics_audit_log[-50:]  # Keep last 50 entries
        }
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=4)

    def update_state(self, observation, result=None):
        self.short_term_memory.append({"observation": observation, "result": result})
        if len(self.short_term_memory) > 10:
            self.short_term_memory.pop(0)
        
        # Track ethics-related results
        if result and result.get("status") == "ethics_blocked":
            self.ethics_audit_log.append({
                "observation": str(observation)[:200],
                "ethics_output": result.get("output", "")[:200],
                "ethics_reason": result.get("ethics_reason", "")[:200]
            })
            self._save_state()

    def set_context_var(self, key, value):
        self.context_variables[key] = value
        self._save_state()

    def set_goal_status(self, goal_id, status):
        self.goal_tracking[goal_id] = status
        self._save_state()

    def get_context(self):
        return {
            "stm": self.short_term_memory[-5:],
            "vars": self.context_variables,
            "goals": self.goal_tracking
        }
