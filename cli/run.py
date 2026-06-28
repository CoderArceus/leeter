import os
import sys
import json
from cli.output import renderer
from cli.analyzer import run_pipeline_unified
from cli.runners.function import FunctionRunner
from cli.runners.stateful_class import StatefulClassRunner
from cli.build import compile_release, execute_with_timeout

def cmd_run(args):
    problem_dir = args.problem
    sol_path = os.path.join(problem_dir, "solution.cpp")
    
    if not os.path.exists(sol_path):
        renderer.error(f"{sol_path} not found.")
        sys.exit(1)
        
    with open(sol_path, 'r') as f:
        stub = f.read()
        
    renderer.print("Analyzing...")
    ir, signals = run_pipeline_unified(stub)
    
    pjson_path = os.path.join(problem_dir, "problem.json")
    if os.path.exists(pjson_path):
        with open(pjson_path, 'r') as f:
            existing_data = json.load(f)
        ir_dict = ir.to_dict()
        existing_data["function"] = ir_dict.get("function")
        existing_data["runner"] = ir_dict.get("runner")
        existing_data["imports"] = ir_dict.get("imports")
        with open(pjson_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
    else:
        with open(pjson_path, 'w') as f:
            json.dump(ir.to_dict(), f, indent=2)
        
    if ir.runner == "function":
        renderer.print("Generating driver...")
        runner = FunctionRunner()
    elif ir.runner == "stateful_class":
        renderer.print("Generating stateful driver...")
        runner = StatefulClassRunner()
    else:
        renderer.error(f"Runner {ir.runner} not implemented yet.")
        sys.exit(1)
        
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    driver_code = runner.generate(ir, include_path=include_path)
    
    os.makedirs(os.path.join(problem_dir, "build"), exist_ok=True)
    driver_path = os.path.join(problem_dir, "build", "driver.cpp")
    
    with open(driver_path, 'w') as f:
        f.write(driver_code)
        
    if not getattr(args, 'no_compile', False):
        success = compile_release(problem_dir)
    else:
        success = True
        
    if success:
        execute_with_timeout(problem_dir, getattr(args, 'timeout', 5))
        from cli.storage import mark_problem_solved
        mark_problem_solved(problem_dir)
