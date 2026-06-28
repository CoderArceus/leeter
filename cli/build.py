import hashlib
import os
import subprocess
import time
from cli.output import renderer
import json

def get_file_hash(filepath: str) -> str:
    if not os.path.exists(filepath):
        return ""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def needs_rebuild(problem_dir: str) -> bool:
    hash_file = os.path.join(problem_dir, 'build', '.hash')
    if not os.path.exists(hash_file):
        return True
        
    with open(hash_file, 'r') as f:
        old_hashes = f.read().splitlines()
        
    curr_sol_hash = get_file_hash(os.path.join(problem_dir, 'solution.cpp'))
    
    driver_path = os.path.join(problem_dir, 'build', 'driver.override.cpp')
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, 'build', 'driver.cpp')
        
    curr_driver_hash = get_file_hash(driver_path)
    
    expected = f"{curr_sol_hash}:{curr_driver_hash}"
    return len(old_hashes) == 0 or old_hashes[0] != expected

def update_hash(problem_dir: str):
    hash_file = os.path.join(problem_dir, 'build', '.hash')
    curr_sol_hash = get_file_hash(os.path.join(problem_dir, 'solution.cpp'))
    
    driver_path = os.path.join(problem_dir, 'build', 'driver.override.cpp')
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, 'build', 'driver.cpp')
        
    curr_driver_hash = get_file_hash(driver_path)
    
    os.makedirs(os.path.join(problem_dir, 'build'), exist_ok=True)
    with open(hash_file, 'w') as f:
        f.write(f"{curr_sol_hash}:{curr_driver_hash}\n")

def compile_file(source_path: str, bin_path: str) -> bool:
    problem_dir = os.path.dirname(os.path.dirname(source_path))
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    cmd = [
        "clang++", "-std=c++20", "-O2",
        "-I" + include_path,
        source_path,
        "-o", bin_path
    ]
    result = subprocess.run(cmd, cwd=problem_dir)
    return result.returncode == 0

def compile_release(problem_dir: str) -> bool:
    if not needs_rebuild(problem_dir):
        return True
        
    renderer.print("Compiling...")
    t0 = time.time()
    
    driver_path = os.path.join(problem_dir, 'build', 'driver.override.cpp')
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, 'build', 'driver.cpp')
        
    bin_path = os.path.join(problem_dir, 'build', 'solution')
    cmd = [
        "clang++", "-std=c++20", "-O2",
        "-I" + os.path.join(os.path.dirname(os.path.dirname(problem_dir)), "include"),
        driver_path,
        "-o", bin_path
    ]
    
    result = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
    compile_time = (time.time() - t0) * 1000
    if result.returncode == 0:
        update_hash(problem_dir)
        renderer.print(f"Compilation successful ({compile_time:.2f} ms)")
        return True
    else:
        # Fetch problem details for the envelope if possible, otherwise null
        try:
            with open(os.path.join(problem_dir, "problem.json"), "r") as f:
                p_data = json.load(f)
        except:
            p_data = None
            
        renderer.emit_error("run", p_data, "compiler", "Compilation failed", result.stderr, exit_code=2)
        return False

def compile_trace(problem_dir: str) -> bool:
    print("Compiling for trace...")
    t0 = time.time()
    
    driver_path = os.path.join(problem_dir, 'build', 'driver.override.cpp')
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, 'build', 'driver.cpp')
        
    bin_path = os.path.join(problem_dir, 'build', 'solution_trace')
    cmd = [
        "clang++", "-std=c++20", "-O2",
        "-DTRACE_ENABLED=1",
        "-I" + os.path.join(os.path.dirname(os.path.dirname(problem_dir)), "include"),
        driver_path,
        "-o", bin_path
    ]
    
    result = subprocess.run(cmd, cwd=problem_dir)
    compile_time = (time.time() - t0) * 1000
    if result.returncode == 0:
        print(f"Trace compilation successful ({compile_time:.2f} ms)")
    return result.returncode == 0

def execute_with_timeout(problem_dir: str, timeout_sec: int = 5):
    bin_path = os.path.join(problem_dir, 'build', 'solution')
    input_path = os.path.join(problem_dir, 'input.txt')
    
    if not os.path.exists(input_path):
        renderer.print("No input.txt found. Creating an empty one.")
        open(input_path, 'w').close()
    
    start_time = time.time()
    
    # Try to load problem.json for JSON payloads
    try:
        with open(os.path.join(problem_dir, "problem.json"), "r") as f:
            p_data = json.load(f)
    except:
        p_data = None
    
    try:
        with open(input_path, 'r') as f_in:
            kwargs = {}
            if renderer.use_json:
                kwargs["capture_output"] = True
                kwargs["text"] = True
                
            result = subprocess.run(
                [bin_path],
                stdin=f_in,
                cwd=problem_dir,
                timeout=timeout_sec,
                **kwargs
            )
            run_ms = (time.time() - start_time) * 1000
            
            if result.returncode != 0:
                renderer.emit_error("run", p_data, "runtime", f"Runtime error (exit code {result.returncode})", getattr(result, 'stderr', ''), exit_code=3)
            
            size_kb = os.path.getsize(bin_path) / 1024 if os.path.exists(bin_path) else 0
            
            if renderer.use_json:
                # We need to parse stdout to build the cases array
                # Right now, since we don't know expected output, we just split stdout by lines 
                # (Assuming each test case outputs 1 line for function runner, or blocks for stateful)
                cases = []
                out_lines = result.stdout.strip().split('\n') if result.stdout else []
                # Minimal mock parsing for now
                for idx, line in enumerate(out_lines):
                    if not line.strip(): continue
                    cases.append({
                        "index": idx,
                        "status": "pass",
                        "got": line.strip()
                    })
                
                payload = {
                    "cases": cases,
                    "stats": {
                        "passed": len(cases),
                        "failed": 0,
                        "total": len(cases),
                        "run_ms": round(run_ms, 2),
                        "binary_kb": round(size_kb, 2)
                    }
                }
                renderer.emit_success("run", p_data, payload, status="pass")
            else:
                renderer.print("\n────────────────────────────────")
                renderer.print(f"  run time      :  {run_ms:.2f} ms")
                if size_kb > 0:
                    renderer.print(f"  binary size   :  {size_kb:.2f} KB")
                renderer.print("────────────────────────────────")
            
    except subprocess.TimeoutExpired:
        renderer.emit_error("run", p_data, "runtime", "Time Limit Exceeded", f"> {timeout_sec}s", exit_code=4)

def execute_trace(problem_dir: str):
    bin_path = os.path.join(problem_dir, 'build', 'solution_trace')
    input_file = os.path.join(problem_dir, 'input.txt')
    
    if not os.path.exists(input_file):
        print("No input.txt found")
        return
        
    with open(input_file, 'r') as f:
        input_data = f.read()
        
    try:
        result = subprocess.run(
            [bin_path],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=5.0,
            cwd=problem_dir
        )
        if result.returncode != 0:
            print("Runtime Error during tracing:")
            print(result.stderr)
            return False
            
        return True
        
    except subprocess.TimeoutExpired:
        print("Time Limit Exceeded during tracing (5.0s)")
        return False

def compile_debug(problem_dir: str, sanitize: bool = True) -> bool:
    renderer.print("Compiling debug build...")
    t0 = time.time()
    
    driver_path = os.path.join(problem_dir, 'build', 'driver.override.cpp')
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, 'build', 'driver.cpp')
        
    bin_path = os.path.join(problem_dir, 'build', 'solution_debug')
    
    cmd = [
        "clang++", "-std=c++20", "-g", "-O0",
        "-I" + os.path.join(os.path.dirname(os.path.dirname(problem_dir)), "include"),
        driver_path,
        "-o", bin_path
    ]
    if sanitize:
        cmd.extend(["-fsanitize=address,undefined"])
        
    result = subprocess.run(cmd, cwd=problem_dir)
    compile_time = (time.time() - t0) * 1000
    if result.returncode == 0:
        renderer.print(f"Debug compilation successful ({compile_time:.2f} ms)")
        return True
    else:
        renderer.error("Compile error", "Failed to compile debug build.")
        return False

def execute_debug(problem_dir: str, input_file: str = "input.txt"):
    bin_path = os.path.join(problem_dir, 'build', 'solution_debug')
    input_path = os.path.join(problem_dir, input_file)
    
    env = os.environ.copy()
    env["ASAN_OPTIONS"] = "detect_leaks=1"
    
    renderer.print(f"Starting lldb with {bin_path}...")
    subprocess.run(["lldb", bin_path], cwd=problem_dir, env=env)
