import os
import json
import copy
from cli.output import renderer
from cli.tasks_manifest import LEETER_TASKS, ZED_KEYMAP

def setup_zed(args, bin_cmd: str, merge_tasks, merge_keymap):
    tasks_to_write = copy.deepcopy(LEETER_TASKS)
    for task in tasks_to_write:
        task["command"] = task["command"].replace("{bin}", bin_cmd)
        
    scope = getattr(args, 'scope', 'project')
    if scope == 'global':
        target_dir = os.path.expanduser("~/.config/zed")
    else:
        target_dir = os.path.abspath(".zed")
        
    tasks_file = os.path.join(target_dir, "tasks.json")
    keymap_file = os.path.join(target_dir, "keymap.json")
    
    if getattr(args, 'dry_run', False):
        renderer.print(f"Would write to {tasks_file}:")
        renderer.print(json.dumps(tasks_to_write, indent=4))
        if getattr(args, 'keybindings', False):
            renderer.print(f"\nWould write to {keymap_file}:")
            renderer.print(json.dumps(ZED_KEYMAP, indent=4))
        return
        
    os.makedirs(target_dir, exist_ok=True)
    
    existing_tasks = []
    if os.path.exists(tasks_file):
        try:
            with open(tasks_file, 'r') as f:
                content = f.read().strip()
                if content:
                    existing_tasks = json.loads(content)
                    if not isinstance(existing_tasks, list):
                        existing_tasks = [existing_tasks]
        except Exception as e:
            renderer.print(f"Failed to read existing tasks.json: {e}")
            existing_tasks = []
            
    merged_tasks = merge_tasks(existing_tasks, tasks_to_write)
    
    with open(tasks_file, 'w') as f:
        json.dump(merged_tasks, f, indent=4)
    renderer.success(f"Zed tasks written to {tasks_file}")
    
    if getattr(args, 'keybindings', False):
        existing_keymap = []
        if os.path.exists(keymap_file):
            try:
                with open(keymap_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        existing_keymap = json.loads(content)
            except Exception as e:
                renderer.print(f"Failed to read existing keymap.json: {e}")
                
        merged_keymap = merge_keymap(existing_keymap, ZED_KEYMAP)
        
        with open(keymap_file, 'w') as f:
            json.dump(merged_keymap, f, indent=4)
        renderer.success(f"Zed keybindings written to {keymap_file}")
