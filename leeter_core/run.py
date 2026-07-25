# leeter_core/run.py
"""Core run functionality extracted from cli/run.py.

Provides a function `run_problem(problem_dir: str, timeout: int = 5, no_compile: bool = False) -> dict`
which compiles (if needed) and executes the solution, returning a JSON‑serializable result map.
"""
import os
import json
from .build import compile_release, execute_with_timeout
from cli.output import renderer
from cli.analyzer import run_pipeline_unified, resolve_need_input
from cli.models import NeedInput
from cli.runners.function import FunctionRunner
from cli.runners.stateful_class import StatefulClassRunner

def run_problem(problem_dir: str, timeout: int = 5, no_compile: bool = False) -> dict:
    # Determine runner and ensure IR is stored in problem.json
    pjson_path = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(pjson_path):
        raise FileNotFoundError("problem.json not found in " + problem_dir)
    with open(pjson_path, "r") as f:
        existing_data = json.load(f)
    # Load IR if already present, otherwise analyze solution.cpp
    ir = None
    if "function" in existing_data and "runner" in existing_data:
        # Minimal reconstruction – the full IR object is not needed for execution here
        ir = type('IR', (), {})()
        ir.runner = existing_data["runner"]
        ir.function = existing_data.get("function")
    else:
        sol_path = os.path.join(problem_dir, "solution.cpp")
        if not os.path.exists(sol_path):
            raise FileNotFoundError("solution.cpp not found in " + problem_dir)
        with open(sol_path, "r") as f:
            stub = f.read()
        ir, signals = run_pipeline_unified(stub)
        for sig in signals:
            if isinstance(sig, NeedInput):
                ir = resolve_need_input(ir, sig)
        # Persist minimal info back to problem.json
        existing_data["function"] = getattr(ir, "function", None)
        existing_data["runner"] = getattr(ir, "runner", None)
        with open(pjson_path, "w") as f:
            json.dump(existing_data, f, indent=2)
    # Generate driver if needed
    if ir.runner == "function":
        runner = FunctionRunner()
    elif ir.runner == "stateful_class":
        runner = StatefulClassRunner()
    else:
        raise ValueError(f"Unsupported runner: {ir.runner}")
    include_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "include")
    driver_code = runner.generate(ir, include_path=include_path)
    build_dir = os.path.join(problem_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    driver_path = os.path.join(build_dir, "driver.cpp")
    with open(driver_path, "w") as f:
        f.write(driver_code)
    if not no_compile:
        try:
            compile_release(problem_dir, build_dir)
        except Exception:
            return {"status": "compile_error"}
    try:
        result = execute_with_timeout(problem_dir, build_dir, timeout)
        return {"status": "success"}
    except Exception:
        return {"status": "runtime_error"}
