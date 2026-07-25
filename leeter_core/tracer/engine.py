import os
import json
import asyncio
import subprocess
import tempfile
from typing import List, Optional, Dict, Any

from leeter_core.exceptions import (
    CompilationError,
    FileNotFoundInProblemError,
    RuntimeError_,
    TimeLimitExceeded,
)
from leeter_core.debugger import DebuggerWrapper

async def _harvest_with_debugger(
    bin_path: str,
    input_path: str,
    breakpoints: List[int],
    watch_exprs: Optional[List[str]] = None,
    max_iterations: int = 500
) -> List[dict]:
    """Automatically steps across loop iterations at breakpoints and harvests watched expressions."""
    events = []
    debugger = DebuggerWrapper(bin_path, input_path)
    try:
        await debugger.start(breakpoints=breakpoints)
        iteration = 1
        while iteration <= max_iterations:
            if debugger.process and debugger.process.returncode is not None:
                break
                
            locals_dict = await debugger.get_locals(watch_exprs=watch_exprs)
            if not locals_dict or all("error" in str(v).lower() for v in locals_dict.values()):
                break
                
            vars_data = {}
            for var_name, info in locals_dict.items():
                if isinstance(info, dict):
                    vars_data[var_name] = str(info.get("value", ""))
                else:
                    vars_data[var_name] = str(info)
                    
            if vars_data:
                events.append({
                    "line": breakpoints[0] if breakpoints else 0,
                    "iteration": iteration,
                    "vars": vars_data,
                    "source": "debugger"
                })
                
            await debugger.continue_execution()
            iteration += 1
    except Exception as e:
        pass
    finally:
        debugger.stop()
    return events


def trace_problem(
    problem_dir: str,
    test_case_input: Optional[str] = None,
    breakpoints: Optional[List[int]] = None,
    watch_exprs: Optional[List[str]] = None
) -> List[dict]:
    """
    Executes the problem solution and tracks element values across loop iterations.
    Supports zero-code temporary build injection directly from gutter selections without editing source files.
    """
    problem_dir = os.path.abspath(problem_dir)
    sol_path = os.path.join(problem_dir, "solution.cpp")
    if not os.path.exists(sol_path):
        raise FileNotFoundInProblemError(f"Solution file not found at {sol_path}")
        
    pjson_path = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(pjson_path):
        raise CompilationError(f"problem.json not found in {problem_dir}")
        
    with open(pjson_path, "r") as f:
        problem_data = json.load(f)
        
    from cli.models import ProblemIR
    from cli.runners.function import FunctionRunner
    from cli.runners.stateful_class import StatefulClassRunner
    from cli.analyzer import run_pipeline_unified
    
    with open(sol_path, "r") as f:
        stub = f.read()
    ir, _ = run_pipeline_unified(stub)
    
    if ir.runner == "function":
        runner = FunctionRunner()
    elif ir.runner == "stateful_class":
        runner = StatefulClassRunner()
    else:
        raise CompilationError(f"Unsupported runner: {ir.runner}")
        
    build_dir = os.path.join(problem_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    # 0. Zero-Code Temporary Build Injection
    # If user selected gutter lines and/or provided watch expressions, inject TRACK(...) into a temporary build file
    injected_sol_path = os.path.join(build_dir, "solution.trace.cpp")
    used_solution_file = "solution.cpp"
    injected_successfully = False
    
    if breakpoints and watch_exprs:
        try:
            lines = stub.splitlines(keepends=True)
            # Make sure every line has a newline
            lines = [l if l.endswith('\n') else l + '\n' for l in lines]
            
            exprs_str = ", ".join([e.strip() for e in watch_exprs if e.strip()])
            if exprs_str:
                for line_num in sorted(set(breakpoints), reverse=True):
                    idx = line_num - 1 # 1-based to 0-based
                    if 0 <= idx < len(lines):
                        line_text = lines[idx].rstrip()
                        insert_idx = idx + 1
                        spaces = " " * (len(lines[idx]) - len(lines[idx].lstrip()) + 4)
                        
                        if line_text.endswith('{'):
                            # Insert at BOTH start of block and before closing brace to capture exact Entry and Exit mutations!
                            balance = 0
                            end_idx = idx + 1
                            for j in range(idx, len(lines)):
                                for ch in lines[j]:
                                    if ch == '{': balance += 1
                                    elif ch == '}': balance -= 1
                                if balance == 0:
                                    end_idx = j
                                    break
                            if end_idx > idx + 1:
                                end_spaces = " " * (len(lines[end_idx]) - len(lines[end_idx].lstrip()) + 4)
                                lines.insert(end_idx, f"{end_spaces}TRACK({exprs_str});\n")
                            
                            start_spaces = " " * (len(lines[idx]) - len(lines[idx].lstrip()) + 4)
                            lines.insert(idx + 1, f"{start_spaces}TRACK({exprs_str});\n")
                        else:
                            spaces = " " * (len(lines[idx]) - len(lines[idx].lstrip()))
                            lines.insert(idx + 1, f"{spaces}TRACK({exprs_str});\n")
                with open(injected_sol_path, "w") as f:
                    f.writelines(lines)
                used_solution_file = "build/solution.trace.cpp"
                injected_successfully = True
        except Exception:
            used_solution_file = "solution.cpp"

    include_dir = os.path.join(os.path.dirname(os.path.dirname(problem_dir)), "include")
    driver_code = runner.generate(
        ir,
        include_path=include_dir,
        solution_file=used_solution_file
    )
    
    driver_override = os.path.join(build_dir, "driver.trace.cpp")
    with open(driver_override, "w") as f:
        f.write(driver_code)
        
    bin_path = os.path.join(build_dir, "solution_tracker")
    
    # Compile binary
    cmd = [
        "clang++", "-std=c++20", "-O0", "-g",
        f"-I{include_dir}",
        f"-I{problem_dir}",
        driver_override,
        "-o", bin_path,
    ]
    
    res = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
    if res.returncode != 0:
        if injected_successfully:
            # If zero-code injection failed compilation (e.g. variable out of scope), fallback to compiling unmodified solution for LLDB harvesting
            driver_code = runner.generate(ir, include_path=include_dir, solution_file="solution.cpp")
            with open(driver_override, "w") as f:
                f.write(driver_code)
            res = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
            if res.returncode != 0:
                raise CompilationError("Tracker Compilation failed", stderr=res.stderr)
            injected_successfully = False
        else:
            raise CompilationError("Tracker Compilation failed", stderr=res.stderr)
        
    # Prepare input file
    input_path = os.path.join(build_dir, "trace_input.txt")
    if test_case_input is not None and test_case_input.strip():
        with open(input_path, "w") as f:
            f.write(test_case_input)
    else:
        orig_input = os.path.join(problem_dir, "input.txt")
        if os.path.exists(orig_input):
            input_path = orig_input
        else:
            with open(input_path, "w") as f:
                f.write("")
                
    events: List[dict] = []
    
    # 1. Execute natively and capture @@LEETER_TRACK@@ outputs from stderr
    try:
        with open(input_path, "r") as f_in:
            proc_res = subprocess.run(
                [bin_path],
                stdin=f_in,
                cwd=problem_dir,
                timeout=5,
                capture_output=True,
                text=True,
            )
            
            if proc_res.returncode != 0 and "@@LEETER_TRACK@@" not in proc_res.stderr and not (breakpoints and not injected_successfully):
                raise RuntimeError_(
                    f"Tracker Runtime error (exit code {proc_res.returncode})",
                    raw_output=proc_res.stderr
                )
                
            for line in proc_res.stderr.splitlines():
                line = line.strip()
                if "@@LEETER_TRACK@@:" in line:
                    idx = line.find("@@LEETER_TRACK@@:") + len("@@LEETER_TRACK@@:")
                    json_str = line[idx:].strip()
                    try:
                        ev = json.loads(json_str)
                        ev["source"] = "native"
                        events.append(ev)
                    except json.JSONDecodeError:
                        pass
    except subprocess.TimeoutExpired:
        raise TimeLimitExceeded("Tracker Time Limit Exceeded", timeout_sec=5)
        
    # 2. If zero-code injection was not active (or yielded no events) and user provided breakpoints, harvest via LLDB/GDB debugger
    if breakpoints and not events and not injected_successfully:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import threading
                deb_events = []
                def run_deb():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    res = new_loop.run_until_complete(_harvest_with_debugger(bin_path, input_path, breakpoints, watch_exprs))
                    new_loop.close()
                    deb_events.extend(res)
                t = threading.Thread(target=run_deb)
                t.start()
                t.join(timeout=10)
                if deb_events:
                    events.extend(deb_events)
            else:
                deb_events = asyncio.run(_harvest_with_debugger(bin_path, input_path, breakpoints, watch_exprs))
                if deb_events:
                    events.extend(deb_events)
        except Exception:
            pass

    return events


if __name__ == "__main__":
    import sys
    prob = sys.argv[1] if len(sys.argv) > 1 else "problems/1_two_sum"
    print(f"Tracking loops for: {prob}")
    try:
        evs = trace_problem(prob, breakpoints=[8], watch_exprs=["i", "nums[i]", "complement", "m"])
        print(json.dumps(evs, indent=2))
    except Exception as e:
        print(f"Error: {e}")
