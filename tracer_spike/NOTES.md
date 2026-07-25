# Tracer Engine Spike Findings

## LLDB MI Feasibility (No-Go)
Our spike verified that using GDB/LLDB Machine Interface (MI) is **not feasible** for this project.
While `gdb --interpreter=mi` works on Linux and Windows (MinGW), **Apple removed `lldb-mi` and `--interpreter=mi` support** from the standard Xcode toolchain several years ago. 

Running `lldb target.out --interpreter=mi` immediately results in:
`error: unknown option: --interpreter=mi`

Attempting to bundle or require users to compile a legacy version of `lldb-mi` would drastically harm the installation experience and reliability.

---

## Fallback Architecture: AST Instrumentation

Since we cannot rely on an external debugger process, we will rewrite the target C++ code **before compilation** to self-report its execution state via `stdout` (or a named pipe/file).

### 1. The Strategy
Instead of stepping line-by-line via `ptrace()`, we will use **Python's `clang.cindex` (libclang)** to parse the user's `solution.cpp`. We will traverse the Abstract Syntax Tree (AST) and automatically inject C++ macros/statements that serialize and print the local variables at every line of execution.

### 2. Instrumentation Example
**User's Original Code:**
```cpp
int target = 9;
for (int i = 0; i < nums.size(); i++) {
    int comp = target - nums[i];
    // ...
}
```

**Instrumented Code (generated behind the scenes):**
```cpp
int target = 9;
__TRACE_EVENT__(1, "int target = 9;", { {"target", to_string(target)} });

for (int i = 0; i < nums.size(); i++) {
    __TRACE_EVENT__(2, "for (int i = 0; i < nums.size(); i++) {", { {"target", to_string(target)}, {"i", to_string(i)} });
    
    int comp = target - nums[i];
    __TRACE_EVENT__(3, "int comp = target - nums[i];", { {"target", to_string(target)}, {"i", to_string(i)}, {"comp", to_string(comp)} });
    // ...
}
```

### 3. Pipeline
1. **Parse**: `clang.cindex.parse("solution.cpp")`
2. **Analyze**: Walk the AST to track variable declarations, scopes, and line numbers.
3. **Rewrite**: Insert the trace macro after every statement (or at the start of blocks).
4. **Compile & Run**: Compile the instrumented file. When run, it simply `printf`s JSON objects formatted strictly according to our `schema.json`.
5. **Consume**: The FastAPI backend captures `stdout` from the executed binary, parses the JSON stream, and forwards it to the React frontend.

### 4. Pros and Cons of AST Instrumentation
**Pros:**
* **100% Cross-Platform**: Depends only on a standard C++ compiler. No debugger quirks.
* **Extremely Fast**: Execution happens at native speed without the massive IPC overhead of stopping and resuming a debugger at every line.
* **No Hangs**: Subprocess timeout constraints (like we use in the `bench`/`stress` modules) work perfectly.

**Cons:**
* Requires a robust AST walker to correctly handle scope tracking.
* Does not support third-party library code stepping (but we only care about the user's `solution.cpp` anyway).
