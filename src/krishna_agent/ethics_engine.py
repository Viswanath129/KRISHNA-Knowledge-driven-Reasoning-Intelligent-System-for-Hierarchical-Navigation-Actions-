"""
KRISHNA AI Ethics Engine (E)
=============================
The moral guardian of the KRISHNA agent. Evaluates every goal, decision,
and action against configurable ethical principles inspired by Dharma.

Integrates with the Intelligence module for nuanced LLM-backed ethical reasoning.
"""

import json
import os
import re
import time
from pydantic import BaseModel, Field


class EthicsVerdict(BaseModel):
    """Structured output from the LLM for ethics evaluation."""
    is_ethical: bool = Field(description="Whether the action is ethically permissible.")
    risk_level: str = Field(description="Risk level: SAFE, LOW, MEDIUM, HIGH, CRITICAL")
    reasoning: str = Field(description="Ethical reasoning and justification.")
    principle_violated: str = Field(description="Which Dharma principle is violated, if any. 'None' if compliant.")
    suggestion: str = Field(description="Suggested alternative if the action is blocked, or 'Proceed' if approved.")


class EthicsEngine:
    """
    The Dharma Guardian — evaluates goals, decisions, and actions
    against ethical principles before allowing execution.
    """

    def __init__(self, intelligence=None, rules_path=None):
        self.intelligence = intelligence
        self.dharma_score = 100
        self.audit_trail = []
        self.rules = self._load_rules(rules_path)
        self.total_evaluations = 0
        self.total_blocked = 0
        self.total_warnings = 0
        print("[Ethics] ⚖️  Dharma Guardian initialized. Ethical oversight active.")

    def _load_rules(self, rules_path=None):
        """Load ethics rules from the configuration JSON."""
        if rules_path is None:
            rules_path = os.path.join(os.path.dirname(__file__), "ethics_rules.json")
        
        try:
            with open(rules_path, "r") as f:
                rules = json.load(f)
            # Validate required list fields — malformed JSON schema fails silently otherwise
            for key in ('blocked_actions', 'sensitive_keywords', 'consent_required_actions', 'principles'):
                if not isinstance(rules.get(key), list):
                    print(f"[Ethics] WARNING: '{key}' is malformed in rules file — resetting to empty list.")
                    rules[key] = []
            if not isinstance(rules.get('risk_levels'), dict):
                print("[Ethics] WARNING: 'risk_levels' is malformed — resetting to empty dict.")
                rules['risk_levels'] = {}
            if not isinstance(rules.get('dharma_scoring'), dict):
                rules['dharma_scoring'] = {"initial_score": 100, "violation_penalty": -15,
                                           "warning_penalty": -5, "compliant_bonus": 2,
                                           "min_score": 0, "max_score": 100}
            print(f"[Ethics] Loaded {len(rules['principles'])} Dharma principles, "
                  f"{len(rules['blocked_actions'])} blocked actions.")
            return rules
        except json.JSONDecodeError as e:
            print(f"[Ethics] CRITICAL: ethics_rules.json is malformed JSON: {e}. Using safe defaults.")
            return {
                "blocked_actions": [],
                "sensitive_keywords": [],
                "consent_required_actions": [],
                "risk_levels": {},
                "dharma_scoring": {
                    "initial_score": 100,
                    "violation_penalty": -15,
                    "warning_penalty": -5,
                    "compliant_bonus": 2,
                    "min_score": 0,
                    "max_score": 100
                },
                "principles": []
            }
        except Exception as e:
            print(f"[Ethics] Warning: Could not load rules ({e}). Using defaults.")

    def _matches_blocked(self, text: str, blocked_phrase: str) -> bool:
        """
        Fuzzy word-order match: all words of the blocked phrase must appear in
        the text in order, with up to 3 optional words between each.
        E.g. 'delete system files' will match 'delete a system files' or
        'please delete all my system files'.
        """
        words = [re.escape(w) for w in blocked_phrase.lower().split()]
        if not words:
            return False
        # Allow up to 3 arbitrary words (non-newline) between each keyword
        gap = r'(?:\W+\w+){0,3}\W+'
        pattern = r'\b' + gap.join(words) + r'\b'
        return bool(re.search(pattern, text.lower()))

    def evaluate_goal(self, goal: str) -> dict:
        """
        Evaluate whether a goal aligns with ethical principles.
        Called by the Navigator before creating a plan.
        """
        self.total_evaluations += 1
        print(f"[Ethics] ⚖️  Evaluating goal ethics: '{goal[:80]}...'")

        # --- Rule-Based Check (fast) ---
        goal_lower = goal.lower()

        # Check blocked actions — fuzzy word-order matching catches variants like
        # 'delete a system files', 'hack into the system', etc.
        for blocked in self.rules.get("blocked_actions", []):
            if self._matches_blocked(goal_lower, blocked):
                return self._create_block_verdict(
                    goal, f"Goal contains blocked action: '{blocked}'",
                    "Ahimsa (Non-violence)"
                )

        # Check sensitive keywords
        for sensitive in self.rules.get("sensitive_keywords", []):
            if self._matches_blocked(goal_lower, sensitive):
                return self._create_warning_verdict(
                    goal, f"Goal involves sensitive data: '{sensitive}'",
                    "Asteya (Non-stealing)"
                )

        # --- LLM-Based Check (nuanced) ---
        if self.intelligence:
            return self._llm_ethics_check(goal, "goal")
        
        # Default: approve with compliance bonus
        return self._create_approve_verdict(goal, "Goal passed all rule-based ethics checks.")

    def evaluate_action(self, action_details: dict) -> dict:
        """
        Pre-execution ethics gate. Called by the Handler before the Actuator executes.
        """
        self.total_evaluations += 1
        tool_name = action_details.get("tool_to_call", "unknown")
        tool_args = action_details.get("tool_args", {})
        decision = action_details.get("decision", "")

        print(f"[Ethics] ⚖️  Evaluating action ethics: tool='{tool_name}'")

        # All tools: check blocked actions in args + decision text (fuzzy match)
        # This catches direct-match bypasses where risk_level is not HIGH.
        combined_check = (json.dumps(tool_args) + " " + decision).lower()
        for blocked in self.rules.get("blocked_actions", []):
            if self._matches_blocked(combined_check, blocked):
                return self._create_block_verdict(
                    f"{tool_name}({tool_args})",
                    f"Blocked intent detected in action: '{blocked}'",
                    "Ahimsa (Non-violence)"
                )

        # Check tool risk level
        risk_level = self.rules.get("risk_levels", {}).get(tool_name, "MEDIUM")
        
        if risk_level == "HIGH":
            # For high-risk tools, do deeper inspection
            args_str = json.dumps(tool_args).lower()
            for blocked in self.rules.get("blocked_actions", []):
                if self._matches_blocked(args_str + " " + decision.lower(), blocked):
                    return self._create_block_verdict(
                        f"{tool_name}({tool_args})",
                        f"High-risk tool with blocked intent: '{blocked}'",
                        "Ahimsa (Non-violence)"
                    )

            # Check for sensitive data in arguments
            for sensitive in self.rules.get("sensitive_keywords", []):
                if sensitive.lower() in args_str:
                    return self._create_warning_verdict(
                        f"{tool_name}({tool_args})",
                        f"High-risk tool accessing sensitive data: '{sensitive}'",
                        "Asteya (Non-stealing)"
                    )

        # Check consent-required actions
        for consent_action in self.rules.get("consent_required_actions", []):
            if consent_action.lower() in decision.lower():
                return self._create_warning_verdict(
                    f"{tool_name}: {decision}",
                    f"Action requires user consent: '{consent_action}'",
                    "Aparigraha (Non-possessiveness)"
                )

        return self._create_approve_verdict(
            f"{tool_name}", f"Action passed ethics review. Risk level: {risk_level}"
        )

    def _llm_ethics_check(self, content: str, content_type: str) -> dict:
        """Use the LLM for nuanced ethical reasoning."""
        prompt = (
            f"Evaluate the following {content_type} for ethical compliance. "
            f"Consider these Dharma principles:\n"
        )
        for p in self.rules.get("principles", []):
            prompt += f"  - {p}\n"
        prompt += (
            f"\nThe {content_type} to evaluate: '{content}'\n\n"
            f"Is this {content_type} ethically permissible? Consider harm potential, "
            f"privacy implications, deception, fairness, and consent."
        )

        try:
            response_str = self.intelligence.query_llm(
                prompt=prompt,
                context={"stm": [], "vars": {}, "goals": {}},
                response_schema=EthicsVerdict
            )
            
            if response_str:
                verdict_data = json.loads(response_str)
                
                if not verdict_data.get("is_ethical", True):
                    risk = verdict_data.get("risk_level", "HIGH")
                    if risk in ("CRITICAL", "HIGH"):
                        return self._create_block_verdict(
                            content,
                            verdict_data.get("reasoning", "LLM ethics check failed."),
                            verdict_data.get("principle_violated", "Unknown")
                        )
                    else:
                        return self._create_warning_verdict(
                            content,
                            verdict_data.get("reasoning", "Ethics concern detected."),
                            verdict_data.get("principle_violated", "Unknown")
                        )
                
                return self._create_approve_verdict(
                    content,
                    verdict_data.get("reasoning", "LLM approved as ethical.")
                )
        except Exception as e:
            print(f"[Ethics] LLM ethics check error: {e}. Falling back to rule-based.")
        
        return self._create_approve_verdict(content, "Fallback: passed rule-based checks.")

    def _create_block_verdict(self, subject: str, reason: str, principle: str) -> dict:
        """Create a BLOCKED verdict — action will NOT execute."""
        scoring = self.rules.get("dharma_scoring", {})
        self.dharma_score = max(
            scoring.get("min_score", 0),
            self.dharma_score + scoring.get("violation_penalty", -15)
        )
        self.total_blocked += 1

        entry = {
            "timestamp": time.time(),
            "type": "BLOCKED",
            "subject": subject[:100],
            "reason": reason,
            "principle": principle,
            "dharma_score": self.dharma_score
        }
        self.audit_trail.append(entry)
        
        print(f"[Ethics] 🚫 BLOCKED: {reason}")
        print(f"[Ethics] Principle violated: {principle}")
        print(f"[Ethics] Dharma Score: {self.dharma_score}/100")

        return {
            "approved": False,
            "type": "BLOCKED",
            "reason": reason,
            "principle": principle,
            "dharma_score": self.dharma_score,
            "suggestion": "This action has been refused on ethical grounds."
        }

    def _create_warning_verdict(self, subject: str, reason: str, principle: str) -> dict:
        """Create a WARNING verdict — action proceeds with caution."""
        scoring = self.rules.get("dharma_scoring", {})
        self.dharma_score = max(
            scoring.get("min_score", 0),
            self.dharma_score + scoring.get("warning_penalty", -5)
        )
        self.total_warnings += 1

        entry = {
            "timestamp": time.time(),
            "type": "WARNING",
            "subject": subject[:100],
            "reason": reason,
            "principle": principle,
            "dharma_score": self.dharma_score
        }
        self.audit_trail.append(entry)

        print(f"[Ethics] ⚠️  WARNING: {reason}")
        print(f"[Ethics] Principle at risk: {principle}")
        print(f"[Ethics] Dharma Score: {self.dharma_score}/100")

        return {
            "approved": True,
            "type": "WARNING",
            "reason": reason,
            "principle": principle,
            "dharma_score": self.dharma_score,
            "suggestion": "Proceed with caution."
        }

    def _create_approve_verdict(self, subject: str, reason: str) -> dict:
        """Create an APPROVED verdict — action is ethically sound."""
        scoring = self.rules.get("dharma_scoring", {})
        self.dharma_score = min(
            scoring.get("max_score", 100),
            self.dharma_score + scoring.get("compliant_bonus", 2)
        )

        entry = {
            "timestamp": time.time(),
            "type": "APPROVED",
            "subject": subject[:100],
            "reason": reason,
            "dharma_score": self.dharma_score
        }
        self.audit_trail.append(entry)

        print(f"[Ethics] ✅ APPROVED: {reason}")
        print(f"[Ethics] Dharma Score: {self.dharma_score}/100")

        return {
            "approved": True,
            "type": "APPROVED",
            "reason": reason,
            "principle": "None",
            "dharma_score": self.dharma_score,
            "suggestion": "Proceed."
        }

    def get_dharma_score(self) -> int:
        """Return the current Dharma compliance score."""
        return self.dharma_score

    def get_audit_trail(self) -> list:
        """Return the full ethics audit trail."""
        return self.audit_trail

    def get_stats(self) -> dict:
        """Return summary statistics about ethical evaluations."""
        return {
            "dharma_score": self.dharma_score,
            "total_evaluations": self.total_evaluations,
            "total_blocked": self.total_blocked,
            "total_warnings": self.total_warnings,
            "total_approved": self.total_evaluations - self.total_blocked - self.total_warnings,
            "audit_trail": self.audit_trail[-20:]  # Last 20 entries
        }
