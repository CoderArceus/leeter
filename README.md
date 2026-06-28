# 🚀 Leeter

**Leeter** is a localized, high-performance, and feature-rich CLI environment for solving LeetCode problems in C++. 

It abstracts away boilerplate code, generates optimized C++ execution drivers, performs rigorous stress testing, and tracks your progress statistics—all right from your terminal and favorite IDE.

---

## ✨ Features

- **⚡️ Automated Scaffolding:** `fetch` problems directly using the LeetCode API. The problem description, constraints, and test cases are parsed automatically into `README.md` and `input.txt`, alongside a fresh C++ stub (`solution.cpp`).
- **🧠 Seamless Local Execution:** Compile and run solutions without boilerplate. Leeter intelligently analyzes your `solution.cpp` stub and dynamically generates a correct `driver.cpp` customized to the problem's function signature or stateful class.
- **🛡️ Stress Testing (Differential Testing):** Provide a `brute.cpp` solution and use the `stress` command to automatically generate random inputs and compare outputs until an edge-case mismatch is found.
- **⏱️ Performance Benchmarking:** The `bench` command runs your isolated function with high-precision `<chrono>` timing to report mean, median, P95, and P99 performance.
- **⏪ Interactive Replay:** The `replay` command allows you to step through operations one by one. This is especially useful for stateful classes like `LRUCache` to watch exactly how the internal state mutates after every method call.
- **📈 Session & Analytics:** Leeter gamifies your process by tracking daily streaks, goals (`total:easy:medium:hard`), and overall metrics using the `session` and `stats` commands.
- **🔌 Editor Integrations:** Out-of-the-box adapters and task bindings for Zed, VSCode, Neovim, and Emacs.

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CoderArceus/leeter.git
   cd leeter
   ```

2. **Alias the CLI:**
   For easy access, add an alias to your shell profile (`~/.zshrc` or `~/.bashrc`):
   ```bash
   alias leeter="python3 $(pwd)/cli/leeter.py"
   ```

3. **Authenticate (Optional but recommended):**
   To fetch premium problems and company tags, provide your LeetCode session cookie.
   ```bash
   leeter auth "YOUR_LEETCODE_SESSION_COOKIE"
   ```

---

## 📖 Usage Guide

Leeter operates inside specific problem directories under the `problems/` folder. Most commands intelligently resolve the active problem if you run them from inside a problem directory.

### 📥 Fetching a Problem
```bash
leeter fetch 1
```
Downloads problem "Two Sum" (ID 1) from LeetCode, parses constraints and examples into `input.txt`, creates `README.md`, and generates a clean `solution.cpp` stub.

### 🏃 Running a Solution
```bash
leeter run
```
Analyzes your `solution.cpp`, automatically generates an optimized C++ driver in `build/driver.cpp`, compiles your code with C++20, and runs it against `input.txt`.

### 🐛 Debugging
```bash
leeter debug
```
Compiles with `-g -O0` and Address/UndefinedBehavior Sanitizers enabled. Launches `lldb` for interactive debugging.

### ⏱️ Benchmarking
```bash
leeter bench --iters 1000
```
Runs your solution thousands of times in an isolated high-precision `<chrono>` loop and reports percentile latency (P95, P99) and standard deviation.

### 🧨 Stress Testing
```bash
leeter stress --iters 1000
```
Compares the output of your `solution.cpp` against a naive `brute.cpp` on randomly generated inputs until a mismatch occurs. Great for finding edge-case bugs without submitting to LeetCode!

### ⏪ Replaying (Stateful problems)
```bash
leeter replay
```
**How it works:** When solving a stateful design problem (like `LRUCache` or `MinStack`), LeetCode typically gives you a sequence of operations like `["LRUCache", "put", "put", "get"]`. 

Using `leeter replay` allows you to **step through these operations one by one manually** by pressing `Enter`. After each operation, Leeter will pause execution and print the exact method that was called, its arguments, and the result. This gives you complete visibility into how your class's internal state is mutating over time, making it much easier to isolate where things go wrong!

### 📊 Session and Stats
- `leeter session`: View your current daily streak, goals, and recent activity.
- `leeter stats`: View overall progress by difficulty and topic tags.

---

## 🛠️ Core Library (`lc.h`)

Leeter includes a master header `lc.h` that is automatically included in all drivers. It provides:
- Data structure definitions matching LeetCode exactly (`TreeNode`, `ListNode`).
- Built-in type parsers and printers.
- Debugging utilities (`dbg`, `trace`, `watch`).
- Visual assertions (`ASSERT_EQ` with diffing).
- Random generators (`randomVector`, `randomTree`, etc.) used internally for stress testing.

---

## 🔌 Editor Integrations

Leeter supports multiple IDEs and allows you to configure your editor to run Leeter tasks directly via keyboard shortcuts automatically. 

The integration scripts are highly advanced:
- **Neovim** dynamically intercepts `leeter run --json` to inject LeetCode test failures as inline virtual text diagnostics directly into your buffer!
- **Emacs** creates a highly polished minor-mode `leeter-mode` that binds keys dynamically and integrates beautifully with `compile-mode`. 

Run the setup command for your editor from the root of the repository:

- **Zed**: `leeter setup zed` (and optionally `--keybindings`)
- **VSCode**: `leeter setup vscode` (and optionally `--keybindings`)
- **Neovim**: `leeter setup neovim`
- **Emacs**: `leeter setup emacs`
- **All Installed**: `leeter setup all`

*Note: You can pass `--dry-run` to any setup command to see exactly what files will be written before committing to the changes.*
