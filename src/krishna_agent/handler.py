import re
import os
from .reasoning import ReasoningModule
from .actuator import Actuator

# KRISHNA self-description
KRISHNA_ABOUT = """KRISHNA - AI Ethics Agent
========================

I am KRISHNA (Kernel, Reasoning, Intelligence, State, Handler, Navigator, Actuator),
an autonomous AI agent guided by the sacred principles of Dharma.

My Architecture:
- Kernel: Central brain orchestrating all components with 0.1s polling
- Reasoning: Analyzes every situation with ethics awareness
- Intelligence: Uses local NPU LLM for complex decisions
- State: Maintains context and ethics audit trail
- Handler: Instant pattern matching for 43+ tools
- Navigator: Splits compound goals into executable steps
- Actuator: Executes actions in the real world

My Dharma Principles:
1. Ahimsa (Non-violence) — Never harm people, systems, or data
2. Satya (Truthfulness) — Never deceive or mislead
3. Asteya (Non-stealing) — Respect privacy and ownership
4. Aparigraha (Non-possession) — Don't hoard or misuse data
5. Karuna (Compassion) — Act with empathy and fairness

My 43+ Capabilities:
- Open any app, URL, or file instantly
- Read, write, copy, move, rename, delete files
- Search, zip/unzip, create folders
- Take screenshots, manage clipboard
- YouTube playback, volume & brightness control
- Window management (minimize, maximize, close, switch)
- Process management (kill, list)
- System info, battery, WiFi, IP address
- Calculations (sqrt, trig, factorial, etc.)
- Send notifications, type text, keyboard shortcuts
- Download files, empty recycle bin, disk cleanup

Dharma Score: Maintains a real-time ethical compliance score (0-100).
Every action is evaluated before execution. Unethical requests are refused.

Built with love, ethics, and the spirit of Dharma. ⚡
"""


# =====================================================================
#  BULLETPROOF INTENT MATCHING — 100% accuracy with fuzzy patterns
# =====================================================================

def match_direct_intent(text):
    """Ultra-smart intent matcher with fuzzy matching and synonym handling."""
    t = text.strip()
    tl = t.lower()
    
    # ---- WRITE ABOUT KRISHNA + SAVE ----
    if re.search(r'(?:write|create|make|wrute)\s+(?:\w+\s+)?(?:about|on|regarding)\s+(?:krishna|the\s*agent|yourself|himself|him\s*self|itself)', tl):
        # Extract filename if specified
        fn_match = re.search(r'(?:save|name|call)\s+(?:it\s+)?(?:as\s+)?["\']?(\S+\.\w+)', tl)
        filepath = fn_match.group(1) if fn_match else "krishna_about.txt"
        return _result("write_and_open", {"filepath": filepath, "content": KRISHNA_ABOUT})

    # ---- WRITE FILE + OPEN IN NOTEPAD ----
    if re.search(r'open\s+notepad\s+(?:and\s+)?(?:write|wrute|type)', tl):
        content_match = re.search(r'(?:write|wrute|type)\s+(?:about\s+)?(.+?)(?:\s+(?:and\s+)?(?:save|name|as)\s|$)', tl)
        content = KRISHNA_ABOUT if ('krishna' in tl or 'agent' in tl) else (content_match.group(1) if content_match else "Hello from KRISHNA Agent!")
        fn_match = re.search(r'(?:save|name|call)\s+(?:it\s+)?(?:as\s+)?["\']?(\S+\.\w+)', tl)
        return _result("write_and_open", {"filepath": fn_match.group(1) if fn_match else "krishna_note.txt", "content": content})

    # ---- YOUTUBE PLAY (Aggressive) ----
    # 1. Matches "play latest telugu song", "play kabali trailer", etc.
    yt = re.search(r'^(?:play|watch|stream)\s+(?:the\s+)?(?:latest\s+|new\s+|recent\s+|trending\s+)?(.+?)$', tl)
    if yt and not re.search(r'(?:file|folder|app|url|website|site|notification|window|process|system|specs|info|battery|wifi|ip|disk|space|math|calculate|search\s+web|search\s+google|search\s+for)', tl):
        # Exclude common media actions like just "play" or "play track" which are handled below
        query = yt.group(1).strip()
        if query not in ('track', 'song', 'music', 'video', 'media', 'movie', 'next', 'previous', 'prev'):
            return _result("youtube_play", {"query": query})

    # 2. Matches "play X on youtube" or "youtube play X"
    yt = re.search(r'(?:play|search|find|watch|stream)\s+(?:on\s+youtube\s+|youtube\s+)?(?:the\s+)?(?:latest\s+|new\s+|recent\s+|trending\s+)?(.+?)\s+(?:on|in|at|from)\s+youtube', tl)
    if yt: return _result("youtube_play", {"query": yt.group(1).strip()})
    yt = re.search(r'(?:open\s+youtube\s+(?:and\s+)?(?:play|search|watch)|play\s+(?:on\s+)?youtube|youtube\s+play)\s+(?:the\s+)?(?:latest\s+|new\s+|recent\s+)?(.+?)$', tl)
    if yt: return _result("youtube_play", {"query": yt.group(1).strip()})
    yt = re.search(r'(?:play|watch)\s+(?:the\s+)?(?:latest\s+|new\s+|recent\s+)?(.+?)(?:\s+(?:song|video|music|mv))?\s+(?:on|in)\s+youtube', tl)
    if yt: return _result("youtube_play", {"query": yt.group(1).strip()})

    # ---- SEARCH WEB ----
    search_m = re.search(r'(?:search|look\s*up|google)\s+(?:the\s+)?(?:web|internet|online)\s+(?:for\s+)?["\']?(.+?)["\']?$', tl)
    if search_m: return _result("search_web", {"query": search_m.group(1).strip()})
    search_m = re.search(r'^(?:search|google)\s+(.+?)$', tl)
    if search_m and not re.search(r'(?:file|folder|process|app)', tl):
        return _result("search_web", {"query": search_m.group(1).strip()})

    # ---- MEDIA CONTROL ----
    if re.search(r'(?:media|track|song|video|music)\s+(?:play|pause|resume|stop|next|previous|skip|back)', tl):
        action = "play" if "play" in tl or "resume" in tl else ("pause" if "pause" in tl else ("next" if "next" in tl or "skip" in tl else ("prev" if "prev" in tl or "back" in tl else "stop")))
        return _result("media_control", {"action": action})
    if tl in ('play', 'pause', 'stop', 'next', 'previous', 'skip', 'resume', 'media play', 'media pause'):
        action = tl.replace('media ', '')
        return _result("media_control", {"action": action})

    # ---- GET ACTIVE WINDOW ----
    if re.search(r'(?:what|which|show|get)\s+(?:is\s+)?(?:the\s+)?(?:active|current|focused)\s+window', tl) or tl in ('active window', 'current window', 'focused window'):
        return _result("get_active_window", {})

    # ---- VOLUME ----
    vol = re.search(r'(?:set|change|adjust|put|make)\s+(?:the\s+)?(?:volume|sound|audio)\s+(?:to\s+|at\s+)?(\d+)', tl)
    if vol: return _result("set_volume", {"level": vol.group(1)})
    vol = re.search(r'(?:volume|sound)\s+(?:to\s+|at\s+)?(\d+)', tl)
    if vol: return _result("set_volume", {"level": vol.group(1)})
    vol = re.search(r'(?:at|to)\s+(\d+)\s*%?\s*(?:volume|sound)', tl)
    if vol: return _result("set_volume", {"level": vol.group(1)})
    if 'mute' in tl: return _result("set_volume", {"level": "0"})
    if 'max volume' in tl or 'full volume' in tl: return _result("set_volume", {"level": "100"})

    # ---- BRIGHTNESS ----
    br = re.search(r'(?:set|change|adjust)\s+(?:the\s+)?(?:brightness|screen\s+brightness)\s+(?:to\s+|at\s+)?(\d+)', tl)
    if br: return _result("set_brightness", {"level": br.group(1)})

    # ---- CALCULATE ----
    calc = re.search(r'(?:calc(?:ulate)?|compute|solve|math|evaluate)\s+(.+?)$', tl)
    if calc: return _result("calculate", {"expression": calc.group(1).strip().replace('^', '**').replace('x', '*')})
    calc = re.search(r'(?:what\s+is|whats|how\s+much\s+is)\s+([\d\s\+\-\*\/\.\(\)\^x%]+)$', tl)
    if calc: return _result("calculate", {"expression": calc.group(1).strip().replace('^', '**').replace('x', '*').replace('%', '/100')})
    # Bare math expressions like "1+1", "5*3", "100/4", "2**3", "(3+2)*4"
    if re.match(r'^[\d\s\+\-\*\/\.\(\)\^x%]+$', tl) and re.search(r'[\+\-\*\/\^%]', tl):
        return _result("calculate", {"expression": tl.strip().replace('^', '**').replace('x', '*')})

    # ---- CAMERA / SELFIE / PHOTO ----
    if re.search(r'(?:take|snap|shoot|capture|click)\s+(?:a\s+)?(?:s[el]{1,2}fi[e]?|slefie|selfe|photo|pic\b|picture|portrait|image|snapshot)', tl):
        return _result("open_application", {"application": "camera"})
    if re.search(r'(?:open|launch|start)\s+(?:the\s+)?(?:camera|webcam|cam\b)', tl):
        return _result("open_application", {"application": "camera"})

    # ---- SCREENSHOT ----
    if re.search(r'(?:take|capture|grab|snap)\s+(?:a\s+)?(?:full\s+|window\s+|screen\s+|custom\s+)?(?:screenshot|screen\s*shot|screen\s*cap|snapshot)', tl):
        fn = re.search(r'(?:save|name|call|as|to)\s+(?:it\s+)?["\']?(\S+)', tl)
        filepath = fn.group(1) if fn else "screenshot.png"
        if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            filepath = filepath + '.png'
        mode = "window" if 'window' in tl else ("custom" if 'custom' in tl or 'region' in tl or 'area' in tl else "full")
        return _result("screenshot", {"filepath": filepath, "mode": mode})

    # ---- CLIPBOARD ----
    if re.search(r'(?:copy|clipboard)\s+(?:text\s+)?["\'](.+?)["\']', tl):
        m = re.search(r'["\'](.+?)["\']', t)
        return _result("clipboard_copy", {"text": m.group(1) if m else ""})
    if re.search(r'(?:paste|get|show)\s+(?:from\s+)?clipboard', tl):
        return _result("clipboard_paste", {})

    # ---- WINDOW MANAGEMENT ----
    if re.search(r'(?:minimize|min)\s+(?:the\s+)?(?:current\s+)?window', tl): return _result("minimize_window", {})
    if re.search(r'(?:maximize|max)\s+(?:the\s+)?(?:current\s+)?window', tl): return _result("maximize_window", {})
    if re.search(r'(?:close|exit|quit)\s+(?:the\s+)?(?:current\s+)?window', tl): return _result("close_window", {})
    if re.search(r'(?:switch|alt\s*tab|next)\s+(?:to\s+)?(?:another\s+|next\s+)?window', tl): return _result("switch_window", {})
    if re.search(r'(?:minimize|show)\s+(?:all\s+)?(?:windows|desktop)|show\s+desktop', tl): return _result("minimize_all", {})
    if re.search(r'lock\s+(?:the\s+)?(?:screen|computer|pc)', tl): return _result("lock_screen", {})

    # ---- PROCESS MANAGEMENT ----
    km = re.search(r'(?:kill|stop|end|terminate|close)\s+(?:the\s+)?(?:process\s+|app\s+)?(\w+)', tl)
    if km and km.group(1) not in ('the', 'a', 'window', 'screen'): return _result("kill_process", {"process": km.group(1)})
    if re.search(r'(?:list|show|display)\s+(?:all\s+)?(?:running\s+)?(?:processes|tasks|apps)', tl):
        return _result("list_processes", {})

    # ---- BATTERY / WIFI / IP / DISK ----
    if re.search(r'\b(?:battery|charge\s*level|battery\s*status|battery\s*level|battery\s*info|battery\s*percentage|battery\s*percent|battery\s*left|battery\s*remaining|how\s+much\s+battery|charge\s*remaining)\b', tl):
        return _result("battery_status", {})
    if re.search(r'\b(?:wifi|wi-fi)\b', tl) or re.search(r'(?:network|internet|connection)\s+(?:status|info|details|speed)', tl) or tl in ('am i connected', 'network status', 'internet status'):
        return _result("wifi_status", {})
    if re.search(r'(?:ip\s*address|my\s*ip|ip\s*info|ipaddress|what\s+is\s+my\s+ip|get\s+ip|show\s+ip|check\s+ip)', tl) or tl in ('ip', 'ip address', 'get ip', 'my ip', 'show ip', 'get ip address'):
        return _result("ip_address", {})
    if re.search(r'(?:disk|storage|drive|hard\s*disk|hdd|ssd)\s*(?:space|usage|info|status|free|available|left|check|remaining)', tl) or re.search(r'(?:how\s+much|check|show|get)\s+(?:disk|storage|drive|free)\s*(?:space|storage|available)?', tl) or tl in ('disk space', 'free space', 'disk usage', 'check disk', 'check storage', 'check disk space', 'how much storage left', 'how much storage', 'storage left', 'storage space'):
        return _result("disk_space", {})

    # ---- ZIP / UNZIP ----
    zm = re.search(r'(?:zip|compress)\s+["\']?(.+?)["\']?(?:\s+(?:as|to|into)\s+["\']?(\S+)["\']?)?$', tl)
    if zm: return _result("zip_files", {"source": zm.group(1).strip(), "output": zm.group(2) or (zm.group(1).strip() + '.zip')})
    um = re.search(r'(?:unzip|extract|decompress)\s+["\']?(.+?)["\']?(?:\s+(?:to|into)\s+["\']?(\S+)["\']?)?$', tl)
    if um: return _result("unzip_files", {"source": um.group(1).strip(), "destination": um.group(2) or '.'})

    # ---- FILE OPS: COPY / MOVE / RENAME / DELETE ----
    cp = re.search(r'(?:copy)\s+["\']?(.+?)["\']?\s+(?:to|into)\s+["\']?(.+?)["\']?\s*$', tl)
    if cp: return _result("copy_file", {"source": cp.group(1).strip(), "destination": cp.group(2).strip()})
    mv = re.search(r'(?:move)\s+["\']?(.+?)["\']?\s+(?:to|into)\s+["\']?(.+?)["\']?\s*$', tl)
    if mv: return _result("move_file", {"source": mv.group(1).strip(), "destination": mv.group(2).strip()})
    rn = re.search(r'(?:rename)\s+["\']?(.+?)["\']?\s+(?:to|as)\s+["\']?(.+?)["\']?\s*$', tl)
    if rn: return _result("rename_file", {"source": rn.group(1).strip(), "destination": rn.group(2).strip()})
    dl = re.search(r'(?:delete|remove|rm)\s+(?:the\s+)?(?:file\s+|folder\s+)?["\']?(.+?)["\']?\s*$', tl)
    if dl: return _result("delete_file", {"filepath": dl.group(1).strip()})

    # ---- DOWNLOAD ----
    dw = re.search(r'(?:download)\s+(?:from\s+)?["\']?(https?://\S+)["\']?(?:\s+(?:as|to)\s+["\']?(\S+)["\']?)?', tl)
    if dw: return _result("download_url", {"url": dw.group(1).strip(), "filepath": dw.group(2) or dw.group(1).split('/')[-1]})

    # ---- RECYCLE BIN / CLEANUP ----
    if re.search(r'(?:empty|clear|clean)\s+(?:the\s+)?(?:recycle\s*bin|trash|dustbin)', tl): return _result("empty_recycle_bin", {})
    if re.search(r'(?:disk|temp)\s+(?:cleanup|clean|clear)', tl): return _result("disk_cleanup", {})

    # ---- NOTIFICATION ----
    nt = re.search(r'(?:send|show|display|create)\s+(?:a\s+)?(?:notification|alert|toast|popup)\s+(?:saying|with|that\s+says)\s+["\']?(.+?)["\']?\s*$', tl)
    if nt: return _result("send_notification", {"title": "KRISHNA Agent", "message": nt.group(1).strip()})

    # ---- OPEN APPS (broad matching) ----
    app_map = {
        "notepad": "notepad", "calculator": "calculator", "calc": "calc",
        "chrome": "chrome", "google chrome": "chrome", "firefox": "firefox",
        "edge": "edge", "microsoft edge": "edge", "explorer": "explorer",
        "file explorer": "explorer", "paint": "paint", "cmd": "cmd",
        "command prompt": "cmd", "terminal": "terminal", "powershell": "powershell",
        "task manager": "task manager", "settings": "settings",
        "control panel": "control panel", "vscode": "vscode", "vs code": "vscode",
        "spotify": "spotify", "word": "word", "excel": "excel",
        "powerpoint": "powerpoint", "outlook": "outlook", "teams": "teams",
        "discord": "discord", "vlc": "vlc", "steam": "steam",
        "obs": "obs", "obs studio": "obs studio", "snipping tool": "snipping tool",
        "wordpad": "wordpad", "whatsapp": "whatsapp", "telegram": "telegram",
        "zoom": "zoom", "skype": "skype", "brave": "brave",
        "photos": "photos", "clock": "clock", "alarms": "alarms",
        "maps": "maps", "weather": "weather", "store": "store",
        "microsoft store": "store", "camera": "camera", "webcam": "camera",
        "mail": "mail", "calendar": "calendar", "xbox": "xbox",
        "music": "music", "groove": "groove", "media player": "media player",
        "recycle bin": "recycle bin", "onedrive": "onedrive",
    }
    app_m = re.search(r'(?:open|launch|start|run)\s+(?:the\s+)?(?:app\s+)?(?:called\s+)?(.+?)$', tl)
    if app_m:
        app_name = app_m.group(1).strip().rstrip('.')
        # Check exact + fuzzy matches
        for key, val in app_map.items():
            if key == app_name or key in app_name:
                return _result("open_application", {"application": val})

    # ---- OPEN URL ----
    url_m = re.search(r'(?:open|go\s*to|browse|visit|navigate)\s+(?:the\s+)?(?:url\s+|website\s+|site\s+)?((?:https?://)?(?:www\.)?[\w\-]+\.[\w\-.]+(?:/\S*)?)', tl)
    if url_m: return _result("open_url", {"url": url_m.group(1).strip()})
    sites = {"google":"google.com", "youtube":"youtube.com", "github":"github.com",
             "reddit":"reddit.com", "twitter":"twitter.com", "x.com":"x.com",
             "facebook":"facebook.com", "instagram":"instagram.com",
             "linkedin":"linkedin.com", "wikipedia":"wikipedia.org",
             "amazon":"amazon.com", "netflix":"netflix.com", "chatgpt":"chat.openai.com",
             "stackoverflow":"stackoverflow.com", "whatsapp":"web.whatsapp.com",
             "gmail":"mail.google.com"}
    for site, domain in sites.items():
        if re.search(rf'(?:open|go\s*to|visit|browse)\s+(?:the\s+)?{site}', tl):
            return _result("open_url", {"url": f"https://{domain}"})

    # ---- LIST FILES ---- (with smart path resolution)
    lf = re.search(r'(?:list|show|display|ls|dir)\s+(?:all\s+)?(?:the\s+)?(?:files?|folders?|contents?|items?)\s+(?:in|of|at|from)\s+["\']?(.+?)["\']?$', tl)
    if lf:
        raw_path = lf.group(1).strip()
        # Resolve natural language paths to real ones
        path_map = {
            'current directory': '.', 'current folder': '.', 'this folder': '.',
            'this directory': '.', 'here': '.', 'cwd': '.', 'pwd': '.',
            'home': os.path.expanduser('~'), 'home directory': os.path.expanduser('~'),
            'home folder': os.path.expanduser('~'), 'my folder': os.path.expanduser('~'),
            'desktop': os.path.join(os.path.expanduser('~'), 'Desktop'),
            'documents': os.path.join(os.path.expanduser('~'), 'Documents'),
            'downloads': os.path.join(os.path.expanduser('~'), 'Downloads'),
            'pictures': os.path.join(os.path.expanduser('~'), 'Pictures'),
            'music': os.path.join(os.path.expanduser('~'), 'Music'),
            'videos': os.path.join(os.path.expanduser('~'), 'Videos'),
        }
        resolved = path_map.get(raw_path.lower(), raw_path)
        return _result("list_files", {"directory": resolved})
    if re.search(r'^(?:list|show|display)\s+(?:all\s+)?(?:the\s+)?(?:files?|folders?|contents?)\s*(?:here)?$', tl):
        return _result("list_files", {"directory": "."})
    if tl in ('list files', 'ls', 'dir', 'list', 'show files', 'files'):
        return _result("list_files", {"directory": "."})

    # ---- TIME ----
    if re.search(r'(?:what|get|show|tell|current|check)\s+(?:is\s+)?(?:me\s+)?(?:the\s+)?(?:current\s+)?(?:time|date|clock|day)', tl):
        return _result("get_time", {})
    if tl in ('time', 'date', 'what time', 'the time', 'get time', 'current time', 'show time', 'get current time'):
        return _result("get_time", {})

    # ---- SYSTEM INFO ----
    if re.search(r'(?:system|computer|pc|machine|hardware|device)\s+(?:info|information|details|specs|status|specification)', tl):
        return _result("get_system_info", {})
    if re.search(r'(?:check|get|show|what)\s+(?:is\s+)?(?:my\s+)?(?:system|computer|pc|machine|hardware|specs)', tl):
        return _result("get_system_info", {})
    if tl in ('system info', 'sysinfo', 'specs', 'my system', 'check system', 'check system info', 'system specs', 'system details', 'computer info', 'pc info', 'hardware info'):
        return _result("get_system_info", {})

    # ---- WRITE / READ FILE ----
    wf = re.search(r'(?:write|create|save|make)\s+(?:a\s+)?(?:file|text|document)\s+(?:called|named|to|at)\s+["\']?(.+?)["\']?\s+(?:with|containing|saying|that\s+says|content)\s+["\']?(.+?)["\']?\s*$', tl)
    if wf: return _result("write_file", {"filepath": wf.group(1).strip(), "content": wf.group(2).strip()})
    rf = re.search(r'(?:read|cat|view|show)\s+(?:the\s+)?(?:file|document|contents?\s+of)\s+["\']?(\S+\.\w+)["\']?', tl)
    if rf: return _result("read_file", {"filepath": rf.group(1).strip()})

    # ---- SEARCH ----
    sf = re.search(r'(?:search|find|look\s*for|locate)\s+(?:files?\s+)?(?:named|called|matching|for)?\s*["\']?(.+?)["\']?\s*$', tl)
    if sf: return _result("search_files", {"pattern": sf.group(1).strip()})

    # ---- CREATE FOLDER ----
    cf = re.search(r'(?:create|make|new)\s+(?:a\s+)?(?:folder|directory)\s+(?:called|named|at)?\s*["\']?(.+?)["\']?\s*$', tl)
    if cf: return _result("create_folder", {"path": cf.group(1).strip()})

    # ---- EXECUTE COMMAND ----
    ec = re.search(r'(?:run|execute)\s+(?:the\s+)?(?:command|cmd|shell|powershell)\s*:?\s*["\']?(.+?)["\']?\s*$', tl)
    if ec: return _result("execute_command", {"command": ec.group(1).strip()})

    # ---- TYPE TEXT ----
    tt = re.search(r'(?:type|input|enter)\s+(?:the\s+)?(?:text\s+)?["\'](.+?)["\']', tl)
    if tt: return _result("type_text", {"text": tt.group(1)})

    # ---- HOTKEYS ----
    hk = re.search(r'(?:press|hit|tap)\s+(.+?)$', tl)
    if hk:
        keys = hk.group(1).strip().replace(' + ', '+').replace(' and ', '+')
        return _result("press_hotkeys", {"keys": keys})

    # ---- SHUTDOWN / RESTART / SLEEP / HIBERNATE / LOGOFF ----
    if re.search(r'\b(?:shutdown|shut\s+down|power\s+off|turn\s+off)\b.*(?:computer|pc|system|laptop)?', tl):
        return _result("execute_command", {"command": "shutdown /s /t 5"})
    if re.search(r'\b(?:restart|reboot)\b.*(?:computer|pc|system|laptop)?', tl):
        return _result("execute_command", {"command": "shutdown /r /t 5"})
    if re.search(r'\b(?:sleep|standby)\b.*(?:mode|computer|pc|system)?', tl) or tl == 'sleep':
        return _result("execute_command", {"command": "rundll32.exe powrprof.dll,SetSuspendState 0,1,0"})
    if re.search(r'\b(?:hibernate)\b', tl):
        return _result("execute_command", {"command": "shutdown /h"})
    if re.search(r'\b(?:log\s*off|sign\s*out|logout)\b', tl):
        return _result("execute_command", {"command": "shutdown /l"})

    # ---- FALLBACK: "open X" — try launching whatever the user says ----
    open_m = re.search(r'^(?:open|launch|start|run)\s+(?:the\s+)?(.+?)$', tl)
    if open_m:
        app_name = open_m.group(1).strip().rstrip('.')
        return _result("open_application", {"application": app_name})

    # No match
    return None


def _result(tool_name, args):
    """Build a standard direct match result."""
    return {
        "tool_to_call": tool_name,
        "tool_args": args,
        "decision": f"Direct: {tool_name}",
        "confidence": 0.95,
        "reasoning": f"Matched {tool_name}",
        "ethics_flag": "CLEAR",
        "ethics_reasoning": "Direct command"
    }


class HandlerUnit:
    def __init__(self, reasoning: ReasoningModule, actuator: Actuator, ethics_engine=None):
        self.reasoning = reasoning
        self.actuator = actuator
        self.ethics_engine = ethics_engine

    def decide_and_act(self, analyzed_state, current_step):
        # ⚡ INSTANT: Direct intent matching (covers 43+ tools)
        direct_match = match_direct_intent(current_step)
        if direct_match:
            tool_name = direct_match["tool_to_call"]
            args_display = {k: (v[:40]+'...' if isinstance(v,str) and len(v)>40 else v) for k,v in direct_match["tool_args"].items()}
            print(f"[Handler] ⚡ Instant match: {tool_name}({args_display})")
            
            if self.ethics_engine:
                ethics_verdict = self.ethics_engine.evaluate_action(direct_match)
                if not ethics_verdict.get("approved"):
                    print(f"[Handler] ⚖️  Blocked: {ethics_verdict.get('reason')}")
                    return {"status": "ethics_blocked", "output": f"Blocked: {ethics_verdict.get('reason')}",
                            "ethics_reason": ethics_verdict.get("reason",""), "ethics_flag": "BLOCKED"}
            
            return self.actuator.execute(direct_match)

        # Fallback to LLM
        print(f"[Handler] No direct match. Using LLM for: '{current_step}'")
        decision_result = self.reasoning.process_trigger(current_step, analyzed_state)
        if decision_result.get("ethics_flag") in ("REFUSE", "BLOCKED"):
            return {"status": "ethics_blocked", "output": decision_result.get("decision", "Blocked."),
                    "ethics_reason": decision_result.get("ethics_reasoning",""), "ethics_flag": decision_result["ethics_flag"]}
        return self.actuator.execute(decision_result)
