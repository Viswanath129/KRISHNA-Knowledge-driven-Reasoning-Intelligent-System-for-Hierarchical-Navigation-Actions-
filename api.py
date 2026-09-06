import asyncio
import json
import os
import subprocess
import time
import glob
import platform
import webbrowser
import datetime
import math
import shutil
import zipfile
import pyautogui
pass # import pygetwindow as gw
pass # import win32gui
pass # import win32con
import psutil
pass # import wmi
import mss
import mss.tools
pass # from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import inspect
import sys

# Auto-install and import websockets for Gemini Live API WS connection
try:
    import websockets
except ImportError:
    print("Installing missing 'websockets' library...")
    subprocess.run([sys.executable, "-m", "pip", "install", "websockets"], check=True)
    import websockets

from src.krishna_agent.state import StateManager
from src.krishna_agent.intelligence import IntelligenceInterface
from src.krishna_agent.reasoning import ReasoningModule
from src.krishna_agent.navigator import Navigator
from src.krishna_agent.actuator import Actuator
from src.krishna_agent.handler import HandlerUnit
from src.krishna_agent.kernel import Kernel
from src.krishna_agent.ethics_engine import EthicsEngine

class AgentContainer:
    def __init__(self):
        self.kernel = None
        self.ethics_engine = None
        self.god_mode = True
        self.power_level = 0
        self.streak = 0
        self.max_streak = 0
        self.total_tasks_done = 0
        self.uptime_start = time.time()
        self.reaction_queue = asyncio.Queue()

    def record_task_done(self, name, tool):
        self.total_tasks_done += 1
        self.streak += 1
        if self.streak > self.max_streak:
            self.max_streak = self.streak
        points = 15
        if self.streak >= 3: points += 5
        if self.streak >= 5: points += 10
        if self.streak >= 8: points += 15
        self.power_level += points
        
        reaction_type = "NORMAL"
        if self.streak >= 15: reaction_type = "LEGENDARY"
        elif self.streak >= 12: reaction_type = "GODLIKE"
        elif self.streak >= 8: reaction_type = "UNSTOPPABLE"
        elif self.streak >= 5: reaction_type = "ON_FIRE"
        elif self.streak >= 3: reaction_type = "COMBO"
        
        self.reaction_queue.put_nowait({
            "type": reaction_type,
            "message": f"Task Completed! Streak: {self.streak}",
            "power": self.power_level,
            "streak": self.streak,
            "task_name": name,
            "tool": tool
        })

    def record_task_failed(self):
        self.streak = 0
        self.reaction_queue.put_nowait({
            "type": "FAILED",
            "message": "Task Failed!",
            "power": self.power_level,
            "streak": 0
        })

    def record_task_blocked(self):
        self.streak = 0
        self.reaction_queue.put_nowait({
            "type": "BLOCKED",
            "message": "Action Blocked by Ethics Engine!",
            "power": self.power_level,
            "streak": 0
        })

    def get_god_stats(self):
        return {
            "god_mode": self.god_mode,
            "power_level": self.power_level,
            "streak": self.streak,
            "max_streak": self.max_streak,
            "total_tasks_done": self.total_tasks_done,
            "uptime_seconds": int(time.time() - self.uptime_start)
        }

agent_container = AgentContainer()

log_queue = asyncio.Queue()
log_subscribers = []  # list of asyncio.Queue — one per SSE client

def broadcast_log(message: str):
    print(message)
    dead = []
    for q in log_subscribers:
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        log_subscribers.remove(q)


# =============================================================
#  30+ TOOLS — The KRISHNA Power Arsenal
# =============================================================

# ---- APP & URL ----
def tool_open_application(**kwargs):
    app_name = kwargs.get('application') or kwargs.get('app') or kwargs.get('name') or kwargs.get('app_name') or ''
    if not app_name: return "Error: Missing 'application'."
    app_map = {
        "camera": "microsoft.windows.camera:", "webcam": "microsoft.windows.camera:",
        "windows camera": "microsoft.windows.camera:",
        "notepad": "notepad.exe", "calculator": "calc.exe", "calc": "calc.exe",
        "paint": "mspaint.exe", "chrome": "chrome.exe", "google chrome": "chrome.exe",
        "firefox": "firefox.exe", "edge": "msedge.exe", "microsoft edge": "msedge.exe",
        "explorer": "explorer.exe", "file explorer": "explorer.exe",
        "cmd": "cmd.exe", "command prompt": "cmd.exe",
        "powershell": "powershell.exe", "terminal": "wt.exe",
        "task manager": "taskmgr.exe", "settings": "ms-settings:",
        "control panel": "control.exe", "snipping tool": "SnippingTool.exe",
        "wordpad": "wordpad.exe", "vscode": "code", "vs code": "code",
        "spotify": "spotify:", "word": "winword.exe", "excel": "excel.exe",
        "powerpoint": "powerpnt.exe", "outlook": "outlook.exe",
        "teams": "ms-teams.exe", "discord": "discord.exe",
        "vlc": "vlc.exe", "obs": "obs64.exe", "obs studio": "obs64.exe",
        "steam": "steam.exe", "epic games": "EpicGamesLauncher.exe",
        "whatsapp": "whatsapp:", "telegram": "telegram.exe",
        "zoom": "zoom.exe", "skype": "skype:", "brave": "brave.exe",
        "photos": "ms-photos:", "clock": "ms-clock:", "alarms": "ms-clock:",
        "maps": "bingmaps:", "weather": "bingweather:", "store": "ms-windows-store:",
        "microsoft store": "ms-windows-store:", "mail": "outlookmail:",
        "calendar": "outlookcal:", "xbox": "xbox:",
        "music": "mswindowsmusic:", "groove": "mswindowsmusic:",
        "media player": "mswindowsmusic:", "onedrive": "onedrive.exe",
        "recycle bin": "explorer.exe shell:RecycleBinFolder",
    }
    exe = app_map.get(app_name.lower(), app_name)
    try:
        if exe.endswith(":"):
            os.startfile(exe)
        elif " " in exe and exe.startswith("explorer.exe"):
            # Special cases like "explorer.exe shell:RecycleBinFolder"
            subprocess.Popen(exe, shell=True)
        else:
            # Check if exe exists on PATH first
            found = shutil.which(exe)
            if found:
                subprocess.Popen([found], creationflags=0x08000000)
            else:
                # Not on PATH — use Windows Search approach (like Win+S)
                # Try Start-Process which can find Store apps and registered apps
                subprocess.Popen(
                    ["powershell", "-WindowStyle", "Hidden", "-Command",
                     f"Start-Process '{exe}' -ErrorAction Stop"],
                    creationflags=0x08000000
                )
        return f"Success: Opened '{app_name}'"
    except Exception as e: return f"Error: {e}"


def tool_open_url(**kwargs):
    url = kwargs.get('url') or kwargs.get('link') or kwargs.get('website') or ''
    if not url: return "Error: Missing 'url'."
    if not url.startswith(('http://', 'https://')): url = 'https://' + url
    try:
        webbrowser.open(url)
        return f"Success: Opened '{url}'"
    except Exception as e: return f"Error: {e}"


def tool_open_file_with(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('file') or kwargs.get('path') or ''
    if not filepath: return "Error: Missing 'filepath'."
    try:
        os.startfile(filepath)
        return f"Success: Opened '{filepath}' with default application"
    except Exception as e: return f"Error: {e}"


# ---- FILE OPS ----
def tool_list_files(**kwargs):
    directory = kwargs.get('directory') or kwargs.get('path') or kwargs.get('folder') or os.getcwd()
    try:
        items = os.listdir(directory)
        result = f"📁 Contents of '{directory}' ({len(items)} items):\n"
        for item in sorted(items):
            full = os.path.join(directory, item)
            if os.path.isdir(full): result += f"  📁 {item}/\n"
            else:
                sz = os.path.getsize(full)
                result += f"  📄 {item} ({sz:,} bytes)\n"
        return result
    except Exception as e: return f"Error: {e}"


def tool_read_file(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('file') or kwargs.get('path') or ''
    if not filepath: return "Error: Missing 'filepath'."
    try:
        with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
        return content[:5000] if len(content) > 5000 else content
    except Exception as e: return f"Error: {e}"


def tool_write_file(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('file') or kwargs.get('path') or ''
    content = kwargs.get('content') or kwargs.get('text') or kwargs.get('data') or ''
    if not filepath: return "Error: Missing 'filepath'."
    try:
        d = os.path.dirname(filepath)
        if d: os.makedirs(d, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
        return f"Success: Wrote {len(content)} chars to '{filepath}'"
    except Exception as e: return f"Error: {e}"


def tool_write_and_open(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('file') or kwargs.get('path') or ''
    content = kwargs.get('content') or kwargs.get('text') or kwargs.get('data') or ''
    if not filepath or not content: return "Error: Missing 'filepath' or 'content'."
    try:
        d = os.path.dirname(filepath)
        if d: os.makedirs(d, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f: f.write(content)
        subprocess.Popen(["notepad.exe", os.path.abspath(filepath)])
        return f"Success: Wrote {len(content)} chars to '{filepath}' and opened in Notepad"
    except Exception as e: return f"Error: {e}"


def tool_rename_file(**kwargs):
    src = kwargs.get('source') or kwargs.get('from') or kwargs.get('old') or kwargs.get('file') or ''
    dst = kwargs.get('destination') or kwargs.get('to') or kwargs.get('new') or kwargs.get('name') or ''
    if not src or not dst: return "Error: Missing 'source' or 'destination'."
    try:
        os.rename(src, dst)
        return f"Success: Renamed '{src}' → '{dst}'"
    except Exception as e: return f"Error: {e}"


def tool_copy_file(**kwargs):
    src = kwargs.get('source') or kwargs.get('from') or kwargs.get('file') or ''
    dst = kwargs.get('destination') or kwargs.get('to') or ''
    if not src or not dst: return "Error: Missing 'source' or 'destination'."
    try:
        shutil.copy2(src, dst)
        return f"Success: Copied '{src}' → '{dst}'"
    except Exception as e: return f"Error: {e}"


def tool_move_file(**kwargs):
    src = kwargs.get('source') or kwargs.get('from') or kwargs.get('file') or ''
    dst = kwargs.get('destination') or kwargs.get('to') or ''
    if not src or not dst: return "Error: Missing 'source' or 'destination'."
    try:
        shutil.move(src, dst)
        return f"Success: Moved '{src}' → '{dst}'"
    except Exception as e: return f"Error: {e}"


def tool_delete_file(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('file') or kwargs.get('path') or ''
    if not filepath: return "Error: Missing 'filepath'."
    try:
        if os.path.isdir(filepath): shutil.rmtree(filepath)
        else: os.remove(filepath)
        return f"Success: Deleted '{filepath}'"
    except Exception as e: return f"Error: {e}"


def tool_search_files(**kwargs):
    pattern = kwargs.get('pattern') or kwargs.get('name') or kwargs.get('query') or ''
    directory = kwargs.get('directory') or kwargs.get('path') or os.getcwd()
    if not pattern: return "Error: Missing 'pattern'."
    try:
        matches = glob.glob(os.path.join(directory, "**", f"*{pattern}*"), recursive=True)[:25]
        if matches: return f"Found {len(matches)} matches:\n" + "\n".join(f"  → {m}" for m in matches)
        return f"No files matching '{pattern}'."
    except Exception as e: return f"Error: {e}"


def tool_create_folder(**kwargs):
    path = kwargs.get('path') or kwargs.get('folder') or kwargs.get('directory') or kwargs.get('name') or ''
    if not path: return "Error: Missing 'path'."
    try:
        os.makedirs(path, exist_ok=True)
        return f"Success: Created folder '{path}'"
    except Exception as e: return f"Error: {e}"


def tool_zip_files(**kwargs):
    source = kwargs.get('source') or kwargs.get('folder') or kwargs.get('file') or ''
    output = kwargs.get('output') or kwargs.get('zipfile') or (source + '.zip')
    if not source: return "Error: Missing 'source'."
    try:
        with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zf:
            if os.path.isdir(source):
                for root, dirs, files in os.walk(source):
                    for f in files:
                        fp = os.path.join(root, f)
                        zf.write(fp, os.path.relpath(fp, source))
            else:
                zf.write(source, os.path.basename(source))
        return f"Success: Zipped '{source}' → '{output}'"
    except Exception as e: return f"Error: {e}"


def tool_unzip_files(**kwargs):
    source = kwargs.get('source') or kwargs.get('zipfile') or kwargs.get('file') or ''
    destination = kwargs.get('destination') or kwargs.get('to') or '.'
    if not source: return "Error: Missing 'source' zip file."
    try:
        with zipfile.ZipFile(source, 'r') as zf:
            zf.extractall(destination)
        return f"Success: Extracted '{source}' → '{destination}'"
    except Exception as e: return f"Error: {e}"


# ---- SYSTEM ----
def tool_get_system_info(**kwargs):
    try:
        total, used, free = shutil.disk_usage("C:\\")
        return (f"System Info:\n  OS: {platform.system()} {platform.release()}\n"
                f"  Machine: {platform.machine()}\n  Processor: {platform.processor()}\n"
                f"  Node: {platform.node()}\n  Python: {platform.python_version()}\n"
                f"  Disk C: {total//(1024**3)}GB total, {used//(1024**3)}GB used, {free//(1024**3)}GB free")
    except Exception as e: return f"Error: {e}"


def tool_get_current_time(**kwargs):
    now = datetime.datetime.now()
    return f"📅 {now.strftime('%A, %B %d, %Y at %I:%M:%S %p')}"


def tool_execute_command(**kwargs):
    command = kwargs.get('command') or kwargs.get('cmd') or ''
    if not command: return "Error: Missing 'command'."
    try:
        r = subprocess.run(["powershell", "-Command", command], capture_output=True, text=True, timeout=30)
        out = (r.stdout + r.stderr).strip()
        return out if out else "Command executed successfully."
    except subprocess.TimeoutExpired: return "Error: Command timed out."
    except Exception as e: return f"Error: {e}"


def tool_kill_process(**kwargs):
    process_name = kwargs.get('process') or kwargs.get('name') or kwargs.get('app') or kwargs.get('process_name') or ''
    if not process_name: return "Error: Missing 'process'."
    try:
        target = process_name
        if target.lower().endswith('.exe'):
            target = target[:-4]
            
        killed = False
        for proc in psutil.process_iter(['name']):
            try:
                if target.lower() in proc.info['name'].lower():
                    proc.kill()
                    killed = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        if process_name.lower().endswith('.exe'):
            exe_name = process_name
        else:
            exe_name = process_name + '.exe'
        subprocess.run(["taskkill", "/F", "/IM", exe_name], capture_output=True)
        
        return f"Success: Killed process matching '{process_name}'"
    except Exception as e: return f"Error: {e}"


def tool_list_processes(**kwargs):
    try:
        r = subprocess.run(["powershell", "-Command",
            "Get-Process | Sort-Object CPU -Descending | Select-Object -First 15 Name,Id,CPU,WorkingSet | Format-Table -AutoSize"],
            capture_output=True, text=True, timeout=10)
        return f"Top 15 Processes:\n{r.stdout}"
    except Exception as e: return f"Error: {e}"


def tool_screenshot(**kwargs):
    filepath = kwargs.get('filepath') or kwargs.get('path') or kwargs.get('file') or 'screenshot.png'
    mode = kwargs.get('mode') or 'full'
    if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
        filepath = filepath + '.png'
        
    dirname = os.path.dirname(os.path.abspath(filepath))
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)
        
    try:
        with mss.mss() as sct:
            if mode == 'window':
                win = gw.getActiveWindow()
                if win:
                    width = win.right - win.left
                    height = win.bottom - win.top
                    monitor = {
                        "left": win.left,
                        "top": win.top,
                        "width": width,
                        "height": height
                    }
                    sct_img = sct.grab(monitor)
                    mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
                else:
                    sct.shot(output=filepath)
            elif mode == 'custom':
                x = int(kwargs.get('x', 0))
                y = int(kwargs.get('y', 0))
                w = int(kwargs.get('width', 800))
                h = int(kwargs.get('height', 600))
                monitor = {"left": x, "top": y, "width": w, "height": h}
                sct_img = sct.grab(monitor)
                mss.tools.to_png(sct_img.rgb, sct_img.size, output=filepath)
            else:
                sct.shot(output=filepath)
        return f"Success: Screenshot ({mode}) saved to '{os.path.abspath(filepath)}'"
    except Exception as e:
        return f"Error: {e}"


def tool_clipboard_copy(**kwargs):
    text = kwargs.get('text') or kwargs.get('content') or ''
    if not text: return "Error: Missing 'text'."
    try:
        subprocess.run(["powershell", "-Command", f"Set-Clipboard -Value '{text}'"], capture_output=True, timeout=5)
        return f"Success: Copied to clipboard: '{text[:50]}...'"
    except Exception as e: return f"Error: {e}"


def tool_clipboard_paste(**kwargs):
    try:
        r = subprocess.run(["powershell", "-Command", "Get-Clipboard"], capture_output=True, text=True, timeout=5)
        return f"Clipboard contents: {r.stdout.strip()}"
    except Exception as e: return f"Error: {e}"


# ---- MEDIA & UI ----
def tool_media_control(**kwargs):
    action = kwargs.get('action') or kwargs.get('command') or ''
    try:
        import pyautogui
        if 'play' in action or 'pause' in action:
            pyautogui.press('playpause')
            return "Success: Media Play/Pause"
        elif 'next' in action or 'skip' in action:
            pyautogui.press('nexttrack')
            return "Success: Next Track"
        elif 'prev' in action or 'back' in action:
            pyautogui.press('prevtrack')
            return "Success: Previous Track"
        elif 'stop' in action:
            pyautogui.press('stoptrack')
            return "Success: Media Stop"
        return "Error: Unknown media action."
    except Exception as e: return f"Error: {e}"


def tool_search_web(**kwargs):
    query = kwargs.get('query') or kwargs.get('q') or ''
    if not query: return "Error: Missing 'query'."
    try:
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Success: Searching web for '{query}'"
    except Exception as e: return f"Error: {e}"


def tool_get_active_window(**kwargs):
    try:
        pass # import pygetwindow as gw
        win = gw.getActiveWindow()
        if win:
            return f"Active Window: '{win.title}' (Size: {win.width}x{win.height})"
        return "No active window found."
    except Exception as e: return f"Error: {e}"


def tool_set_volume(**kwargs):
    level = kwargs.get('level') or kwargs.get('volume') or kwargs.get('percent')
    if level is None: return "Error: Missing 'level'."
    try:
        level = max(0, min(100, int(level)))
        devices = AudioUtilities.GetSpeakers()
        volume = devices.EndpointVolume
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Success: Volume set to {level}%"
    except Exception as e: return f"Error: {e}"


def tool_youtube_play(**kwargs):
    query = kwargs.get('query') or kwargs.get('search') or kwargs.get('song') or kwargs.get('video') or ''
    if not query: return "Error: Missing 'query'."
    try:
        webbrowser.open(f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}")
        return f"Success: YouTube search for '{query}'"
    except Exception as e: return f"Error: {e}"


def tool_send_notification(**kwargs):
    title = kwargs.get('title') or "KRISHNA Agent"
    message = kwargs.get('message') or kwargs.get('body') or kwargs.get('text') or ''
    if not message: return "Error: Missing 'message'."
    try:
        ps = f"""
        Add-Type -AssemblyName System.Windows.Forms
        $b = New-Object System.Windows.Forms.NotifyIcon
        $b.Icon = [System.Drawing.SystemIcons]::Information
        $b.BalloonTipTitle = '{title}'
        $b.BalloonTipText = '{message}'
        $b.Visible = $true
        $b.ShowBalloonTip(5000)
        Start-Sleep -Seconds 3
        $b.Dispose()
        """
        subprocess.Popen(["powershell", "-Command", ps], creationflags=0x08000000)
        return f"Success: Notification sent: '{message}'"
    except Exception as e: return f"Error: {e}"


def tool_type_text(**kwargs):
    text = kwargs.get('text') or kwargs.get('content') or ''
    if not text: return "Error: Missing 'text'."
    try:
        import pyautogui
        time.sleep(0.5)
        pyautogui.write(text, interval=0.01)
        return f"Success: Typed '{text}'"
    except Exception as e: return f"Error: {e}"


def tool_press_hotkeys(**kwargs):
    keys = kwargs.get('keys') or ''
    if not keys: return "Error: Missing 'keys'."
    try:
        import pyautogui
        if isinstance(keys, str):
            key_list = [k.strip() for k in keys.split('+')]
            pyautogui.hotkey(*key_list)
        return f"Success: Pressed hotkeys '{keys}'"
    except Exception as e: return f"Error: {e}"


def tool_mouse_click(**kwargs):
    x = kwargs.get('x')
    y = kwargs.get('y')
    try:
        import pyautogui
        if x is not None and y is not None:
            pyautogui.click(int(x), int(y))
            return f"Success: Clicked at ({x}, {y})"
        pyautogui.click()
        return "Success: Clicked at current position"
    except Exception as e: return f"Error: {e}"


def tool_calculate(**kwargs):
    expression = kwargs.get('expression') or ''
    if not expression: return "Error: Missing 'expression'."
    try:
        # Basic safe eval
        allowed_chars = "0123456789+-*/(). "
        if all(c in allowed_chars for c in expression):
            result = eval(expression)
            return f"Result: {result}"
        return "Error: Invalid characters in expression."
    except Exception as e: return f"Error: {e}"


def tool_minimize_window(**kwargs):
    try:
        import pyautogui
        pyautogui.hotkey('win', 'down')
        return "Success: Window minimized"
    except Exception as e: return f"Error: {e}"


def tool_maximize_window(**kwargs):
    try:
        import pyautogui
        pyautogui.hotkey('win', 'up')
        return "Success: Window maximized"
    except Exception as e: return f"Error: {e}"


def tool_close_window(**kwargs):
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'f4')
        return "Success: Window closed"
    except Exception as e: return f"Error: {e}"


def tool_switch_window(**kwargs):
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'tab')
        return "Success: Switched window"
    except Exception as e: return f"Error: {e}"


def tool_minimize_all(**kwargs):
    try:
        import pyautogui
        pyautogui.hotkey('win', 'd')
        return "Success: Desktop shown"
    except Exception as e: return f"Error: {e}"


def tool_lock_screen(**kwargs):
    try:
        subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], shell=True)
        return "Success: Screen locked"
    except Exception as e: return f"Error: {e}"


def tool_set_brightness(**kwargs):
    level = kwargs.get('level') or 50
    try:
        level = max(0, min(100, int(level)))
        c = wmi.WMI(namespace="wmi")
        methods = c.WmiMonitorBrightnessMethods()
        for m in methods:
            m.WmiSetBrightness(level, 1)
        return f"Success: Brightness set to {level}%"
    except Exception as e: return f"Error: {e}"


def tool_battery_status(**kwargs):
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            return f"Battery: {battery.percent}% {'(Charging)' if battery.power_plugged else '(Discharging)'}"
        return "Battery info not available."
    except Exception as e: return f"Error: {e}"


def tool_wifi_status(**kwargs):
    try:
        r = subprocess.run(["netsh", "wlan", "show", "interfaces"], capture_output=True, text=True)
        return f"WiFi Status:\n{r.stdout}"
    except Exception as e: return f"Error: {e}"


def tool_download_url(**kwargs):
    url = kwargs.get('url') or ''
    filepath = kwargs.get('filepath') or 'downloaded_file'
    if not url: return "Error: Missing 'url'."
    try:
        import requests
        response = requests.get(url, timeout=30)
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return f"Success: Downloaded '{url}' to '{filepath}'"
    except Exception as e: return f"Error: {e}"


def tool_empty_recycle_bin(**kwargs):
    try:
        ps = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
        subprocess.run(["powershell", "-Command", ps], shell=True)
        return "Success: Recycle bin emptied"
    except Exception as e: return f"Error: {e}"


def tool_disk_cleanup(**kwargs):
    try:
        # Just show temp file size as "cleanup"
        ps = "Get-ChildItem $env:TEMP -Recurse | Measure-Object -Property Length -Sum"
        r = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True)
        return f"Cleanup status: {r.stdout}"
    except Exception as e: return f"Error: {e}"


def tool_disk_space(**kwargs):
    try:
        total, used, free = shutil.disk_usage("/")
        return f"Disk Space: {free // (2**30)} GB free of {total // (2**30)} GB"
    except Exception as e: return f"Error: {e}"


def tool_ip_address(**kwargs):
    try:
        import socket
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        return f"IP Address: {ip} (Hostname: {hostname})"
    except Exception as e: return f"Error: {e}"


def tool_analyze_screen(**kwargs):
    """Takes a screenshot and describes it using Multimodal LLM."""
    filepath = "screen_analysis.png"
    try:
        import pyautogui
        img = pyautogui.screenshot()
        img.save(filepath)
        
        # We need the intelligence interface to call Gemini with the image
        # For simplicity, we'll assume the kernel's intelligence has a method for this
        # or we'll just implement a quick call here if we have the key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: Gemini API key missing. Cannot analyze screen."
        
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        
        with open(filepath, "rb") as f:
            image_bytes = f.read()
            
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                "Describe what is currently visible on this computer screen. "
                "Identify open windows, active apps, and any important information.",
                types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            ]
        )
        
        return f"Screen Analysis:\n{response.text}"
    except Exception as e:
        return f"Error analyzing screen: {e}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    import dotenv
    dotenv.load_dotenv(override=True)
    
    state = StateManager()
    intelligence = IntelligenceInterface()
    
    # Register ALL 45+ tools
    tools = {
        "open_application": (tool_open_application, "Opens app: notepad, chrome, calc, vscode, explorer, edge, paint, word, excel, discord, spotify, steam, etc."),
        "open_url": (tool_open_url, "Opens URL in browser."),
        "open_file": (tool_open_file_with, "Opens file with default app."),
        "list_files": (tool_list_files, "Lists files in directory."),
        "read_file": (tool_read_file, "Reads text file."),
        "write_file": (tool_write_file, "Writes to file."),
        "write_and_open": (tool_write_and_open, "Writes file + opens in Notepad."),
        "rename_file": (tool_rename_file, "Renames/moves a file."),
        "copy_file": (tool_copy_file, "Copies file."),
        "move_file": (tool_move_file, "Moves file."),
        "delete_file": (tool_delete_file, "Deletes file/folder."),
        "search_files": (tool_search_files, "Searches files by pattern."),
        "create_folder": (tool_create_folder, "Creates folder."),
        "zip_files": (tool_zip_files, "Zips files/folders."),
        "unzip_files": (tool_unzip_files, "Extracts zip files."),
        "get_system_info": (tool_get_system_info, "System info (OS/CPU/disk)."),
        "get_time": (tool_get_current_time, "Current date/time."),
        "execute_command": (tool_execute_command, "Runs PowerShell command."),
        "kill_process": (tool_kill_process, "Kills a process."),
        "list_processes": (tool_list_processes, "Lists running processes."),
        "screenshot": (tool_screenshot, "Takes screenshot."),
        "clipboard_copy": (tool_clipboard_copy, "Copies text to clipboard."),
        "clipboard_paste": (tool_clipboard_paste, "Gets clipboard content."),
        "set_volume": (tool_set_volume, "Sets volume 0-100%."),
        "youtube_play": (tool_youtube_play, "YouTube search/play."),
        "youtube": (tool_youtube_play, "Alias for youtube_play."),
        "search_web": (tool_search_web, "Searches Google for a query."),
        "media_control": (tool_media_control, "Media control: play, pause, next, prev, stop."),
        "get_active_window": (tool_get_active_window, "Returns title of currently focused window."),
        "analyze_screen": (tool_analyze_screen, "Takes a screenshot and describes what is on the screen using AI vision."),
        "send_notification": (tool_send_notification, "Windows notification."),
        "press_hotkeys": (tool_press_hotkeys, "Presses keyboard shortcuts."),
        "type_text": (tool_type_text, "Types into focused window."),
        "mouse_click": (tool_mouse_click, "Clicks at coordinates."),
        "calculate": (tool_calculate, "Math: sqrt, sin, cos, factorial, etc."),
        "minimize_window": (tool_minimize_window, "Minimizes current window."),
        "maximize_window": (tool_maximize_window, "Maximizes current window."),
        "close_window": (tool_close_window, "Closes current window (Alt+F4)."),
        "switch_window": (tool_switch_window, "Switches window (Alt+Tab)."),
        "minimize_all": (tool_minimize_all, "Minimizes all windows (Win+D)."),
        "lock_screen": (tool_lock_screen, "Locks screen."),
        "set_brightness": (tool_set_brightness, "Sets screen brightness 0-100%."),
        "battery_status": (tool_battery_status, "Gets battery info."),
        "wifi_status": (tool_wifi_status, "Gets WiFi info."),
        "download_url": (tool_download_url, "Downloads file from URL."),
        "empty_recycle_bin": (tool_empty_recycle_bin, "Empties recycle bin."),
        "disk_cleanup": (tool_disk_cleanup, "Shows temp file sizes."),
        "disk_space": (tool_disk_space, "Gets disk space for all drives."),
        "ip_address": (tool_ip_address, "Gets IP addresses."),
    }
    
    for name, (func, desc) in tools.items():
        intelligence.register_tool(name, func, desc)
    
    ethics = EthicsEngine(intelligence=intelligence)
    reasoning = ReasoningModule(intelligence, ethics_engine=ethics)
    actuator = Actuator(intelligence, ethics_engine=ethics)
    navigator = Navigator(intelligence, ethics_engine=ethics)
    handler = HandlerUnit(reasoning, actuator, ethics_engine=ethics)
    kernel = Kernel(state, navigator, handler, ethics_engine=ethics)
    
    agent_container.kernel = kernel
    agent_container.ethics_engine = ethics
    
    # Wire up god mode reaction callbacks
    kernel.on_task_complete = lambda name, tool: agent_container.record_task_done(name, tool)
    kernel.on_task_failed = lambda: agent_container.record_task_failed()
    kernel.on_task_blocked = lambda: agent_container.record_task_blocked()
    
    import builtins
    original_print = builtins.print
    def custom_print(*args, **kwargs):
        msg = " ".join(str(a) for a in args)
        original_print(msg, **kwargs)
        # Fan out to all SSE subscribers
        dead = []
        for q in log_subscribers:
            try:
                q.put_nowait(msg)
            except (asyncio.QueueFull, Exception):
                dead.append(q)
        for q in dead:
            if q in log_subscribers:
                log_subscribers.remove(q)
    builtins.print = custom_print

    broadcast_log(f"Agent initialized. {len(tools)} tools loaded. Ethics Engine ACTIVE.")
    task = asyncio.create_task(kernel.start_loop())
    yield
    kernel.stop_loop()
    task.cancel()
    builtins.print = original_print

app = FastAPI(lifespan=lifespan)

class GoalRequest(BaseModel):
    goal: str

class FloodRequest(BaseModel):
    goals: list
    delay_ms: int = 50  # Milliseconds between each queued goal

@app.post("/api/flood_test")
async def flood_test(request: FloodRequest):
    """Stress test: batch-submit up to 50 goals to test queue handling, memory, and UI."""
    if not agent_container.kernel:
        return JSONResponse(content={"error": "Kernel not initialized"}, status_code=500)
    goals = [str(g).strip()[:500] for g in request.goals[:50]]  # Cap at 50, limit length
    queued = 0
    for goal in goals:
        if goal:
            agent_container.kernel.pending_goals.append(goal)
            queued += 1
            if request.delay_ms > 0:
                await asyncio.sleep(request.delay_ms / 1000)
    broadcast_log(f"[FLOOD TEST] ⚡ Queued {queued} goals for stress testing")
    return JSONResponse(content={"status": "success", "queued": queued})

@app.post("/api/goal")
async def receive_goal(request: GoalRequest):
    if agent_container.kernel:
        agent_container.kernel.pending_goals.append(request.goal)
        broadcast_log(f"[API] Goal queued: {request.goal}")
        return {"status": "success", "message": "Goal received."}
    return {"status": "error", "message": "Kernel not initialized."}

@app.get("/api/ethics")
async def get_ethics_status():
    if agent_container.ethics_engine:
        return JSONResponse(content=agent_container.ethics_engine.get_stats())
    return JSONResponse(content={"error": "Not initialized."}, status_code=500)

@app.get("/api/tasks")
async def get_tasks():
    if agent_container.kernel:
        return JSONResponse(content={"tasks": agent_container.kernel.get_task_results()})
    return JSONResponse(content={"tasks": []})

@app.get("/api/logs")
async def event_stream(request: Request):
    q = asyncio.Queue(maxsize=500)
    log_subscribers.append(q)
    async def gen():
        try:
            while True:
                if await request.is_disconnected(): break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=15)
                    yield {"event": "message", "id": str(time.time()), "retry": 3000, "data": json.dumps({"text": msg})}
                except asyncio.TimeoutError:
                    # Send keepalive ping to prevent connection timeout
                    yield {"event": "message", "id": "hb", "data": json.dumps({"text": "[heartbeat]"})}
        except (asyncio.CancelledError, Exception):
            pass
        finally:
            if q in log_subscribers:
                log_subscribers.remove(q)
    return EventSourceResponse(gen())

@app.get("/api/godmode")
async def get_god_mode():
    return JSONResponse(content=agent_container.get_god_stats())

@app.post("/api/godmode/toggle")
async def toggle_god_mode():
    agent_container.god_mode = not agent_container.god_mode
    status = "ACTIVATED" if agent_container.god_mode else "DEACTIVATED"
    broadcast_log(f"[GOD MODE] {status}! Power Level: {agent_container.power_level}")
    return JSONResponse(content={"god_mode": agent_container.god_mode, "status": status})

@app.get("/api/reactions")
async def get_reactions(request: Request):
    async def gen():
        while True:
            if await request.is_disconnected(): break
            try:
                reaction = await asyncio.wait_for(agent_container.reaction_queue.get(), timeout=30)
                yield {"event": "reaction", "data": json.dumps(reaction)}
            except asyncio.TimeoutError:
                yield {"event": "heartbeat", "data": json.dumps({"type": "ping"})}
    return EventSourceResponse(gen())

FUNCTION_DECLARATIONS = [
    {
        "name": "open_application",
        "description": "Opens a desktop application by name (e.g. notepad, calculator, chrome, vs code, paint, control panel, settings, task manager, spotify, recycle bin).",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "application": {"type": "STRING", "description": "The name of the application to open."}
            },
            "required": ["application"]
        }
    },
    {
        "name": "open_url",
        "description": "Opens a website URL in the default web browser.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "url": {"type": "STRING", "description": "The website URL to open."}
            },
            "required": ["url"]
        }
    },
    {
        "name": "screenshot",
        "description": "Takes a screenshot of the computer screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "filepath": {"type": "STRING", "description": "Path to save the screenshot image. Default: screenshot.png"},
                "mode": {"type": "STRING", "description": "Screenshot mode: 'full' or 'window'. Default: 'full'"}
            }
        }
    },
    {
        "name": "set_volume",
        "description": "Sets the system volume level.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "level": {"type": "INTEGER", "description": "Volume percentage level from 0 to 100."}
            },
            "required": ["level"]
        }
    },
    {
        "name": "set_brightness",
        "description": "Sets the screen brightness level.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "level": {"type": "INTEGER", "description": "Brightness percentage level from 0 to 100."}
            },
            "required": ["level"]
        }
    },
    {
        "name": "press_hotkeys",
        "description": "Simulates pressing key combinations or keyboard shortcuts (e.g. 'ctrl+c', 'win+d', 'alt+f4', 'enter').",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "keys": {"type": "STRING", "description": "Key combinations separated by spaces or plus signs."}
            },
            "required": ["keys"]
        }
    },
    {
        "name": "type_text",
        "description": "Types specified text characters into the currently active/focused window.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "text": {"type": "STRING", "description": "The text string to type."}
            },
            "required": ["text"]
        }
    },
    {
        "name": "mouse_click",
        "description": "Clicks at the specified coordinates (X, Y) on the screen.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "x": {"type": "INTEGER", "description": "X coordinate."},
                "y": {"type": "INTEGER", "description": "Y coordinate."}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "get_time",
        "description": "Gets the current date and time on the laptop.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "get_system_info",
        "description": "Retrieves laptop operating system specs, disk space, and details.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "execute_command",
        "description": "Runs a custom shell or PowerShell command on the laptop.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "command": {"type": "STRING", "description": "The command string to execute."}
            },
            "required": ["command"]
        }
    },
    {
        "name": "kill_process",
        "description": "Kills a running application or background process.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "process_name": {"type": "STRING", "description": "The name of the process/application to terminate."}
            },
            "required": ["process_name"]
        }
    },
    {
        "name": "list_processes",
        "description": "Lists the currently running top CPU processes on the system.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "minimize_all",
        "description": "Minimizes all windows to show the desktop.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "lock_screen",
        "description": "Locks the Windows laptop session immediately.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "wifi_status",
        "description": "Retrieves the current network and wifi connection status.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "empty_recycle_bin",
        "description": "Empties the Windows Recycle Bin.",
        "parameters": {"type": "OBJECT", "properties": {}}
    },
    {
        "name": "youtube_play",
        "description": "Searches and plays a video on YouTube.",
        "parameters": {
            "type": "OBJECT",
            "properties": {
                "query": {"type": "STRING", "description": "YouTube search query."}
            },
            "required": ["query"]
        }
    },
    {
        "name": "analyze_screen",
        "description": "Takes a screenshot of the computer screen and analyzes it using Gemini's visual intelligence to describe what is currently visible.",
        "parameters": {"type": "OBJECT", "properties": {}}
    }
]

def get_setup_message():
    return {
        "setup": {
            "model": "models/gemini-2.0-flash-exp",
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {
                            "voiceName": "Puck"
                        }
                    }
                }
            },
            "systemInstruction": {
                "parts": [
                    {
                        "text": (
                            "You are KRISHNA, an insanely powerful, low-latency, real-time voice-controlled agent "
                            "with full laptop control capabilities. You speak in a highly natural, energetic, witty, "
                            "and engaging voice (Puck). You can fully control the user's laptop using the provided "
                            "tools. You must execute all user tasks by invoking the appropriate tools. If the ethics "
                            "engine blocks an action, you will be notified, and you should explain why the action "
                            "cannot be executed."
                        )
                    }
                ]
            },
            "tools": [
                {
                    "functionDeclarations": FUNCTION_DECLARATIONS
                }
            ]
        }
    }

@app.websocket("/ws/live")
async def websocket_live(websocket: WebSocket):
    await websocket.accept()
    broadcast_log("[WS Proxy] Browser client connected to Live Voice session.")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        broadcast_log("[WS Proxy] ERROR: GEMINI_API_KEY not set.")
        await websocket.close(code=1008)
        return
        
    gemini_url = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContent?key={api_key}"
    
    try:
        async with websockets.connect(gemini_url) as gemini_ws:
            broadcast_log("[WS Proxy] Connected to Gemini Multimodal Live API.")
            
            # Send setup message
            setup_msg = get_setup_message()
            await gemini_ws.send(json.dumps(setup_msg))
            broadcast_log("[WS Proxy] Sent session setup to Gemini.")
            
            async def browser_to_gemini():
                try:
                    async for message in websocket.iter_text():
                        # Forward browser mic chunks/commands directly to Gemini
                        data = json.loads(message)
                        
                        if data.get("type") == "client_interrupted":
                            interrupt_payload = {
                                "clientContent": {
                                    "turns": [],
                                    "turnComplete": False
                                }
                            }
                            await gemini_ws.send(json.dumps(interrupt_payload))
                            continue
                            
                        await gemini_ws.send(message)
                except Exception as e:
                    broadcast_log(f"[WS Proxy] Browser to Gemini loop closed: {e}")
                    raise
                    
            async def gemini_to_browser():
                try:
                    async for raw_message in gemini_ws:
                        response = json.loads(raw_message)
                        
                        if "serverContent" in response:
                            server_content = response["serverContent"]
                            model_turn = server_content.get("modelTurn", {})
                            parts = model_turn.get("parts", [])
                            
                            for part in parts:
                                if "inlineData" in part:
                                    audio_data = part["inlineData"].get("data")
                                    if audio_data:
                                        await websocket.send_json({
                                            "type": "audio",
                                            "data": audio_data
                                        })
                                elif "text" in part:
                                    text_val = part["text"]
                                    if text_val:
                                        await websocket.send_json({
                                            "type": "caption",
                                            "text": text_val
                                        })
                                        
                            if server_content.get("turnComplete"):
                                await websocket.send_json({"type": "turn_complete"})
                                
                            if server_content.get("interrupted"):
                                await websocket.send_json({"type": "interrupted"})
                                
                        elif "toolCall" in response:
                            tool_call = response["toolCall"]
                            function_calls = tool_call.get("functionCalls", [])
                            
                            for call in function_calls:
                                call_id = call.get("id")
                                name = call.get("name")
                                args = call.get("args", {})
                                
                                broadcast_log(f"[Live Tool] Gemini requests: {name}({args})")
                                
                                if not agent_container.ethics_engine:
                                    result_str = "Error: Ethics Engine not initialized."
                                    agent_container.record_task_failed()
                                else:
                                    action_details = {
                                        "tool_to_call": name,
                                        "tool_args": args,
                                        "decision": f"Real-time voice request to run {name} with arguments {args}"
                                    }
                                    verdict = agent_container.ethics_engine.evaluate_action(action_details)
                                    
                                    if verdict.get("approved"):
                                        intelligence = agent_container.ethics_engine.intelligence
                                        tool_info = intelligence.get_tool(name)
                                        if tool_info:
                                            func = tool_info["func"]
                                            try:
                                                broadcast_log(f"[Live Actuator] Running {name}...")
                                                if asyncio.iscoroutinefunction(func):
                                                    result_str = await func(**args)
                                                else:
                                                    result_str = func(**args)
                                                
                                                broadcast_log(f"[Live Actuator] Success: {result_str}")
                                                agent_container.record_task_done(name, name)
                                            except Exception as exec_err:
                                                result_str = f"Error executing tool: {exec_err}"
                                                broadcast_log(f"[Live Actuator] Failure: {result_str}")
                                                agent_container.record_task_failed()
                                        else:
                                            result_str = f"Error: Tool '{name}' is not registered on the backend."
                                            agent_container.record_task_failed()
                                    else:
                                        result_str = f"Action ethically blocked by Dharma Ethics Engine. Reason: {verdict.get('reason')}. Principle: {verdict.get('principle')}."
                                        broadcast_log(f"[Live Actuator] BLOCKED: {result_str}")
                                        agent_container.record_task_blocked()
                                
                                tool_response = {
                                    "toolResponse": {
                                        "functionResponses": [
                                            {
                                                "response": {"output": result_str},
                                                "id": call_id,
                                                "name": name
                                            }
                                        ]
                                    }
                                }
                                await gemini_ws.send(json.dumps(tool_response))
                                broadcast_log(f"[Live Tool] Returned tool response to Gemini.")
                except Exception as e:
                    broadcast_log(f"[WS Proxy] Gemini to Browser loop closed: {e}")
                    raise
            
            await asyncio.gather(browser_to_gemini(), gemini_to_browser())
            
    except WebSocketDisconnect:
        broadcast_log("[WS Proxy] Browser client disconnected.")
    except Exception as err:
        broadcast_log(f"[WS Proxy] Error in WebSocket Proxy: {err}")
    finally:
        try:
            await websocket.close()
        except:
            pass
        broadcast_log("[WS Proxy] Live Voice session closed.")

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    with open("index.html", "r") as f: return f.read()

# Serve JS/CSS/static files from project root
app.mount("/", StaticFiles(directory="."), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, reload=True)
