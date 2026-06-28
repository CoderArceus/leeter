import os
import sys
import json
import subprocess
import math

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.models import ProblemIR
from cli.runners.function import FunctionRunner
from cli.build import compile_file
from cli.output import renderer

def calculate_stats(times):
    n = len(times)
    times.sort()
    mean = sum(times) / n
    median = times[n // 2]
    p95 = times[int(n * 0.95)]
    p99 = times[int(n * 0.99)]
    variance = sum((x - mean) ** 2 for x in times) / n
    stddev = math.sqrt(variance)
    return {
        "mean_ns": mean,
        "median_ns": median,
        "p95_ns": p95,
        "p99_ns": p99,
        "stddev_ns": stddev
    }

def print_stats(name, stats):
    renderer.print(f"\n--- Benchmark Results: {name} ---")
    renderer.print(f"Mean:   {stats['mean_ns']/1000.0:.2f} µs")
    renderer.print(f"Median: {stats['median_ns']/1000.0:.2f} µs")
    renderer.print(f"P95:    {stats['p95_ns']/1000.0:.2f} µs")
    renderer.print(f"P99:    {stats['p99_ns']/1000.0:.2f} µs")
    renderer.print(f"StdDev: {stats['stddev_ns']/1000.0:.2f} µs")

def cmd_bench(args):
    problem_dir = args.problem
    if not os.path.exists(os.path.join(problem_dir, "problem.json")):
        renderer.emit_error("bench", None, "fs", f"problem.json not found in {problem_dir}", exit_code=5)
        
    with open(os.path.join(problem_dir, "problem.json"), "r") as f:
        problem_data = json.load(f)
        ir = ProblemIR.from_dict(problem_data)
        
    if ir.runner != "function":
        renderer.emit_error("bench", problem_data, "runner", "Benchmarking is only supported for function runners.", exit_code=5)
        
    renderer.print("Generating benchmark driver...")
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    
    runner = FunctionRunner()
    driver_code = runner.generate(ir, include_path=include_path, solution_file="solution.cpp", mode="bench")
    
    build_dir = os.path.join(problem_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    with open(os.path.join(build_dir, "bench_driver.cpp"), "w") as f: f.write(driver_code)
    
    renderer.print("Compiling benchmark binary...")
    if not compile_file(os.path.join(build_dir, "bench_driver.cpp"), os.path.join(build_dir, "bench.out")):
        renderer.emit_error("bench", problem_data, "compiler", "Compilation of benchmark failed.", exit_code=2)
        
    input_path = os.path.join(problem_dir, "input.txt")
    if not os.path.exists(input_path):
        renderer.emit_error("bench", problem_data, "fs", "input.txt not found", exit_code=5)
        
    with open(input_path, 'r') as f:
        test_case = f.read()
        
    renderer.print("Running 1000 iterations...")
    try:
        res = subprocess.run([os.path.join(build_dir, "bench.out")], input=test_case, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        renderer.emit_error("bench", problem_data, "runtime", "Benchmark failed", e.stderr, exit_code=3)
        
    try:
        times = json.loads(res.stdout)
    except Exception as e:
        renderer.emit_error("bench", problem_data, "runtime", "Failed to parse benchmark times", res.stdout, exit_code=5)
        
    if not times:
        renderer.emit_error("bench", problem_data, "runtime", "No times recorded.", exit_code=5)
        
    stats = calculate_stats(times)
    
    if not renderer.use_json:
        print_stats("solution.cpp", stats)
    else:
        payload = {
            "iterations": len(times),
            "mean_ms": round(stats['mean_ns']/1000000.0, 2),
            "median_ms": round(stats['median_ns']/1000000.0, 2),
            "p95_ms": round(stats['p95_ns']/1000000.0, 2),
            "p99_ms": round(stats['p99_ns']/1000000.0, 2),
            "stddev_ms": round(stats['stddev_ns']/1000000.0, 2)
        }
        renderer.emit_success("bench", problem_data, payload)
    
    # Update benchmark history
    if "benchmark_history" not in problem_data:
        problem_data["benchmark_history"] = []
    problem_data["benchmark_history"].append(stats)
    
    with open(os.path.join(problem_dir, "problem.json"), "w") as f:
        json.dump(problem_data, f, indent=2)
