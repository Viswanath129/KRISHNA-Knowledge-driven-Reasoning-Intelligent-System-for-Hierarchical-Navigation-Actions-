import json
from pydantic import BaseModel, Field
from .intelligence import IntelligenceInterface, extract_json

class DecisionSchema(BaseModel):
    decision: str = Field(description="The primary action chosen.")
    confidence: float = Field(description="Confidence from 0.0 to 1.0.")
    reasoning: str = Field(description="Rationale for selecting the tool.")
    tool_to_call: str = Field(description="Tool name from AVAILABLE TOOLS, or 'none'.")
    tool_args: str = Field(description="JSON string of tool arguments, e.g. '{\"key\": \"val\"}'")
    ethics_flag: str = Field(description="CLEAR, CAUTION, or REFUSE.")
    ethics_reasoning: str = Field(description="Ethics considerations.")

class ReasoningModule:
    def __init__(self, intelligence: IntelligenceInterface, ethics_engine=None):
        self.intelligence = intelligence
        self.ethics_engine = ethics_engine

    def process_trigger(self, trigger_data, state_context):
        print(f"[Reasoning] Analyzing context for trigger: {trigger_data}")
        
        decision_json_str = self.intelligence.query_llm(
            prompt=trigger_data,
            context=state_context,
            response_schema=DecisionSchema
        )
        
        if decision_json_str:
            try:
                # Try parsing — the intelligence module should have already extracted JSON
                decision_dict = json.loads(decision_json_str)
            except json.JSONDecodeError:
                # Try robust extraction one more time
                decision_dict = extract_json(decision_json_str)
            
            if decision_dict:
                # Normalize tool_args to dict
                tool_args = decision_dict.get('tool_args', {})
                if isinstance(tool_args, str):
                    if tool_args:
                        try:
                            tool_args = json.loads(tool_args)
                        except json.JSONDecodeError:
                            tool_args = {}
                    else:
                        tool_args = {}
                decision_dict['tool_args'] = tool_args if isinstance(tool_args, dict) else {}
                
                # Normalize tool_to_call
                tool_name = decision_dict.get('tool_to_call', '')
                if tool_name and tool_name.lower() in ('none', 'null', 'n/a', ''):
                    decision_dict['tool_to_call'] = None

                # --- Ethics Gate ---
                if self.ethics_engine:
                    ethics_flag = decision_dict.get("ethics_flag", "CLEAR")
                    if ethics_flag == "REFUSE":
                        print(f"[Reasoning] ⚖️  LLM self-flagged ethics REFUSAL")
                        return {
                            "decision": f"REFUSED: {decision_dict.get('ethics_reasoning', '')}",
                            "confidence": 1.0,
                            "reasoning": decision_dict.get('ethics_reasoning', ''),
                            "tool_to_call": None,
                            "tool_args": {},
                            "ethics_flag": "REFUSE",
                            "ethics_reasoning": decision_dict.get('ethics_reasoning', '')
                        }
                    
                    ethics_verdict = self.ethics_engine.evaluate_action(decision_dict)
                    if not ethics_verdict.get("approved"):
                        print(f"[Reasoning] ⚖️  Ethics Engine BLOCKED: {ethics_verdict.get('reason')}")
                        return {
                            "decision": f"BLOCKED: {ethics_verdict.get('reason')}",
                            "confidence": 1.0,
                            "reasoning": ethics_verdict.get("reason", ""),
                            "tool_to_call": None,
                            "tool_args": {},
                            "ethics_flag": "BLOCKED",
                            "ethics_reasoning": ethics_verdict.get("reason", "")
                        }

                print(f"[Reasoning] Selected Tool: {decision_dict.get('tool_to_call')}")
                return decision_dict
            else:
                print(f"[Reasoning] Could not parse LLM response. Raw: {decision_json_str[:200]}")
                 
        # Fallback
        print(f"[Reasoning] Falling back to default response.")
        return {
            "decision": "Could not parse LLM response.",
            "confidence": 0.0,
            "reasoning": "LLM returned unparseable output.",
            "tool_to_call": None,
            "tool_args": {},
            "ethics_flag": "CLEAR",
            "ethics_reasoning": "N/A"
        }
