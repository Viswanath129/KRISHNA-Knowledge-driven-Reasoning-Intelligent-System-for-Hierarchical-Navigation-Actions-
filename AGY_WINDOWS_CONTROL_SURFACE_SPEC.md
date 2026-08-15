# AGY Windows Control Surface Specification

## Purpose

This specification defines the Windows control layer for AGY Desktop Agent.

AGY SHALL NOT be designed as an LLM that blindly emits CMD or PowerShell. It SHALL operate as a multi-channel Windows control system that chooses the safest, fastest, and most reliable execution path for each intent.

Core principle:

```text
USER INTENT
   ↓
INTENT + RISK CLASSIFIER
   ↓
AGY CONTROL STRATEGY ENGINE
   ↓
FASTEST RELIABLE CONTROL SURFACE
   ↓
WINDOWS
   ↓
OBSERVATION
   ↓
VERIFICATION
   ↓
TASK COMPLETE / RECOVER
```

---

# 1. Control Surface Hierarchy

AGY SHALL expose these control channels:

1. Native Windows APIs
2. Windows UI Automation (UIA)
3. Keyboard shortcuts / hotkeys
4. Mouse and keyboard injection
5. PowerShell
6. CMD and native executables
7. Windows Voice Access / speech capabilities
8. MCP servers and external capability adapters
9. UACC/application-specific adapters
10. Vision-based computer use

The system SHALL choose channels dynamically rather than forcing every task through one mechanism.

---

# 2. Control Priority

Default strategy priority:

```text
P0  Native Windows API
P1  UI Automation
P2  Application-native API / adapter
P3  Deterministic keyboard shortcut
P4  Deterministic mouse/keyboard input
P5  PowerShell / native executable
P6  CMD
P7  UACC / external adapter where appropriate
P8  Voice Access compatibility path
P9  Vision-based computer use
```

Important:

- Lower numeric priority means preferred path.
- The priority MAY change when reliability, availability, permissions, latency, or application context changes.
- Vision SHALL normally be the fallback rather than the first choice for deterministic Windows controls.

---

# 3. Latency Model

AGY SHALL be optimized for a two-speed architecture.

## Fast path

Used for deterministic actions that do not require LLM reasoning.

Examples:

```text
volume +
volume -
lock
show desktop
open Run
switch window
focus existing process
minimize window
maximize window
clipboard read
known shortcut
known process action
known UIA action
```

Target:

```text
Agent routing: sub-millisecond to low-millisecond class
Local execution: low-millisecond class where Windows/application state permits
```

These are targets, not universal guarantees.

## Reasoning path

Used when intent, context, planning, ambiguity, or recovery requires an LLM.

```text
USER
 ↓
LLM interpretation
 ↓
structured action plan
 ↓
local deterministic execution
```

The LLM SHALL NOT be unnecessarily involved in repetitive micro-actions.

---

# 4. Windows Shortcut Engine

AGY SHALL maintain a structured shortcut registry rather than memorizing shortcuts in the prompt.

## Core Windows shortcuts

```text
Win + A            Quick Settings / system panel
Win + B            Focus notification area
Win + C            Copilot / supported Windows experience
Win + D            Show/hide desktop
Win + E            File Explorer
Win + F            Feedback Hub on supported configurations
Win + G            Game Bar
Win + H            Voice typing
Win + I            Settings
Win + K            Cast / wireless display connection
Win + L            Lock device
Win + N            Notifications / calendar
Win + P            Projection / display mode
Win + Q            Search on supported configurations
Win + R            Run
Win + S            Search
Win + U            Accessibility
Win + V            Clipboard history
Win + W            Widgets on supported configurations
Win + X            Quick Link / power user menu
Win + Z            Snap layouts
Win + Tab          Task View
Win + Space        Input language switch
Win + Shift + S    Screen snipping
Win + PrtScn       Full screen screenshot
Win + Ctrl + D     Create virtual desktop
Win + Ctrl + Left  Previous virtual desktop
Win + Ctrl + Right Next virtual desktop
Win + Ctrl + F4    Close current virtual desktop
Alt + Tab          Switch applications
Alt + F4           Close active window
Ctrl + Shift + Esc Task Manager
```

The exact availability of some Windows-key combinations can vary by Windows version/configuration.

## Shortcut abstraction

Every shortcut SHALL be represented as structured data:

```json
{
  "id": "windows.open_settings",
  "sequence": ["WIN", "I"],
  "risk": "safe",
  "latency_class": "ultra_fast",
  "reversible": true,
  "requires_focus": false,
  "verification": "window_detected"
}
```

## Application shortcut registry

AGY SHOULD support application-scoped shortcut profiles for:

```text
Browsers
VS Code
Visual Studio
Windows Terminal
File Explorer
Microsoft Office
PowerPoint
Word
Excel
Creative applications
Developer tools
Communication applications
```

Application shortcuts MUST NOT override global safety rules.

---

# 5. Native Windows API Surface

Whenever a supported Windows API can perform an operation deterministically, AGY SHOULD prefer it over simulated user input.

Capability families:

```text
Window management
Process management
Audio
Display
Power
Clipboard
Notifications
Input
Filesystem
Networking
Bluetooth
Devices
Sessions
Services
System information
Security state observation
```

Examples:

```text
system.volume.get
system.volume.set
system.mute
system.display.list
system.display.brightness.get
system.display.brightness.set
window.list
window.focus
window.minimize
window.maximize
window.restore
window.close
process.list
process.start
process.stop
clipboard.read
clipboard.write
system.lock
```

---

# 6. Windows UI Automation Layer

UI Automation SHALL be treated as a first-class semantic control surface.

AGY SHOULD inspect:

```text
Window
ControlType
Name
AutomationId
ClassName
BoundingRectangle
IsEnabled
IsOffscreen
Patterns
Children
Parents
Keyboard focus
```

Common UIA actions:

```text
Invoke
Toggle
Select
Expand
Collapse
SetValue
RangeValue
Scroll
Transform
Window actions
Text retrieval
Focus
```

Example:

```text
User: "Click Send"

AGY:
  locate focused application
  inspect UIA tree
  find ControlType=Button, Name=Send
  verify enabled=true
  invoke
  verify expected post-action state
```

AGY SHALL prefer semantic UIA selection over coordinate-based clicking when possible.

---

# 7. Computer Input Layer

For applications that do not expose adequate semantic controls, AGY SHALL support:

```text
mouse_move
left_click
right_click
middle_click
double_click
mouse_down
mouse_up
drag
scroll
horizontal_scroll
key_down
key_up
key_press
hotkey
type_text
paste_text
```

Input SHALL be scoped to the intended window where possible.

AGY SHALL avoid coordinate actions if a stable UIA element, application API, or shortcut is available.

---

# 8. PowerShell Layer

PowerShell SHALL be a high-capability system execution surface.

Use cases:

```text
Complex filesystem work
System configuration
Process automation
Service management
Device inspection
Network inspection
Registry operations where explicitly permitted
Scheduled tasks
Windows management interfaces
Scripted multi-step workflows
```

AGY SHOULD prefer typed native tools over generated shell text when an equivalent capability exists.

Example:

```text
Preferred:
process.stop(pid=4210)

Fallback:
powershell.execute("Stop-Process -Id 4210")
```

---

# 9. CMD / Native Executable Layer

CMD SHALL remain available for compatibility and direct Windows command execution.

Potential tools:

```text
cmd.execute
exe.execute
where
whoami
ipconfig
netstat
netsh
tasklist
taskkill
shutdown
schtasks
winget
start
```

Generated shell commands MUST pass the policy engine before execution.

---

# 10. Voice Access Layer

Voice Access SHALL be treated as a Windows-native compatibility and accessibility channel.

AGY SHOULD NOT route every action through speech synthesis and Voice Access because that adds unnecessary latency and an additional recognition layer.

Preferred:

```text
AGY voice input
 ↓
AGY intent understanding
 ↓
Native API / UIA / shortcut
```

Voice Access MAY be used when:

```text
Direct automation is unavailable
An accessibility workflow benefits from it
The user explicitly requests voice interaction
A supported application exposes only voice-compatible interaction
```

---

# 11. MCP Layer

MCP SHALL provide modular tool discovery and integration.

AGY SHALL place policy enforcement above MCP execution.

```text
AGY Host
   ↓
MCP Client
   ↓
MCP Server
   ↓
Capability Adapter
   ↓
Windows / Application
```

Example tools:

```text
windows.open_application
windows.close_application
windows.list_windows
windows.focus_window
windows.get_ui_tree
windows.get_active_window

computer.screenshot
computer.click
computer.type
computer.scroll
computer.hotkey

system.volume_get
system.volume_set
system.brightness_get
system.brightness_set

process.list
process.start
process.stop

filesystem.search
filesystem.read
filesystem.write
filesystem.move
filesystem.delete

shell.execute
```

MCP SHALL NOT be allowed to bypass AGY risk policy.

---

# 12. UACC / Application Adapter Layer

UACC SHALL be integrated as an optional application/control adapter boundary.

The adapter interface SHOULD expose:

```text
capabilities()
inspect()
act()
verify()
health()
```

Example:

```text
uacc.application.inspect("Chrome")
uacc.application.open("Chrome")
uacc.application.act(...)
uacc.application.verify(...)
```

AGY SHALL dynamically prefer a UACC adapter when it offers a more reliable deterministic action than generic computer use.

---

# 13. Vision / Computer-Use Layer

Vision SHALL be the universal fallback for visually rendered interfaces.

Flow:

```text
Screenshot
 ↓
Perception
 ↓
Target grounding
 ↓
Action
 ↓
New screenshot
 ↓
Verification
```

Vision actions SHALL include:

```text
click target
double click target
select region
drag target
scroll region
type into target
read visible content
identify UI state
```

AGY MUST NOT trust visual action completion without an observation/verification step when correctness matters.

---

# 14. Observation Bus

AGY SHALL maintain an event-driven observation system.

Sources:

```text
UIA tree changes
Window events
Process events
Filesystem events
Clipboard events
Power state
Display state
Audio state
Command output
Application adapters
Screenshots
```

AGY SHALL cache frequently used state to reduce repeated inspection latency.

Example world state:

```json
{
  "active_window": "Chrome",
  "windows": [],
  "processes": [],
  "audio": {
    "volume": 63,
    "muted": false
  },
  "display": {
    "brightness": 71
  }
}
```

---

# 15. Adaptive Control Strategy

For every intent AGY SHALL calculate:

```text
correctness
reliability
latency
risk
availability
required permissions
verification cost
```

Then choose the best path.

Example:

```text
Intent: "Increase volume"

Native audio API       ✓ preferred
Media-key shortcut     ✓ fallback
UIA                     unnecessary
PowerShell              unnecessary
Vision                  prohibited unless required
```

Example:

```text
Intent: "Click Send"

UIA button invocation  ✓ preferred
Keyboard shortcut       ✓ fallback
Mouse                    ✓ fallback
Vision                   ✓ final fallback
```

---

# 16. Risk Classification

Every tool and every action SHALL have a risk class.

## R0 — Safe / routine

Automatic execution.

Examples:

```text
open application
focus window
switch window
read public/local workspace content already authorized
volume change
brightness change
scroll
copy
paste
screenshot
play/pause
open settings
```

## R1 — Low impact / reversible

Automatic execution unless policy overrides.

Examples:

```text
rename file
move non-critical file
change application preference
change window layout
create ordinary file
```

## R2 — Moderate impact

Execute automatically only with clear scope; otherwise ask.

Examples:

```text
bulk rename
bulk move
modify many files
install ordinary user application
change persistent configuration
```

## R3 — High impact / potentially destructive

Explicit confirmation required immediately before execution.

Examples:

```text
delete files
empty recycle bin
stop important services
terminate critical applications
restart system
shutdown system
log out
change firewall rules
modify security settings
bulk overwrite
```

## R4 — Critical / security-sensitive

Require strong confirmation and, where appropriate, elevated authorization.

Examples:

```text
credential handling
security bypass
administrator-level changes
remote control configuration
sensitive data transmission
security software modification
credential-store access
mass deletion
irreversible disk operations
```

Actions that violate hard security policy SHALL be denied rather than confirmed.

---

# 17. Just-In-Time Verification Policy

AGY SHALL NOT ask the user to confirm every harmless action.

AGY SHALL ask only when the action crosses the configured risk threshold.

Correct:

```text
User: "Increase volume"
AGY: executes immediately.
```

Correct:

```text
User: "Delete report.pdf"
AGY:
"This will permanently delete report.pdf. Proceed?"
```

Correct:

```text
User: "Shutdown the laptop"
AGY:
"Shutdown will close active applications and end your current session. Shut down now?"
```

Confirmation MUST occur immediately before the sensitive action, not many steps earlier.

---

# 18. Confirmation Design

Confirmation messages SHALL be:

```text
Concise
Specific
Non-manipulative
Clear about consequence
Clear about target
```

Bad:

```text
Are you sure?
```

Good:

```text
This will permanently delete 14 files from C:\\Projects\\Temp.
Do you want me to proceed?
```

AGY SHALL never hide destructive consequences behind vague language.

---

# 19. Approval Scopes

The user MAY optionally grant scoped temporary approval.

Examples:

```text
Allow this action once
Allow this action for this task
Allow deletes inside this folder for this task
Allow non-administrator shell commands for this session
```

AGY SHALL NOT convert a narrow approval into unrestricted lifetime approval.

---

# 20. Hard Deny Rules

AGY SHALL refuse or block actions that violate configured security policy, even if the model requests them.

Examples MAY include:

```text
credential theft
secret exfiltration
security bypass
malware execution
unauthorized remote access
persistent covert surveillance
destructive actions without authorization
privilege escalation outside policy
```

The policy engine SHALL be independent from model-generated instructions.

---

# 21. Tool Contracts

Every tool SHALL declare metadata.

Example:

```json
{
  "name": "filesystem.delete",
  "risk": "R3",
  "reversible": false,
  "requires_confirmation": true,
  "requires_admin": false,
  "latency_class": "fast",
  "verification": "path_absent_or_recycle_bin_state"
}
```

The model SHALL receive structured tool schemas rather than a giant list of undocumented commands.

---

# 22. Verification Contract

Every action SHOULD define its success signal.

Examples:

```text
open_application
→ process exists + window exists

volume_set
→ observed volume == requested value

window_focus
→ foreground window == target

file_move
→ source absent + destination present

file_delete
→ deletion state confirmed

shutdown
→ user explicitly confirmed immediately before invocation
```

If verification fails:

```text
observe again
 ↓
retry with same strategy if safe
 ↓
try alternate strategy
 ↓
recover
 ↓
report honestly
```

AGY SHALL never claim success solely because a command returned exit code 0 when the real-world state contradicts it.

---

# 23. Fast-Path Execution

The following categories SHOULD bypass LLM reasoning after intent is resolved:

```text
Known shortcuts
Known volume actions
Known brightness actions
Window focus/minimize/maximize
Play/pause
Simple scrolling
Clipboard operations
Known process actions
Known app launch
Known UIA actions
```

Example:

```text
"volume up"
 ↓
intent cache
 ↓
audio tool
 ↓
execute
 ↓
verify
```

No second LLM call is required.

---

# 24. Batch Execution

AGY SHALL group compatible safe actions into a single execution transaction where possible.

Example:

```text
"Open VS Code, open my project, and maximize it."
```

Possible batch:

```text
launch VS Code
wait for process/window event
open project
maximize window
verify final state
```

AGY SHOULD avoid unnecessary model round-trips between deterministic steps.

---

# 25. Parallelism

Independent safe actions MAY run concurrently.

Example:

```text
Read file A ─┐
Read file B ─┼→ gather → reason
Read file C ─┘
```

Conflicting or state-sensitive actions MUST remain ordered.

Example:

```text
close window
→ verify closed
→ reopen
```

---

# 26. Recovery Engine

When a tool fails:

```text
FAIL
 ↓
Classify failure
 ↓
Was target missing?
Was permission denied?
Was app not ready?
Was window changed?
Was input blocked?
Was tool unavailable?
 ↓
Select alternate strategy
 ↓
Verify
```

AGY SHOULD automatically recover from transient failures without asking the user when the recovery is safe.

Example:

```text
UIA lookup failed
 ↓
refresh UI tree
 ↓
retry
 ↓
keyboard shortcut
 ↓
computer-use fallback
```

---

# 27. Action Idempotency

Tools SHOULD declare whether actions are idempotent.

Examples:

```text
set_volume(50)       → idempotent
set_brightness(70)   → idempotent
focus_window(X)      → mostly idempotent
press_key(Delete)    → NOT idempotent
click_button(Send)   → NOT idempotent
send_message         → NOT idempotent
shutdown             → NOT safely repeatable
```

AGY MUST be conservative when retrying non-idempotent actions.

---

# 28. Context-Aware Targeting

AGY SHALL resolve ambiguous targets from:

```text
active application
focused window
recent conversation context
visible UI
filesystem scope
user wording
current task state
```

Example:

```text
"Close it"
```

AGY should resolve "it" to the currently relevant window rather than guessing globally.

If ambiguity can materially change the result, AGY SHALL ask.

---

# 29. Shell Safety

Shell commands SHALL be parsed and classified before execution.

The policy engine SHOULD inspect for:

```text
recursive deletion
disk formatting
system shutdown
credential access
security configuration changes
privilege escalation
network exfiltration
persistence mechanisms
mass file modification
```

Examples:

```text
Get-Process
→ R0

Get-ChildItem
→ R0/R1 depending on scope

Remove-Item -Recurse
→ R3

Format-Volume
→ R4

Shutdown /s
→ R3
```

The LLM SHALL NOT be able to bypass this by changing command wording.

---

# 30. Security Boundary

AGY SHALL follow least privilege.

Default:

```text
No administrator privilege
No unrestricted credentials
No unrestricted filesystem
No unrestricted network access
No hidden persistence
```

Elevation SHALL be explicit and task-scoped.

Sensitive capabilities SHOULD run through isolated helpers or sandboxes where practical.

---

# 31. Audit Log

Every meaningful action SHALL produce structured telemetry.

Example:

```json
{
  "timestamp": "2026-08-15T22:00:00+05:30",
  "task_id": "task_123",
  "intent": "increase volume",
  "tool": "system.volume.set",
  "strategy": "native_api",
  "risk": "R0",
  "approval": "auto",
  "result": "success",
  "latency_ms": 3.4
}
```

Sensitive values SHALL NOT be written into logs.

---

# 32. Capability Discovery

At startup AGY SHALL discover:

```text
Windows version
Available native APIs
Available UIA providers
Connected MCP servers
Available UACC/application adapters
Shell availability
Voice Access availability
Vision capability
Audio devices
Display devices
Permissions
```

The resulting capability matrix SHALL be cached.

---

# 33. Capability Matrix

Example:

| Capability | API | UIA | Shortcut | Shell | Input | Vision | Risk |
|---|---:|---:|---:|---:|---:|---:|---|
| Open app | Yes | Sometimes | Yes | Yes | Yes | Yes | R0 |
| Close window | Yes | Yes | Yes | Yes | Yes | Yes | R0/R1 |
| Volume | Yes | Sometimes | Yes | Yes | Yes | No | R0 |
| Brightness | Often | Sometimes | Device-specific | Sometimes | Yes | No | R0 |
| Clipboard | Yes | Sometimes | Yes | Yes | Yes | No | R0 |
| Screenshot | Yes | No | Yes | Yes | No | No | R0 |
| Click UI | Sometimes | Yes | Sometimes | No | Yes | Yes | R0/R1 |
| Read UI text | Sometimes | Yes | No | Sometimes | No | Yes | R0 |
| Delete file | Yes | Sometimes | No | Yes | Yes | No | R3 |
| Shutdown | Yes | No | Yes | Yes | Yes | No | R3 |
| Registry change | Yes | No | No | Yes | No | No | R3/R4 |
| Security change | Yes | Sometimes | No | Yes | No | No | R4 |

This matrix SHALL be dynamic rather than treated as a permanent static truth.

---

# 34. Example End-to-End Workflows

## Safe action

```text
User: "Turn volume up"

Intent
 ↓
R0 classification
 ↓
Native audio capability
 ↓
Execute
 ↓
Verify volume increased
 ↓
Done
```

## Shortcut action

```text
User: "Open settings"

Intent
 ↓
Known deterministic shortcut
 ↓
Win + I
 ↓
Verify Settings window
 ↓
Done
```

## UIA action

```text
User: "Click Send"

Inspect active window
 ↓
UIA locate Send button
 ↓
Invoke
 ↓
Verify message state
 ↓
Done
```

## Destructive action

```text
User: "Delete this folder"
 ↓
Resolve exact path
 ↓
Calculate scope
 ↓
R3
 ↓
Ask immediately before deletion
 ↓
User confirms
 ↓
Delete
 ↓
Verify
 ↓
Report result
```

## Dangerous system action

```text
User: "Shutdown"
 ↓
Resolve shutdown intent
 ↓
R3
 ↓
Ask:
"Shutdown will close active applications and end your session. Shut down now?"
 ↓
Confirm
 ↓
Execute
```

---

# 35. Humble Failure Behavior

AGY SHALL never pretend.

If an action failed:

```text
"I couldn't complete that because Chrome is not responding."
```

Not:

```text
"Done."
```

If confidence is low:

```text
"I found two folders named Reports. Which one do you mean?"
```

AGY SHOULD prefer a precise question over a dangerous guess.

---

# 36. Human-Like Task Loop

AGY SHALL behave like a highly capable computer operator:

```text
SEE
 ↓
UNDERSTAND
 ↓
PLAN
 ↓
ACT
 ↓
OBSERVE
 ↓
VERIFY
 ↓
ADAPT
 ↓
COMPLETE
```

But unlike a human, AGY SHOULD exploit deterministic system interfaces whenever available to improve speed, repeatability, and accuracy.

---

# 37. Golden Rule

AGY SHALL follow this decision tree for every action:

```text
Can the intent be resolved safely?
        │
      NO ──────→ ASK
        │
       YES
        ↓
Is there a native deterministic control?
        │
      YES ─────→ USE IT
        │
       NO
        ↓
Is there a stable UIA/application adapter?
        │
      YES ─────→ USE IT
        │
       NO
        ↓
Is there a deterministic shortcut/input path?
        │
      YES ─────→ USE IT
        │
       NO
        ↓
Can PowerShell/CMD safely perform it?
        │
      YES ─────→ POLICY CHECK → EXECUTE
        │
       NO
        ↓
Can UACC/MCP provide a reliable capability?
        │
      YES ─────→ POLICY CHECK → EXECUTE
        │
       NO
        ↓
Use computer vision / computer-use fallback
        │
        ↓
VERIFY
```

---

# 38. Final Architecture

```text
                         USER
                          │
                   TEXT / VOICE
                          │
                          ▼
                   ┌─────────────┐
                   │   AGY LLM   │
                   │ reasoning   │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
                   │ ORCHESTRATOR│
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │ POLICY/RISK │
                   └──────┬──────┘
                          │
                   ┌──────▼──────┐
                   │STRATEGY ENG.│
                   └──────┬──────┘
                          │
       ┌──────────────────┼───────────────────┐
       │                  │                   │
       ▼                  ▼                   ▼
 Native API             UIA           Application/UACC
       │                  │                   │
       └──────────────────┼───────────────────┘
                          │
               ┌──────────▼──────────┐
               │ Shortcuts / Input   │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │ PowerShell / CMD   │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │ MCP Capability Bus  │
               └──────────┬──────────┘
                          │
               ┌──────────▼──────────┐
               │ Computer Use/Vision │
               └──────────┬──────────┘
                          │
                          ▼
                       WINDOWS
                          │
                          ▼
                     OBSERVATION
                          │
                          └──────────────→ AGY
```

---

# 39. Non-Negotiable Requirements

AGY MUST:

- Prefer deterministic local execution over unnecessary LLM inference.
- Prefer native Windows capabilities over fragile screen coordinates.
- Use UIA as a primary semantic GUI control layer.
- Support Windows shortcuts as first-class tools.
- Support PowerShell and CMD as controlled execution surfaces.
- Support MCP as an extensibility protocol.
- Support UACC/application adapters through a stable interface.
- Use vision as a fallback for opaque interfaces.
- Verify important actions using observed system state.
- Ask for confirmation immediately before dangerous irreversible actions.
- Never silently convert a dangerous action into an approved action.
- Never claim success without evidence.
- Never use model-generated text to bypass policy controls.
- Apply least privilege and scoped authorization.
- Maintain auditable structured execution events.
- Recover automatically from safe transient failures.
- Ask the user only when ambiguity or risk materially requires it.

# 40. Design Objective

AGY should feel like:

```text
Fast like a command line.

Precise like a native Windows API.

Aware like a UI automation system.

Flexible like a computer-use agent.

Extensible like MCP.

Accessible like Voice Access.

Adaptive like an autonomous agent.

Careful like a security-conscious operator.
```

The goal is not unrestricted execution.

The goal is **maximum useful control with minimum unnecessary friction and strong protection at the exact moments where mistakes become costly.**
