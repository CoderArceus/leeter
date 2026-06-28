# Leeter - Comprehensive User Guide

Welcome to **Leeter**, your localized, high-performance, and feature-rich CLI environment for solving LeetCode problems in C++. Leeter abstracts away boilerplate code, generates optimized C++ execution drivers, performs rigorous stress testing, and tracks your progress statistics.

This guide covers everything you can do with Leeter.

---

## 1. Getting Started

### Fetching a Problem
To start working on a problem, use the `fetch` command with the problem's ID.
```bash
./leeter fetch <Problem ID>
```
**Example:** `./leeter fetch 1` (Fetches Two Sum).
This command queries the LeetCode API, creates a new folder in `problems/`, downloads the problem description into `README.md`, extracts the example test cases into `input.txt`, and generates a `solution.cpp` template containing the correct function signature.

### Editing Your Code
Simply open the `solution.cpp` inside the newly created folder (e.g., `problems/1_two_sum/solution.cpp`) and write your C++ solution.

---

## 2. Running and Debugging

### Executing Your Solution
To compile and run your solution against the test cases in `input.txt`, simply run:
```bash
./leeter run
```
*Note: If you run this from outside a problem directory, provide the path:*
```bash
./leeter run --problem problems/1_two_sum
```

### Adding Custom Test Cases
Test cases are stored in `input.txt`. For standard function runners, test cases are separated by **blank lines**.
To quickly add a test case from your clipboard, use:
```bash
./leeter paste
```
This reads your clipboard and automatically appends the contents to `input.txt`.

### Step-by-Step Replay Debugging
For complex data structures (like Linked Lists or Trees) or stateful classes (like `LRUCache`), standard output can be hard to follow. Run the replay tool:
```bash
./leeter replay
```
This enables an interactive prompt where you press `Enter` to step through the execution of each operation one by one, watching the internal state evolve!

---

## 3. Validation and Benchmarking

### Stress Testing (Differential Testing)
Not sure if your solution works for all edge cases? Write a simple, guaranteed-correct $O(N^2)$ brute-force solution in `brute.cpp`, and then run the stress tester:
```bash
./leeter stress
```
You can also specify the number of iterations (e.g., `--iters 10000`).
The stress tester dynamically generates random inputs, feeds them to both your `solution.cpp` and `brute.cpp`, and immediately flags any output mismatches, providing you with the exact PRNG seed and input array that caused the failure.

### Performance Benchmarking
Want to see how fast your solution *really* is?
```bash
./leeter bench
```
This command strips away all I/O overhead and isolates your function using `<chrono>`, running it 1,000 times to calculate the **Mean, Median, P95, P99, and Standard Deviation** in nanoseconds. The statistics are automatically saved to your `problem.json` history.

---

## 4. Tracking Your Progress

Leeter gamifies your learning and keeps track of everything you accomplish. Whenever you successfully `run` or `stress` test a problem, it is automatically marked as solved!

### View Your Session
```bash
./leeter session
```
Displays your **Current Streak**, your **Daily Goal**, your **Recent Solves**, and **Suggested Problems** (unsolved problems currently in your workspace).

**Update your Daily Goal:**
```bash
./leeter session --goal "5:1:3:1" 
```
*(Format is `Total : Easy : Medium : Hard`)*

### View Overall Statistics
```bash
./leeter stats
```
Calculates exactly how many Easy, Medium, and Hard problems you've solved out of the ones you've fetched, and displays your global average solution time in microseconds.

---

## 5. Organization and Polish

### Taking Notes
Want to jot down your thoughts, time complexities, or alternative approaches? 
1. Open the problem's README using Zed:
   ```bash
   ./leeter note --problem problems/1_two_sum
   ```
2. Scroll to the bottom and write under the `---` and `## My Notes` section.
3. If you ever `fetch` the problem again to reset the description, Leeter will **preserve** all your notes!

### Searching Your Workspace
Need to find that one Dynamic Programming problem you solved weeks ago?
```bash
./leeter search "dynamic programming"
```
This performs a fuzzy search across problem titles, LeetCode tags, and even the text inside your personal `README.md` notes.

### Editor Integrations
Leeter provides native integration adapters for major editors. You can find these in the `adapters/` folder.

#### Zed
Zed tasks are provided in `adapters/zed/tasks.json`.
To enable them, symlink or copy this file to your workspace's `.zed` folder:
```bash
mkdir -p .zed
ln -sf ../adapters/zed/tasks.json .zed/tasks.json
```
You can then open the Command Palette (`cmd-shift-p`) and type `task: spawn` to run commands like `Run`, `Bench`, and `Replay`.

#### VSCode
VSCode tasks and keybindings are provided in `adapters/vscode/`.
To enable them, symlink or copy them to your workspace's `.vscode` folder:
```bash
mkdir -p .vscode
ln -sf ../adapters/vscode/tasks.json .vscode/tasks.json
ln -sf ../adapters/vscode/keybindings.json .vscode/keybindings.json
```

#### Neovim
A Neovim Lua plugin is provided in `adapters/neovim/leetcode.lua`.
You can load it in your Neovim configuration (`init.lua`) by copying it to your `lua/` directory and calling `require('leetcode').setup()`. It will open a floating terminal for commands and pipe JSON test results directly into Neovim Diagnostics!

#### Emacs
An Emacs Lisp package is provided in `adapters/emacs/leetcode.el`.
You can load it in your Emacs configuration by adding the `adapters/emacs` directory to your `load-path` and adding `(require 'leetcode)`. It binds commands under `C-c l` by default.
