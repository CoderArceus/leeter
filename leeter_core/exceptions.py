# leeter_core/exceptions.py
"""Shared exception hierarchy for leeter_core.

All core functions raise these instead of calling the CLI renderer.
The FastAPI layer maps them to HTTP status codes; the thin CLI wrapper
maps them to renderer.emit_error() calls with the appropriate exit codes.
"""


class LeeterError(Exception):
    """Base class for all leeter_core errors."""
    pass


# ── File-system / lookup errors ──────────────────────────────────────────

class ProblemNotFoundError(LeeterError):
    """problem.json (or another required file) could not be located."""
    pass


class FileNotFoundInProblemError(LeeterError):
    """A required file (solution.cpp, input.txt, brute.cpp, …) is missing."""
    pass


# ── Runner / analysis errors ─────────────────────────────────────────────

class UnsupportedRunnerError(LeeterError):
    """The problem's runner type is not supported for the requested operation."""
    pass


# ── Build errors ─────────────────────────────────────────────────────────

class CompilationError(LeeterError):
    """clang++ returned a non-zero exit code."""

    def __init__(self, message: str, stderr: str = ""):
        super().__init__(message)
        self.stderr = stderr


# ── Execution errors ─────────────────────────────────────────────────────

class RuntimeError_(LeeterError):
    """The compiled binary exited with a non-zero code.

    Named with a trailing underscore to avoid shadowing the builtin
    RuntimeError.  Callers can import it as ``from leeter_core.exceptions
    import RuntimeError_ as LCRuntimeError`` if the name collision matters.
    """

    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


class TimeLimitExceeded(LeeterError):
    """The binary did not finish within the allowed timeout."""

    def __init__(self, message: str, timeout_sec: int = 0):
        super().__init__(message)
        self.timeout_sec = timeout_sec


# ── Benchmark-specific errors ────────────────────────────────────────────

class BenchmarkExecutionError(LeeterError):
    """The benchmark binary failed or produced unparseable output."""

    def __init__(self, message: str, raw_output: str = ""):
        super().__init__(message)
        self.raw_output = raw_output


# ── Stress-test-specific errors ──────────────────────────────────────────

class StressMismatchError(LeeterError):
    """Solution and brute-force produced different outputs."""

    def __init__(self, message: str, *, iteration: int, seed: int,
                 input_data: str, solution_output: str, brute_output: str):
        super().__init__(message)
        self.iteration = iteration
        self.seed = seed
        self.input_data = input_data
        self.solution_output = solution_output
        self.brute_output = brute_output
