"""
Intentionally vulnerable sample file for SAST benchmark testing.
Contains patterns guaranteed to trigger Bandit (exec, os.system).
"""
import os

def unsafe_exec(user_input: str):
    # Triggers Bandit B102: exec_used
    exec(user_input)

def unsafe_system(cmd: str):
    # Triggers Bandit B605/B602: start_process_with_a_shell / os_system
    os.system(cmd)
