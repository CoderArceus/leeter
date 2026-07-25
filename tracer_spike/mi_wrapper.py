import subprocess
import platform
import os
import sys

def compile_target():
    print("Compiling target.cpp with -g -O0...")
    cmd = ["clang++", "-g", "-O0", "target.cpp", "-o", "target.out"]
    subprocess.run(cmd, check=True)

def parse_mi_output(stdout: str):
    """
    Dummy parser for MI stdout to demonstrate structure.
    In a real GDB/LLDB-MI setup, we'd use a robust MI parser library.
    """
    events = []
    lines = stdout.splitlines()
    for line in lines:
        if line.startswith('*stopped'):
            # Example parsing of *stopped event
            events.append({"event": "stopped", "raw": line})
        elif line.startswith('^done'):
            events.append({"event": "done", "raw": line})
    return events

def run_debugger():
    sys_name = platform.system()
    if sys_name == "Darwin":
        # macOS: try lldb-mi or lldb --interpreter=mi
        print("Detected macOS. Attempting to use LLDB MI...")
        debugger_cmd = ["lldb", "target.out", "--interpreter=mi"]
    elif sys_name == "Windows":
        print("Detected Windows. Attempting to use GDB MI...")
        debugger_cmd = ["gdb", "--interpreter=mi", "target.out"]
    else:
        print("Detected Linux. Attempting to use GDB MI...")
        debugger_cmd = ["gdb", "--interpreter=mi", "target.out"]

    print(f"Spawning: {' '.join(debugger_cmd)}")
    
    try:
        proc = subprocess.Popen(
            debugger_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        print(f"ERROR: Debugger executable '{debugger_cmd[0]}' not found.")
        sys.exit(1)

    # We send MI commands
    commands = [
        "-break-insert main\n",
        "-exec-run\n",
        "-exec-next\n",
        "-stack-list-variables --print-values\n",
        "-gdb-exit\n"
    ]

    for cmd in commands:
        proc.stdin.write(cmd)
    
    proc.stdin.flush()
    
    stdout, stderr = proc.communicate()
    
    if proc.returncode != 0:
        print(f"\nDebugger exited with error code {proc.returncode}")
        if "unknown option: --interpreter=mi" in stderr:
            print("\nCRITICAL FAILURE: LLDB on macOS does not support --interpreter=mi.")
            print("Apple removed lldb-mi from Xcode tools.")
            print("MI-based tracing is unfeasible out-of-the-box on macOS.")
        else:
            print(f"Stderr:\n{stderr}")
        sys.exit(1)

    print("\nDebugger completed successfully. MI Output snippet:")
    print(stdout[:500] + "...\n")
    
    events = parse_mi_output(stdout)
    print(f"Parsed {len(events)} MI events.")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    compile_target()
    run_debugger()
