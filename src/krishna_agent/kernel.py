import time
import asyncio
import concurrent.futures
from .state import StateManager
from .navigator import Navigator
from .handler import HandlerUnit

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

class Kernel:
    def __init__(self, state: StateManager, navigator: Navigator, handler: HandlerUnit, ethics_engine=None):
        self.state = state
        self.navigator = navigator
        self.handler = handler
        self.ethics_engine = ethics_engine
        self.is_running = False
        self.pending_goals = []
        # Task tracking for UI timeline
        self.task_results = []  # [{name, tool, status, result, time}]
        self._task_id = 0
        # Callbacks for god mode reactions
        self.on_task_complete = None
        self.on_task_failed = None
        self.on_task_blocked = None

    async def start_loop(self):
        self.is_running = True
        self._was_idle = False
        print("[Kernel] Starting Asynchronous Agent Loop Manager...")
        if self.ethics_engine:
            print("[Kernel] Ethics Engine is ACTIVE. All actions will be ethically evaluated.")
        
        while self.is_running:
            try:
                while self.pending_goals:
                    goal = self.pending_goals.pop(0)
                    self.receive_input(goal)
                
                if self.navigator.priority_queue:
                    self._was_idle = False
                    await self._loop_tick()
                else:
                    if not self._was_idle:
                        dharma = ""
                        if self.ethics_engine:
                            dharma = f" Dharma Score: {self.ethics_engine.get_dharma_score()}/100"
                        print(f"[Kernel] Goal achieved or no tasks left. System is idle.{dharma}")
                        self._was_idle = True
            except Exception as e:
                import traceback
                print(f"[Kernel] Critical error: {e}")
                traceback.print_exc()

            await asyncio.sleep(0.1)

    async def _loop_tick(self):
        print("\n=== Active Agent Cycle ===")
        
        observation = self.state.short_term_memory[-1] if self.state.short_term_memory else "No recent input"
        print(f"[Kernel] Event Dispatcher observed: {observation}")
        context = self.state.get_context()
        
        while True:
            next_step = self.navigator.get_next_step()
            if not next_step:
                break
            
            if next_step.startswith("[ETHICS BLOCK]"):
                print(f"[Kernel] {next_step}")
                self._add_task(next_step, "", "blocked", next_step)
                self.state.update_state(observation=next_step, result={"status": "ethics_blocked", "output": next_step})
                continue

            print(f"[Kernel] ⚙️ Processing: {next_step}")
            
            # Track task as running
            tid = self._add_task(next_step, "", "running", "")
            
            # Run handler in thread pool so we don't block the async event loop
            # This allows SSE logs to stream in real-time during execution
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(_executor, self.handler.decide_and_act, context, next_step)
            
            # Extract tool name from result
            tool_name = result.get("tool_used") or result.get("tool_to_call") or ""
            
            if result.get("status") == "ethics_blocked":
                print(f"[Kernel] 🚫 Action ethically blocked: {result.get('output')}")
                self._update_task(tid, tool_name, "blocked", result.get('output', 'Ethics blocked'))
                if self.on_task_blocked:
                    self.on_task_blocked()
            elif result.get("status") == "error":
                print(f"[Kernel] ❌ Task failed: {result.get('output', '')[:100]}")
                self._update_task(tid, tool_name, "error", result.get('output', 'Failed')[:100])
                self.navigator.handle_error(f"Failed {next_step}: {result}")
                if self.on_task_failed:
                    self.on_task_failed()
            else:
                output = result.get('output', '')[:100]
                print(f"[Kernel] ✅ Task completed: {tool_name} → {output}")
                self._update_task(tid, tool_name, "done", output)
                if self.on_task_complete:
                    self.on_task_complete(next_step, tool_name)
            
            self.state.update_state(observation=next_step, result=result)
            await asyncio.sleep(0)  # yield to event loop for SSE delivery

    def _add_task(self, name, tool, status, result):
        self._task_id += 1
        t = time.strftime("%H:%M:%S")
        self.task_results.append({
            "id": self._task_id,
            "name": name,
            "tool": tool,
            "status": status,
            "result": result,
            "time": t
        })
        # Keep last 200 tasks (increased from 50 to prevent UI data loss)
        if len(self.task_results) > 200:
            self.task_results = self.task_results[-200:]
        return self._task_id

    def _update_task(self, tid, tool, status, result):
        for t in self.task_results:
            if t["id"] == tid:
                if tool: t["tool"] = tool
                t["status"] = status
                t["result"] = result
                t["time"] = time.strftime("%H:%M:%S")
                break

    def get_task_results(self):
        return list(self.task_results)

    def receive_input(self, data):
        print(f"[Kernel] Received asynchronous event: {data}")
        self.state.update_state(observation=data)
        self.navigator.set_goal(data)

    def stop_loop(self):
        self.is_running = False
