# Leeter Project Renovation Status

## Core Goal
Transform `leeter` into a high-performance, focused development tool with two primary superpowers:
1. **Effortless Problem Pulling**: Pull problems from LeetCode cleanly using just the Problem ID or URL.
2. **Advanced Loop & Element Tracking**: An intuitive, powerful tracking system that allows developers to select elements/variables and see exactly how their values evolve and change across loop iterations without clutter or friction.
3. **Streamlined UI/UX**: Remove unnecessary noise (Benchmark, Stress test, Brute force comparison tab) to make the workflow clean and state-of-the-art.

## Current Progress & Milestones

- [x] **Phase 1: Native C++ Loop Tracking API (`include/tracker.h`)**
  - Create `include/tracker.h` with a powerful variadic `TRACK(var1, var2, ...)` macro.
  - Automatically records line number, iteration count, and JSON-serialized string values of all watched elements.
  - Integrate `#include "tracker.h"` into `include/lc.h`.

- [x] **Phase 2: Backend Tracking & Iteration Harvester Engine (`leeter_core/tracer/engine.py`)**
  - Renovate the tracking engine to capture both native `TRACK(...)` loop outputs AND automatic LLDB/GDB watch expression harvesting across breakpoint iterations.
  - Provide unified structured iteration history with variable mutation calculation.
  - Simplify endpoints in `webapp/routers/trace.py` and `webapp/routers/workspace.py`.

- [x] **Phase 3: Streamline & Purge Clutter in the Web UI**
  - Clean out Benchmark, Stress, and `Brute.cpp` tabs from `ActionBar.tsx`, `Workspace.tsx`, and `Sidebar.tsx`.
  - Build the new state-of-the-art **Loop Tracker / Iteration Inspector** pane with value change diffing (old value ➔ new value highlighted when mutated across iterations).

- [x] **Phase 4: End-to-End Verification**
  - Verify pulling by problem ID works flawlessly.
  - Run verification tests on loop tracking with a real multi-iteration problem (like Two Sum) to verify instant visibility of variable changes across loop iterations.

## Zero-Code Gutter Tracking & UI Precision Enhancements
- [x] **Backend Dual Entry/Exit Probing (`leeter_core/tracer/engine.py`)**
  - Upgraded zero-code injection to probe both at block opening (entry state) and right before the matching closing brace (exit state after mutation).
  - Ensures final calculation outcomes of every iteration are captured before loop condition exit occurs.
- [x] **UI Un-Squished Mutation & LeetCode Console Overhaul (`LoopTrackerViewer.tsx`, `Workspace.tsx`)**
  - Removed "Highlight mutations only" filter option since loop elements naturally transition and mutate across iterations.
  - Replaced horizontal scroll boxes with a wide (450px) two-tier stacked layout for variable mutations (`old_value ➔ new_value`), eliminating gray scrollbars and visual squishing.
  - Transformed raw JSON console output into an authentic **LeetCode Test Result Section** complete with **Accepted/Wrong Answer** status tags, runtime/memory statistic badges, multi-testcase navigation tabs, and dedicated dark cards for **Input**, **Output**, and **Expected** values.
- [x] **Code Syntax Highlighting, Markdown & Interactive Panel Resizing (`CodeViewer.tsx`, `Workspace.tsx`)**
  - Integrated `prismjs` and `react-simple-code-editor` into [CodeViewer.tsx](file:///Users/aryan/leeter/webapp/frontend/src/components/CodeViewer.tsx) with dark syntax themes for C++, Markdown, and JSON while retaining 100% synchronized custom Gutter Loop Tracking.
  - Resolved Vite development server CommonJS/ESM module interop (`(EditorComponent as any).default || EditorComponent`) to prevent React DOM component object errors during live development.
  - Added smooth interactive drag bars (splitters with `cursor-col-resize` and `cursor-row-resize`, glowing cyan active states, and pill handles) allowing live resizing of both the bottom Test Result console and the right Loop Tracker sidebar without stutter.

## Status Summary
✨ **Syntax Highlighting & Interactive Panel Resizing Complete!** The code editor now features vibrant dark-mode C++/Markdown syntax highlighting while maintaining zero-code gutter loop selection and complete Vite dev compatibility. Users can also dynamically resize both the bottom Test Result console and right Loop Tracker panels with drag handles. All 17 automated pytest suites verified passing!
