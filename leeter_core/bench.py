# leeter_core/bench.py
"""Core benchmarking functionality – pure library.

The CLI and the FastAPI server import this module and handle presentation
(printing, JSON payloads, HTTP status codes) themselves.

Public API
----------
bench_problem(problem_dir, iterations=1000) -> dict
    Run the benchmark driver and return timing statistics.
    Raises ProblemNotFoundError, UnsupportedRunnerError,
    FileNotFoundInProblemError, CompilationError, or
    BenchmarkExecutionError on failure.
"""

import os
import json
import subprocess

from .build import compile_file
from .stats import calculate_stats
from .exceptions import (
    BenchmarkExecutionError,
    CompilationError,
    FileNotFoundInProblemError,
    ProblemNotFoundError,
    UnsupportedRunnerError,
)

# cli.models and cli.runners.function are *pure* modules (no renderer
# dependency) so importing them here does not introduce a presentation-
# layer coupling.  They will eventually be moved into leeter_core too,
# but that's a separate refactoring step.
from cli.models import ProblemIR
from cli.runners.function import FunctionRunner


def bench_problem(problem_dir: str, iterations: int = 1000) -> dict:
    """Run the benchmark driver for *problem_dir* and return timing stats.

    Parameters
    ----------
    problem_dir : str
        Absolute or relative path to the problem directory.
    iterations : int, optional
        Passed through for callers that want to override the default
        iteration count.  The C++ bench driver currently decides its
        own loop count, but the parameter is kept in the signature so
        that future drivers (or API callers) can use it.

    Returns
    -------
    dict
        Keys: iterations, mean_ns, median_ns, p95_ns, p99_ns, stddev_ns.

    Raises
    ------
    ProblemNotFoundError
        If ``problem.json`` does not exist in *problem_dir*.
    UnsupportedRunnerError
        If the problem's runner is not ``function``.
    FileNotFoundInProblemError
        If ``input.txt`` is missing.
    CompilationError
        If the benchmark driver fails to compile.
    BenchmarkExecutionError
        If the benchmark binary crashes or produces unparseable output.
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
            f"Benchmarking only supports `function` runners "
            f"(found {ir.runner!r})"
        )

    # ── 2. Generate benchmark driver ─────────────────────────────────────
    include_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "include",
    )
    runner = FunctionRunner()
    driver_code = runner.generate(
        ir,
        include_path=include_path,
        solution_file="solution.cpp",
        mode="bench",
    )

    import tempfile
    with tempfile.TemporaryDirectory() as build_dir:
        driver_path = os.path.join(build_dir, "bench_driver.cpp")
        with open(driver_path, "w") as f:
            f.write(driver_code)

        # ── 3. Compile the driver ────────────────────────────────────────────
        bin_path = os.path.join(build_dir, "bench.out")
        compile_file(driver_path, bin_path, problem_dir)  # raises CompilationError

        # ── 4. Execute the benchmark binary ──────────────────────────────────
        input_path = os.path.join(problem_dir, "input.txt")
        if not os.path.exists(input_path):
            raise FileNotFoundInProblemError(
                "input.txt not found for benchmark run"
            )

        with open(input_path, "r") as f:
            test_case = f.read()

        try:
            result = subprocess.run(
                [bin_path],
                input=test_case,
                capture_output=True,
                text=True,
                check=True,
                cwd=problem_dir,
            )
        except subprocess.CalledProcessError as e:
            raise BenchmarkExecutionError(
                "Benchmark binary returned non-zero exit code",
                raw_output=e.stderr,
            )

        # ── 5. Parse JSON timing output ──────────────────────────────────────
        try:
            times = json.loads(result.stdout)
        except Exception:
            raise BenchmarkExecutionError(
                "Failed to parse benchmark JSON output",
                raw_output=result.stdout,
            )
    
        if not times:
            raise BenchmarkExecutionError(
                "Benchmark driver emitted no timing data"
            )
    
        # ── 6. Compute statistics ────────────────────────────────────────────
        stats = calculate_stats(times)
    
        # ── 7. Persist benchmark history ─────────────────────────────────────
        problem_data.setdefault("benchmark_history", []).append(stats)
        with open(pjson_path, "w") as f:
            json.dump(problem_data, f, indent=2)
    
        # ── 8. Return raw stats ──────────────────────────────────────────────
        return {
            "iterations": len(times),
            "mean_ns": stats["mean_ns"],
            "median_ns": stats["median_ns"],
            "p95_ns": stats["p95_ns"],
            "p99_ns": stats["p99_ns"],
            "stddev_ns": stats["stddev_ns"],
        }
