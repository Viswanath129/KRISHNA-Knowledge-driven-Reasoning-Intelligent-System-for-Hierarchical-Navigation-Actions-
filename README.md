# KRISHNA Agent Architecture

KRISHNA is an experimental research framework for studying the design and reliability of tool-using, multi-step AI agents.

This is a Python implementation of the **KRISHNA** (Kernel, Reasoning, Intelligence, State, Handler, Navigator, and Actuator) agent architecture based on the provided diagram.

## Components

- **K – Kernel (`kernel.py`):** Core Engine that manages the Agent Loop, dispatches events, and synchronizes the system.
- **R – Reasoning Module (`reasoning.py`):** Acts as the Logic Planner and Context Analyzer. Processes triggers using the LLM.
- **I – Intelligence Interface (`intelligence.py`):** The connectivity layer. Interfaces with cloud LLMs (e.g., Gemini), the knowledge base, and the tools registry.
- **S – State Manager (`state.py`):** Memory and Context. Maintains short-term memory, long-term storage, context variables, and goal tracking.
- **H – Handler Unit (`handler.py`):** Action Decision Hub. Bridges thought and action, consulting the reasoning module to decide on tasks.
- **N – Navigator (`navigator.py`):** Task & Workflow Manager. Handles the priority queue, multi-step planning, and error re-tasking.
- **A – Actuator (`actuator.py`):** Action Executor. Calls necessary tools, executes physical/digital tasks, and sends responses out.

## Live Loop

The system operates continuously through the following cycle:
1. **Observe (Input):** Perceiving environmental or user data.
2. **Analyze (K+R):** The Kernel and Reasoning module process observations.
3. **Decide (H):** The Handler unit chooses the specific step.
4. **Act (A):** The Actuator executes the operation.
5. **Update State (S):** The results/context are saved to memory.
6. **Repeat**

## How to Run

1. Make sure Python 3.x is installed.
2. Run the main orchestration file:
   ```bash
   python main.py
   ```
