import os
import json
import copy
import platform
from cli.output import renderer
from cli.tasks_manifest import LEETER_TASKS

VSCODE_KEYBINDINGS = [
    { "key": "ctrl+shift+r", "command": "workbench.action.tasks.runTask", "args": "Leeter: Run"    },
    { "key": "ctrl+shift+d", "command": "workbench.action.tasks.runTask", "args": "Leeter: Debug"  },
    { "key": "ctrl+shift+b", "command": "workbench.action.tasks.runTask", "args": "Leeter: Bench"  },
    { "key": "ctrl+shift+t", "command": "workbench.action.tasks.runTask", "args": "Leeter: Stress" },
    { "key": "ctrl+shift+p", "command": "workbench.action.tasks.runTask", "args": "Leeter: Replay" }
]

def map_task_to_vscode(task, bin_cmd):
    # VSCode requires type, options.cwd, presentation, group, problemMatcher
    label = task["label"]
    base_cmd = task["command"].replace("{bin}", bin_cmd)
    
    # Map the cwd
    if task["cwd"] == "$ZED_DIRNAME" or task["cwd"] == "problem_dir":
        cwd = "${fileDirname}"
    else:
        cwd = "${workspaceFolder}"
        
    vscode_task = {
        "label": label,
        "type": "shell",
        "command": base_cmd,
        "options": { "cwd": cwd },
        "problemMatcher": []
    }
    
    # Map reveal / presentation
    if task.get("use_new_terminal"):
        vscode_task["presentation"] = { "reveal": "always", "panel": "new" }
    else:
        vscode_task["presentation"] = { "reveal": "always", "panel": "shared", "clear": True }
        
    # Default build task for Run
    if label == "Leeter: Run":
        vscode_task["group"] = { "kind": "build", "isDefault": True }
        
    return vscode_task

def get_vscode_global_config_dir():
    sys = platform.system()
    if sys == "Darwin":
        return os.path.expanduser("~/Library/Application Support/Code/User")
    elif sys == "Windows":
        return os.path.expandvars(r"%APPDATA%\Code\User")
    else:
        return os.path.expanduser("~/.config/Code/User")

def setup_vscode(args, bin_cmd: str, merge_tasks, merge_keymap):
    scope = getattr(args, 'scope', 'project')
    if scope == 'global':
        renderer.print("[Warning] VSCode does not support global tasks. Falling back to project-local (.vscode/tasks.json).")
        
    target_dir = os.path.abspath(".vscode")
    tasks_file = os.path.join(target_dir, "tasks.json")
    
    # Prepare VSCode tasks
    vscode_tasks = [map_task_to_vscode(t, bin_cmd) for t in LEETER_TASKS]
    
    if getattr(args, 'dry_run', False):
        renderer.print(f"Would write to {tasks_file}:")
        renderer.print(json.dumps({ "version": "2.0.0", "tasks": vscode_tasks }, indent=4))
        if getattr(args, 'keybindings', False):
            kb_file = os.path.join(get_vscode_global_config_dir(), "keybindings.json")
            renderer.print(f"\nWould append to global {kb_file}:")
            renderer.print(json.dumps(VSCODE_KEYBINDINGS, indent=4))
        return
        
    os.makedirs(target_dir, exist_ok=True)
    
    # Read existing tasks.json
    existing_tasks = []
    tasks_version = "2.0.0"
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    if isinstance(existing_data, dict):
                        existing_tasks = existing_data.get("tasks", [])
                        tasks_version = existing_data.get("version", "2.0.0")
                    elif isinstance(existing_data, list):
                        existing_tasks = existing_data
        except Exception as e:
            renderer.print(f"Failed to read existing tasks.json: {e}")
            
    merged_tasks = merge_tasks(existing_tasks, vscode_tasks)
    
    with open(tasks_file, 'w') as f:
        json.dump({ "version": tasks_version, "tasks": merged_tasks }, f, indent=4)
    renderer.success(f"VSCode tasks written to {tasks_file}")
    
    # Global keybindings
    if getattr(args, 'keybindings', False):
        kb_dir = get_vscode_global_config_dir()
        kb_file = os.path.join(kb_dir, "keybindings.json")
        os.makedirs(kb_dir, exist_ok=True)
        
        existing_kb = []
        if os.path.exists(kb_file):
            try:
                # VSCode keybindings can have comments (JSONC), so this might fail.
                # A robust implementation would use a JSONC parser, but standard json works if clean.
                with open(kb_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        existing_kb = json.loads(content)
            except Exception as e:
                renderer.print(f"[Warning] Failed to parse existing keybindings.json (possibly contains comments): {e}")
                renderer.print("Skipping automatic keybindings merge.")
                existing_kb = None
                
        if existing_kb is not None:
            # Avoid complete duplicates based on key + command
            def is_duplicate(kb):
                for ekb in existing_kb:
                    if ekb.get("key") == kb["key"] and ekb.get("command") == kb["command"]:
                        return True
                return False
                
            for kb in VSCODE_KEYBINDINGS:
                if not is_duplicate(kb):
                    existing_kb.append(kb)
                    
            with open(kb_file, 'w') as f:
                json.dump(existing_kb, f, indent=4)
            renderer.success(f"VSCode keybindings written to {kb_file}")
