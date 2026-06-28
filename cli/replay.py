import os
import sys
import json

def cmd_replay(args):
    problem_dir = args.problem
    
    from cli.analyzer import run_pipeline_unified
    from cli.runners.function import FunctionRunner
    from cli.runners.stateful_class import StatefulClassRunner
    from cli.build import compile_trace, execute_trace
    
    sol_path = os.path.join(problem_dir, "solution.cpp")
    if not os.path.exists(sol_path):
        print(f"Error: {sol_path} not found.")
        sys.exit(1)
        
    with open(sol_path, 'r') as f:
        stub = f.read()
        
    print("Preparing replay...")
    ir, _ = run_pipeline_unified(stub)
    
    if ir.runner == "function":
        runner = FunctionRunner()
    elif ir.runner == "stateful_class":
        runner = StatefulClassRunner()
    else:
        print(f"Runner {ir.runner} not supported for replay.")
        sys.exit(1)
        
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    driver_code = runner.generate(ir, include_path=include_path)
    
    os.makedirs(os.path.join(problem_dir, "build"), exist_ok=True)
    driver_path = os.path.join(problem_dir, "build", "driver.cpp")
    with open(driver_path, 'w') as f:
        f.write(driver_code)
        
    if not compile_trace(problem_dir):
        sys.exit(1)
        
    if not execute_trace(problem_dir):
        sys.exit(1)
        
    trace_path = os.path.join(problem_dir, "build", "trace.json")
    if not os.path.exists(trace_path):
        print(f"Error: No trace generated. Did you use the SNAPSHOT() macro?")
        sys.exit(1)
        
    try:
        with open(trace_path, 'r') as f:
            trace = json.load(f)
    except Exception as e:
        print(f"Error reading trace file: {e}")
        sys.exit(1)
        
    print(f"\n--- Replay for {os.path.basename(problem_dir)} ---")
    
    for idx, event in enumerate(trace):
        os.system('clear' if os.name == 'posix' else 'cls')
        print(f"=== Step {idx + 1}/{len(trace)} ===")
        
        etype = event.get("type")
        if etype == "method_call":
            method = event.get("method")
            args_arr = event.get("args", [])
            args_str = ", ".join(json.dumps(a) if not isinstance(a, str) else str(a) for a in args_arr)
            print(f"\n➔ {method}({args_str})")
            
        elif etype == "method_return":
            ret = event.get("return")
            ret_str = json.dumps(ret) if not isinstance(ret, str) else str(ret)
            print(f"\n↩ return: {ret_str}")
            
        elif etype == "snapshot":
            cls = event.get("class", "Unknown")
            data = event.get("data")
            print(f"\n[State: {cls}]")
            if isinstance(data, dict):
                for k, v in data.items():
                    val_str = json.dumps(v) if not isinstance(v, str) else str(v)
                    print(f"  {k}: {val_str}")
            elif isinstance(data, list):
                val_str = json.dumps(data) if not isinstance(data, str) else str(data)
                print(f"  {val_str}")
            else:
                val_str = json.dumps(data) if not isinstance(data, str) else str(data)
                print(f"  {val_str}")
                
        elif etype == "user_snapshot":
            line = event.get("line")
            names = [n.strip() for n in event.get("names", "").split(",")]
            values = event.get("values", [])
            print(f"\n[Snapshot @ Line {line}]")
            for n, v in zip(names, values):
                val_str = json.dumps(v, indent=2) if isinstance(v, (dict, list)) else str(v)
                print(f"  {n} = {val_str}")
        else:
            print(f"\nUnknown event: {event}")
            
        print("\n[Press Enter to step, q to quit]")
        try:
            cmd = input()
            if cmd.strip().lower() == 'q':
                break
        except (KeyboardInterrupt, EOFError):
            break
            
    print("\n--- End of Replay ---")
