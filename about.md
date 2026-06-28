# About Leeter

**Leeter** is a localized, high-performance, and feature-rich CLI environment for solving LeetCode problems in C++. It abstracts away boilerplate code, generates optimized C++ execution drivers, performs rigorous stress testing, and tracks your progress statistics—all right from your terminal and favorite IDE.

## Features at a Glance

- **Automated Scaffolding:** `fetch` problems directly using the LeetCode API. The problem description, constraints, and test cases are parsed automatically into `README.md` and `input.txt`, alongside a fresh C++ stub (`solution.cpp`).
- **Seamless Local Execution:** Compile and run solutions without boilerplate. Leeter intelligently analyzes your `solution.cpp` stub and dynamically generates a correct `driver.cpp` customized to the problem's function signature or stateful class.
- **Stress Testing (Differential Testing):** Provide a `brute.cpp` solution and use the `stress` command to automatically generate random inputs and compare outputs until an edge-case mismatch is found.
- **Performance Benchmarking:** The `bench` command runs your isolated function with high-precision `<chrono>` timing to report mean, median, P95, and P99 performance.
- **Interactive Replay:** The `replay` command allows you to step through operations one by one—especially useful for stateful classes like `LRUCache`. 
- **Session & Analytics:** Leeter gamifies your process by tracking daily streaks, goals (`total:easy:medium:hard`), and overall metrics using the `session` and `stats` commands.
- **Editor Integrations:** Out-of-the-box adapters and task bindings for Zed, VSCode, Neovim, and Emacs.

## Architecture

Leeter is built with a decoupled architecture focusing on a clean separation between analysis, code generation, and execution. 

1. **Parser & Analyzer Pipeline:** 
   - Uses sub-analyzers (StubAnalyzer, RunnerResolver, TypeAnalyzer) to inspect C++ stubs and populate a `ProblemIR` (Intermediate Representation).
   - Generates deterministic inputs/outputs via a customized JSON-to-C++ parser.
2. **Runners:** 
   - `FunctionRunner`: Handles typical function-signature problems (e.g., Two Sum).
   - `StatefulClassRunner`: Handles class-based problems with state manipulation (e.g., Min Stack).
   - `InteractiveRunner`: Handles interactive/oracle-style problems.
3. **Execution Engine:** 
   - Wraps executions with timeouts and sanitizers (`ASan`, `UBSan`, `LSan`).
   - Produces event traces (`trace.json`) that power the replay and benchmarking features.
4. **Storage Layer:** 
   - A `~/.lc/session.json` tracks user progression across the workspace.
   - Individual `problem.json` files track metadata, benchmarking history, and local solver status.

## Core Library (`lc.h`)

Leeter includes a master header `lc.h` containing:
- Built-in type parsers (`parse<T>`) and printers (`print<T>`).
- Debugging utilities (`dbg`, `trace`, `watch`).
- Visual assertions (`ASSERT_EQ` with diffing).
- Data structure definitions matching LeetCode exactly (`TreeNode`, `ListNode`).
- Random generators (`randomVector`, `randomTree`, etc.) used internally for stress testing.

## Tech Stack
- **Python 3:** Core CLI and analysis logic.
- **C++20:** Base language target for compiled drivers and the `lc.h` framework library.
