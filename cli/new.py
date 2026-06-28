import os
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
        
    renderer.success(f"Created {folder_name}/")
