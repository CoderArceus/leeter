# leeter_core/stress.py
"""Core stress-testing functionality – pure library.

Extracted from cli/stress.py.  No renderer, no sys.exit.  Errors are
signalled via exceptions from leeter_core.exceptions.

Public API
----------
stress_test(problem_dir, iterations=1000, seed=None, timeout=2,
            on_progress=None) -> StressResult
    Compile sol/brute/gen, run iterations, compare outputs.
    Raises StressMismatchError on first divergence.
    Raises CompilationError, RuntimeError_, TimeLimitExceeded as needed.

generate_random_expr(t) -> str
    Pure helper – generates a random C++ expression for a given CppType.

generate_gen_cpp(ir, include_path) -> str
    Pure helper – generates the random-input-generator C++ source.
"""

import json
import os
import random
import subprocess
from dataclasses import dataclass
from typing import Callable, Optional

from .build import compile_file
from .exceptions import (
    BenchmarkExecutionError,
    CompilationError,
    FileNotFoundInProblemError,
    ProblemNotFoundError,
    RuntimeError_,
    StressMismatchError,
    TimeLimitExceeded,
    UnsupportedRunnerError,
)

# Pure data classes / codegen – no renderer dependency
from cli.models import ProblemIR, CppType, Primitive, Vector, Pointer
from cli.runners.function import FunctionRunner, to_cpp_type


# ── Result data class ────────────────────────────────────────────────────

@dataclass
class StressResult:
    """Returned on a fully-successful stress run (no mismatch found)."""
    passed_iterations: int


# ── Pure codegen helpers (moved verbatim from cli/stress.py) ─────────────

def generate_random_expr(t: CppType) -> str:
    """Return a C++ expression that produces a random value of type *t*."""
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
        if (isinstance(t.inner, Vector)
                and isinstance(t.inner.inner, Primitive)
                and t.inner.inner.name in ("int", "long long")):
            return "randomMatrix(5 + rand() % 10, 5 + rand() % 10, -50, 50)"
        return f"vector<{to_cpp_type(t.inner)}>()"
    elif isinstance(t, Pointer):
        if t.name == "TreeNode*":
            return "randomTree(1 + rand() % 20, -50, 50)"
        elif t.name == "ListNode*":
            return "randomLinkedList(1 + rand() % 20, -50, 50)"
    return f"{to_cpp_type(t)}()"


def generate_gen_cpp(ir: ProblemIR, include_path: str) -> str:
    """Generate the C++ source for the random-input generator."""
    lines = [
        f'#include "{include_path}/lc.h"',
        "int main(int argc, char** argv) {",
        "    if (argc > 1) srand(atoi(argv[1]));",
        "    else srand(time(NULL));",
    ]
    for i, param in enumerate(ir.function.parameters):
        expr = generate_random_expr(param.type)
        lines.append(f"    auto p{i} = {expr};")
        lines.append(f"    print(p{i});")
    lines.append("    return 0;")
    lines.append("}")
    return "\n".join(lines) + "\n"


# ── Core stress-test function ────────────────────────────────────────────

def stress_test(
    problem_dir: str,
    iterations: int = 1000,
    seed: Optional[int] = None,
    timeout: int = 2,
    on_progress: Optional[Callable[[int], None]] = None,
) -> StressResult:
    """Run a stress test comparing solution.cpp against brute.cpp.

    Parameters
    ----------
    problem_dir : str
        Path to the problem directory.
    iterations : int
        Number of random test cases to generate and compare.
    seed : int or None
        If provided, use this fixed seed for every iteration (useful for
        reproducing a specific failure).  Otherwise a random seed is
        chosen per iteration.
    timeout : int
        Per-execution timeout in seconds for sol / brute / gen binaries.
    on_progress : callable or None
        Optional callback invoked with the current iteration number
        (e.g. every 100 iterations) so the caller can log progress
        without the core module printing anything.

    Returns
    -------
    StressResult
        On success (all iterations passed).

    Raises
    ------
    ProblemNotFoundError
        If problem.json is missing.
    UnsupportedRunnerError
        If the runner is not ``function``.
    FileNotFoundInProblemError
        If brute.cpp is missing.
    CompilationError
        If any of the three binaries fail to compile.
    RuntimeError_
        If gen / sol / brute crash at runtime.
    TimeLimitExceeded
        If sol or brute exceed the timeout.
    StressMismatchError
        If solution and brute produce different outputs.
    """
    # ── 1. Load problem metadata ─────────────────────────────────────────
    pjson_path = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(pjson_path):
        raise ProblemNotFoundError(
            f"problem.json not found in {problem_dir}"
        )

    with open(pjson_path, "r") as f:
        problem_data = json.load(f)

    ir = ProblemIR.from_dict(problem_data)

    if ir.runner != "function":
        raise UnsupportedRunnerError(
            "Stress testing is only supported for function runners."
        )

    brute_path = os.path.join(problem_dir, "brute.cpp")
    if not os.path.exists(brute_path):
        raise FileNotFoundInProblemError(
            f"brute.cpp not found in {problem_dir}"
        )

    # ── 2. Generate drivers ──────────────────────────────────────────────
    include_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "include",
    )

    runner = FunctionRunner()
    sol_driver_code = runner.generate(
        ir, include_path=include_path, solution_file="solution.cpp"
    )
    brute_driver_code = runner.generate(
        ir, include_path=include_path, solution_file="brute.cpp"
    )
    gen_code = generate_gen_cpp(ir, include_path=include_path)

    import tempfile
    with tempfile.TemporaryDirectory() as build_dir:
        with open(os.path.join(build_dir, "sol_driver.cpp"), "w") as f:
            f.write(sol_driver_code)
        with open(os.path.join(build_dir, "brute_driver.cpp"), "w") as f:
            f.write(brute_driver_code)
        with open(os.path.join(build_dir, "gen.cpp"), "w") as f:
            f.write(gen_code)

        # ── 3. Compile all three ─────────────────────────────────────────────
        # compile_file raises CompilationError on failure
        compile_file(
            os.path.join(build_dir, "sol_driver.cpp"),
            os.path.join(build_dir, "sol.out"),
            problem_dir,
        )
        compile_file(
            os.path.join(build_dir, "brute_driver.cpp"),
            os.path.join(build_dir, "brute.out"),
            problem_dir,
        )
        compile_file(
            os.path.join(build_dir, "gen.cpp"),
            os.path.join(build_dir, "gen.out"),
            problem_dir,
        )

        # ── 4. Run iterations ────────────────────────────────────────────────
        sol_bin = os.path.join(build_dir, "sol.out")
        brute_bin = os.path.join(build_dir, "brute.out")
        gen_bin = os.path.join(build_dir, "gen.out")
        output_order = problem_data.get("output_order")

        for i in range(iterations):
            iter_seed = seed if seed is not None else random.randint(0, (1 << 31) - 1)

            # ── 4a. Generator ────────────────────────────────────────────────
            try:
                gen_res = subprocess.run(
                    [gen_bin, str(iter_seed)],
                    capture_output=True, text=True, check=True, cwd=problem_dir,
                )
            except subprocess.CalledProcessError as e:
                raise RuntimeError_(
                    f"Generator failed with seed {iter_seed}",
                    raw_output=e.stderr,
                )

            test_case = gen_res.stdout
    
            # ── 4b. Solution ─────────────────────────────────────────────────
            try:
                sol_res = subprocess.run(
                    [sol_bin],
                    input=test_case,
                    capture_output=True, text=True,
                    timeout=timeout,
                )
                if sol_res.returncode != 0:
                    raise RuntimeError_(
                        f"Solution crashed (exit code {sol_res.returncode}) "
                        f"with seed {iter_seed}",
                        raw_output=(
                            f"Input:\n{test_case}\nStderr:\n{sol_res.stderr}"
                        ),
                    )
            except subprocess.TimeoutExpired:
                raise TimeLimitExceeded(
                    f"Solution Timeout! (seed={iter_seed})",
                    timeout_sec=timeout,
                )
    
            # ── 4c. Brute-force ──────────────────────────────────────────────
            try:
                brute_res = subprocess.run(
                    [brute_bin],
                    input=test_case,
                    capture_output=True, text=True,
                    timeout=timeout,
                )
                if brute_res.returncode != 0:
                    raise RuntimeError_(
                        f"Brute crashed (exit code {brute_res.returncode}) "
                        f"with seed {iter_seed}",
                        raw_output=(
                            f"Input:\n{test_case}\nStderr:\n{brute_res.stderr}"
                        ),
                    )
            except subprocess.TimeoutExpired:
                raise TimeLimitExceeded(
                    f"Brute Timeout! (seed={iter_seed})",
                    timeout_sec=timeout,
                )
    
            # ── 4d. Compare outputs ──────────────────────────────────────────
            sol_out = sol_res.stdout.strip()
            brute_out = brute_res.stdout.strip()
    
            mismatch = False
            if output_order == "unordered":
                try:
                    sol_arr = sorted(json.loads(sol_out))
                    brute_arr = sorted(json.loads(brute_out))
                    mismatch = sol_arr != brute_arr
                except Exception:
                    mismatch = sol_out != brute_out
            else:
                mismatch = sol_out != brute_out
    
            if mismatch:
                raise StressMismatchError(
                    f"Mismatch found at iteration {i} (seed={iter_seed})",
                    iteration=i,
                    seed=iter_seed,
                    input_data=test_case.strip(),
                    solution_output=sol_out,
                    brute_output=brute_out,
                )
    
            # ── 4e. Optional progress callback ───────────────────────────────
            if on_progress and i > 0 and i % 100 == 0:
                on_progress(i)
    
        return StressResult(passed_iterations=iterations)
