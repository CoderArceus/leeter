import os
import sys
import subprocess

def cmd_note(args):
    problem_dir = args.problem
    readme_path = os.path.join(problem_dir, "README.md")
    
    if not os.path.exists(readme_path):
        print(f"Error: {readme_path} not found.")
        sys.exit(1)
        
    print(f"Opening {readme_path} in Zed...")
    try:
        # Assuming `zed` is in PATH. If not, this might fail, but it's what the spec requires.
        subprocess.run(["zed", readme_path], check=True)
    except FileNotFoundError:
        print("Error: 'zed' command not found in PATH.")
    except Exception as e:
        print(f"Failed to open Zed: {e}")
