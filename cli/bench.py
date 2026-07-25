"""CLI bench command – thin wrapper around leeter_core.bench.

All business logic lives in leeter_core.bench.bench_problem().
This module is only responsible for:
  1. Wiring argparse args to the core function.
  2. Translating exceptions into renderer.emit_error() / sys.exit() calls.
  3. Formatting successful output (human-readable or JSON).
"""

import os
import sys
import json
import math

from cli.output import renderer

# ── Pure stat helpers used only by the CLI for pretty-printing ───────────

def print_stats(name: str, stats: dict) -> None:
    """Human-readable benchmark output to the terminal."""
    renderer.print(f"\n--- Benchmark Results: {name} ---")
    renderer.print(f"Mean:   {stats['mean_ns']/1000.0:.2f} µs")
    renderer.print(f"Median: {stats['median_ns']/1000.0:.2f} µs")
    renderer.print(f"P95:    {stats['p95_ns']/1000.0:.2f} µs")
    renderer.print(f"P99:    {stats['p99_ns']/1000.0:.2f} µs")
    renderer.print(f"StdDev: {stats['stddev_ns']/1000.0:.2f} µs")


# ── CLI command entry-point ──────────────────────────────────────────────

def cmd_bench(args):
    from leeter_core.bench import bench_problem
    from leeter_core.exceptions import (
        ProblemNotFoundError,
        UnsupportedRunnerError,
        FileNotFoundInProblemError,
        CompilationError,
        BenchmarkExecutionError,
    )

    problem_dir = args.problem

    # Load problem.json upfront so we can include it in error payloads,
    # matching the original CLI behaviour.
    pjson_path = os.path.join(problem_dir, "problem.json")
    problem_data = None
    if os.path.exists(pjson_path):
        try:
            with open(pjson_path, "r") as f:
                problem_data = json.load(f)
        except Exception:
            pass

    try:
        renderer.print("Generating benchmark driver...")
        renderer.print("Compiling benchmark binary...")
        renderer.print("Running 1000 iterations...")

        stats = bench_problem(problem_dir, iterations=getattr(args, "iters", 1000))

    except ProblemNotFoundError as exc:
        renderer.emit_error(
            "bench", problem_data, "fs", str(exc), exit_code=5
        )
    except UnsupportedRunnerError as exc:
        renderer.emit_error(
            "bench", problem_data, "runner", str(exc), exit_code=5
        )
    except FileNotFoundInProblemError as exc:
        renderer.emit_error(
            "bench", problem_data, "fs", str(exc), exit_code=5
        )
    except CompilationError as exc:
        renderer.emit_error(
            "bench", problem_data, "compiler",
            "Compilation of benchmark failed.", exc.stderr, exit_code=2
        )
    except BenchmarkExecutionError as exc:
        renderer.emit_error(
            "bench", problem_data, "runtime",
            str(exc), exc.raw_output, exit_code=3
        )

    # ── Success path ─────────────────────────────────────────────────────
    if not renderer.use_json:
        print_stats("solution.cpp", stats)
    else:
        payload = {
            "iterations": stats["iterations"],
            "mean_ms": round(stats["mean_ns"] / 1_000_000.0, 2),
            "median_ms": round(stats["median_ns"] / 1_000_000.0, 2),
            "p95_ms": round(stats["p95_ns"] / 1_000_000.0, 2),
            "p99_ms": round(stats["p99_ns"] / 1_000_000.0, 2),
            "stddev_ms": round(stats["stddev_ns"] / 1_000_000.0, 2),
        }
        renderer.emit_success("bench", problem_data, payload)
