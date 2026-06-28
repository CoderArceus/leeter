# 🚀 Leeter

**Leeter** is a high-performance CLI environment for solving LeetCode problems locally in C++.

It handles the boilerplate, generates execution drivers, and tracks your progress—all from your terminal and favorite IDE.

---

## ✨ Features

| Feature | Description |
| :--- | :--- |
| **⚡️ Fetch** | Automatically downloads problems, constraints, and test cases straight into a local `problems/` directory. |
| **🧠 Auto-Driver** | No `main()` needed. Leeter dynamically generates a C++ driver matching your function signature. |
| **🛡️ Stress Testing** | Compare your solution against a naive `brute.cpp` on randomized inputs to find edge-case failures. |
| **⏱️ Benchmarking** | High-precision `<chrono>` timing reports mean, median, P95, and P99 latencies. |
| **⏪ Replay & Snapshot**| Step through state mutations one-by-one. Pause execution anywhere using the `SNAPSHOT()` macro. |
| **📈 Analytics** | Gamified session tracking, daily streaks, and topic/difficulty progress. |
| **🔌 IDE Native** | Auto-configured task bindings and inline diagnostics for Zed, VSCode, Neovim, and Emacs. |

---

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/CoderArceus/leeter.git
   cd leeter
   ```

2. **Alias the CLI (in `~/.zshrc` or `~/.bashrc`):**
   ```bash
   alias leeter="python3 $(pwd)/cli/leeter.py"
   ```

3. *(Optional)* **Authenticate for premium problems:**
   ```bash
   leeter auth "YOUR_LEETCODE_SESSION_COOKIE"
   ```

---

## 📖 Usage Guide

Run commands from inside any problem folder. Leeter will automatically resolve your active context.

### 📥 1. Start a Problem
```bash
leeter fetch 1
```
Downloads "Two Sum" (ID 1) and scaffolds `solution.cpp`, `input.txt`, and a `README.md`.

### 🏃 2. Run & Debug
```bash
leeter run      # Compiles and runs against input.txt
leeter debug    # Launches lldb with Address/UB Sanitizers
```

### ⏱️ 3. Test & Optimize
```bash
leeter bench --iters 1000   # Benchmarks execution latency
leeter stress --iters 1000  # Fuzz tests against brute.cpp
```

---

## ⏪ Replay & Visual Debugging

Debugging stateful problems (like `LRUCache`) is notoriously difficult. `leeter replay` solves this.

```bash
leeter replay
```

**How it works:**
Step through operations sequentially by pressing `Enter`. After each step, Leeter reveals the invoked method, arguments, and return values, letting you watch the internal state mutate in real-time.

**The `SNAPSHOT()` Macro:**
Inject `SNAPSHOT(var1, var2)` anywhere in your C++ code. The replay engine will automatically pause execution when it hits the macro and display the live variable values!

```cpp
for (int i = 0; i < n; i++) {
    sum += nums[i];
    SNAPSHOT(i, sum); // Replay will pause here!
}
```

---

## 🔌 IDE Integration

Leeter supports deep integration with your favorite editor. 
Run the setup command from the repository root:

```bash
leeter setup vscode      # VSCode tasks
leeter setup zed         # Zed tasks
leeter setup neovim      # Neovim virtual-text diagnostics
leeter setup emacs       # Emacs compile-mode
```

*(Pass `--dry-run` to preview the exact config files that will be generated.)*
