import asyncio
import datetime
import os

from src.krishna_agent.state import StateManager
from src.krishna_agent.intelligence import IntelligenceInterface
from src.krishna_agent.reasoning import ReasoningModule
from src.krishna_agent.navigator import Navigator
from src.krishna_agent.actuator import Actuator
from src.krishna_agent.handler import HandlerUnit
from src.krishna_agent.kernel import Kernel
from src.krishna_agent.ethics_engine import EthicsEngine

# --- Tools ---
import subprocess
import webbrowser
import platform


def tool_open_application(**kwargs):
    app_name = kwargs.get('application') or kwargs.get('app') or kwargs.get('name')
    if not app_name:
        return "Error: Missing 'application' argument."
    app_map = {
        "notepad": "notepad.exe", "calculator": "calc.exe", "calc": "calc.exe",
        "chrome": "chrome.exe", "explorer": "explorer.exe", "paint": "mspaint.exe",
    }
    exe = app_map.get(app_name.lower(), app_name)
    try:
        subprocess.Popen(exe, shell=True)
        return f"Success: Opened '{app_name}'"
    except Exception as e:
        return f"Error: {e}"


def tool_open_url(**kwargs):
    url = kwargs.get('url') or kwargs.get('link')
    if not url:
        return "Error: Missing 'url' argument."
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    webbrowser.open(url)
    return f"Success: Opened '{url}'"


def tool_list_files(**kwargs):
    directory = kwargs.get('directory') or kwargs.get('path') or os.getcwd()
    try:
        items = os.listdir(directory)
        return f"Contents of '{directory}':\n" + "\n".join(f"  {'📁' if os.path.isdir(os.path.join(directory, i)) else '📄'} {i}" for i in sorted(items))
    except Exception as e:
        return f"Error: {e}"


def tool_get_current_time(**kwargs):
    return f"Current time: {datetime.datetime.now().strftime('%A, %B %d, %Y at %I:%M:%S %p')}"


def tool_get_system_info(**kwargs):
    return f"OS: {platform.system()} {platform.release()}, Machine: {platform.machine()}, Processor: {platform.processor()}"


async def main():
    print("Welcome to the KRISHNA AI Ethics Agent (LOCAL LLM)\n")
    print("Initializing components...")
    
    state = StateManager()
    intelligence = IntelligenceInterface()
    
    intelligence.register_tool("open_application", tool_open_application, "Opens an app by name (e.g. 'notepad', 'chrome').")
    intelligence.register_tool("open_url", tool_open_url, "Opens a URL in the browser. Provide 'url'.")
    intelligence.register_tool("list_files", tool_list_files, "Lists files in a directory. Provide 'directory'.")
    intelligence.register_tool("get_time", tool_get_current_time, "Returns the current time.")
    intelligence.register_tool("get_system_info", tool_get_system_info, "Returns system info.")
    
    ethics = EthicsEngine(intelligence=intelligence)
    reasoning = ReasoningModule(intelligence, ethics_engine=ethics)
    actuator = Actuator(intelligence, ethics_engine=ethics)
    navigator = Navigator(intelligence, ethics_engine=ethics)
    handler = HandlerUnit(reasoning, actuator, ethics_engine=ethics)
    kernel = Kernel(state, navigator, handler, ethics_engine=ethics)
    
    print("Agent is ready. LOCAL LLM + Ethics Engine ACTIVE.")
    print("-" * 30)
    
    goal = "Open notepad and then tell me the current time."
    print(f"\n[User Goal Trigger]: {goal}\n")
    
    kernel.receive_input(goal)
    await kernel.start_loop()

if __name__ == "__main__":
    asyncio.run(main())
