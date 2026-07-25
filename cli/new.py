import os
import json
from cli.output import renderer

def cmd_new(args):
    if not getattr(args, 'name', None):
        name = input("Problem name: ")
        diff = input("Difficulty [easy/medium/hard]: ")
        runner_type = input("Runner [function/stateful/interactive]: ")
        args.name = name
        args.difficulty = diff
        args.runner = runner_type
        
    folder_name = "problems/" + args.name.replace(" ", "_").lower()
    if getattr(args, 'id', None):
        folder_name = f"problems/{args.id}_" + args.name.replace(" ", "_").lower()
        
    os.makedirs(folder_name, exist_ok=True)
    sol_path = os.path.join(folder_name, "solution.cpp")
    if not os.path.exists(sol_path):
        with open(sol_path, 'w') as f:
            f.write("class Solution {\npublic:\n    // Add your code here\n};\n")
    
    input_path = os.path.join(folder_name, "input.txt")
    if not os.path.exists(input_path):
        open(input_path, 'w').close()

    # Create problem.json so the folder is recognized by the rest of the framework
    pjson_path = os.path.join(folder_name, "problem.json")
    if not os.path.exists(pjson_path):
        problem_data = {
            "id": getattr(args, 'id', 0) or 0,
            "title": args.name,
            "difficulty": getattr(args, 'difficulty', 'medium') or 'medium',
            "runner": getattr(args, 'runner', 'function') or 'function',
            "solved": False,
            "framework_version": 2,
        }
        with open(pjson_path, 'w') as f:
            json.dump(problem_data, f, indent=2)

    renderer.success(f"Created {folder_name}/")
