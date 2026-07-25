# leeter_core/build.py
"""Core compilation and execution utilities – pure library.

Extracted from cli/build.py.  All presentation-layer concerns (renderer,
print, sys.exit) have been removed.  Errors are signalled via exceptions
from leeter_core.exceptions so that callers (CLI wrapper, FastAPI router)
can handle them in their own way.

Public API
----------
- get_file_hash(filepath) -> str
- needs_rebuild(problem_dir) -> bool
- update_hash(problem_dir)
- compile_file(source_path, bin_path) -> None          [raises CompilationError]
- compile_release(problem_dir) -> CompileResult        [raises CompilationError]
- compile_debug(problem_dir, sanitize=True) -> None    [raises CompilationError]
- execute_with_timeout(problem_dir, timeout_sec=5) -> RunResult
"""

import hashlib
import os
import subprocess
import time
import json
import tempfile
from dataclasses import dataclass, field
from typing import List, Optional

from .exceptions import (
    CompilationError,
    FileNotFoundInProblemError,
    RuntimeError_,
    TimeLimitExceeded,
)


# ── Result data classes ──────────────────────────────────────────────────

@dataclass
class CompileResult:
    compile_time_ms: float
    skipped: bool = False


@dataclass
class CaseResult:
    index: int
    status: str
    got: str


@dataclass
class RunResult:
    cases: List[CaseResult] = field(default_factory=list)
    passed: int = 0
    failed: int = 0
    total: int = 0
    run_ms: float = 0.0
    binary_kb: float = 0.0
    stdout: str = ""
    stderr: str = ""


# ── Compilation ──────────────────────────────────────────────────────────

def _include_dir_for(problem_dir: str) -> str:
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "include",
    )


def compile_file(source_path: str, bin_path: str, problem_dir: str) -> None:
    include_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "include",
    )
    cmd = [
        "clang++", "-std=c++20", "-O2",
        f"-I{include_path}",
        f"-I{os.path.abspath(problem_dir)}",
        source_path,
        "-o", bin_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise CompilationError(
            f"Compilation of {os.path.basename(source_path)} failed",
            stderr=result.stderr,
        )


def compile_release(problem_dir: str, build_dir: str) -> CompileResult:
    t0 = time.time()
    problem_dir = os.path.abspath(problem_dir)

    driver_path = os.path.join(problem_dir, "driver.override.cpp")
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, "driver.cpp")

    bin_path = os.path.join(build_dir, "solution")
    include_dir = os.path.join(os.path.dirname(problem_dir), "include")
    
    cmd = [
        "clang++", "-std=c++20", "-O2",
        f"-I{include_dir}",
        f"-I{problem_dir}",
        driver_path,
        "-o", bin_path,
    ]

    result = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
    compile_time = (time.time() - t0) * 1000

    if result.returncode != 0:
        raise CompilationError("Compilation failed", stderr=result.stderr)

    return CompileResult(compile_time_ms=compile_time)


def compile_debug(problem_dir: str, build_dir: str, sanitize: bool = True) -> CompileResult:
    t0 = time.time()
    problem_dir = os.path.abspath(problem_dir)

    driver_path = os.path.join(problem_dir, "driver.override.cpp")
    if not os.path.exists(driver_path):
        driver_path = os.path.join(problem_dir, "driver.cpp")

    bin_path = os.path.join(build_dir, "solution_debug")
    include_dir = os.path.join(os.path.dirname(problem_dir), "include")
    
    cmd = [
        "clang++", "-std=c++20", "-g", "-O0",
        f"-I{include_dir}",
        f"-I{problem_dir}",
        driver_path,
        "-o", bin_path,
    ]
    if sanitize:
        cmd.extend(["-fsanitize=address,undefined"])

    result = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
    compile_time = (time.time() - t0) * 1000

    if result.returncode != 0:
        raise CompilationError("Debug compilation failed", stderr=result.stderr)

    return CompileResult(compile_time_ms=compile_time)


# ── Execution ────────────────────────────────────────────────────────────

def execute_with_timeout(
    problem_dir: str,
    build_dir: str,
    timeout_sec: int = 5,
) -> RunResult:
    problem_dir = os.path.abspath(problem_dir)
    bin_path = os.path.join(build_dir, "solution")
    input_path = os.path.join(problem_dir, "input.txt")

    if not os.path.exists(bin_path):
        raise FileNotFoundInProblemError(f"Binary not found at {bin_path}.")

    if not os.path.exists(input_path):
        open(input_path, "w").close()

    start_time = time.time()

    try:
        with open(input_path, "r") as f_in:
            result = subprocess.run(
                [bin_path],
                stdin=f_in,
                cwd=problem_dir,
                timeout=timeout_sec,
                capture_output=True,
                text=True,
            )
            run_ms = (time.time() - start_time) * 1000

            if result.returncode != 0:
                raise RuntimeError_(
                    f"Runtime error (exit code {result.returncode})",
                    raw_output=result.stderr,
                )

            size_kb = (
                os.path.getsize(bin_path) / 1024
                if os.path.exists(bin_path)
                else 0
            )

            cases: List[CaseResult] = []
            out_lines = (
                result.stdout.strip().split("\n") if result.stdout else []
            )
            for idx, line in enumerate(out_lines):
                if not line.strip():
                    continue
                cases.append(CaseResult(index=idx, status="pass", got=line.strip()))

            return RunResult(
                cases=cases,
                passed=len(cases),
                failed=0,
                total=len(cases),
                run_ms=round(run_ms, 2),
                binary_kb=round(size_kb, 2),
                stdout=result.stdout,
                stderr=result.stderr,
            )

    except subprocess.TimeoutExpired:
        raise TimeLimitExceeded(
            "Time Limit Exceeded",
            timeout_sec=timeout_sec,
        )

def run_problem_pipeline(problem_dir: str, timeout_sec: int = 5) -> RunResult:
    """End-to-end pipeline to compile and run a problem in a tempdir."""
    problem_dir = os.path.abspath(problem_dir)
    
    # Generate the driver
    pjson_path = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(pjson_path):
        from .exceptions import ProblemNotFoundError
        raise ProblemNotFoundError(f"problem.json not found in {problem_dir}")
        
    with open(pjson_path, "r") as f:
        problem_data = json.load(f)
        
    from cli.models import ProblemIR
    from cli.runners.function import FunctionRunner
    
    ir = ProblemIR.from_dict(problem_data)
    runner = FunctionRunner()
    
    include_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "include",
    )
    
    driver_code = runner.generate(
        ir,
        include_path=include_path,
        solution_file="solution.cpp"
    )

    with tempfile.TemporaryDirectory() as build_dir:
        # Write the driver to the tempdir
        driver_path = os.path.join(build_dir, "driver.cpp")
        with open(driver_path, "w") as f:
            f.write(driver_code)
            
        # Compile it (modifying compile_release slightly inline to use driver_path)
        t0 = time.time()
        bin_path = os.path.join(build_dir, "solution")
        cmd = [
            "clang++", "-std=c++20", "-O2",
            f"-I{include_path}",
            f"-I{problem_dir}",
            driver_path,
            "-o", bin_path,
        ]
        
        result = subprocess.run(cmd, cwd=problem_dir, capture_output=True, text=True)
        if result.returncode != 0:
            raise CompilationError("Compilation failed", stderr=result.stderr)
            
        return execute_with_timeout(problem_dir, build_dir, timeout_sec)
