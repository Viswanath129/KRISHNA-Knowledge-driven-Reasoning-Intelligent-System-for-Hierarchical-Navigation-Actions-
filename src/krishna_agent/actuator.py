class Actuator:
    def __init__(self, intelligence_gateway, ethics_engine=None):
         self.intelligence = intelligence_gateway
         self.ethics_engine = ethics_engine
         
    def execute(self, action_details):
        print(f"[Actuator] Physical/Digital Execution Layer Triggered.")
        
        tool_name = action_details.get("tool_to_call")
        tool_args = action_details.get("tool_args", {})
        
        if not tool_name:
             print("[Actuator] No specific tool requested by Reasoning. Relying on default decision string.")
             return {"status": "success", "output": action_details.get("decision", "No action needed.")}
             
        # --- Final Ethics Gate ---
        if self.ethics_engine:
            ethics_verdict = self.ethics_engine.evaluate_action(action_details)
            if not ethics_verdict.get("approved"):
                print(f"[Actuator] 🚫 ETHICS BLOCK at execution layer: {ethics_verdict.get('reason')}")
                return {
                    "status": "ethics_blocked",
                    "output": f"Execution refused: {ethics_verdict.get('reason')}",
                    "ethics_reason": ethics_verdict.get("reason", "")
                }

        # Look up the registered tool
        tool_record = self.intelligence.get_tool(tool_name)
        
        if tool_record and callable(tool_record["func"]):
            print(f"[Actuator] ---> Executing Tool: {tool_name} with args {tool_args}")
            try:
                result = tool_record["func"](**tool_args)
                
                # Log successful execution to ethics audit
                if self.ethics_engine:
                    print(f"[Actuator] ✅ Tool executed successfully. Ethics audit logged.")
                
                return {"status": "success", "output": result, "tool_used": tool_name}
            except Exception as e:
                print(f"[Actuator] Tool '{tool_name}' failed to execute: {e}")
                return {"status": "error", "error_message": str(e), "output": f"Error: {e}", "tool_used": tool_name}
        else:
            print(f"[Actuator] Error: Tool '{tool_name}' is not registered.")
            return {"status": "error", "error_message": f"Tool '{tool_name}' not found.", "output": f"Error: Tool '{tool_name}' not found.", "tool_used": tool_name}
