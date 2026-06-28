import os
import sys
import subprocess
import platform

def get_clipboard():
    sys_name = platform.system()
    if sys_name == 'Darwin':
        return subprocess.run(['pbpaste'], capture_output=True, text=True).stdout
    elif sys_name == 'Linux':
        try:
            return subprocess.run(['xclip', '-o', '-selection', 'clipboard'], capture_output=True, text=True).stdout
        except FileNotFoundError:
            try:
                return subprocess.run(['xsel', '-o', '-b'], capture_output=True, text=True).stdout
            except FileNotFoundError:
                print("Error: Neither xclip nor xsel is installed.")
                sys.exit(1)
    else:
        print(f"Error: Unsupported OS {sys_name}")
        sys.exit(1)

def cmd_paste(args):
    problem_dir = args.problem
    if not os.path.exists(problem_dir):
        print(f"Error: {problem_dir} does not exist.")
        sys.exit(1)
        
    clipboard_text = get_clipboard()
    if not clipboard_text:
        print("Clipboard is empty.")
        return
        
    # LeetCode inputs are usually bracketed arrays or strings.
    # The clipboard text can be dumped right into input.txt
    
    input_path = os.path.join(problem_dir, "input.txt")
    with open(input_path, "w") as f:
        f.write(clipboard_text.strip() + "\n")
        
    print(f"Pasted clipboard contents into {input_path}")
