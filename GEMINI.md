# Project Orchestration: Gemini CLI + Claude Code

## Workflow: Conductor & Execution Agent
In this workspace, Gemini CLI acts as the **Conductor** and Claude Code acts as the **Execution Agent**.

### Gemini CLI Role (Conductor)
- Perform high-level reasoning and system mapping.
- Analyze complex design plans and architectural requirements.
- Draft optimized, structural prompts for execution.
- **Output Format:** Provide execution commands formatted specifically for Claude Code's one-shot execution flags:
  - `claude --print "[Optimized Prompt]"`
  - `claude -p "[Optimized Prompt]"`

### Claude Code Role (Execution Agent)
- Handle local filesystem modifications.
- Execute targeted scripts and updates.
- Perform fast, agentic coding tasks based on Gemini CLI's structural prompts.

### Constraints
- Do not suggest third-party proxies (e.g., LiteLLM).
- Do not suggest external API keys or middle-man apps.
- Operate strictly within the local machine environment.
