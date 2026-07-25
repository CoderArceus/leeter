"""CLI stress command – thin wrapper around leeter_core.stress.

All business logic lives in leeter_core.stress.stress_test().
This module is only responsible for:
  1. Wiring argparse args to the core function.
  2. Translating exceptions into renderer.emit_error() / sys.exit() calls.
  3. Formatting successful / mismatch output (human-readable or JSON).
"""

import os
import sys
import json

from cli.output import renderer


def cmd_stress(args):
    from leeter_core.stress import stress_test, StressResult
    from leeter_core.analytics import mark_problem_solved
    from leeter_core.exceptions import (
        ProblemNotFoundError,
        UnsupportedRunnerError,
        FileNotFoundInProblemError,
        CompilationError,
        RuntimeError_,
        TimeLimitExceeded,
        StressMismatchError,
    )

    problem_dir = args.problem

    # Load problem_data for error/success payloads
    pjson_path = os.path.join(problem_dir, "problem.json")
    problem_data = None
    if os.path.exists(pjson_path):
        try:
            with open(pjson_path, "r") as f:
                problem_data = json.load(f)
        except Exception:
            pass

    iters = args.iters or 1000
    seed_opt = args.seed
    timeout = args.timeout or 2

    def on_progress(iteration: int) -> None:
        renderer.print(f"Passed {iteration} iterations...")

    try:
        renderer.print("Generating stress drivers...")
        renderer.print("Compiling sol, brute, and gen binaries...")
        renderer.print(f"Starting {iters} stress iterations...")

        result = stress_test(
            problem_dir,
            iterations=iters,
            seed=seed_opt,
            timeout=timeout,
            on_progress=on_progress,
        )

    except ProblemNotFoundError as exc:
        renderer.emit_error(
            "stress", problem_data, "fs", str(exc), exit_code=5
        )
    except UnsupportedRunnerError as exc:
        renderer.emit_error(
            "stress", problem_data, "runner", str(exc), exit_code=5
        )
    except FileNotFoundInProblemError as exc:
        renderer.emit_error(
            "stress", problem_data, "fs", str(exc), exit_code=5
        )
    except CompilationError as exc:
        renderer.emit_error(
            "stress", problem_data, "compiler", str(exc), exc.stderr,
            exit_code=2,
        )
    except RuntimeError_ as exc:
        renderer.emit_error(
            "stress", problem_data, "runtime", str(exc), exc.raw_output,
            exit_code=3,
        )
    except TimeLimitExceeded as exc:
        renderer.emit_error(
            "stress", problem_data, "runtime", str(exc),
            f"> {exc.timeout_sec}s", exit_code=4,
        )
    except StressMismatchError as exc:
        payload = {
            "found_at_iteration": exc.iteration,
            "seed": exc.seed,
            "input": exc.input_data,
            "solution_output": exc.solution_output,
            "brute_output": exc.brute_output,
        }
        if renderer.use_json:
            renderer.emit_success(
                "stress", problem_data, payload, status="fail"
            )
            sys.exit(1)
        else:
            renderer.print(f"\n[MISMATCH] Found bug! (seed={exc.seed})")
            renderer.print(f"Input:\n{exc.input_data}")
            renderer.print(f"Solution Output:\n{exc.solution_output}")
            renderer.print(f"Brute Output:\n{exc.brute_output}")
            sys.exit(1)

    # ── Success path ─────────────────────────────────────────────────────
    renderer.print(f"\nSuccess! Passed {iters} iterations.")
    if renderer.use_json:
        renderer.emit_success(
            "stress", problem_data,
            {"passed_iterations": iters}, status="pass",
        )

    mark_problem_solved(problem_dir)
