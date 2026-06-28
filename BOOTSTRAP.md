# LeetCode Framework — Bootstrap Checklist

Architecture is frozen. This document is a linear implementation checklist.
Work top to bottom. Each milestone is independently usable before the next begins.

---

## Ground rules

- Never edit `solution.cpp` to make the harness work.
- `build/` is always gitignored.
- Tests are written before the code they test.
- No milestone expands in scope to include work from a later milestone.

---

## Milestone 1 — Core Library

**Goal:** `#include "lc.h"` works. You can write a solution manually, compile it
against a hand-written driver, and see correct output.

Nothing in this milestone is framework-aware. It's just a header library.

### Parser

- [ ] `parse<int>()`
- [ ] `parse<long long>()`
- [ ] `parse<double>()`
- [ ] `parse<bool>()`
- [ ] `parse<string>()`
- [ ] `parse<vector<int>>()`
- [ ] `parse<vector<long long>>()`
- [ ] `parse<vector<string>>()`
- [ ] `parse<vector<vector<int>>>()`
- [ ] `parse<TreeNode*>()` — null/NULL accepted
- [ ] `parse<ListNode*>()`
- [ ] `has_input()` — returns false when stdin is exhausted
- [ ] Multiple test cases separated by blank lines work correctly

**Parser tests** (`tests/parser/`):

Each test is a pair: `<name>.txt` (stdin) and `<name>.expected` (parsed value as JSON).
Run with `leetcode test parser`.

- [ ] `int_simple` — `42`
- [ ] `bool_true`, `bool_false`
- [ ] `vector_int` — `[1,2,3,4,5]`
- [ ] `vector_empty` — `[]`
- [ ] `vector_vector_int` — `[[1,2],[3,4]]`
- [ ] `vector_vector_empty` — `[[],[]]`
- [ ] `string_with_spaces` — `"hello world"`
- [ ] `tree_simple` — `[1,2,3]`
- [ ] `tree_with_nulls` — `[1,2,3,null,4]`
- [ ] `tree_null` — `[]`
- [ ] `list_simple` — `[1,2,3,4,5]`
- [ ] `multiple_cases` — two inputs separated by blank line
- [ ] `whitespace_tolerance` — extra spaces around brackets

### Printer

- [ ] `print(int)`
- [ ] `print(long long)`
- [ ] `print(double)`
- [ ] `print(bool)` — `true`/`false`
- [ ] `print(string)`
- [ ] `print(vector<T>)` — `[1,2,3]`
- [ ] `print(vector<vector<T>>)` — `[[1,2],[3,4]]`
- [ ] `print(pair<A,B>)` — `[a,b]`
- [ ] `print(set<T>)` — sorted
- [ ] `print(map<K,V>)` — `[[k1,v1],[k2,v2]]`
- [ ] `print(TreeNode*)` — BFS order with nulls
- [ ] `print(ListNode*)` — `[1,2,3,4]`
- [ ] All output to stdout only

### Debug

- [ ] `dbg(scalar)` — prints to stderr
- [ ] `dbg(vector)` — `[debug] arr = [1,2,3]`
- [ ] `dbg(a, b, c)` — multiple values, one per line
- [ ] `dbg(map)` — arrow formatting
- [ ] `dbg(TreeNode*)` — BFS notation
- [ ] `dbg(ListNode*)` — chain notation
- [ ] `dbg(vector<vector<T>>)` — matrix formatting
- [ ] `trace(a, b)` — `[trace] a = ..., b = ...`
- [ ] `watch(vec)` — iteration counter + caret
- [ ] `dbg(INFO, x)`, `dbg(WARN, x)`, `dbg(ERROR, x)`
- [ ] `#define LC_DEBUG_LEVEL WARN` suppresses INFO
- [ ] `#define LC_NO_DEBUG` compiles all macros to no-ops
- [ ] Color output when `isatty(STDERR_FILENO)` is true
- [ ] No color when stderr is redirected

### Assertions

- [ ] `ASSERT_EQ(result, expected)` — passes silently
- [ ] `ASSERT_EQ` — failure prints visual diff
- [ ] `ASSERT_EQ` on vectors — `^` points to first differing index
- [ ] `ASSERT_EQ` on 2D arrays — reports row and column
- [ ] `ASSERT_NEAR(result, expected, epsilon)`
- [ ] `ASSERT_TRUE(condition)`
- [ ] Multiple assertions accumulate — summary at end: `✓ 3/3 passed`
- [ ] Partial failure: `1/3 passed, 2 failed`

### Timer

- [ ] `Timer t; t.start(); ... t.stop();` — prints to stderr
- [ ] `ScopeTimer t("label")` — prints on destruction

### Data structures

- [ ] `TreeNode` definition matches LeetCode exactly
- [ ] `ListNode` definition matches LeetCode exactly
- [ ] `print_tree(root)` — ASCII visual
- [ ] `print_inorder`, `print_preorder`, `print_postorder`, `print_levelorder`
- [ ] `free_tree(root)`
- [ ] `print_list_verbose(head)` — `1 -> 2 -> 3 -> NULL`
- [ ] `free_list(head)`

### Random generators

- [ ] `randomVector(n, lo, hi)`
- [ ] `randomMatrix(rows, cols, lo, hi)`
- [ ] `randomTree(n, lo, hi)`
- [ ] `randomLinkedList(n, lo, hi)`
- [ ] `randomString(n, charset)`
- [ ] Seeded: `srand(seed)` before generating — same seed gives same output

### Snapshot API

- [ ] `SnapshotValue` type — Object, Array, String, Number, Boolean, Null
- [ ] `emit_snapshot(obj)` — no-op if `to_snapshot` overload not found
- [ ] `emit_snapshot(obj)` — calls `to_snapshot(obj)` if overload exists
- [ ] Snapshot output goes to stderr in human-readable form

### Master header

- [ ] `#include "lc.h"` pulls everything in
- [ ] Compiles cleanly with `-std=c++20 -Wall -Wextra`
- [ ] Zero warnings

### Milestone 1 done when

Write a Two Sum solution in `solution.cpp`. Write a `driver.cpp` by hand that calls it.
Compile and run. Output matches LeetCode's expected output exactly.

---

## Milestone 2 — Analyzer and Problem IR

**Goal:** Given a LeetCode starter stub, the analyzer produces a correct `ProblemIR`.
Nothing is generated yet. No CLI exists yet.

### ProblemIR schema

- [ ] Define `ProblemIR` as a dataclass/struct in Python
- [ ] Define `CppType` as a recursive tagged union
  - [ ] `Primitive`, `Pointer`, `Vector`, `Array`, `Optional`, `Pair`, `Tuple`, `Map`, `Unknown`
  - [ ] Parser handles arbitrary nesting depth
- [ ] Define `DetectionResult` with `candidate`, `evidence`, `ambiguous`, `alternatives`
- [ ] Define `Capability` enum
- [ ] `ProblemIR` is immutable after construction — no mutation after creation
- [ ] `ProblemIR` serializes to/from JSON (`problem.json`)
- [ ] `framework_version: 2` included in all serialized IRs

### Sub-analyzers (each is a pure function `ProblemIR → ProblemIR`)

- [ ] `StubAnalyzer` — parses C++ stub, populates `function` or `stateful_class` or `interactive`
  - [ ] Detects `Solution` class with single public method → `function`
  - [ ] Detects class with constructor + multiple methods (no `Solution`) → `stateful_class`
  - [ ] Detects class inheriting from a base class → `interactive`
  - [ ] Populates return type, parameter names, parameter types as `CppType`
- [ ] `RunnerResolver` — reads structural fields, populates `runner` and `runner_detection`
  - [ ] Reads plugin manifests to match runner (no `supports()` calls on runner instances)
  - [ ] Sets `ambiguous: true` when confidence is unclear
  - [ ] Emits `NeedInput` signal when ambiguous
- [ ] `TypeAnalyzer` — validates all `CppType` values in the IR
  - [ ] Emits `Warn` for `Unknown` types (does not fail)
- [ ] `CapabilityAnalyzer` — computes capabilities from runner + IR
  - [ ] `stress_test` only if random generators exist for all parameter types
  - [ ] `replay` only if runner is `StatefulClassRunner` or `InteractiveRunner`

### Analyzer pipeline

- [ ] Pipeline composes sub-analyzers in order
- [ ] Each stage returns a new IR (functional — no mutation)
- [ ] Pipeline handles `PipelineSignal`: `Continue`, `NeedInput`, `Warn`, `Fail`
- [ ] `NeedInput` pauses pipeline, renders prompt, collects choice, resumes

### Analyzer tests (`tests/analyzer/`)

Each test is a pair: `<problem>/stub.cpp` and `<problem>/expected_ir.json`.
Run with `leetcode test analyzer`. Write expected IR files before implementing.

- [ ] `two_sum` — FunctionRunner, two params `vector<int>&` + `int`, returns `vector<int>`
- [ ] `binary_search` — FunctionRunner, simple primitive types
- [ ] `lru_cache` — StatefulClassRunner, constructor + get + put
- [ ] `min_stack` — StatefulClassRunner, constructor + push + pop + top + getMin
- [ ] `guess_number` — InteractiveRunner, inherits from GuessGame
- [ ] `climb_stairs` — FunctionRunner, single int param, returns int
- [ ] `nested_iterator` — ambiguous detection, triggers NeedInput
- [ ] `exotic_types` — function with unsupported type, produces Unknown, emits Warn

---

## Milestone 3 — FunctionRunner and Build System

**Goal:** `leetcode run` works for single-function problems. No fetch yet. You manually
create the folder and paste the solution. Press run, see output.

### FunctionRunner

- [ ] Plugin manifest: `name`, `version`, `supports: [function]`, `provides: [run, benchmark, stress_test, multiple_cases, trace]`
- [ ] `generate(ProblemIR) → BuildArtifacts` — produces `build/driver.cpp` content
  - [ ] Generates `parse<T>()` call for each parameter
  - [ ] Generates `sol.functionName(params...)` call
  - [ ] Generates `print(result)` call
  - [ ] Wraps in `while (has_input())` loop
  - [ ] `#include`s `solution.cpp` and `lc.h`
  - [ ] Handles `Unknown` type: emits commented-out stub, logs warning
- [ ] `capabilities(ProblemIR) → [Capability]`
- [ ] `build/driver.override.cpp` takes precedence if present
- [ ] Generated driver written to `build/driver.cpp` (never to source tree)

**FunctionRunner tests** (`tests/runner/function/`):

- [ ] `two_sum` — generated driver compiles and produces correct output
- [ ] `void_return` — function returns void, no `print()` call generated
- [ ] `unknown_type` — generates commented stub, does not crash

### Build system

- [ ] Release build: `clang++ -std=c++20 -O2 -I../../include build/driver.cpp -o build/solution`
- [ ] Debug build: `clang++ -std=c++20 -g -O0 -fsanitize=address,undefined ... -o build/solution_debug`
- [ ] LeakSanitizer enabled on debug builds (`ASAN_OPTIONS=detect_leaks=1`)
- [ ] macOS: `leaks` wrapper used instead of LSan
- [ ] Incremental builds: hash `solution.cpp` + `problem.json` + generator version
  - [ ] Hash stored in `build/.hash`
  - [ ] Compilation skipped if hash unchanged
  - [ ] `build/driver.override.cpp` included in hash if present
- [ ] Timeout: `timeout 5s ./build/solution < input.txt`
- [ ] TLE message: `✗ Time Limit Exceeded (> 5s)`
- [ ] Execution statistics printed to stderr after every run
  - [ ] compile time, run time, peak memory (`getrusage` on macOS), binary size

### Event trace (minimal)

- [ ] Execution engine writes `build/trace.json`
- [ ] Events: `run_start`, `case_start`, `case_end`, `run_end` with stats
- [ ] `run_end` includes compile_ms, run_ms, peak_rss_mb, binary_kb

### Zed tasks

- [ ] `Run` — release build → execute → stdout + stderr to terminal
- [ ] `Debug` — debug build with ASan/UBSan → lldb
- [ ] `Generate Driver` — regenerates `build/driver.cpp` from IR
- [ ] `Clean` — removes `build/` under current problem folder
- [ ] Tasks resolve active problem from currently open file's directory

### CLI (minimal)

- [ ] `leetcode run` — full run pipeline
- [ ] `leetcode gen <folder>` — analyze + generate driver only
- [ ] `leetcode new <name>` — creates folder with empty `solution.cpp` and `input.txt`
  - [ ] Prompts: problem name, difficulty, driver type
- [ ] Active problem resolution: `--problem` flag → cwd → most recent
- [ ] `leetcode auth <cookie>` — stores cookie to `~/.lc/session.json`

### Milestone 3 done when

Create `problems/1_two_sum/` by hand. Paste a Two Sum solution. Run `leetcode run`.
Output matches. Change the solution to something wrong. Run again. Assertion fails with
visual diff. Run `leetcode debug`. ASan catches an out-of-bounds access you introduced.

---

## Milestone 4 — Fetch

**Goal:** `leetcode fetch 347` creates a complete problem folder ready to run.

### GraphQL integration

- [ ] Endpoint: `https://leetcode.com/graphql`
- [ ] Query: `questionData` — fetches title, difficulty, topicTags, acRate, content,
  codeSnippets, exampleTestcases, hints, sampleTestCase, metaData, similarQuestions
- [ ] `companyTagStats` attempted but omitted gracefully on 403 (Premium gate)
- [ ] Session cookie read from `~/.lc/session.json`
- [ ] Retry with backoff on 429
- [ ] Meaningful error if cookie is missing or expired

### Artifact creation

- [ ] Folder name: `<id>_<slug>` (e.g., `347_top_k_frequent_elements`)
- [ ] `solution.cpp` — starter stub, exactly as provided by LeetCode, no modifications
- [ ] `input.txt` — example inputs pre-populated, one test case per blank-line block
- [ ] `problem.json` — serialized IR with `framework_version: 2`
- [ ] `README.md` — structured as specified: title, difficulty, acceptance, URL,
  constraints, examples, hints, related problems, My Notes section
- [ ] `build/` not created on fetch — only on first run
- [ ] Fetch is idempotent: re-fetching does not overwrite content below `---` in README
- [ ] Fetch does not overwrite `solution.cpp` if it already exists

### Analyzer invoked on fetched stub

- [ ] `leetcode fetch` runs the full Analyzer after download
- [ ] IR written to `problem.json` immediately
- [ ] If runner is ambiguous, user is prompted before `problem.json` is written

### CLI

- [ ] `leetcode fetch <id>` — full fetch pipeline
- [ ] `leetcode open <id>` — opens folder in Zed + URL in browser
- [ ] `leetcode paste` — reads clipboard (`pbpaste` / `xclip`) → writes to `input.txt`

### Milestone 4 done when

Run `leetcode fetch 1`. Inspect the folder. Run `leetcode run`. Output is correct without
touching any file. Run `leetcode fetch 146`. Inspect. Observe that StatefulClassRunner
is detected. Observe that capabilities exclude `benchmark` by default.

---

## Milestone 5 — StatefulClassRunner and Replay

**Goal:** `leetcode run` works for LRU Cache and similar problems. `leetcode replay`
shows operations step by step.

### StatefulClassRunner

- [ ] Plugin manifest: `name`, `version`, `supports: [stateful_class]`,
  `provides: [run, trace, replay, multiple_cases]`
- [ ] `generate(ProblemIR) → BuildArtifacts`
  - [ ] Generates operation loop over `ops` and `args` arrays
  - [ ] Constructor call: `obj = new ClassName(args[0][0], ...)`
  - [ ] Method dispatch: one `else if` branch per method in IR
  - [ ] `is_void` from IR determines whether to capture return value
  - [ ] `emit_event("method_call", ...)` before each call
  - [ ] `emit_event("method_return", ...)` after each call
  - [ ] `emit_snapshot(obj)` after each call (no-op if no overload)
  - [ ] Output: LeetCode format `[null,null,1,null,-1]`

### Event trace (extended)

- [ ] Events: `method_call` with method name and args
- [ ] Events: `method_return` with return value (or null for void)
- [ ] Events: `snapshot` with type name and `SnapshotValue` payload
- [ ] Trace written to `build/trace.json` atomically on run completion

### Replay renderer

- [ ] `leetcode replay` reads `build/trace.json`
- [ ] Renders each operation with separator, method name, args, return value
- [ ] Renders snapshot state if present in trace
- [ ] `--case N` flag: replay only test case N
- [ ] `--op N` flag: jump to operation N within a case

### Snapshot API (complete)

- [ ] `emit_snapshot(obj)` — detects `to_snapshot` overload via SFINAE
- [ ] `SnapshotValue` serializes to/from JSON for trace storage
- [ ] Replay renderer displays Object as aligned key-value table
- [ ] Replay renderer displays Array inline

### Milestone 5 done when

Run `leetcode fetch 146`. Implement LRU Cache. Run `leetcode run`. Output correct.
Run `leetcode replay`. Watch each operation printed step by step with cache state if
`to_snapshot` is provided, operations-only if not.

---

## Milestone 6 — Stress Testing and Benchmarking

**Goal:** `leetcode stress` and `leetcode bench` work for FunctionRunner problems.

### Stress tester

- [ ] Requires `brute.cpp` in problem folder alongside `solution.cpp`
- [ ] Compiles both as separate binaries
- [ ] Generates random input via `include/random.h` with seed
- [ ] Runs both binaries on same input
- [ ] Diffs stdout
- [ ] Reports first mismatch: input, solution output, brute output, seed
- [ ] `--iters N` (default 1000), `--timeout N` (per-run limit, default 2s)
- [ ] `--seed N` — reproduce a specific failure
- [ ] `random_seed` event written to trace for reproducibility
- [ ] Order-independent comparison when `"output_order": "unordered"` in `problem.json`

### Benchmark runner

- [ ] Separate benchmark driver generated by FunctionRunner in benchmark mode
- [ ] Input parsed once, outside timed loop
- [ ] 10-iteration warmup (discarded)
- [ ] N iterations (default 1000), input cloned before each
- [ ] Reports: mean, median, p95, p99, stddev
- [ ] Results appended to `benchmark_history` in `problem.json`
- [ ] `--compare` flag: runs `solution.cpp` and `solution2.cpp`, reports delta

### Capability enforcement

- [ ] `leetcode stress` on a StatefulClassRunner problem without opt-in: clear error
- [ ] `leetcode bench` on a StatefulClassRunner problem without opt-in: clear error
- [ ] Both commands explain how to opt in via `problem.json`

### Milestone 6 done when

Implement a naive O(n²) Two Sum as `brute.cpp`. Run `leetcode stress` on a correct
O(n) solution. All 1000 iterations pass. Introduce a bug in the solution. Stress finds
it within a few iterations and reports the seed. Run `leetcode bench`. See timing report.

---

## Milestone 7 — Session, Stats, and Polish

**Goal:** The tool feels finished. Stats are tracked. Session mode is motivating.

### Storage layer

- [ ] Per-problem: `problem.json` persists `solved`, `solve_time_ms`, `notes`,
  `benchmark_history`
- [ ] `solved` and `solve_time_ms` written automatically when all assertions pass
- [ ] Session state: `~/.lc/session.json` — streak, daily goals, recent solves
- [ ] Streak incremented when at least one problem solved per day
- [ ] Storage read at pipeline start, written at pipeline end
- [ ] No pipeline stage reads/writes Storage directly

### Session mode

- [ ] `leetcode session` — displays today's goal, progress, streak, recent solves,
  suggestions
- [ ] `leetcode session --goal "5:1:3:1"` — set today's goal (total:easy:medium:hard)
- [ ] Suggested problems: unsolved problems from `problems/` ordered by difficulty

### Stats

- [ ] `leetcode stats` — solved count by difficulty, recent activity, avg solve time
- [ ] `leetcode search <query>` — searches titles and tags across `problems/`

### Note-taking

- [ ] `leetcode note` — opens `README.md` in Zed at the My Notes section
- [ ] Fetch and re-fetch never overwrite content below `---` separator

### Clipboard

- [ ] `leetcode paste` — reads clipboard, writes to `input.txt`
- [ ] macOS: `pbpaste`; Linux: `xclip -o` or `xsel -o`
- [ ] Zed task with keybinding `⌘⇧V`

### Zed tasks (complete)

- [ ] `Stress Test` — prompts for iteration count, runs stress
- [ ] `Bench` — runs benchmark
- [ ] `Replay` — runs replay renderer
- [ ] `New Problem` — wizard
- [ ] `Session` — opens session display

### Migration

- [ ] CLI reads `framework_version` from `problem.json`
- [ ] Migration functions defined for each version transition
- [ ] Unknown future version: abort with clear message, do not corrupt
- [ ] `leetcode migrate` — manually trigger migration on all problem folders

### Milestone 7 done when

Solve five problems across two days. Run `leetcode session`. Streak shows correctly.
Run `leetcode stats`. Counts match. Run `leetcode search tree`. Results filtered.
Run `leetcode paste` after copying an example from LeetCode. `input.txt` updated.

---

## What comes after Bootstrap

The following are explicitly deferred. Do not implement during Bootstrap.

- **InteractiveRunner** (stateless oracle only) — after Milestone 5 pattern is solid
- **Runner AST layer** — when a second language target is needed; extract from existing
  C++ generator rather than building speculatively
- **Plugin discovery** — dynamic manifest loading from a plugins directory; not needed
  until there are more than three runners
- **GUI replay** — trace format already supports it; renderer is the only addition
- **Java / Python / Rust** — IR is language-agnostic; runners are the extension point
- **Competitive programming helpers** — separate file, not part of this framework

---

## Test runner

- [ ] `leetcode test parser` — runs all `tests/parser/` cases
- [ ] `leetcode test analyzer` — runs all `tests/analyzer/` cases
- [ ] `leetcode test runner` — compiles and runs all `tests/runner/` cases
- [ ] `leetcode test` — runs all test suites, reports pass/fail counts
- [ ] Tests are run in CI (GitHub Actions or equivalent) on every push

---

## Definition of done (Bootstrap complete)

1. `leetcode fetch <id>` works for at least 20 problems across all runner types.
2. `leetcode run` produces correct output for all fetched problems.
3. `leetcode stress` finds bugs in intentionally broken solutions.
4. `leetcode bench` reports stable timing for optimized solutions.
5. `leetcode replay` shows LRU Cache operations step by step.
6. `leetcode session` tracks a real solving streak.
7. All `leetcode test` suites pass.
8. `solution.cpp` from any problem can be pasted into LeetCode and submitted without modification.
