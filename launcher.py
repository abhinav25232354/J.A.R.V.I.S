import subprocess # Executing multiple processes simoutenously
import os # Locating Input and Execution task terminals
import sys

open("task.txt", "w").close()
# input_path = os.path.abspath("F:/AI Assistant (Jarvis)/Development_Chamber(Testing and Debugging)/project/input_terminal.py")
input_path = os.path.abspath("F:/AI Assistant (Jarvis)/main.py")
task_path = os.path.abspath("F:/AI Assistant (Jarvis)/task_terminal.py")
system_monitoring = os.path.abspath("F:/AI Assistant (Jarvis)/System_monitor_system.py")
maintaining_history = os.path.abspath("F:/AI Assistant (Jarvis)/active_window_monitoring.py")

subprocess.Popen(f'start cmd /k python "{task_path}"', shell=True) # Execution Task Terminal 
subprocess.Popen(f'start cmd /k python "{input_path}"', shell=True) # Input Task Terminal
# subprocess.Popen(f'start cmd /k python "{system_monitoring}"', shell=True)
# maintaining_history = os.path.abspath("F:/AI Assistant (Jarvis)/active_window_monitoring.py")

# High GPU Tasks

# subprocess.Popen(
#     [sys.executable, maintaining_history],
#     creationflags=subprocess.CREATE_NO_WINDOW
# )
# subprocess.Popen(
#     [sys.executable, system_monitoring],
#     creationflags=subprocess.CREATE_NO_WINDOW
# )