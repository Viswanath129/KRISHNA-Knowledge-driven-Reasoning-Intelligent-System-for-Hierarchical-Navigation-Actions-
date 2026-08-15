import argparse
import sys
import os
import json
import asyncio
import subprocess
import time
import pyautogui
import pygetwindow as gw
import win32gui
import win32con
import psutil
import wmi
import speech_recognition as sr
import win32com.client
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

# Disable PyAutoGUI fail-safe to prevent termination when mouse hits screen corners
pyautogui.FAILSAFE = False

# -----------------------------------------------------------------------------
# Helper: Focus Window
# -----------------------------------------------------------------------------
def focus_window(title):
    # Case-insensitive substring match
    windows = gw.getWindowsWithTitle(title)
    if not windows:
        # Search all titles for case-insensitive match
        all_titles = gw.getAllTitles()
        matching_titles = [t for t in all_titles if title.lower() in t.lower()]
        if matching_titles:
            windows = gw.getWindowsWithTitle(matching_titles[0])
            
    if windows:
        win = windows[0]
        try:
            hwnd = win._hWnd
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(hwnd)
            time.sleep(0.3)  # Wait for animation to finish
            return win
        except Exception as e:
            print(f"Warning: Could not focus window using win32 API: {e}")
            try:
                win.activate()
                time.sleep(0.3)
                return win
            except Exception:
                pass
    return None

# -----------------------------------------------------------------------------
# Helper: Capture Screenshot
# -----------------------------------------------------------------------------
def capture_screenshot(output_path=None, window_title=None):
    import mss
    import mss.tools
    
    if not output_path:
        output_path = "screenshot.png"
        
    dirname = os.path.dirname(os.path.abspath(output_path))
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)
        
    with mss.mss() as sct:
        if window_title:
            win = focus_window(window_title)
            if win:
                # bounding box: (left, top, right, bottom)
                width = win.right - win.left
                height = win.bottom - win.top
                monitor = {
                    "left": win.left,
                    "top": win.top,
                    "width": width,
                    "height": height
                }
                print(f"Capturing window '{win.title}' at region {monitor}...")
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=output_path)
            else:
                print(f"Window '{window_title}' not found. Capturing primary screen.")
                sct.shot(output=output_path)
        else:
            print("Capturing full screen...")
            sct.shot(output=output_path)
            
    print(f"Screenshot saved to: {output_path}")

# -----------------------------------------------------------------------------
# Helper: App Lifecycle
# -----------------------------------------------------------------------------
def subprocess_app_open(target, args=None):
    common_apps = {
        "chrome": "chrome.exe",
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "whatsapp": "whatsapp.exe",
        "explorer": "explorer.exe",
        "vscode": "code.cmd" if os.name == "nt" else "code"
    }
    cmd = common_apps.get(target.lower(), target)
    if args:
        cmd = f"{cmd} {args}"
    print(f"Opening app: {cmd}")
    subprocess.Popen(cmd, shell=True)

def subprocess_app_close(target, force=False):
    print(f"Closing app matching: {target}")
    # Try taskkill
    cmd = ["taskkill", "/IM", f"{target}.exe"]
    if force:
        cmd.append("/F")
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Substring process close via psutil
    for proc in psutil.process_iter(['name']):
        try:
            if target.lower() in proc.info['name'].lower():
                if force:
                    proc.kill()
                else:
                    proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

# -----------------------------------------------------------------------------
# Helper: Volume Control via PyCaw
# -----------------------------------------------------------------------------
def get_audio_volume():
    devices = AudioUtilities.GetSpeakers()
    return devices.EndpointVolume

def control_volume(action, val=None):
    try:
        volume = get_audio_volume()
        if action == "set":
            v = int(val)
            volume.SetMasterVolumeLevelScalar(v / 100.0, None)
            print(f"Volume set to {v}%")
        elif action == "inc":
            step = int(val) if val else 5
            curr = int(round(volume.GetMasterVolumeLevelScalar() * 100))
            new_v = min(100, curr + step)
            volume.SetMasterVolumeLevelScalar(new_v / 100.0, None)
            print(f"Volume increased to {new_v}%")
        elif action == "dec":
            step = int(val) if val else 5
            curr = int(round(volume.GetMasterVolumeLevelScalar() * 100))
            new_v = max(0, curr - step)
            volume.SetMasterVolumeLevelScalar(new_v / 100.0, None)
            print(f"Volume decreased to {new_v}%")
        elif action == "mute":
            volume.SetMute(True, None)
            print("Audio muted")
        elif action == "unmute":
            volume.SetMute(False, None)
            print("Audio unmuted")
    except Exception as e:
        print(f"Error controlling volume: {e}")

# -----------------------------------------------------------------------------
# Helper: Brightness Control via WMI
# -----------------------------------------------------------------------------
def control_brightness(action, val=None):
    try:
        c = wmi.WMI(namespace="wmi")
        methods = c.WmiMonitorBrightnessMethods()
        monitors = c.WmiMonitorBrightness()
        curr = 50
        if monitors:
            curr = monitors[0].CurrentBrightness
            
        if action == "set":
            v = int(val)
            for m in methods:
                m.WmiSetBrightness(v, 1)
            print(f"Brightness set to {v}%")
        elif action == "inc":
            step = int(val) if val else 10
            new_v = min(100, curr + step)
            for m in methods:
                m.WmiSetBrightness(new_v, 1)
            print(f"Brightness increased to {new_v}%")
        elif action == "dec":
            step = int(val) if val else 10
            new_v = max(0, curr - step)
            for m in methods:
                m.WmiSetBrightness(new_v, 1)
            print(f"Brightness decreased to {new_v}%")
    except Exception as e:
        print(f"Error controlling brightness: {e}")

# -----------------------------------------------------------------------------
# Helper: Media Control Keypresses
# -----------------------------------------------------------------------------
def control_media(action):
    key_map = {
        "play": "playpause",
        "pause": "playpause",
        "toggle": "playpause",
        "next": "nexttrack",
        "prev": "prevtrack"
    }
    key = key_map.get(action.lower())
    if key:
        pyautogui.press(key)
        print(f"Media command '{action}' executed.")
    else:
        print(f"Unknown media command: {action}")

# -----------------------------------------------------------------------------
# Helper: STT & TTS Voice Engine
# -----------------------------------------------------------------------------
def speak(text):
    try:
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        print(f"TTS: {text}")
        speaker.Speak(text)
    except Exception as e:
        print(f"TTS Error: {e}")

def listen_and_transcribe():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=1.0)
        print("Listening...")
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=8)
            text = r.recognize_google(audio)
            print(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            print("Listening timed out.")
            return None
        except Exception as e:
            print(f"STT Error: {e}")
            return None

def run_voice_listen(wake_word="agy"):
    speak(f"Voice engine active. Wake word is {wake_word}.")
    while True:
        text = listen_and_transcribe()
        if text:
            text_lower = text.lower().strip()
            if "exit" in text_lower or "quit" in text_lower:
                speak("Exiting voice engine.")
                break
            if wake_word.lower() in text_lower:
                cmd_text = text_lower.replace(wake_word.lower(), "", 1).strip()
                if cmd_text:
                    speak(f"Running command: {cmd_text}")
                    subprocess.run(["C:\\Users\\kasiv\\AppData\\Local\\agy\\bin\\agy_core.exe", "--print", cmd_text])

def run_voice_prompt():
    speak("I am listening. Tell me your prompt.")
    text = listen_and_transcribe()
    if text:
        speak(f"Processing command: {text}")
        res = subprocess.run(["C:\\Users\\kasiv\\AppData\\Local\\agy\\bin\\agy_core.exe", "--print", text], capture_output=True, text=True)
        if res.stdout:
            print(res.stdout)
        if res.stderr:
            print(res.stderr, file=sys.stderr)
        speak("Command complete.")
    else:
        speak("I didn't capture any speech.")

# -----------------------------------------------------------------------------
# MCP Client Config & Proxy Calling
# -----------------------------------------------------------------------------
def load_mcp_config():
    paths = [
        "agy.mcp.json",
        "C:\\Users\\kasiv\\agy.mcp.json",
        "C:\\Users\\kasiv\\AppData\\Local\\agy\\agy.mcp.json"
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config {p}: {e}")
    return None

async def call_mcp_proxy_tool(server_name, tool_name, tool_args):
    config = load_mcp_config()
    if not config or "mcpServers" not in config:
        return {"success": False, "message": "mcpServers config not found in agy.mcp.json"}
        
    server_conf = config["mcpServers"].get(server_name)
    if not server_conf:
        return {"success": False, "message": f"Server '{server_name}' not defined in config"}
        
    command = server_conf.get("command")
    args_list = server_conf.get("args", [])
    env = server_conf.get("env", {})
    
    full_env = os.environ.copy()
    for k, v in env.items():
        if v.startswith("${") and v.endswith("}"):
            env_var = v[2:-1]
            v = full_env.get(env_var, "")
        full_env[k] = v
        
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    server_params = StdioServerParameters(
        command=command,
        args=args_list,
        env=full_env
    )
    try:
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, tool_args)
                content_list = []
                for c in result.content:
                    if hasattr(c, "text"):
                        content_list.append({"type": "text", "text": c.text})
                    elif hasattr(c, "data"):
                        content_list.append({"type": "image", "data": c.data, "mimeType": c.mimeType})
                return {"success": not getattr(result, "isError", False), "content": content_list}
    except Exception as e:
        return {"success": False, "message": f"MCP communication error: {e}"}

# -----------------------------------------------------------------------------
# Execute Unified Tool Calls
# -----------------------------------------------------------------------------
async def execute_tool_call(tool_name, args):
    if tool_name == "gui_action":
        action = args.get("action")
        coord = args.get("coordinate", [])
        text = args.get("text", "")
        scroll_amt = args.get("scroll_amount", 0)
        
        if action == "click" and len(coord) >= 2:
            pyautogui.click(coord[0], coord[1], duration=0.1)
            return {"success": True, "message": f"Clicked at {coord}"}
        elif action == "move" and len(coord) >= 2:
            pyautogui.moveTo(coord[0], coord[1], duration=0.1)
            return {"success": True, "message": f"Moved to {coord}"}
        elif action == "drag" and len(coord) >= 2:
            pyautogui.dragTo(coord[0], coord[1], duration=0.5)
            return {"success": True, "message": f"Dragged to {coord}"}
        elif action == "type" and text:
            pyautogui.write(text, interval=0.02)
            return {"success": True, "message": f"Typed: {text}"}
        elif action == "keycombo" and text:
            keys = [k.strip() for k in text.split('+')]
            pyautogui.hotkey(*keys)
            return {"success": True, "message": f"Pressed keys: {text}"}
        elif action == "scroll" and scroll_amt:
            pyautogui.scroll(scroll_amt)
            return {"success": True, "message": f"Scrolled {scroll_amt}"}
        elif action == "screenshot":
            capture_screenshot(text or "screenshot.png")
            return {"success": True, "message": "Screenshot captured"}
        else:
            return {"success": False, "message": f"Unknown or invalid gui_action action: {action}"}
            
    elif tool_name == "system_control":
        domain = args.get("domain")
        action = args.get("action")
        target = args.get("target")
        val = args.get("value")
        
        if domain == "audio":
            control_volume(action, val)
            return {"success": True, "message": f"Audio volume {action} executed"}
        elif domain == "display":
            control_brightness(action, val)
            return {"success": True, "message": f"Display brightness {action} executed"}
        elif domain == "media":
            control_media(action)
            return {"success": True, "message": f"Media command {action} executed"}
        elif domain == "process":
            if action == "open":
                subprocess_app_open(target)
                return {"success": True, "message": f"Process opened: {target}"}
            elif action == "close":
                subprocess_app_close(target, force=True)
                return {"success": True, "message": f"Process terminated: {target}"}
            elif action == "focus":
                win = focus_window(target)
                return {"success": bool(win), "message": f"Focused window: {target}"}
        return {"success": False, "message": f"Unknown system_control settings: domain={domain}, action={action}"}
        
    elif tool_name == "mcp_proxy":
        server_name = args.get("server_name")
        tool_name = args.get("tool_name")
        tool_args = args.get("arguments", {})
        res = await call_mcp_proxy_tool(server_name, tool_name, tool_args)
        return res
        
    else:
        return {"success": False, "message": f"Unknown tool: {tool_name}"}

# -----------------------------------------------------------------------------
# Main Arguments Parser
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="AGY Universal Desktop Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Universal Desktop Agent subcommands")
    
    # gui subcommand
    gui_parser = subparsers.add_parser("gui", help="GUI automation primitives")
    gui_sub = gui_parser.add_subparsers(dest="gui_action")
    
    screenshot_parser = gui_sub.add_parser("screenshot", help="Capture screenshot")
    screenshot_parser.add_argument("--output", help="Path to save file")
    screenshot_parser.add_argument("--window", help="Title of target window to capture")
    
    move_parser = gui_sub.add_parser("move", help="Move mouse to coordinates")
    move_parser.add_argument("x", type=int)
    move_parser.add_argument("y", type=int)
    
    click_parser = gui_sub.add_parser("click", help="Click at mouse coordinates")
    click_parser.add_argument("x", type=int)
    click_parser.add_argument("y", type=int)
    click_parser.add_argument("--button", default="left", choices=["left", "right", "double"])
    
    drag_parser = gui_sub.add_parser("drag", help="Drag mouse from coordinates")
    drag_parser.add_argument("x1", type=int)
    drag_parser.add_argument("y1", type=int)
    drag_parser.add_argument("x2", type=int)
    drag_parser.add_argument("y2", type=int)
    
    scroll_parser = gui_sub.add_parser("scroll", help="Scroll")
    scroll_parser.add_argument("amount", type=int)
    scroll_parser.add_argument("--direction", default="down", choices=["up", "down"])
    
    type_parser = gui_sub.add_parser("type", help="Type text with human timing")
    type_parser.add_argument("text")
    type_parser.add_argument("--delay-ms", type=int, default=20)
    
    keycombo_parser = gui_sub.add_parser("keycombo", help="Perform key combinations")
    keycombo_parser.add_argument("combo")
    
    keypress_parser = gui_sub.add_parser("keypress", help="Simulate a keypress")
    keypress_parser.add_argument("key")
    
    # uacc subcommand
    uacc_parser = subparsers.add_parser("uacc", help="Hardware & low-level OS automation")
    uacc_sub = uacc_parser.add_subparsers(dest="uacc_action")
    
    app_parser = uacc_sub.add_parser("app", help="Process and Application Lifecycle")
    app_parser.add_argument("action", choices=["open", "close", "focus"])
    app_parser.add_argument("target")
    app_parser.add_argument("--args", help="CLI flags to pass to opened application")
    app_parser.add_argument("--force", action="store_true", help="Force terminate process")
    
    volume_parser = uacc_sub.add_parser("volume", help="System volume level controls")
    volume_parser.add_argument("action", choices=["set", "inc", "dec", "mute", "unmute"])
    volume_parser.add_argument("value", nargs="?", default=None)
    
    display_parser = uacc_sub.add_parser("display", help="System display controls")
    display_sub = display_parser.add_subparsers(dest="display_sub_action")
    brightness_parser = display_sub.add_parser("brightness", help="Display brightness level controls")
    brightness_parser.add_argument("brightness_action", choices=["set", "inc", "dec"])
    brightness_parser.add_argument("value", nargs="?", default=None)
    
    media_parser = uacc_sub.add_parser("media", help="System hardware media controls")
    media_parser.add_argument("action", choices=["play", "pause", "toggle", "next", "prev"])
    
    # voice subcommand
    voice_parser = subparsers.add_parser("voice", help="Multimodal voice engines")
    voice_sub = voice_parser.add_subparsers(dest="voice_action")
    
    listen_parser = voice_sub.add_parser("listen", help="Listen in background for wake word")
    listen_parser.add_argument("--wake-word", default="agy")
    listen_parser.add_argument("--stt", default="whisper-base")
    listen_parser.add_argument("--tts", default="kokoro")
    
    prompt_parser = voice_sub.add_parser("prompt", help="Single shot voice execution prompt")
    
    # execute subcommand (JSON entrypoint)
    execute_parser = subparsers.add_parser("execute", help="Execute tool from JSON schema mapping")
    execute_parser.add_argument("--json", required=True, help="Raw JSON payload mapping to tool schema")
    
    args = parser.parse_args()
    
    if args.command == "gui":
        if args.gui_action == "screenshot":
            capture_screenshot(args.output, args.window)
        elif args.gui_action == "move":
            pyautogui.moveTo(args.x, args.y, duration=0.1)
        elif args.gui_action == "click":
            clicks = 2 if args.button == "double" else 1
            btn = "left" if args.button == "double" else args.button
            pyautogui.click(args.x, args.y, button=btn, clicks=clicks, duration=0.1)
        elif args.gui_action == "drag":
            pyautogui.moveTo(args.x1, args.y1)
            pyautogui.dragTo(args.x2, args.y2, duration=0.5)
        elif args.gui_action == "scroll":
            amt = -args.amount if args.direction == "down" else args.amount
            pyautogui.scroll(amt)
        elif args.gui_action == "type":
            pyautogui.write(args.text, interval=args.delay_ms / 1000.0)
        elif args.gui_action == "keycombo":
            keys = [k.strip() for k in args.combo.split("+")]
            pyautogui.hotkey(*keys)
        elif args.gui_action == "keypress":
            pyautogui.press(args.key)
            
    elif args.command == "uacc":
        if args.uacc_action == "app":
            if args.action == "open":
                subprocess_app_open(args.target, args.args)
            elif args.action == "close":
                subprocess_app_close(args.target, args.force)
            elif args.action == "focus":
                win = focus_window(args.target)
                if win:
                    print(f"Focused window: {win.title}")
                else:
                    print(f"Window matching '{args.target}' not found.")
        elif args.uacc_action == "volume":
            control_volume(args.action, args.value)
        elif args.uacc_action == "display":
            if args.display_sub_action == "brightness":
                control_brightness(args.brightness_action, args.value)
        elif args.uacc_action == "media":
            control_media(args.action)
            
    elif args.command == "voice":
        if args.voice_action == "listen":
            run_voice_listen(args.wake_word)
        elif args.voice_action == "prompt":
            run_voice_prompt()
            
    elif args.command == "execute":
        try:
            payload = json.loads(args.json)
            tool_name = payload.get("name")
            tool_args = payload.get("parameters") or payload.get("arguments") or payload
            if not tool_name:
                if "coordinate" in tool_args or "scroll_amount" in tool_args or "action" in tool_args:
                    tool_name = "gui_action"
                elif "domain" in tool_args:
                    tool_name = "system_control"
                elif "server_name" in tool_args:
                    tool_name = "mcp_proxy"
                    
            loop = asyncio.get_event_loop()
            res = loop.run_until_complete(execute_tool_call(tool_name, tool_args))
            print(json.dumps(res, indent=2))
        except Exception as e:
            print(json.dumps({"success": False, "message": f"Execution error: {e}"}))

if __name__ == "__main__":
    main()
