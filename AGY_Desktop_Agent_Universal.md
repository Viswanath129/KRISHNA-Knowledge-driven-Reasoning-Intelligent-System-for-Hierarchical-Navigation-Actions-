# AGY Universal Desktop Agent (Autonomous OS & UI Automation Specification)

## 1. System Philosophy & High-Level Architecture

The **AGY Desktop Agent** is an autonomous, multimodal execution system designed to operate a computer exactly like a human operator—seeing the screen, interpreting visual layouts, dispatching keystrokes and mouse events, manipulating the operating system shell, and routing contextual queries through standard extension protocols.

```
                                 ┌──────────────────────────────┐
                                 │   Unified Interaction Core   │
                                 │  • CLI Prompt (`agy "..."`)  │
                                 │  • Voice Engine (VAD/Whisper)│
                                 └──────────────┬───────────────┘
                                                │
                                                ▼
                                 ┌──────────────────────────────┐
                                 │   AGY Perception & Planner   │
                                 │   • Vision-Language Router   │
                                 │   • Dynamic Coordinate Mapper│
                                 │   • Intent / Action Loop     │
                                 └──────┬───────┬────────┬──────┘
                                        │       │        │
                   ┌────────────────────┘       │        └────────────────────┐
                   ▼                            ▼                             ▼
       ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐
       │   Computer Use (GUI)   │  │    UACC OS Automation  │  │   MCP Extension Hub    │
       │ • Screen Capture / OCR │  │ • App Lifecycle/Process│  │ • Filesystem & Repos   │
       │ • Mouse / Click / Drag │  │ • Display / Brightness │  │ • Web Search / APIs    │
       │ • Virtual Keystrokes   │  │ • Audio / Master Volume│  │ • DBs, Slack, Notion   │
       └────────────────────────┘  └────────────────────────┘  └────────────────────────┘
```

---

## 2. Tri-Engine Execution Topology

The agent determines the optimal execution tier dynamically:

| Layer | Trigger Conditions | Core Mechanics | Latency |
| :--- | :--- | :--- | :--- |
| **Direct OS (UACC)** | System settings, process management, raw shell tasks, audio/display. | PowerShell, WMI, Win32 API, Bash, direct syscalls. | < 50ms |
| **External Hub (MCP)** | Data retrieval, repository analysis, web indexing, structured APIs. | JSON-RPC 2.0 via standard MCP servers. | 100ms - 500ms |
| **Human-in-the-Loop GUI** | Unscriptable desktop apps, complex web UIs, form filling, reading menus. | Screenshot capture, visual element grounding, mouse/keyboard simulation. | 400ms - 1.2s |

---

## 3. Computer Use & Visual Grounding Specification

When interacting with graphical desktop environments, the agent follows an iterative **Perception-Action-Verification (PAV)** loop.

### 3.1 PAV Control Loop
1. **Perception**: Capture normalized display buffer ($1920 	imes 1080$ or scaled down to $1280 	imes 720$).
2. **Grounding**: Predict bounding boxes or target $(x, y)$ coordinates for UI elements (buttons, inputs, menus).
3. **Execution**: Issue synthetic hardware events using direct OS API hooks.
4. **Verification**: Capture diff screenshot to ensure the UI state changed as expected.

### 3.2 Direct GUI Action Primitives (Win32 / PyAutoGUI / xdotool)
```bash
# Capture full display or specific window
agy gui screenshot [--output <path>] [--window <title>]

# Mouse controls
agy gui move <x> <y>
agy gui click <x> <y> [--button left|right|double]
agy gui drag <x1> <y1> <x2> <y2>
agy gui scroll <amount> [--direction up|down]

# Human-like typing & keyboard control
agy gui type "<text>" [--delay-ms 20]
agy gui keycombo "<ctrl+shift+p>"
agy gui keypress "<enter|tab|esc|backspace>"
```

---

## 4. Universal Access & Control Contract (UACC)

Low-level commands bypass visual rendering to execute instantly via native shell subsystems:

### 4.1 CLI Syntax Reference
```bash
# Process and Application Lifecycle
agy uacc app open <app_name> [--args <flags>]
agy uacc app close <app_name> [--force]
agy uacc app focus <window_title>

# System & Hardware Control
agy uacc volume set <0-100> | inc <step> | dec <step> | mute | unmute
agy uacc display brightness set <0-100> | inc <step> | dec <step>
agy uacc media play | pause | toggle | next | prev
```

### 4.2 PowerShell Engine Implementation
```powershell
# Fast volume step decrement
$obj = New-Object -ComObject WScript.Shell
$obj.SendKeys([char]174)

# Set monitor brightness directly via WMI
(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, 65)

# Fast Application Termination
Stop-Process -Name "discord" -Force -ErrorAction SilentlyContinue
```

---

## 5. Model Context Protocol (MCP) Integration

External tools and workspaces are configured via `agy.mcp.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "C:/Workspace"]
    },
    "browser-tools": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    },
    "web-search": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-brave-search"],
      "env": { "BRAVE_API_KEY": "${BRAVE_API_KEY}" }
    }
  }
}
```

---

## 6. Voice Engine & Real-Time Multimodal Streaming

```
[ Microphone ] ──> [ WebRTC / VAD ] ──> [ faster-whisper / Local STT ]
                                                     │
                                                     ▼
[ Audio Out ] <── [ Piper / Kokoro TTS ] <── [ AGY Agent Planner ]
```

### Voice CLI Control
```bash
# Start background voice listener with hotword trigger
agy voice listen --wake-word="agy" --stt=whisper-base --tts=kokoro

# Single-shot voice execution
agy voice prompt
```

---

## 7. Unified Agent Tool Schema (JSON Manifest)

```json
{
  "tools": [
    {
      "name": "gui_action",
      "description": "Executes physical mouse, keyboard, or screenshot actions on the desktop.",
      "parameters": {
        "type": "object",
        "properties": {
          "action": { "type": "string", "enum": ["click", "move", "drag", "type", "keycombo", "scroll", "screenshot"] },
          "coordinate": { "type": "array", "items": { "type": "integer" }, "description": "[x, y] coordinates" },
          "text": { "type": "string", "description": "Text to type or shortcut combo" },
          "scroll_amount": { "type": "integer" }
        },
        "required": ["action"]
      }
    },
    {
      "name": "system_control",
      "description": "Controls low-level OS settings (volume, brightness, power, media, app process).",
      "parameters": {
        "type": "object",
        "properties": {
          "domain": { "type": "string", "enum": ["audio", "display", "media", "process"] },
          "action": { "type": "string" },
          "target": { "type": "string" },
          "value": { "type": "integer" }
        },
        "required": ["domain", "action"]
      }
    },
    {
      "name": "mcp_proxy",
      "description": "Dispatches execution requests to connected MCP servers.",
      "parameters": {
        "type": "object",
        "properties": {
          "server_name": { "type": "string" },
          "tool_name": { "type": "string" },
          "arguments": { "type": "object" }
        },
        "required": ["server_name", "tool_name", "arguments"]
      }
    }
  ]
}
```

---

## 8. Multi-Step Execution Trace Example

**Goal**: *"Open WhatsApp, search for Alex, send him a screenshot of the bug report in VS Code, and mute my laptop."*

```
Plan & Execution Trace:
├─ [1. UACC]        --> Launch/Focus WhatsApp: `agy uacc app open whatsapp`
├─ [2. UACC]        --> Mute system audio: `agy uacc volume mute`
├─ [3. Vision/GUI]  --> Screen capture active display & locate search input box at (240, 115)
├─ [4. Vision/GUI]  --> `agy gui click 240 115` && `agy gui type "Alex"` && `agy gui keypress "enter"`
├─ [5. MCP Engine]  --> Read file context via MCP: `filesystem:read_file "./reports/bug.log"`
├─ [6. Vision/GUI]  --> `agy gui screenshot --window "VS Code" --output "./tmp/snippet.png"`
├─ [7. Vision/GUI]  --> Focus WhatsApp chat box at (600, 940) and paste clipboard / drop attachment
└─ [8. Feedback]    --> Speak TTS: "Bug report screenshot sent to Alex and laptop muted."
```
