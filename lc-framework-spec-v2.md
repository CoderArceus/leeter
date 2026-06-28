# LeetCode Development Framework — Architecture Specification v2

---

## Preamble

This document is an architecture specification, not a feature list. It defines the
system boundaries, module contracts, data flow, and extension points for a local C++
LeetCode development environment. Implementation details (specific CLI flags, exact
compiler invocations, Zed task names) are deferred to implementation notes at the end.

The specification has evolved through several design sessions. This version supersedes
all prior drafts.

---

## 1. Design Principles

These principles take precedence over every specific design decision in this document.
When a decision conflicts with a principle, revise the decision.

### 1.1 The solution is unaware of the framework

`solution.cpp` contains exactly what you would submit to LeetCode. It `#include`s
nothing from the framework. It references no framework types. It has no awareness that
a harness exists. If you copy it into LeetCode's editor and click Submit, it works.

This is non-negotiable. Any design that requires touching `solution.cpp` to make the
harness work is wrong.

### 1.2 Generated artifacts are ephemeral

Files produced by the build system — drivers, compiled binaries, traces — are build
artifacts, not source files. They live in `build/`, are excluded from version control,
and are regenerated on every run. You never edit them. If you need to override generated
behavior, the framework provides an explicit override mechanism rather than letting you
patch a generated file.

### 1.3 All framework knowledge flows through the IR

The Problem IR (Section 3) is the single source of truth for everything the framework
knows about a problem. No downstream component (runner, benchmark, stress tester,
replay renderer) reads or parses `solution.cpp` directly. The IR is produced once by
the Analyzer and consumed by everything else.

### 1.4 Every stage has a single responsibility

The pipeline (Section 4) is composed of stages. Each stage transforms one thing. A
stage that both parses and generates is two stages. Shared state between stages flows
through typed data structures, not global variables or files read by convention.

### 1.5 Capabilities are declared, not assumed

Every runner declares which capabilities it supports. The CLI checks capabilities before
invoking features. An unsupported capability produces a clear error, not a silent
failure or a wrong result.

---

## 2. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                         CLI                             │
│   (thin dispatcher — no business logic lives here)      │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      Pipeline                           │
│                                                         │
│  Source → Analyzer → [IR] → Runner → Build → Execute   │
│                                  ↓                      │
│                               Trace                     │
└────────────┬──────────────────────────────┬────────────┘
             │                              │
             ▼                              ▼
┌────────────────────┐          ┌───────────────────────┐
│      Storage       │          │       Renderer        │
│  (persistent state)│          │  (trace → output)     │
└────────────────────┘          └───────────────────────┘
```

### Modules

**CLI** — Parses commands, resolves the active problem folder, invokes pipeline stages.
Contains no business logic. All real work happens in the pipeline or its stages.

**Pipeline** — Orchestrates stage execution. Handles resumable flows when a stage
requires user input. Owns the stage graph; individual stages do not know about each
other.

**Analyzer** — Consumes LeetCode source (stub or fetched metadata) and produces a
Problem IR. Composed of sub-analyzers (see Section 3.2).

**Problem IR** — The typed intermediate representation of everything the framework
knows about a problem. Defined in Section 3.

**Runner plugins** — Implement execution strategies for different problem categories.
Each runner consumes an IR and produces build artifacts. Defined in Section 5.

**Build system** — Compiles artifacts, manages the `build/` directory, invokes the
compiler with appropriate flags. Not a runner; runners call into it.

**Execution engine** — Runs compiled binaries, enforces timeouts, collects traces.
Emits a structured event log.

**Trace** — The structured event log produced during execution. Consumed by the
Renderer and stored by Storage.

**Storage** — Persistent state across invocations. Owns streaks, solved status,
benchmark history, session goals, notes. The pipeline reads from Storage at start and
writes at end. Storage does not know about the pipeline's internal stages.

**Renderer** — Consumes a trace and produces human-readable output. Multiple renderer
implementations exist (terminal, replay, benchmark report). Renderers do not know about
execution.

---

## 3. Problem IR

The Problem IR is a typed in-memory structure populated by the Analyzer and consumed by
every downstream component. It is also serialized to `problem.json` for persistence.

### 3.1 Schema

```yaml
ProblemIR:
  # Identity
  id: int                        # LeetCode problem number
  title: string
  difficulty: Easy | Medium | Hard
  url: string
  tags: [string]
  acceptance_rate: float

  # Runner selection
  runner: RunnerKind             # resolved by Analyzer
  runner_detection: DetectionResult

  # Structure — exactly one of these is populated
  function:                      # populated for FunctionRunner
    name: string
    return_type: CppType
    parameters: [Parameter]      # { name: string, type: CppType }

  stateful_class:                # populated for StatefulClassRunner
    name: string
    constructor: [Parameter]
    methods: [Method]            # { name, return_type, parameters, is_void }

  interactive:                   # populated for InteractiveRunner
    oracle_class: string
    mock_interface: string       # the interface the solution calls

  # I/O
  input_format: InputFormat      # how to parse input.txt for this runner
  output_format: OutputFormat    # how to print results

  # Examples (from LeetCode)
  examples: [Example]            # { input: string, output: string, explanation: string }

  # Capabilities advertised by the resolved runner
  capabilities: [Capability]

  # Metadata
  hints: [string]
  constraints: [string]
  related_problems: [int]
  companies: [string]            # omitted if not available (Premium)
  notes: string                  # user-written, persisted across runs
  solved: bool
  solve_time_ms: int | null
  benchmark_history: [BenchmarkResult]
```

### 3.2 Analyzer pipeline

The Analyzer is itself a pipeline of sub-analyzers. Each sub-analyzer enriches the IR
and passes it forward. No sub-analyzer generates files.

```
StubAnalyzer
    Reads solution.cpp or the fetched stub.
    Populates: function or stateful_class or interactive (structural fields only).

RunnerResolver
    Reads the structural fields from StubAnalyzer.
    Produces: runner (RunnerKind) and runner_detection (DetectionResult).
    May emit NeedInput if detection is ambiguous (see Section 3.3).

TypeAnalyzer
    Reads parameter types from the structural fields.
    Validates that all types are parseable by the core library.
    Emits warnings for unsupported types (does not fail; runner handles gracefully).

CapabilityAnalyzer
    Reads runner and structural fields.
    Produces: capabilities list.
    Example: stress_test requires random generators for all parameter types.
    Example: replay requires stateful_class or interactive.
```

### 3.3 Runner detection

The RunnerResolver produces a `DetectionResult`, not a confidence score.

```yaml
DetectionResult:
  candidate: RunnerKind
  evidence: [string]           # human-readable reasons
  ambiguous: bool
  alternatives: [DetectionAlternative]   # populated only if ambiguous: true
```

Example — unambiguous:

```yaml
candidate: StatefulClassRunner
evidence:
  - "No Solution class found"
  - "Class with constructor detected: LRUCache(int capacity)"
  - "Multiple public methods: get, put"
  - "Input format matches operation array pattern"
ambiguous: false
```

Example — ambiguous:

```yaml
ambiguous: true
alternatives:
  - candidate: FunctionRunner
    evidence:
      - "Solution class present"
      - "Single public method"
  - candidate: StatefulClassRunner
    evidence:
      - "Constructor-like method present"
      - "Method count ambiguous (1)"
```

When `ambiguous: true`, the pipeline emits a `NeedInput` signal (Section 4.3) rather
than guessing.

### 3.4 CppType

All parameter and return types in the IR are represented as `CppType`, a recursive
value type owned by the framework.

```
CppType:
  Primitive:   int | long long | double | bool | string | void
  Pointer:     TreeNode* | ListNode*
  Vector:      Vector(inner: CppType)
  Array:       Array(inner: CppType, size: int)
  Optional:    Optional(inner: CppType)
  Pair:        Pair(first: CppType, second: CppType)
  Tuple:       Tuple(elements: [CppType])
  Map:         Map(key: CppType, value: CppType)
  Unknown:     Unknown(raw: string)   # fallback for unsupported types
```

The type parser is recursive and handles any nesting depth. `Unknown` is emitted (not
an error) for types the parser cannot represent. Runners check for `Unknown` and decide
how to handle it (emit a commented stub, prompt the user, or fail gracefully).

---

## 4. Pipeline

### 4.1 Stage graph

```
fetch:   [Source] → [StubAnalyzer] → [RunnerResolver] → [TypeAnalyzer]
                  → [CapabilityAnalyzer] → [ArtifactGenerator] → [Storage.write]

run:     [StubAnalyzer] → [RunnerResolver] → [TypeAnalyzer] → [CapabilityAnalyzer]
       → [ArtifactGenerator] → [Compiler] → [ExecutionEngine] → [Renderer] → [Storage.write]

replay:  [Storage.read(trace)] → [Renderer(ReplayRenderer)]

bench:   [StubAnalyzer] → ... → [Compiler(BenchmarkMode)] → [ExecutionEngine]
       → [Renderer(BenchmarkRenderer)] → [Storage.write(benchmark_history)]

stress:  [StubAnalyzer] → ... → [Compiler(ReleaseMode)] → [Compiler(BruteMode)]
       → [StressEngine] → [Renderer(StressRenderer)]

stats:   [Storage.read] → [Renderer(StatsRenderer)]
```

CLI commands invoke named stage sequences. Adding a new command means defining a new
stage sequence, not modifying existing stages.

### 4.2 Data flow

Stages communicate through typed structs, not files or global state. A stage receives
its input type and returns its output type. The pipeline is responsible for wiring them.

```
Source           → RawProblem
RawProblem       → PartialIR       (after StubAnalyzer)
PartialIR        → PartialIR       (each sub-analyzer enriches in place)
PartialIR        → ProblemIR       (after CapabilityAnalyzer — IR is now complete)
ProblemIR        → BuildArtifacts  (ArtifactGenerator)
BuildArtifacts   → Binary          (Compiler)
Binary           → TraceLog        (ExecutionEngine)
TraceLog         → void            (Renderer — side effect: terminal output)
TraceLog         → void            (Storage.write — side effect: persistence)
```

### 4.3 Resumable pipelines

Some stages cannot proceed without user input. Rather than blocking or silently
choosing, they emit a `PipelineSignal`.

```
PipelineSignal:
  Continue                    # normal case — proceed to next stage
  NeedInput(prompt: Prompt)   # pause and collect user input
  Warn(message: string)       # continue but surface a warning
  Fail(reason: string)        # abort with an error message
```

When a stage emits `NeedInput`, the pipeline:
1. Renders the prompt to the terminal
2. Collects the user's choice
3. Injects it back into the stage as if it had been produced automatically
4. Resumes from that stage

No stage skips this mechanism. No stage handles terminal I/O directly.

Example prompt (runner ambiguity):

```
Unable to determine runner automatically.

Detected candidates:

  1. FunctionRunner
     ✓ Solution class present
     ✓ Single public method: int maxProfit(vector<int>& prices)

  2. StatefulClassRunner
     ✓ Constructor-like method present
     ✗ Only one method found (ambiguous)

Choose runner [1/2]:
```

### 4.4 Override mechanism

When `build/driver.override.cpp` exists in the problem folder, the ArtifactGenerator
skips generation and the Compiler uses the override file directly. This is the escape
hatch for exotic problem structures. The override is committed to version control (it is
source, not a build artifact). The presence of an override is noted in `problem.json`.

---

## 5. Runner Plugins

### 5.1 Runner interface

Every runner implements:

```cpp
struct Runner {
    // Returns true if this runner can handle the given IR.
    // Called by RunnerResolver as one input to detection.
    bool supports(const ProblemIR&) const;

    // Produces build artifacts from the IR.
    // Never reads solution.cpp directly.
    BuildArtifacts generate(const ProblemIR&) const;

    // Returns the capabilities this runner provides for the given IR.
    // May differ per-problem (e.g., stress_test depends on type support).
    std::vector<Capability> capabilities(const ProblemIR&) const;
};
```

`BuildArtifacts` contains the content of `build/driver.cpp` and any auxiliary files
the runner needs. Artifacts are written to disk by the pipeline, not the runner.

### 5.2 FunctionRunner

Handles problems with a single function on a `Solution` class.

Generated driver structure:

```cpp
#include "../solution.cpp"
#include "../../include/lc.h"

int main() {
    while (has_input()) {
        auto param0 = parse<T0>();
        auto param1 = parse<T1>();
        // ...

        Solution sol;
        auto result = sol.functionName(param0, param1, ...);

        print(result);
    }
    return 0;
}
```

Capabilities: `run`, `benchmark`, `stress_test`, `multiple_cases`, `trace`.

Benchmark mode generates a separate driver that clones input before each iteration and
omits I/O:

```cpp
// Benchmark driver — I/O happens once, outside the timed loop
auto input = parse_all<Params>();
warmup(sol, input);

BenchmarkResult result;
for (int i = 0; i < N; i++) {
    auto cloned = clone(input);       // fresh copy per iteration
    auto t0 = now();
    sol.functionName(cloned...);
    result.record(now() - t0);
}
print_benchmark(result);
```

This measures the algorithm, not the harness.

### 5.3 StatefulClassRunner

Handles problems where the solution is a class with a constructor and multiple methods,
exercised through an operation array.

Input format:

```
["LRUCache","put","put","get","put","get","get"]
[[2],[1,1],[2,2],[1],[3,3],[1],[4]]
```

Generated driver structure:

```cpp
#include "../solution.cpp"
#include "../../include/lc.h"

int main() {
    while (has_input()) {
        auto ops  = parse<vector<string>>();
        auto args = parse<vector<vector<Value>>>();

        ClassName* obj = nullptr;
        vector<Value> outputs;

        for (size_t i = 0; i < ops.size(); i++) {
            emit_event("method_call", ops[i], args[i]);

            if (ops[i] == "ClassName") {
                obj = new ClassName(/* constructor args */);
                outputs.push_back(null_value());
                emit_event("method_return", null_value());
            }
            else if (ops[i] == "put") {
                obj->put(args[i][0], args[i][1]);
                outputs.push_back(null_value());
                emit_event("method_return", null_value());
                emit_snapshot(obj);             // if to_snapshot overload exists
            }
            else if (ops[i] == "get") {
                auto r = obj->get(args[i][0]);
                outputs.push_back(r);
                emit_event("method_return", r);
                emit_snapshot(obj);
            }
        }

        print(outputs);    // LeetCode format: [null,null,null,1,null,3]
        delete obj;
    }
    return 0;
}
```

The runner inspects the IR's `stateful_class.methods` to determine which methods return
`void` (emit `null`) and which return a value (emit the return value). This information
comes from the IR, not from parsing `solution.cpp` again.

Capabilities: `run`, `trace`, `replay`, `multiple_cases`.

Note: `benchmark` and `stress_test` are not in the default capability set for
StatefulClassRunner because meaningful benchmarking of stateful classes requires
problem-specific operation sequences. The user can enable them manually via
`problem.json`.

### 5.4 InteractiveRunner

Handles problems where the solution interacts with a hidden oracle (e.g.,
`guess(int num)` in Guess Number Higher or Lower).

Scope for v1: stateless oracles only. The mock holds the answer and returns the
appropriate response. Stateful oracles (call limits, ordering constraints) are out of
scope and documented as such.

Generated driver instantiates the mock, passes it to the solution function, and
verifies the result.

Capabilities: `run`, `trace`. Not `benchmark`, `stress_test`, or `replay` in v1.

### 5.5 Adding a new runner

1. Implement the `Runner` interface.
2. Register it with the `RunnerResolver`.
3. Add any new `Capability` values it introduces.
4. The rest of the framework requires no changes.

---

## 6. Core Library

The core library (`include/`) is header-only, depends only on the C++ standard library,
and is completely decoupled from the runner system. It is the only part of the framework
that `solution.cpp` would ever legitimately include — but as stated in Principle 1.1,
`solution.cpp` never does.

### 6.1 Parser — `include/parser.h`

Recursive template specialization. `parse<T>()` works for any `T` constructible from
the `CppType` hierarchy. Adding a new type requires one additional specialization.

```cpp
template<typename T> T parse();
bool has_input();
```

The parser reads from stdin. Whitespace and bracket formatting follow LeetCode's exact
notation. `null` and `NULL` are both accepted in tree/list input.

### 6.2 Printer — `include/printer.h`

```cpp
template<typename T> void print(const T& value);
```

Output always goes to stdout. The format matches LeetCode's output exactly so results
can be compared by eye. Supported types mirror the parser.

### 6.3 Debug library — `include/debug.h`

All output goes to stderr. Never mixed with stdout.

```cpp
// Variadic — accepts any combination of supported types
dbg(x);
dbg(i, j, k);
dbg(arr);
dbg(mp);
dbg(tree);
dbg(head);
dbg(grid);

// Named trace
trace(left, right);

// Iteration watcher — designed for DP tables
watch(dp);   // call inside a loop; prints value + caret at last-written index

// Debug levels
dbg(INFO,  arr);
dbg(WARN,  x);
dbg(ERROR, node);

// Compile-time level filter
#define LC_DEBUG_LEVEL WARN   // suppresses INFO

// Compile-time disable — all macros become no-ops
#define LC_NO_DEBUG
```

Color output is applied when `isatty(STDERR_FILENO)` is true and stripped otherwise.

### 6.4 Assertions — `include/assert.h`

```cpp
ASSERT_EQ(result, expected);
ASSERT_NEAR(result, expected, epsilon);
ASSERT_TRUE(condition);
```

Failure output includes a visual diff with `^` pointing to the first differing element.
Multiple assertions accumulate; a summary is printed at the end of each test case.

### 6.5 Timer — `include/timer.h`

```cpp
Timer t;
t.start();
// ...
t.stop();   // prints to stderr: [timer] 0.73 ms

// RAII variant
{ ScopeTimer t("label"); /* ... */ }   // prints on destruction
```

### 6.6 Snapshot API — `include/snapshot.h`

Opt-in. The framework provides a `SnapshotValue` type and an `emit_snapshot` function.
The user provides a `to_snapshot` overload for their class.

```cpp
// Framework-defined value tree (no JSON dependency)
struct SnapshotValue {
    using Object  = map<string, SnapshotValue>;
    using Array   = vector<SnapshotValue>;
    using Variant = variant<nullptr_t, bool, long long, double, string, Object, Array>;
    Variant data;
};

// User provides this for their class (optional)
SnapshotValue to_snapshot(const LRUCache& cache) {
    return SnapshotValue::Object{
        {"capacity", cache.capacity},
        {"size",     (long long)cache.map.size()},
        {"order",    /* MRU to LRU key list */}
    };
}
```

If `to_snapshot` is not provided, `emit_snapshot` is a no-op. Replay still works —
it shows operations and return values, just not internal state.

The `SnapshotValue` type is serialized into the trace log. The Renderer decides how to
display it (JSON, ASCII table, diagram). Serialization is a rendering concern, not a
snapshot concern.

### 6.7 Random generators — `include/random.h`

Used by the stress tester. Seeded deterministically so failures are reproducible.

```cpp
randomVector(n, lo, hi);
randomMatrix(rows, cols, lo, hi);
randomTree(n, lo, hi);
randomLinkedList(n, lo, hi);
randomGraph(n, num_edges);
randomString(n, charset);
```

### 6.8 Data structures — `include/tree.h`, `include/list.h`

LeetCode-compatible definitions, unchanged from standard LeetCode usage.

```cpp
struct TreeNode { int val; TreeNode *left, *right; TreeNode(int x); };
struct ListNode { int val; ListNode *next;          ListNode(int x); };
```

Visual tree printer:

```
print_tree(root);

      1
     / \
    2   3
     \
      4
```

Traversal helpers: `print_inorder`, `print_preorder`, `print_postorder`,
`print_levelorder`. Memory: `free_tree`, `free_list`.

### 6.9 Master header — `include/lc.h`

```cpp
#pragma once
#include <bits/stdc++.h>
#include "tree.h"
#include "list.h"
#include "parser.h"
#include "printer.h"
#include "debug.h"
#include "timer.h"
#include "assert.h"
#include "snapshot.h"
#include "random.h"
```

The generated driver includes only this.

---

## 7. Event Trace

Every execution produces a structured event log. The log is consumed by the Renderer
and stored by Storage. The execution engine does not know about rendering; the renderer
does not know about execution.

### 7.1 Event schema

```json
{ "event": "run_start",      "timestamp": 0 }
{ "event": "case_start",     "index": 0 }
{ "event": "method_call",    "method": "put", "args": [1, 5] }
{ "event": "method_return",  "value": null }
{ "event": "snapshot",       "type": "LRUCache", "state": { ... } }
{ "event": "assert_pass",    "case": 0 }
{ "event": "assert_fail",    "case": 0, "expected": "...", "got": "..." }
{ "event": "case_end",       "index": 0 }
{ "event": "run_end",        "stats": { "compile_ms": 410, "run_ms": 0.73, "peak_rss_mb": 3.2, "binary_kb": 84 } }
```

For FunctionRunner, the trace uses `function_call` / `function_return` instead of
`method_call` / `method_return`. The event schema is extensible; runners may emit
additional event types. Renderers ignore unknown event types.

### 7.2 Replay

`leetcode replay` reads the trace from Storage and passes it to `ReplayRenderer`.
Replay is deterministic given the same trace. Random inputs are captured in the trace
as a seed event so stress test failures can be reproduced exactly:

```json
{ "event": "random_seed", "seed": 47 }
```

The ReplayRenderer displays stateful class problems step by step:

```
─── Operation 1 ──────────────────────────────
LRUCache(2)

─── Operation 2 ──────────────────────────────
put(1, 1)
returned: null

  capacity : 2
  size     : 1
  order    : [1]

─── Operation 3 ──────────────────────────────
put(2, 2)
returned: null

  capacity : 2
  size     : 2
  order    : [2, 1]

─── Operation 4 ──────────────────────────────
get(1)
returned: 1

  capacity : 2
  size     : 2
  order    : [1, 2]    ← 1 promoted to MRU
```

State display only appears if `to_snapshot` is provided for the class.

### 7.3 Execution statistics

Appended to every run's terminal output (stderr):

```
────────────────────────────────
  compile time  :  0.41 s
  run time      :  0.73 ms
  peak memory   :  3.2 MB
  binary size   :  84 KB
────────────────────────────────
```

`peak_rss_mb` uses `/proc/self/peak_rss` on Linux and `getrusage` on macOS. If
unavailable, the field is omitted.

---

## 8. Storage

Storage is the persistence boundary. It is read at the start of a pipeline run and
written at the end. No stage reads from or writes to Storage directly; the pipeline
mediates access.

### 8.1 Owned data

- Per-problem: `problem.json` (IR fields that survive across runs: `solved`,
  `solve_time_ms`, `notes`, `benchmark_history`, `runner` override if manually set)
- Session state: `~/.lc/session.json` (streak, today's goals, recent activity)
- Trace log: `build/trace.json` (last run only; overwritten each run)

### 8.2 Separation from the pipeline

The pipeline is stateless between invocations. All persistent state lives in Storage.
A pipeline run that produces no user-visible output still writes to Storage if it
produces a trace or updates solved status.

---

## 9. CLI

The CLI is a thin dispatcher. Each command resolves to a named stage sequence and
invokes it. No business logic lives in CLI handlers.

```
leetcode fetch <id>         Source + Analyze + Generate artifacts
leetcode run                Analyze + Generate + Compile + Execute + Render
leetcode debug              Same as run, debug build, launches lldb
leetcode replay             Render(ReplayRenderer) from last trace
leetcode bench [--iters N]  Analyze + Generate(BenchmarkMode) + Compile + Execute + Render(BenchmarkRenderer)
leetcode stress [--iters N] Analyze + Compile(Release+Brute) + StressEngine + Render(StressRenderer)
leetcode gen                Analyze + Generate artifacts only (regenerates driver)
leetcode new <name>         Interactive problem setup wizard
leetcode stats              Render(StatsRenderer) from Storage
leetcode session            Display + update session goals from Storage
leetcode open <id>          Open folder in Zed + problem URL in browser
leetcode search <query>     Search problem titles and tags in Storage
leetcode auth <cookie>      Store LeetCode session cookie
leetcode note               Open README.md under My Notes section
```

### 9.1 Active problem resolution

Commands that operate on a problem folder resolve the active folder by:
1. The `--problem` flag if provided
2. The current working directory if it is a problem folder
3. The most recently accessed problem folder from Storage

### 9.2 Capability enforcement

Before invoking a capability (e.g., `replay`, `bench`, `stress`), the CLI checks the
active problem's IR for that capability. If the capability is absent:

```
✗ replay is not available for this problem.

  The active runner (FunctionRunner) does not support replay.
  Replay requires StatefulClassRunner or InteractiveRunner.

  If this problem should use a different runner, set it in problem.json:
    "runner": "stateful_class"
  Then run: leetcode gen
```

---

## 10. Fetch Pipeline

`leetcode fetch <id>` is the most important command. It sets up everything.

### 10.1 GraphQL query

Endpoint: `https://leetcode.com/graphql`

Query: `questionData` with fields:
- `questionId`, `title`, `difficulty`, `topicTags`, `acRate`
- `content` (HTML problem description)
- `codeSnippets` (starter code by language)
- `exampleTestcases` (raw example input)
- `hints`, `sampleTestCase`, `metaData` (contains function signature JSON)
- `companyTagStats` (Premium — omit gracefully if 403)
- `similarQuestions`

Authentication: session cookie from `~/.lc/session.json`, set with `leetcode auth`.

### 10.2 Artifacts created

```
problems/<id>_<slug>/
├── solution.cpp       ← LeetCode starter stub, exactly as provided
├── input.txt          ← example inputs, pre-populated
├── problem.json       ← serialized IR
└── README.md          ← title, difficulty, constraints, examples, hints
```

`build/` is created on first run, not on fetch. It contains no source files.

### 10.3 README structure

```markdown
# <id>. <Title>

**Difficulty:** Medium  
**Acceptance:** 58.3%  
**URL:** https://leetcode.com/problems/<slug>/

## Constraints
...

## Examples
...

## Hints
...

## Related Problems
...

---

## My Notes

**Time Complexity:**

**Space Complexity:**

**Key Insight:**

**Mistakes:**
```

The "My Notes" section is written by the user via `leetcode note`. The framework never
overwrites content below the `---` separator.

---

## 11. Stress Testing

`leetcode stress` requires a `brute.cpp` in the problem folder alongside `solution.cpp`.
`brute.cpp` implements the same class/function name and signature.

The stress engine:
1. Generates random input using `include/random.h`
2. Runs both binaries on the same input
3. Diffs stdout
4. Reports the first mismatch with the seed for reproduction

```
✗ Mismatch found on iteration 47

Input:
[3,1,4,1,5,9,2,6]
2

Solution : [5,3]
Brute    : [3,5]

Reproduce: leetcode stress --seed 47
```

Order-independent comparison: for problems where output order is unspecified (e.g., Top
K Frequent Elements), the stress engine sorts both outputs before comparing. This is
declared in `problem.json`:

```json
"output_order": "unordered"
```

---

## 12. Benchmark Mode

`leetcode bench` measures algorithm runtime, not harness overhead.

The benchmark runner:
1. Parses all inputs once, before timing
2. Runs a short warmup (10 iterations, discarded)
3. Runs N iterations (default 1000), cloning input before each
4. Reports mean, median, p95, p99, stddev

```
────────────────────────────────────────
  Benchmark: topKFrequent
  Iterations: 1000
  Input size: n=10000
────────────────────────────────────────
  mean    :  0.83 ms
  median  :  0.81 ms
  p95     :  1.12 ms
  p99     :  1.38 ms
  stddev  :  0.09 ms
────────────────────────────────────────
```

Results are appended to `benchmark_history` in `problem.json`. `leetcode bench
--compare` runs both `solution.cpp` and `solution2.cpp` and reports the delta.

---

## 13. Build System

Each problem compiles independently. No CMake, no Makefile, no shared build state.

### Release build

```bash
clang++ -std=c++20 -O2 \
    -I../../include \
    build/driver.cpp \
    -o build/solution
```

### Debug build

```bash
clang++ -std=c++20 -g -O0 \
    -fsanitize=address,undefined \
    -I../../include \
    build/driver.cpp \
    -o build/solution_debug
ASAN_OPTIONS=detect_leaks=1 ./build/solution_debug < input.txt
```

LeakSanitizer is enabled on debug builds via `ASAN_OPTIONS=detect_leaks=1`. On macOS,
LSan requires running under `leaks` separately — the debug task handles this
automatically.

Timeout enforcement (release builds only):

```bash
timeout 5s ./build/solution < input.txt
```

On TLE: `✗ Time Limit Exceeded (> 5s)`

`solution.cpp` is `#include`-d by `build/driver.cpp`, not compiled separately.

---

## 14. Folder Structure

```
cpp/
├── .zed/
│   └── tasks.json
│
├── include/
│   ├── lc.h
│   ├── parser.h
│   ├── printer.h
│   ├── debug.h
│   ├── timer.h
│   ├── assert.h
│   ├── snapshot.h
│   ├── tree.h
│   ├── list.h
│   └── random.h
│
├── cli/
│   ├── leetcode.py       ← CLI entry point
│   ├── fetch.py          ← GraphQL downloader
│   ├── analyze.py        ← Analyzer pipeline
│   ├── gen_driver.py     ← ArtifactGenerator (writes to build/)
│   ├── runners/
│   │   ├── function.py
│   │   ├── stateful_class.py
│   │   └── interactive.py
│   ├── stress.py
│   ├── bench.py
│   └── stats.py
│
└── problems/
    └── 146_lru_cache/
        ├── solution.cpp          ← only file you edit
        ├── brute.cpp             ← optional, for stress testing
        ├── input.txt
        ├── problem.json
        ├── README.md
        └── build/               ← gitignored
            ├── driver.cpp        ← ephemeral, regenerated on every run
            ├── driver.override.cpp  ← optional; used instead of generated driver
            ├── solution          ← compiled binary
            ├── solution_debug
            └── trace.json        ← last run's event log
```

---

## 15. Zed Integration

`.zed/tasks.json` defines tasks that can be triggered from the editor.

| Task | Action |
|---|---|
| **Run** | Release build → execute with 5s timeout → stdout + stderr to terminal |
| **Debug** | Debug build with ASan/UBSan → execute under `lldb` in a pane |
| **Generate Driver** | `leetcode gen` on current problem folder |
| **Stress Test** | Prompt for iterations → `leetcode stress` |
| **Bench** | `leetcode bench` on current problem folder |
| **Replay** | `leetcode replay` (reads last trace) |
| **Clean** | Remove `build/` under current problem folder |
| **New Problem** | `leetcode new` wizard |

Tasks resolve the active problem from the currently open file's directory.

---

## 16. Session Mode

`leetcode session` displays and manages daily goals.

```
────────────────────────────────────────
  Today's Goal: 5 problems (1 Easy, 3 Medium, 1 Hard)
  Progress    : 2 / 5
  Streak      : 14 days
────────────────────────────────────────
  Recent
  ✓ 146  LRU Cache           Medium   12:43
  ✓ 200  Number of Islands   Medium   08:21
────────────────────────────────────────
  Suggested
  → 42   Trapping Rain Water Hard
  → 739  Daily Temperatures  Medium
────────────────────────────────────────
```

Session state is owned by Storage. `solved` and `solve_time_ms` in `problem.json` are
written automatically when a run passes all assertions.

---

## 17. Clipboard Integration

`leetcode paste` reads the clipboard and writes it to `input.txt` in the active problem
folder. This replaces the open-file-paste-save workflow for updating example inputs.

Platform implementation: `pbpaste` on macOS, `xclip -o` or `xsel -o` on Linux.

The keyboard shortcut for "paste to input.txt" can be registered as a Zed task with a
keybinding (recommended: `⌘⇧V`).

---

## 18. What This Spec Deliberately Excludes

**Competitive programming helpers** (DSU, segment tree, Fenwick tree, sieve, modular
arithmetic) are out of scope. They belong in a separate `cp_helpers.h` copied into
individual solutions when needed.

**Multiple languages.** The IR is designed to be language-agnostic, and runner plugins
are the natural extension point for Java, Python, or Rust support. This is explicitly
deferred. v1 is C++ only.

**SQL and Shell problems.** Separate domains. Ignored by the framework.

**Stateful interactive oracles.** InteractiveRunner v1 handles stateless oracles only.
Problems with call limits or ordering constraints require a custom override driver.

**Fast I/O** (`ios_base::sync_with_stdio(false)`) is not in the harness. Add it inside
`solution.cpp` if a specific problem requires it. It does not belong in the framework.

**GUI replay.** The trace format supports it; the v1 renderer is terminal-only.

---

## Appendix: Capability Reference

| Capability | FunctionRunner | StatefulClassRunner | InteractiveRunner |
|---|---|---|---|
| `run` | ✓ | ✓ | ✓ |
| `multiple_cases` | ✓ | ✓ | — |
| `trace` | ✓ | ✓ | ✓ |
| `replay` | — | ✓ | — |
| `benchmark` | ✓ | opt-in | — |
| `stress_test` | ✓ | opt-in | — |

Capabilities marked `opt-in` are available but not auto-detected. Enable in
`problem.json`:

```json
"capabilities": ["benchmark", "stress_test"]
```
