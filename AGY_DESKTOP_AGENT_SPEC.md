# AGY Desktop Agent — Windows-Native Autonomous Control Specification

**Document:** AGY Desktop Agent Runtime Specification  
**Version:** 2.0  
**Target:** Windows 11+  
**Primary runtime:** `agy.exe`  
**Design goal:** Human-level computer interaction with Windows-native control, MCP extensibility, UACC-style application/control adapters, intelligent approval, verification, and low-latency execution.

> **Core principle:** AGY is not a CMD wrapper. CMD/PowerShell is one execution backend inside a capability-oriented Windows agent. The agent should prefer deterministic local APIs and semantic UI automation, use computer vision only when necessary, and reserve LLM reasoning for ambiguity, planning, and recovery.

---

## 1. Mission

AGY is a local-first desktop agent that can understand a user's natural-language or voice intent, inspect the Windows environment, select the safest and fastest control mechanism, execute the task, verify the result, recover from failure, and report the outcome clearly.

AGY should feel like a highly capable human operator while remaining bounded by explicit safety policy and user control.

### Design objectives

- Human-level desktop interaction.
- Windows-native control whenever a deterministic API exists.
- Semantic UI automation before coordinate-based clicking.
- Local-first execution and minimal network dependency.
- Millisecond-class local actions where technically achievable.
- LLM calls only when they add value.
- Automatic approval for routine, reversible, low-risk actions.
- Explicit verification for destructive, irreversible, security-sensitive, financial, communication, or privilege-changing actions.
- Continuous state awareness instead of repeatedly rediscovering the desktop.
- MCP-based extensibility.
- UACC/application-specific adapters where available.
- Full auditability without storing unnecessary sensitive content.

---

# 2. Non-Negotiable Principles

### 2.1 Capability over command

Never design the system as:

```text
LLM -> generated CMD -> Windows
```

Design it as:

```text
User
  -> Intent
  -> Agent Orchestrator
  -> Policy + Approval
  -> Capability Router
  -> Best Windows Control Surface
  -> Verification
  -> State Update
```

PowerShell/CMD is a capability, not the control plane.

### 2.2 Fast path first

AGY must prefer deterministic execution paths in this order unless policy or capability availability dictates otherwise:

```text
1. Direct Windows/native API
2. UI Automation / semantic control
3. Application-specific adapter / UACC
4. Existing application API / protocol
5. Keyboard shortcut / SendInput
6. PowerShell / CMD / shell
7. Accessibility / Voice Access bridge
8. Vision-based computer use
9. LLM-guided recovery
```

The ordering is a preference, not an absolute rule. The router may choose a lower layer when it is demonstrably more reliable for the target application.

### 2.3 Observe -> Act -> Verify

Every consequential action follows:

```text
OBSERVE
   -> SELECT
   -> ACT
   -> VERIFY
   -> UPDATE WORLD STATE
```

Never assume success merely because an API returned without throwing an error.

### 2.4 Least privilege

AGY must not require Administrator privileges for normal operation.

Elevation is a separate capability and must have separate policy treatment.

### 2.5 User intent is authoritative, but safety boundaries remain active

A user request may authorize AGY to act, but cannot automatically authorize dangerous actions that require a confirmation gate under policy.

### 2.6 Never pretend

AGY must distinguish:

- executed successfully
- partially completed
- execution failed
- execution not attempted
- verification unavailable
- user approval required

Do not report success unless the result is verified or the operation has an explicitly defined reliable completion signal.

---

# 3. High-Level Architecture

```text
                           USER
                 ┌──────────┴──────────┐
                 │                     │
              TEXT/CLI              VOICE
                 │                     │
                 └──────────┬──────────┘
                            ▼
                  ┌───────────────────┐
                  │    AGY HOST        │
                  │                    │
                  │ Session Manager    │
                  │ Intent Resolver    │
                  │ Task Manager       │
                  │ Memory / Context   │
                  └─────────┬─────────┘
                            ▼
                  ┌───────────────────┐
                  │ AGENT ORCHESTRATOR │
                  │                    │
                  │ Observe            │
                  │ Plan               │
                  │ Route              │
                  │ Execute            │
                  │ Verify             │
                  │ Recover            │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ POLICY ENGINE      │
                  │                    │
                  │ Risk classifier    │
                  │ Approval engine    │
                  │ Scope boundaries   │
                  │ Privilege checks   │
                  └─────────┬─────────┘
                            │
                            ▼
                  ┌───────────────────┐
                  │ CAPABILITY ROUTER  │
                  └─────────┬─────────┘
                            │
          ┌─────────────────┼───────────────────┐
          ▼                 ▼                   ▼
    WINDOWS CORE         MCP BUS          APP/UACC ADAPTERS
          │                 │                   │
          ▼                 ▼                   ▼
   ┌─────────────┐   ┌─────────────┐    ┌──────────────┐
   │ Native APIs │   │ MCP Servers │    │ Application  │
   │ Win32       │   │ Browser     │    │ adapters     │
   │ PowerShell  │   │ Files       │    │ selectors    │
   │ Input       │   │ Git         │    │ semantic UI  │
   │ Audio       │   │ custom      │    │ app APIs     │
   │ Display     │   └─────────────┘    └──────────────┘
   │ Processes   │
   └──────┬──────┘
          │
          ▼
   ┌───────────────────────────────┐
   │ WINDOWS INTERACTION FABRIC    │
   │                               │
   │ UI Automation                 │
   │ SendInput / keyboard          │
   │ Window management             │
   │ Clipboard                     │
   │ Screenshots                   │
   │ Accessibility                 │
   │ Voice Access bridge           │
   │ Shell                         │
   └──────────────┬────────────────┘
                  │
                  ▼
              WINDOWS OS
                  │
                  ▼
             WORLD STATE
                  │
                  └──────────────► ORCHESTRATOR
```

Windows UI Automation exposes the desktop as a tree of automation elements, with properties and control patterns that can be queried and manipulated programmatically. AGY should exploit that semantic structure before falling back to image-based interaction. [Microsoft UI Automation Specification](https://learn.microsoft.com/en-us/windows/win32/winauto/ui-automation-specification)

---

# 4. Core Runtime Components

## 4.1 `agy-host`

Owns:

- user session
- task lifecycle
- model interface
- context window
- approval UI
- policy configuration
- event bus
- audit stream

## 4.2 `agy-orchestrator`

Runs the agent loop:

```text
receive intent
 -> resolve goal
 -> inspect state
 -> create minimal plan
 -> select capability
 -> request approval if required
 -> execute
 -> verify
 -> repair/retry if needed
 -> finish
```

## 4.3 `agy-world`

Maintains a compact local model of the current machine:

```yaml
windows:
  - hwnd: ...
    title: ...
    process: ...
    focused: true
    ui_signature: ...
processes:
  - pid: ...
    name: ...
audio:
  volume: ...
  muted: ...
displays:
  - id: ...
    brightness: ...
clipboard:
  hash: ...
network:
  connected: true
```

Only retain the minimum information necessary for the current task.

## 4.4 `agy-policy`

Classifies actions before execution.

Possible decisions:

```text
ALLOW_AUTOMATIC
ALLOW_WITH_REVIEW
REQUIRE_CONFIRMATION
DENY
```

## 4.5 `agy-router`

Chooses the fastest reliable control surface.

Example:

```text
volume +5%
 -> Windows audio API

click "Send"
 -> UI Automation InvokePattern

open app
 -> native process launch / App activation

canvas drawing
 -> screenshot + vision + input

complex unknown UI
 -> UIA -> screenshot -> model recovery
```

## 4.6 `agy-exec`

Contains isolated executors for:

- Windows API
- Win32
- UI Automation
- PowerShell
- CMD
- process management
- file operations
- input injection
- clipboard
- audio
- display
- shell commands
- browser controls

## 4.7 `agy-mcp`

MCP host/client layer for external tools and capability servers.

MCP should extend AGY, not replace its Windows-native fast path.

## 4.8 `agy-vision`

Optional perception layer for:

- screenshots
- visual targeting
- OCR
- canvas applications
- inaccessible controls
- remote desktops
- UI recovery

## 4.9 `agy-memory`

Store:

- short-lived task state
- successful interaction patterns
- user preferences explicitly learned
- application-specific selectors
- failure/recovery patterns

Never silently turn sensitive desktop content into permanent memory.

---

# 5. Tool Contract

Every capability exposed to the model should have a strict schema.

Example:

```json
{
  "name": "windows.volume.set",
  "description": "Set system output volume",
  "risk": "low",
  "reversible": true,
  "requires_confirmation": false,
  "latency_class": "ultra_low",
  "input": {
    "percent": "integer 0..100"
  }
}
```

Dangerous example:

```json
{
  "name": "windows.system.shutdown",
  "description": "Shut down Windows",
  "risk": "critical",
  "reversible": false,
  "requires_confirmation": true,
  "latency_class": "local",
  "input": {
    "delay_seconds": "integer"
  }
}
```

The model never gets unrestricted access to an arbitrary executor without going through the capability contract.

---

# 6. Intelligent Auto-Approval Model

AGY must not use a simplistic rule such as "user said it, therefore approve."

Use a multi-factor decision:

```text
RISK = f(
    reversibility,
    impact,
    scope,
    privilege,
    data sensitivity,
    external side effects,
    financial consequence,
    communication consequence,
    confidence,
    task context
)
```

## 6.1 Risk classes

### R0 — Passive / observation

Auto-approve.

Examples:

- screenshot
- inspect windows
- inspect UI
- list processes
- read non-sensitive task files
- check volume
- check brightness
- detect current application

### R1 — Safe reversible actions

Auto-approve.

Examples:

- open application
- switch application
- focus window
- minimize/maximize
- scroll
- type into an explicitly targeted field
- copy text
- change volume
- mute/unmute
- change brightness
- play/pause media
- move/resize normal windows

### R2 — User-data modification, reversible or recoverable

Usually auto-approve when scope is clear and task intent is explicit.

Examples:

- create a folder
- create a document
- rename a file
- move a file inside the working scope
- edit a document
- create a draft email
- modify project files

Escalate if:

- bulk operation
- unusual scope
- sensitive files
- uncertainty about target
- overwrite of important data

### R3 — External side effect / meaningful user commitment

Require confirmation unless the user has explicitly pre-authorized the exact operation class for the current task.

Examples:

- send an email
- send a chat message
- post publicly
- submit a form
- purchase an item
- make a booking
- publish content
- upload sensitive data
- share a file externally

### R4 — Destructive / irreversible / high impact

Always require explicit confirmation immediately before execution.

Examples:

- delete permanent files
- empty recycle bin
- shutdown
- restart
- factory reset
- format a drive
- terminate critical/system processes
- uninstall important software
- revoke credentials
- disable security controls
- change firewall/security policy
- modify startup persistence
- wipe data

### R5 — Forbidden

Never execute through ordinary AGY autonomy.

Examples:

- credential theft
- disabling security to bypass protections
- covert surveillance
- unauthorized access
- persistence intended to evade user control
- destructive actions against third-party systems without authorization
- hidden exfiltration

---

# 7. Confirmation UX

The approval prompt must be short, specific, humble, and actionable.

Bad:

```text
Are you sure?
```

Good:

```text
This will permanently delete 18 files (1.4 GB) from:
D:\Projects\OldBuilds

This cannot be undone.

Proceed?  [Yes] [No]
```

For shutdown:

```text
I can shut down Windows now. Unsaved work may be lost.

Proceed with shutdown?  [Shut down] [Cancel]
```

For sending a message:

```text
Ready to send this message to Rahul:
"..."

This will leave your device.
Send it?  [Send] [Cancel]
```

AGY must not manipulate the user into approval.

Do not say:

```text
"Don't worry, nothing bad will happen."
```

Say what is actually known.

---

# 8. Approval Scope

Approvals should be narrowly scoped.

A confirmation for:

```text
Delete these 18 files
```

must not automatically authorize:

```text
Delete all files in D:\
```

A user may explicitly create a temporary policy:

```text
For this task, automatically approve file renames and moves inside:
D:\Projects\Demo
```

The permission expires at task/session boundary unless the user explicitly saves it.

---

# 9. Batch Approval

AGY may group homogeneous operations to reduce interruption.

Example:

```text
The task will:
1. rename 12 screenshots
2. move them to D:\Screenshots\2026
3. create one index file

All operations are reversible within the current task.

Allow this batch? [Allow] [Review]
```

Do not batch unrelated dangerous actions together.

Never hide a critical action inside a large batch approval.

---

# 10. User Intent Resolution

Interpret natural language semantically.

Examples:

```text
"Make the volume louder"
-> volume.increase

"Turn it down a bit"
-> volume.decrease by default step

"Close Chrome"
-> locate Chrome -> request close

"Kill Chrome"
-> terminate process, higher risk than normal close

"Get rid of these files"
-> ambiguous destructive intent -> inspect target -> require confirmation before permanent deletion

"Clean this folder"
-> DO NOT guess deletion scope; inspect and clarify via targeted confirmation UI
```

The agent should infer obvious low-risk details but should not invent critical scope.

---

# 11. Ambiguity Policy

AGY should avoid unnecessary questions.

Use this hierarchy:

```text
If safe inference exists:
    infer and act.

If multiple safe interpretations exist:
    choose the most likely one and state it briefly.

If consequences differ materially:
    ask a targeted question.

If action is dangerous:
    inspect exact scope and request confirmation.
```

Example:

```text
User: "Close the browser."

If exactly one browser window is active:
-> close it.

If five browser windows exist:
-> close active browser session only if context is obvious;
   otherwise show the candidates.
```

---

# 12. Latency Architecture

The phrase "~ms latency" applies to the local control plane, not to arbitrary LLM inference or external network requests.

AGY must minimize end-to-end latency by separating the system into paths.

## 12.1 L0 — deterministic local path

Target: sub-10 ms where practical; exact latency depends on Windows APIs, scheduling, hardware, and operation.

Examples:

- read cached world state
- volume adjustment
- media key
- process lookup from cache
- focus known window
- local state read

## 12.2 L1 — semantic local path

Target: tens of milliseconds where practical.

Examples:

- UI Automation element lookup
- window enumeration
- control invocation
- local PowerShell command

## 12.3 L2 — application adapter path

Target: low hundreds of milliseconds where practical.

Examples:

- browser automation
- application-specific APIs
- UACC adapter workflows

## 12.4 L3 — perception path

Typically slower.

Examples:

- screenshot capture
- OCR
- vision model
- complex UI reconstruction

## 12.5 L4 — reasoning path

Potentially highest latency.

Used for:

- ambiguous intent
- long-horizon planning
- error recovery
- unfamiliar applications
- complex multi-step tasks

### Critical optimization

Never ask the LLM to perform an action that a deterministic local router can perform safely and correctly.

---

# 13. Hot Path Cache

AGY should maintain caches for:

- active window
- process-to-window mapping
- common application launchers
- recent UIA selectors
- known app adapters
- keyboard shortcuts
- current audio/display state
- previous successful action routes

Example:

```text
"open VS Code"

previous successful route:
App activation -> direct

Do not ask the model how to do it again.
```

---

# 14. UI Automation Strategy

Use Windows UI Automation as a semantic interaction layer.

A UIA element may expose:

- Name
- AutomationId
- ControlType
- bounding rectangle
- enabled state
- focus state
- control patterns
- hierarchy

Windows UI Automation supports element trees and control patterns such as Invoke for actionable controls. [Microsoft UI Automation Tree Overview](https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-treeoverview)

Execution example:

```text
find window
 -> find Button(Name="Send")
 -> validate enabled=true
 -> Invoke
 -> verify message state
```

Do not click by coordinates when a stable semantic control exists.

Microsoft's desktop automation tooling similarly emphasizes UI elements/selectors instead of image recognition or absolute coordinates for supported controls. [Microsoft Power Automate UI elements](https://learn.microsoft.com/en-us/power-automate/desktop-flows/ui-elements)

---

# 15. Computer-Use Fallback

When semantic control fails:

```text
capture screenshot
 -> detect relevant application/window
 -> identify target
 -> generate action
 -> execute input
 -> capture result
 -> verify
```

The vision system must know that visual confidence is not equivalent to action authorization.

For example:

```text
Vision: "This looks like the Delete button."
Policy: "Delete is R4."
Result: confirmation required.
```

Vision can locate an action; policy decides whether it may execute.

---

# 16. Voice Architecture

AGY should support:

```text
Microphone
 -> speech recognition
 -> intent normalization
 -> AGY command
```

Windows 11 Voice Access is itself capable of controlling apps, controls, mouse/keyboard and dictation locally, making it a useful compatibility/accessibility subsystem. [Microsoft Voice Access command list](https://support.microsoft.com/en-us/accessibility/windows/voice-access/voice-access-command-list)

AGY should prefer direct APIs over speaking commands into Voice Access because a synthetic voice -> speech recognition round trip adds latency and an unnecessary failure point.

Use Voice Access as:

- user-facing accessibility integration
- fallback interaction surface
- compatibility layer for unsupported UI
- optional voice-control bridge

Do not depend on it for the entire control architecture.

---

# 17. MCP Architecture

AGY should operate as an MCP host/client and expose or consume capability servers.

Suggested capability domains:

```text
windows
computer
filesystem
browser
terminal
process
media
display
clipboard
network
communications
developer
custom-app
```

MCP tools should contain metadata such as:

```yaml
name:
risk:
reversible:
requires_confirmation:
required_privilege:
latency_class:
input_schema:
output_schema:
verification_method:
side_effects:
```

The MCP layer is an extensibility bus; it must not bypass AGY's central policy engine.

---

# 18. UACC / Application Adapter Layer

Where a UACC implementation is available, AGY should treat it as an application-specific semantic adapter.

Example:

```text
AGY
 -> discover app adapter
 -> query application capabilities
 -> use native semantic actions
 -> verify result
```

Recommended adapter abstraction:

```typescript
interface AppAdapter {
  id: string;
  supports(app: AppIdentity): number;
  discover(): Promise<AppState>;
  actions(): Capability[];
  execute(action: Action): Promise<ActionResult>;
  verify(action: Action, result: ActionResult): Promise<Verification>;
}
```

If UACC is unavailable or cannot safely perform an operation, route to Windows UI Automation or another capability layer.

Do not hard-code assumptions about a specific UACC implementation into the core; keep it behind an adapter boundary.

---

# 19. Shell / CMD / PowerShell

Shell access is powerful and must be controlled.

### Preferred model

```text
capability command
   -> validated structured arguments
   -> generated shell only if necessary
   -> execution
   -> captured output
   -> verification
```

Do not allow the model to construct arbitrary shell commands without policy inspection.

Example:

```text
windows.process.stop(pid=8420)
```

is preferred over:

```text
powershell "Stop-Process -Id 8420 -Force"
```

The shell path remains available when Windows-native capabilities are insufficient.

---

# 20. Destructive Action Firewall

These operations require explicit just-in-time confirmation even if the user previously asked AGY to "do everything":

```text
PERMANENT_DELETE
RECYCLE_BIN_EMPTY
DISK_FORMAT
FACTORY_RESET
SYSTEM_SHUTDOWN
SYSTEM_RESTART
CRITICAL_PROCESS_TERMINATION
SECURITY_CONTROL_DISABLE
FIREWALL_DISABLE
CREDENTIAL_REVOCATION
SYSTEM_RESTORE_DESTRUCTIVE_CHANGE
MASS_FILE_DELETION
MASS_DATA_OVERWRITE
PRIVILEGE_ESCALATION
EXTERNAL_PUBLISH
EXTERNAL_SEND
FINANCIAL_TRANSACTION
IRREVERSIBLE_ACCOUNT_CHANGE
```

The confirmation must occur immediately before the side effect and must describe the real target.

---

# 21. Safe Defaults

When uncertainty exists:

```text
Prefer reversible over irreversible.
Prefer local over external.
Prefer draft over send.
Prefer copy over overwrite.
Prefer move to recycle bin over permanent deletion.
Prefer inspect over modify.
Prefer least privilege over elevation.
Prefer user confirmation over irreversible guessing.
```

---

# 22. Verification Engine

Verification should be action-specific.

Examples:

```text
open app
 -> process exists + window exists

close app
 -> target window/process no longer exists

volume +10
 -> query current volume

send message
 -> verify sent state / message presence

file rename
 -> old path absent + new path exists

delete
 -> exact target absent AND confirmation recorded

shutdown
 -> confirmation accepted + shutdown API accepted
```

Verification failures trigger recovery, not immediate success reporting.

---

# 23. Recovery Engine

AGY should classify failures:

```text
TARGET_NOT_FOUND
APP_NOT_READY
UI_CHANGED
PERMISSION_DENIED
PRIVILEGE_REQUIRED
TIMEOUT
NETWORK_FAILURE
TOOL_FAILURE
VERIFICATION_FAILURE
AMBIGUOUS_STATE
```

Recovery strategy:

```text
retry deterministic operation
 -> refresh state
 -> try alternate capability
 -> use UIA
 -> use keyboard shortcut
 -> use vision
 -> ask model for recovery plan
 -> ask user only when necessary
```

Do not repeat a failed action blindly.

---

# 24. Concurrency

AGY may perform independent safe tasks concurrently.

Example:

```text
"Open VS Code, set volume to 40%, and create a project folder."
```

Possible execution:

```text
Task A: open VS Code
Task B: set volume
Task C: create folder
```

But actions touching the same resource must be serialized.

Example:

```text
focus Chrome
click address bar
```

must preserve order.

---

# 25. Task Planning

Avoid huge plans when a short plan is sufficient.

Use progressive planning:

```text
Goal
 -> next best action
 -> observe
 -> next best action
```

For long tasks:

```text
Goal
 -> high-level phases
 -> execute one phase
 -> verify
 -> adapt remaining plan
```

The environment may change while AGY is working; plans must remain mutable.

---

# 26. Human-Like Interaction Model

AGY should behave like a competent human operator:

- understand context
- avoid unnecessary actions
- maintain focus
- use shortcuts
- inspect before changing unknown state
- verify important outcomes
- recover gracefully
- avoid repeating questions
- admit uncertainty
- explain only when necessary

AGY should be concise during normal execution.

Example:

```text
User: "Open Chrome and search for Qualcomm NPU benchmarks."

AGY:
"Opening Chrome and searching."

[execute]

AGY:
"Done."
```

For dangerous actions:

```text
AGY:
"This will permanently delete 28 files (3.1 GB). Proceed?"
```

---

# 27. Confidence Model

Separate three concepts:

```text
INTENT_CONFIDENCE
ACTION_CONFIDENCE
VERIFICATION_CONFIDENCE
```

Example:

```text
Intent = 0.99
Action target = 0.94
Verification = 0.99
```

A high intent score must not override low action confidence or a safety gate.

---

# 28. Observability and Audit

Record structured events:

```json
{
  "timestamp": "...",
  "task_id": "...",
  "action": "windows.volume.set",
  "risk": "low",
  "approval": "automatic",
  "executor": "windows-audio-api",
  "latency_ms": 3.7,
  "verification": "success"
}
```

For sensitive data:

- prefer hashes/metadata
- avoid logging raw secrets
- avoid unnecessary screenshots
- allow audit retention limits
- provide a clear local audit viewer

---

# 29. Security Boundaries

AGY should separate:

```text
USER SESSION
AGENT HOST
POLICY ENGINE
TOOL REGISTRY
EXECUTOR
ELEVATED EXECUTOR
NETWORK/MCP
```

An untrusted MCP server must not automatically gain the authority of AGY's local Windows executor.

MCP tools are treated as external capabilities and must pass AGY policy checks before use.

---

# 30. Secret Handling

Never expose to the model unless absolutely necessary:

- Windows passwords
- authentication tokens
- private keys
- browser cookies
- password-store contents
- credential-manager secrets
- session tokens

AGY should pass opaque handles where possible.

Example:

```text
credential.store("GitHub")
 -> credential_handle = cred_17
```

Instead of:

```text
password = "..."
```

---

# 31. Network Policy

Local operations should not require network access.

When a task needs the network:

```text
identify destination
 -> classify data sensitivity
 -> policy check
 -> execute
 -> verify
```

Do not allow hidden data exfiltration through arbitrary MCP servers or shell commands.

---

# 32. Application Discovery

On startup, AGY should discover:

```text
running processes
windows
installed applications
available MCP servers
known app adapters
UIA providers
audio devices
monitors
clipboard capabilities
network state
```

Do this incrementally and cache results.

Do not continuously scan the entire machine at high frequency.

---

# 33. Event-Driven State Updates

Prefer events over polling where Windows exposes suitable event mechanisms.

Examples:

```text
window created
window closed
foreground changed
process started
process exited
UI element changed
clipboard changed
media state changed
```

This reduces latency and CPU usage.

---

# 34. Deterministic Command Vocabulary

AGY should expose first-class capabilities including:

```text
APP
  open
  close
  focus
  minimize
  maximize
  switch

WINDOW
  list
  focus
  move
  resize
  close

INPUT
  click
  double_click
  right_click
  drag
  type
  keypress
  hotkey
  scroll

SCREEN
  screenshot
  region
  inspect

UI
  find
  read
  invoke
  select
  toggle
  expand
  collapse

AUDIO
  volume.set
  volume.increase
  volume.decrease
  mute
  unmute
  play
  pause
  next
  previous

DISPLAY
  brightness.set
  brightness.increase
  brightness.decrease
  display.switch

PROCESS
  list
  start
  stop
  restart

FILES
  list
  search
  read
  create
  copy
  move
  rename
  delete

SHELL
  cmd
  powershell

VOICE
  listen
  dictate
  accessibility_bridge

MCP
  discover
  connect
  invoke

APP_ADAPTER
  discover
  capabilities
  execute
```

Each command must map to a typed capability contract and policy metadata.

---

# 35. Example Execution Traces

## Safe action

```text
USER:
"Increase volume by 10%."

AGY:
intent = volume.increase(10)
policy = R1 / automatic
route = native-audio-api
execute = success
verify = volume == previous + 10
latency = 4 ms

AGY:
"Done."
```

## Dangerous action

```text
USER:
"Delete this folder."

AGY:
inspect target
calculate scope
policy = R4

AGY:
"This will permanently delete 2,143 files (8.7 GB). Continue?"

USER:
"Yes."

AGY:
re-check target
execute
verify
report
```

## Unclear action

```text
USER:
"Clean this folder."

AGY:
No destructive interpretation without scope.

AGY:
"I found 91 files. Do you want me to remove temporary files only, or delete everything?"
```

## UI automation

```text
USER:
"Click Send."

AGY:
UIA search
 -> Button(Name="Send")
 -> enabled = true
 -> policy for send = R3
 -> confirmation
 -> Invoke
 -> verify sent
```

---

# 36. Performance Rules

1. Keep the AGY host resident when possible.
2. Keep hot MCP connections alive.
3. Cache application identities.
4. Cache UIA selectors with invalidation.
5. Reuse process handles safely.
6. Avoid repeated screenshots.
7. Avoid LLM calls for deterministic commands.
8. Batch state reads when independent.
9. Prefer OS events to polling.
10. Measure actual latency in the audit stream.
11. Do not promise a fixed "few milliseconds" for operations that depend on app startup, UI rendering, network latency, vision inference, or LLM inference.

---

# 37. Reliability Rules

Before action:

```text
Is target known?
Is capability available?
Is authority sufficient?
Is risk acceptable?
```

After action:

```text
Did executor report success?
Did the environment change as expected?
Does verification agree?
```

If verification fails:

```text
do not claim success
```

---

# 38. "God Mode" Interpretation

AGY may be described as having broad capability, but its implementation must not interpret "god mode" as unrestricted authority.

The intended meaning is:

```text
maximum capability
+ minimum unnecessary friction
+ strong situational awareness
+ fast execution
+ intelligent recovery
+ explicit safety boundaries
```

The agent should be powerful enough to do almost anything the user legitimately wants on their own machine, without becoming a mechanism for accidental destruction or concealed misuse.

---

# 39. Recommended Project Structure

```text
agy/
├── core/
│   ├── orchestrator/
│   ├── planner/
│   ├── intent/
│   ├── world/
│   ├── memory/
│   └── verification/
│
├── policy/
│   ├── classifier/
│   ├── approval/
│   ├── rules/
│   └── audit/
│
├── windows/
│   ├── win32/
│   ├── uia/
│   ├── process/
│   ├── window/
│   ├── audio/
│   ├── display/
│   ├── input/
│   ├── clipboard/
│   └── shell/
│
├── adapters/
│   ├── uacc/
│   ├── browser/
│   ├── vscode/
│   └── custom/
│
├── mcp/
│   ├── host/
│   ├── client/
│   ├── registry/
│   └── servers/
│
├── perception/
│   ├── screenshot/
│   ├── ocr/
│   └── vision/
│
├── voice/
│   ├── stt/
│   ├── voice-access/
│   └── wakeword/
│
├── ui/
│   ├── approval/
│   ├── tray/
│   └── diagnostics/
│
└── cli/
    └── agy.exe
```

---

# 40. Agent Loop Reference Pseudocode

```python
async def run_task(user_input):
    intent = await resolve_intent(user_input)

    while not intent.complete:
        state = world.observe_minimal()

        action = planner.next_action(
            intent=intent,
            state=state,
            memory=memory.relevant()
        )

        risk = policy.classify(action, state, intent)

        if risk.decision == "DENY":
            return report_denied(action)

        if risk.decision == "REQUIRE_CONFIRMATION":
            approved = await approval.request(action)
            if not approved:
                return report_cancelled(action)

        route = router.select(
            action=action,
            state=state,
            preference="fastest_reliable"
        )

        result = await executor.run(route, action)
        verification = await verifier.check(action, result, world)

        if verification.success:
            world.update(verification.state)
            intent.advance(action, verification)
            continue

        recovery = recovery_engine.plan(
            action=action,
            result=result,
            verification=verification,
            state=world.state()
        )

        if recovery.requires_user:
            return ask_user(recovery.question)

        await recovery.execute()

    return report_success(intent)
```

---

# 41. Final Design Contract

AGY is successful when the following experience is true:

```text
User:
"Open VS Code, create a folder called NIDAR,
open it, create main.py, and start writing a
basic drone telemetry server."

AGY:

1. Understand objective.
2. Inspect VS Code state.
3. Launch/focus VS Code.
4. Use semantic UI/application APIs.
5. Create folder.
6. Open folder.
7. Create file.
8. Write code.
9. Verify file contents.
10. Report completion.
```

For a dangerous task:

```text
User:
"Shut down my laptop."

AGY:

Recognize intent.
Check current state.
Classify as R4 / irreversible session action.
Show exact confirmation.
Wait.
Re-check approval.
Execute.
Verify acceptance.
```

For an unknown application:

```text
UIA
 -> app adapter
 -> keyboard
 -> vision
 -> model-guided recovery
```

The user should not need to know which subsystem was used unless useful for diagnostics.

---

# 42. Definition of Done

AGY Desktop Agent v2 is considered architecturally complete when it provides:

- [x] local agent host
- [x] intent resolution
- [x] world-state model
- [x] policy engine
- [x] automatic approval for routine actions
- [x] explicit confirmation for destructive/high-impact actions
- [x] capability router
- [x] Windows-native action layer
- [x] UI Automation integration
- [x] shell fallback
- [x] computer-use fallback
- [x] voice/accessibility integration
- [x] MCP host/client integration
- [x] UACC/application adapter boundary
- [x] verification engine
- [x] recovery engine
- [x] latency instrumentation
- [x] audit logging
- [x] least-privilege operation
- [x] secret isolation
- [x] event-driven state updates
- [x] task/session-scoped approvals
- [x] clear success/failure semantics

---

# 43. One-Sentence Architecture

> **AGY is a local-first Windows agent that converts intent into verified capabilities through a policy-aware orchestrator, routing each action to the fastest reliable control surface—native Windows APIs, UI Automation, UACC/application adapters, MCP tools, shell, accessibility, or vision—while automatically approving low-risk reversible work and requiring just-in-time confirmation for destructive or consequential actions.**

