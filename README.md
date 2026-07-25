# 🚀 Leeter
**Next-Gen C++ LeetCode Web IDE & Zero-Code Loop Tracker**

**Leeter** is a state-of-the-art local development environment and CLI suite designed for mastering LeetCode problems in C++. It eliminates boilerplate code, dynamically scaffolds test case drivers, and introduces an innovative **Zero-Code Gutter Loop Tracker** that visualizes variable mutations across iterations without ever altering your source files.

---

## ✨ Key Features & Innovations

### 🎯 1. Zero-Code Gutter Loop Tracking
Stop cluttering your algorithms with temporary debug prints or intrusive macros!
- **Interactive Gutter Selection**: Simply click line numbers in the editor gutter to mark your target loops or statements.
- **Dynamic Expression Watch**: Type variable names or complex expressions (e.g., `arr[z+1]`, `nums[i]`, `complement`, `z`) directly into the IDE tag watcher.
- **Dual Entry/Exit Harvester**: Leeter invisibly injects lightweight AST-aligned probes during temporary build compilation to record both initial block entry states and post-calculation mutated outcomes.
- **Un-Squished Stacked Cards**: Inspect every loop iteration in a dedicated right-hand sidebar featuring wide, two-tier transition cards (`old_value ➔ new_value`) with vibrant cyan badges and zero clipping.

### 🖥️ 2. Authentic LeetCode Test Result Console
Mirror the official LeetCode execution interface right in your local environment.
- **Status Tags**: Clear, high-contrast **Accepted** tags in rich emerald green with checkmark indicators, or **Wrong Answer / Runtime Error** alerts in bold rose.
- **Real-Time Execution Stats**: Displays precise runtime latency (`ms`) and binary footprint (`KB`) statistics.
- **Interactive Multi-Case Tabs**: Seamlessly switch between test cases (**Case 1**, **Case 2**, etc.) with live pass/fail status dots.
- **Structured Detail View**: Displays dedicated dark-themed monospace cards for **Input**, **Output**, and **Expected** results.

### 🎨 3. Rich Syntax Highlighting & Markdown Editor
- Integrated `prismjs` and `react-simple-code-editor` overlay featuring the sleek `prism-tomorrow` dark theme.
- Automatic grammar resolution for C++ (`solution.cpp`), Markdown, and structured testcase inputs (`input.txt`).
- Preserves exact 1-to-1 vertical scroll synchronization and line alignment with your custom tracking gutter.

### 📐 4. Interactive Splitter Panel Resizing
- Custom zero-dependency fluid drag splitters allow live 60-FPS resizing of both workspace panels without layout stutter.
- **Vertical Divider (`cursor-row-resize`)**: Adjust the height of the bottom Test Result console between 40px and 650px.
- **Horizontal Divider (`cursor-col-resize`)**: Adjust the width of the right Loop Tracker sidebar between 260px and 950px.
- Styled with subtle gray rails that illuminate with glowing neon borders and rounded drag handles upon hover and dragging.

### 📥 5. Direct Problem Scaffolding
Pull LeetCode problems instantly using their problem ID or URL slug:
```bash
leeter fetch 1846
```
Automatically scaffolds a dedicated directory in `problems/<id>_<slug>/` complete with boilerplate C++ solution code, sample inputs, and markdown descriptions.

---

## 🛠️ Installation & Quickstart

### Prerequisites
- **Python**: 3.11+
- **Node.js**: 18+ (for Web IDE)
- **C++ Compiler**: C++17 compatible (`clang++`, `g++`, or LLVM Apple Clang)
- **Git**: Latest version

### 1. Clone & Install Core CLI
```bash
git clone https://github.com/CoderArceus/leeter.git
cd leeter
pip install -e .
```

### 2. Build Frontend & Launch Web IDE
Leeter includes an integrated FastAPI backend and Vite React frontend stack:
```bash
# Build the production Vite React frontend
cd webapp/frontend
npm install && npm run build
cd ../..

# Launch the integrated Leeter DX Server
./leeter_dev.py
```
Open **`http://localhost:5173`** in your browser to experience the Web IDE!

---

## 📖 CLI Command Reference

You can operate Leeter entirely via terminal commands inside any problem directory or from the root:

| Command | Description |
| :--- | :--- |
| `leeter fetch <id>` | Scaffolds a new LeetCode problem template by ID or slug in `problems/`. |
| `leeter run` | Compiles your solution against the dynamic runner and executes `input.txt`. |
| `leeter trace` | Executes zero-code headless loop tracking with optional JSON structured output. |
| `leeter bench` | High-precision `<chrono>` execution latency analysis (Mean, Median, P95, P99). |
| `leeter stress` | Fuzz testing engine that validates your solution against a naive `brute.cpp`. |
| `leeter stats` | Analytics and streak tracking across your solved problem set. |

---

## 🧪 Testing & Verification

Leeter relies on a modular architecture (`leeter_core`) backed by a comprehensive automated pytest matrix:
```bash
# Run the full automated test suite
python3 -m pytest
```
Covering 17 complete test suites spanning AST source transformation, zero-code trace engine injection, stress fuzzing, analytics storage, and runner binaries.

---

## 📄 License
MIT License. Created and curated by **CoderArceus**.
