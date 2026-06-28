import os
import sys
import json
import time
import subprocess
import random

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.models import ProblemIR, CppType, Primitive, Vector, Pointer
from cli.runners.function import FunctionRunner, to_cpp_type
from cli.build import compile_file, execute_with_timeout
from cli.output import renderer

def generate_random_expr(t: CppType) -> str:
    if isinstance(t, Primitive):
        if t.name in ("int", "long long"):
            return "(-50 + rand() % 100)"
        elif t.name == "double":
            return "(rand() / (double)RAND_MAX)"
        elif t.name == "bool":
            return "(rand() % 2 == 0)"
        elif t.name == "string":
            return 'randomString(5 + rand() % 15, "abcdefghijklmnopqrstuvwxyz")'
        elif t.name == "char":
            return "(char)('a' + rand() % 26)"
    elif isinstance(t, Vector):
        if isinstance(t.inner, Primitive) and t.inner.name in ("int", "long long"):
            return "randomVector(5 + rand() % 15, -50, 50)"
        if isinstance(t.inner, Vector) and isinstance(t.inner.inner, Primitive) and t.inner.inner.name in ("int", "long long"):
            return "randomMatrix(5 + rand() % 10, 5 + rand() % 10, -50, 50)"
        return f"vector<{to_cpp_type(t.inner)}>()"
    elif isinstance(t, Pointer):
        if t.name == "TreeNode*":
            return "randomTree(1 + rand() % 20, -50, 50)"
        elif t.name == "ListNode*":
            return "randomLinkedList(1 + rand() % 20, -50, 50)"
    return f"{to_cpp_type(t)}()"

def generate_gen_cpp(ir: ProblemIR, include_path: str) -> str:
    lines = []
    lines.append(f'#include "{include_path}/lc.h"')
    lines.append('int main(int argc, char** argv) {')
    lines.append('    if (argc > 1) srand(atoi(argv[1]));')
    lines.append('    else srand(time(NULL));')
    for i, param in enumerate(ir.function.parameters):
        expr = generate_random_expr(param.type)
        lines.append(f'    auto p{i} = {expr};')
        lines.append(f'    print(p{i});')
    lines.append('    return 0;')
    lines.append('}')
    return "\n".join(lines) + "\n"

def cmd_stress(args):
    problem_dir = args.problem
    if not os.path.exists(os.path.join(problem_dir, "problem.json")):
        renderer.emit_error("stress", None, "fs", f"problem.json not found in {problem_dir}", exit_code=5)
        
    with open(os.path.join(problem_dir, "problem.json"), "r") as f:
        problem_data = json.load(f)
        ir = ProblemIR.from_dict(problem_data)
        
    if ir.runner != "function":
        renderer.emit_error("stress", problem_data, "runner", "Stress testing is only supported for function runners.", exit_code=5)
        
    brute_path = os.path.join(problem_dir, "brute.cpp")
    if not os.path.exists(brute_path):
        renderer.emit_error("stress", problem_data, "fs", f"brute.cpp not found in {problem_dir}", exit_code=5)
        
    renderer.print("Generating stress drivers...")
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    
    runner = FunctionRunner()
    sol_driver_code = runner.generate(ir, include_path=include_path, solution_file="solution.cpp")
    brute_driver_code = runner.generate(ir, include_path=include_path, solution_file="brute.cpp")
    gen_code = generate_gen_cpp(ir, include_path=include_path)
    
    build_dir = os.path.join(problem_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    with open(os.path.join(build_dir, "sol_driver.cpp"), "w") as f: f.write(sol_driver_code)
    with open(os.path.join(build_dir, "brute_driver.cpp"), "w") as f: f.write(brute_driver_code)
    with open(os.path.join(build_dir, "gen.cpp"), "w") as f: f.write(gen_code)
    
    renderer.print("Compiling sol, brute, and gen binaries...")
    if not compile_file(os.path.join(build_dir, "sol_driver.cpp"), os.path.join(build_dir, "sol.out")):
        renderer.emit_error("stress", problem_data, "compiler", "Compilation of solution failed.", exit_code=2)
    if not compile_file(os.path.join(build_dir, "brute_driver.cpp"), os.path.join(build_dir, "brute.out")):
        renderer.emit_error("stress", problem_data, "compiler", "Compilation of brute failed.", exit_code=2)
    if not compile_file(os.path.join(build_dir, "gen.cpp"), os.path.join(build_dir, "gen.out")):
        renderer.emit_error("stress", problem_data, "compiler", "Compilation of generator failed.", exit_code=2)
        
    iters = args.iters or 1000
    seed_opt = args.seed
    
    renderer.print(f"Starting {iters} stress iterations...")
    for i in range(iters):
        seed = seed_opt if seed_opt is not None else random.randint(0, (1<<31)-1)
        
        # Run generator
        try:
            gen_res = subprocess.run([os.path.join(build_dir, "gen.out"), str(seed)], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            renderer.emit_error("stress", problem_data, "runtime", f"Generator failed with seed {seed}", e.stderr, exit_code=3)
            
        test_case = gen_res.stdout
        
        # Run sol
        try:
            sol_res = subprocess.run([os.path.join(build_dir, "sol.out")], input=test_case, capture_output=True, text=True, timeout=args.timeout or 2)
        except subprocess.TimeoutExpired:
            renderer.emit_error("stress", problem_data, "runtime", f"Solution Timeout! (seed={seed})", f"Input:\n{test_case}", exit_code=4)
            
        # Run brute
        try:
            brute_res = subprocess.run([os.path.join(build_dir, "brute.out")], input=test_case, capture_output=True, text=True, timeout=args.timeout or 2)
        except subprocess.TimeoutExpired:
            renderer.emit_error("stress", problem_data, "runtime", f"Brute Timeout! (seed={seed})", f"Input:\n{test_case}", exit_code=4)
            
        sol_out = sol_res.stdout.strip()
        brute_out = brute_res.stdout.strip()
        
        mismatch = False
        if problem_data.get("output_order") == "unordered":
            try:
                sol_arr = sorted(json.loads(sol_out))
                brute_arr = sorted(json.loads(brute_out))
                mismatch = sol_arr != brute_arr
            except Exception:
                mismatch = sol_out != brute_out
        else:
            mismatch = sol_out != brute_out
            
        if mismatch:
            payload = {
                "found_at_iteration": i,
                "seed": seed,
                "input": test_case.strip(),
                "solution_output": sol_out,
                "brute_output": brute_out
            }
            if renderer.use_json:
                renderer.emit_success("stress", problem_data, payload, status="fail")
                sys.exit(1)
            else:
                renderer.print(f"\n[MISMATCH] Found bug! (seed={seed})")
                renderer.print(f"Input:\n{test_case.strip()}")
                renderer.print(f"Solution Output:\n{sol_out}")
                renderer.print(f"Brute Output:\n{brute_out}")
                sys.exit(1)
            
        if i > 0 and i % 100 == 0:
            renderer.print(f"Passed {i} iterations...")
            
    renderer.print(f"\nSuccess! Passed {iters} iterations.")
    if renderer.use_json:
        renderer.emit_success("stress", problem_data, {"passed_iterations": iters}, status="pass")
    
    from cli.storage import mark_problem_solved
    mark_problem_solved(problem_dir)
