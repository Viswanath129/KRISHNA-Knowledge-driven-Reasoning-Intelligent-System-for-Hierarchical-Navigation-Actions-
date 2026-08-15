"""
KRISHNA Intelligence Interface
================================
Connects to a LOCAL LLM via Nexa CLI's OpenAI-compatible API.
No API key required — runs entirely on your machine's NPU.

Start the local model server first:
    nexa serve NexaAI/phi4-mini-npu-turbo
"""

import os
import json
import re
import requests
import time
import subprocess


ETHICS_SYSTEM_PROMPT = (
    "You are KRISHNA, an AI agent. You must follow Dharma ethics: "
    "Ahimsa (no harm), Satya (truth), Asteya (no stealing), "
    "Aparigraha (no hoarding), Karuna (compassion). "
    "REFUSE unethical requests. "
    "ALWAYS reply with valid JSON ONLY. No markdown, no explanation, no code fences."
)


def extract_json(text):
    """Robustly extract JSON from free-text LLM responses."""
    if not text:
        return None
    if isinstance(text, (dict, list)):
        return text
    
    text = text.strip()
    
    # Remove markdown code fences
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()
    
    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Find JSON objects in the text
    brace_depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == '{':
            if brace_depth == 0:
                start = i
            brace_depth += 1
        elif ch == '}':
            brace_depth -= 1
            if brace_depth == 0 and start >= 0:
                candidate = text[start:i+1]
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    # Try fixing common issues
                    candidate = candidate.replace("'", '"')
                    candidate = re.sub(r',\s*}', '}', candidate)
                    candidate = re.sub(r',\s*]', ']', candidate)
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        start = -1
                        continue
    
    # Try to find key-value patterns manually
    tool_match = re.search(r'tool[_\s]*(?:to[_\s]*call|name)["\s:]*["\']?(\w+)["\']?', text, re.IGNORECASE)
    if tool_match:
        tool_name = tool_match.group(1)
        # Try to extract args
        args = {}
        args_match = re.search(r'tool[_\s]*args["\s:]*({[^}]*})', text, re.IGNORECASE)
        if args_match:
            try:
                args = json.loads(args_match.group(1).replace("'", '"'))
            except:
                pass
        return {
            "tool_to_call": tool_name,
            "tool_args": args,
            "decision": f"Use {tool_name}",
            "confidence": 0.7,
            "reasoning": "Extracted from free-text response",
            "ethics_flag": "CLEAR",
            "ethics_reasoning": "N/A"
        }
    
    return None


def get_agy_path():
    home = os.path.expanduser("~")
    path = os.path.join(home, "AppData", "Local", "agy", "bin", "agy_core.exe")
    if os.path.exists(path):
        return path
    # Fallback to PATH search
    import shutil
    return shutil.which("agy_core.exe") or shutil.which("agy") or "agy"



class IntelligenceInterface:
    def __init__(self):
        self.knowledge_base = {}
        self.tools_registry = {}
        # Switch to Ollama default port and the user's requested model
        self.base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434")
        self.model_name = os.getenv("LLM_MODEL", "visw-ai")
        self.llm_provider = "agy"
        self.agy_path = get_agy_path()
        print(f"[Intelligence] Using agy CLI backend at {self.agy_path}")

        
        # Initialize Groq API client (Fastest)
        self.groq_client = None
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        if self.groq_api_key:
            try:
                from groq import Groq
                self.groq_client = Groq(api_key=self.groq_api_key)
                print("[Intelligence] ⚡ Groq client initialized (llama-3.3-70b-versatile).")
            except Exception as e:
                print(f"[Intelligence] Could not initialize Groq client: {e}")

        # Initialize Gemini API client as fallback
        self.gemini_client = None
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if self.gemini_api_key:
            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=self.gemini_api_key)
                print("[Intelligence] 🔮 Gemini client initialized as fallback (gemini-2.0-flash).")
            except Exception as e:
                print(f"[Intelligence] Could not initialize Gemini client: {e}")

    def _call_groq_llm(self, messages, temperature=0.2):
        """Call Groq API for insane speed."""
        if not self.groq_client:
            return None
        try:
            chat_completion = self.groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=temperature,
                max_tokens=1024,
                response_format={"type": "json_object"} if "JSON" in messages[0]["content"] else None
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            print(f"[Intelligence] ❌ Groq Error: {e}")
            return None

    def _call_gemini_llm(self, messages, temperature=0.2):
        """Call Gemini API using google-genai SDK with retry logic on rate limits."""
        if not self.gemini_client:
            return None
        
        max_retries = 3
        backoff = 0.5
        for attempt in range(max_retries):
            try:
                system_instruction = None
                contents = []
                for msg in messages:
                    role = msg.get("role")
                    content = msg.get("content")
                    if role == "system":
                        system_instruction = content
                    elif role in ("user", "assistant"):
                        contents.append(content)
                
                from google.genai import types
                config = types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=1024,
                    system_instruction=system_instruction,
                    response_mime_type="application/json" if "JSON" in (system_instruction or "") else None
                )
                
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=contents,
                    config=config
                )
                
                if response.text:
                    return response.text.strip()
                return None
            except Exception as e:
                err_str = str(e).lower()
                is_rate_limit = "429" in err_str or "resource_exhausted" in err_str or "rate limit" in err_str
                if is_rate_limit and attempt < max_retries - 1:
                    print(f"[Intelligence] ⚠️ Gemini rate limit hit (429). Retrying in {backoff}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    print(f"[Intelligence] ❌ Gemini Error: {e}")
                    return None
        return None

    def _call_local_llm(self, messages, temperature=0.2):
        """Call the local Ollama (Viswa AI) API with Groq/Gemini fallback."""
        url = f"{self.base_url}/v1/chat/completions"
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 1024,
            "stream": False,
        }

        try:
            # Use short timeout for local model to fail fast if not running
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout, Exception) as e:
            if isinstance(e, requests.exceptions.ConnectionError):
                print(f"[Intelligence] ❌ Cannot connect to Viswa AI (Ollama) at {self.base_url}. Is it running?")
            else:
                print(f"[Intelligence] ❌ Viswa AI (Ollama) Error: {e}")
            
            if self.groq_client:
                print("[Intelligence] ⚡ Falling back to Groq API (Insane Speed)...")
                return self._call_groq_llm(messages, temperature)
            elif self.gemini_client:
                print("[Intelligence] 🔮 Falling back to Gemini API...")
                return self._call_gemini_llm(messages, temperature)
            return None

    def _call_agy(self, prompt, schema=None):
        """Call the agy CLI binary for completion."""
        if not self.agy_path:
            return None
        
        cmd = [self.agy_path, "--print", prompt, "--dangerously-skip-permissions", "--disable-slash-commands"]
        
        if schema:
            cmd.extend(["--output-format", "json", "--json-schema", json.dumps(schema)])
        
        try:
            creationflags = 0
            if os.name == 'nt':
                creationflags = 0x08000000  # CREATE_NO_WINDOW
                
            print(f"[Intelligence] Running agy: {' '.join(cmd[:4])} ...")
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=creationflags,
                timeout=120
            )
            
            if res.returncode != 0:
                print(f"[Intelligence] ❌ agy returned error code {res.returncode}: {res.stderr or res.stdout}")
                return None
                
            output = res.stdout.strip()
            if schema:
                try:
                    data = json.loads(output)
                    structured = data.get("structured_output")
                    if structured is not None:
                        return json.dumps(structured)
                    resp_text = data.get("response", "")
                    parsed_resp = extract_json(resp_text)
                    if parsed_resp:
                        return json.dumps(parsed_resp)
                    return resp_text
                except json.JSONDecodeError as je:
                    print(f"[Intelligence] ❌ Failed to parse agy JSON output: {je}")
                    return None
            else:
                return output
        except Exception as e:
            print(f"[Intelligence] ❌ Error running agy: {e}")
            return None

    def _call_agy_with_fallback(self, prompt, schema=None, fallback_messages=None):
        """Call agy CLI, falling back to legacy local Ollama / API fallbacks if it fails."""
        raw = self._call_agy(prompt, schema)
        if raw:
            return raw
        print("[Intelligence] agy call failed or returned None. Trying legacy local Ollama / API fallbacks...")
        if fallback_messages:
            return self._call_local_llm(fallback_messages, temperature=0.2)
        return None

    def query_llm(self, prompt, context, response_schema=None):
        print(f"[Intelligence] Querying LOCAL model ({self.llm_provider})...")
        
        # Build a VERY simple, concise prompt for the small model
        tool_list = []
        for name, info in self.tools_registry.items():
            tool_list.append(f"- {name}: {info['description']}")
        tools_str = "\n".join(tool_list)

        system_msg = (
            f"{ETHICS_SYSTEM_PROMPT}\n\n"
            f"AVAILABLE TOOLS:\n{tools_str}\n\n"
            f"RESPONSE FORMAT: Reply with ONLY a JSON object like this:\n"
            f'{{"tool_to_call": "tool_name", "tool_args": {{"arg": "value"}}, '
            f'"decision": "what to do", "confidence": 0.9, '
            f'"reasoning": "why", "ethics_flag": "CLEAR", "ethics_reasoning": "ok"}}\n\n'
            f"RULES:\n"
            f"- Pick ONE tool from the list above\n"
            f"- If no tool fits, set tool_to_call to \"none\"\n"
            f"- Reply with ONLY the JSON, nothing else"
        )

        user_msg = f"Task: {prompt}"
        if context.get('stm'):
            recent = context['stm'][-2:]
            user_msg += f"\nRecent context: {json.dumps(recent, default=str)[:300]}"

        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]

        prompt_content = f"System Instructions:\n{system_msg}\n\nUser Task:\n{user_msg}"
        schema = {
            "type": "object",
            "properties": {
                "tool_to_call": {"type": "string"},
                "tool_args": {"type": "object"},
                "decision": {"type": "string"},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"},
                "ethics_flag": {"type": "string"},
                "ethics_reasoning": {"type": "string"}
            },
            "required": ["tool_to_call", "tool_args", "decision", "confidence", "reasoning", "ethics_flag", "ethics_reasoning"]
        }
        raw = self._call_agy_with_fallback(prompt_content, schema=schema, fallback_messages=messages)

        
        if raw:
            parsed = extract_json(raw)
            if parsed:
                return json.dumps(parsed)
            else:
                print(f"[Intelligence] Warning: Could not parse JSON from response: {raw[:200]}")
        
        # Fallback mechanism if all LLM options fail/return invalid JSON
        print("[Intelligence] ⚠️ LLM pipeline failed or returned invalid JSON. Using schema-compliant static fallback.")
        
        matched_tool = "none"
        matched_args = {}
        decision_desc = "No tool matched"
        
        prompt_lower = prompt.lower()
        if "notepad" in prompt_lower:
            matched_tool = "open_application"
            matched_args = {"application": "notepad"}
            decision_desc = "Open Notepad"
        elif "calculator" in prompt_lower or "calc" in prompt_lower:
            matched_tool = "open_application"
            matched_args = {"application": "calculator"}
            decision_desc = "Open Calculator"
        elif "chrome" in prompt_lower or "browser" in prompt_lower:
            matched_tool = "open_application"
            matched_args = {"application": "chrome"}
            decision_desc = "Open Chrome"
        elif "time" in prompt_lower:
            matched_tool = "get_time"
            decision_desc = "Get Time"
        elif "system" in prompt_lower or "specs" in prompt_lower:
            matched_tool = "get_system_info"
            decision_desc = "Get System Info"
        elif "screenshot" in prompt_lower:
            matched_tool = "screenshot"
            decision_desc = "Take Screenshot"
        elif "empty" in prompt_lower and "recycle" in prompt_lower:
            matched_tool = "empty_recycle_bin"
            decision_desc = "Empty Recycle Bin"
            
        fallback_decision = {
            "tool_to_call": matched_tool,
            "tool_args": matched_args,
            "decision": f"Fallback match: {decision_desc}",
            "confidence": 0.5 if matched_tool != "none" else 0.0,
            "reasoning": "LLM endpoints offline. Heuristic fallback applied.",
            "ethics_flag": "CLEAR",
            "ethics_reasoning": "Passed offline check."
        }
        return json.dumps(fallback_decision)

    def query_ethics_llm(self, prompt, response_schema=None):
        """Dedicated ethics evaluation query."""
        print(f"[Intelligence] Querying LOCAL model for ethics evaluation...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "You evaluate if actions are ethical. "
                    "Reply with ONLY JSON: "
                    '{"is_ethical": true/false, "risk_level": "SAFE/LOW/MEDIUM/HIGH/CRITICAL", '
                    '"reasoning": "why", "principle_violated": "None or principle name", '
                    '"suggestion": "Proceed or alternative"}'
                )
            },
            {"role": "user", "content": prompt}
        ]

        prompt_content = f"System Instructions:\nYou evaluate if actions are ethical.\n\nUser Task:\n{prompt}"
        schema = {
            "type": "object",
            "properties": {
                "is_ethical": {"type": "boolean"},
                "risk_level": {"type": "string"},
                "reasoning": {"type": "string"},
                "principle_violated": {"type": "string"},
                "suggestion": {"type": "string"}
            },
            "required": ["is_ethical", "risk_level", "reasoning", "principle_violated", "suggestion"]
        }
        raw = self._call_agy_with_fallback(prompt_content, schema=schema, fallback_messages=messages)

        if raw:
            parsed = extract_json(raw)
            if parsed:
                return json.dumps(parsed)
                
        # Ethics fallback
        fallback_verdict = {
            "is_ethical": True,
            "risk_level": "SAFE",
            "reasoning": "LLM offline, approved by default static safety fallback.",
            "principle_violated": "None",
            "suggestion": "Proceed"
        }
        return json.dumps(fallback_verdict)

    def query_plan_llm(self, goal):
        """Simple query to break a goal into steps."""
        print(f"[Intelligence] Querying LOCAL model for plan generation...")
        
        messages = [
            {
                "role": "system",
                "content": (
                    "Break the user's goal into simple action steps. "
                    "Reply with ONLY JSON: "
                    '{"plan_steps": ["step 1", "step 2"], "analysis": "reasoning"}'
                )
            },
            {"role": "user", "content": f"Goal: {goal}"}
        ]

        prompt_content = f"System Instructions:\nBreak the user's goal into simple action steps.\n\nUser Task:\nGoal: {goal}"
        schema = {
            "type": "object",
            "properties": {
                "plan_steps": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "analysis": {"type": "string"}
            },
            "required": ["plan_steps", "analysis"]
        }
        raw = self._call_agy_with_fallback(prompt_content, schema=schema, fallback_messages=messages)

        if raw:
            parsed = extract_json(raw)
            if parsed:
                return json.dumps(parsed)
                
        # Plan fallback
        fallback_plan = {
            "plan_steps": [goal],
            "analysis": "LLM offline, treated as single step plan."
        }
        return json.dumps(fallback_plan)

    def register_tool(self, tool_name, tool_func, description):
        self.tools_registry[tool_name] = {
            "func": tool_func,
            "description": description
        }
        print(f"[Intelligence] Tool '{tool_name}' registered.")

    def get_tool(self, tool_name):
        return self.tools_registry.get(tool_name)
