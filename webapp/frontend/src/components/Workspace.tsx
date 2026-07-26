import { useState, useEffect } from "react";
import { ActionBar } from "./ActionBar";
import { LoopTrackerViewer, type TrackEvent } from "./LoopTrackerViewer";
import { CodeViewer } from "./CodeViewer";
import { apiClient } from "../api/client";
import { AxiosError } from "axios";
import { cn } from "../lib/utils";

export function Workspace() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ message: string; details?: string } | null>(null);
  const [result, setResult] = useState<any>(null);
  const [traceEvents, setTraceEvents] = useState<TrackEvent[]>([]);
  const [selectedIteration, setSelectedIteration] = useState<number | null>(null);

  const [breakpoints, setBreakpoints] = useState<number[]>([]);
  const [watchExpressions, setWatchExpressions] = useState<string[]>([]);
  
  const [files, setFiles] = useState<{ [key: string]: string }>({});
  const [problemDir, setProblemDir] = useState<string>("problems/1_two_sum");
  const [problems, setProblems] = useState<string[]>([]);
  
  const [activeTab, setActiveTab] = useState<"statement" | "code" | "input" | "expected">("code");
  const [activeTestCaseIndex, setActiveTestCaseIndex] = useState<number>(0);
  const [showFetchModal, setShowFetchModal] = useState(false);
  const [fetchInput, setFetchInput] = useState("");
  const [isFetching, setIsFetching] = useState(false);
  const [consoleHeight, setConsoleHeight] = useState<number>(290);
  const [sidebarWidth, setSidebarWidth] = useState<number>(450);

  // Real, functioning IDE Settings with localStorage persistence
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [editorFont, setEditorFont] = useState(() => localStorage.getItem("leeter_font") || 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace');
  const [fontSize, setFontSize] = useState(() => Number(localStorage.getItem("leeter_font_size")) || 13);
  const [tabSize, setTabSize] = useState(() => Number(localStorage.getItem("leeter_tab_size")) || 4);

  const handleStartResizeConsole = (e: React.MouseEvent) => {
    e.preventDefault();
    const startY = e.clientY;
    const startHeight = consoleHeight;
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaY = startY - moveEvent.clientY;
      setConsoleHeight(Math.max(40, Math.min(650, startHeight + deltaY)));
    };
    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  const handleStartResizeSidebar = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const startWidth = sidebarWidth;
    const handleMouseMove = (moveEvent: MouseEvent) => {
      const deltaX = startX - moveEvent.clientX;
      setSidebarWidth(Math.max(260, Math.min(950, startWidth + deltaX)));
    };
    const handleMouseUp = () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
    };
    document.addEventListener("mousemove", handleMouseMove);
    document.addEventListener("mouseup", handleMouseUp);
  };

  useEffect(() => {
    apiClient.getProblems().then((data) => {
      setProblems(data);
      if (data.length > 0 && !data.includes("problems/1_two_sum")) {
        setProblemDir(data[0]);
      }
    }).catch(err => console.error("Failed to fetch problems:", err));
  }, []);

  useEffect(() => {
    const eventSource = new EventSource(`/api/workspace/events?problem_dir=${encodeURIComponent(problemDir)}`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setFiles(data);
      } catch (err) {
        console.error("Failed to parse workspace event:", err);
      }
    };
    eventSource.onerror = (err) => console.error("SSE connection error:", err);
    return () => eventSource.close();
  }, [problemDir]);

  const handleError = (err: unknown) => {
    if (err instanceof AxiosError && err.response) {
      const data = err.response.data;
      setError({ message: data.detail || err.message, details: data.stderr || data.raw_output });
    } else {
      setError({ message: err instanceof Error ? err.message : "Unknown error occurred" });
    }
  };

  const saveAllFiles = async () => {
    try {
      const promises: Promise<any>[] = [];
      if (files["solution.cpp"] !== undefined) {
        promises.push(apiClient.saveCode(problemDir, files["solution.cpp"]));
      }
      if (files["input.txt"] !== undefined) {
        promises.push(apiClient.saveTestCase(problemDir, files["input.txt"]));
      }
      if (files["expected.txt"] !== undefined) {
        promises.push(apiClient.saveExpected(problemDir, files["expected.txt"]));
      }
      if (files["problem_statement.txt"] !== undefined) {
        promises.push(apiClient.saveProblemStatement(problemDir, files["problem_statement.txt"]));
      }
      await Promise.all(promises);
    } catch (err) {
      console.error("Error auto-saving files:", err);
    }
  };

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setActiveTestCaseIndex(0);
    try {
      await saveAllFiles();
      const res = await apiClient.run(problemDir);
      setResult(res);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTrack = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    setSelectedIteration(null);
    try {
      await saveAllFiles();
      const events = await apiClient.trace(
        problemDir, 
        files["input.txt"], 
        breakpoints.length > 0 ? breakpoints : undefined, 
        watchExpressions.length > 0 ? watchExpressions : undefined
      );
      setTraceEvents(events);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleBreakpoint = (line: number) => {
    setBreakpoints(prev => 
      prev.includes(line) ? prev.filter(l => l !== line) : [...prev, line]
    );
  };

  const handleSave = async (filename: string, content: string, apiCall: (dir: string, content: string) => Promise<any>) => {
    try {
      await apiCall(problemDir, content);
    } catch (err) {
      console.error(`Failed to save ${filename}:`, err);
      setError({ message: `Failed to save ${filename}.` });
    }
  };

  const handleFetchSubmit = async () => {
    if (!fetchInput.trim()) return;
    setIsFetching(true);
    setError(null);
    try {
      const res = await apiClient.fetchProblem(fetchInput);
      const newProblems = await apiClient.getProblems();
      setProblems(newProblems);
      setProblemDir(res.folder);
      setShowFetchModal(false);
      setFetchInput("");
    } catch (err) {
      handleError(err);
    } finally {
      setIsFetching(false);
    }
  };

  const handleDeleteCurrentProblem = async () => {
    if (!confirm(`Are you sure you want to delete problem "${problemDir.replace('problems/', '')}"?`)) return;
    setLoading(true);
    setError(null);
    try {
      await apiClient.deleteProblem(problemDir);
      const newProblems = await apiClient.getProblems();
      setProblems(newProblems);
      if (newProblems.length > 0) {
        setProblemDir(newProblems[0]);
      }
      setResult(null);
      setTraceEvents([]);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const handleResetAllProblems = async () => {
    if (!confirm("Are you sure you want to reset your workspace and delete ALL downloaded problems?")) return;
    setLoading(true);
    setError(null);
    try {
      await apiClient.resetProblems();
      const newProblems = await apiClient.getProblems();
      setProblems(newProblems);
      if (newProblems.length > 0) {
        setProblemDir(newProblems[0]);
      }
      setResult(null);
      setTraceEvents([]);
      setShowSettingsModal(false);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  };

  const renderLeetCodeResult = () => {
    if (!result) return null;

    const stats = result.payload?.stats;
    const cases: Array<any> = result.payload?.cases || [];
    const currentCase = cases[activeTestCaseIndex] || cases[0];
    const isFail = result.status === 'fail' || (stats && stats.failed > 0);
    const isSuccess = !isFail && (result.status === 'pass' || (stats && stats.passed === stats.total && stats.total > 0));

    // Get matching raw input from input.txt if available
    const inputContent = files["input.txt"] || "N/A";
    const inputLines = inputContent.split("\n").filter(l => l.trim() !== "");
    const caseInput = inputLines[activeTestCaseIndex] !== undefined ? inputLines[activeTestCaseIndex] : inputContent;

    return (
      <div className="flex flex-col h-full bg-[#121216] text-gray-200 select-text overflow-hidden font-sans">
        {/* Status and Stats Header Bar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-[#27272a] bg-[#18181e] shrink-0">
          <div className="flex items-center gap-3">
            {isSuccess ? (
              <span className="text-[#2cbb5d] font-bold text-sm flex items-center gap-1.5">
                <span className="material-symbols-outlined text-[#2cbb5d] text-lg font-bold">check_circle</span>
                Accepted
              </span>
            ) : isFail ? (
              <span className="text-rose-400 font-bold text-sm flex items-center gap-1.5">
                <span className="material-symbols-outlined text-rose-400 text-lg font-bold">error</span>
                Wrong Answer
              </span>
            ) : (
              <span className="text-cyan-400 font-bold text-sm flex items-center gap-1.5">
                <span className="material-symbols-outlined text-cyan-400 text-lg font-bold">help_outline</span>
                Executed (Unverified)
              </span>
            )}
            {stats && (
              <span className="text-xs text-gray-300 font-medium bg-[#27272a]/60 px-2.5 py-0.5 rounded-full border border-white/5">
                {stats.passed} / {stats.total} test cases passed {stats.failed > 0 ? `(${stats.failed} failed)` : ""}
              </span>
            )}
          </div>

          {stats && (
            <div className="flex items-center gap-3 text-xs font-mono">
              {stats.run_ms !== undefined && (
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1c1c22] rounded-lg border border-[#27272a]">
                  <span className="text-gray-400">Runtime:</span>
                  <span className="text-cyan-300 font-bold">{stats.run_ms} ms</span>
                </div>
              )}
              {stats.binary_kb > 0 && (
                <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#1c1c22] rounded-lg border border-[#27272a]">
                  <span className="text-gray-400">Memory:</span>
                  <span className="text-purple-300 font-bold">{stats.binary_kb} KB</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Test Cases Details View */}
        <div className="flex-1 overflow-auto p-3">
          {cases.length > 0 ? (
            <div className="space-y-3 max-w-full">
              {/* Test Case Tabs */}
              <div className="flex items-center gap-2 border-b border-[#27272a]/80 pb-2 flex-wrap">
                {cases.map((c, i) => {
                  const isSelected = (activeTestCaseIndex === i) || (i === 0 && activeTestCaseIndex >= cases.length);
                  const casePass = c.status === 'pass';
                  const caseFail = c.status === 'fail';
                  const dotColor = casePass ? "bg-[#2cbb5d]" : caseFail ? "bg-rose-500" : "bg-cyan-400";
                  return (
                    <button
                      key={i}
                      onClick={() => setActiveTestCaseIndex(i)}
                      className={`px-3 py-1 rounded-lg font-semibold text-xs transition-all flex items-center gap-2 select-none ${
                        isSelected
                          ? "bg-[#272730] text-white border border-cyan-500/50 shadow-sm shadow-cyan-500/10"
                          : "bg-[#16161b] text-gray-400 hover:text-gray-200 border border-[#27272a]"
                      }`}
                    >
                      <span className={`w-2 h-2 rounded-full ${dotColor}`} />
                      Case {i + 1}
                    </button>
                  );
                })}
              </div>

              {/* Current Selected Case Cards */}
              {currentCase && (
                <div className="grid grid-cols-3 gap-3">
                  {/* Input */}
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider pl-0.5 flex items-center gap-1">
                      <span className="material-symbols-outlined text-xs text-blue-400">input</span> Input
                    </span>
                    <div className="p-2.5 bg-[#18181e] rounded-xl border border-[#27272a] font-mono text-xs text-gray-200 whitespace-pre-wrap select-all shadow-inner overflow-auto max-h-40">
                      {caseInput}
                    </div>
                  </div>

                  {/* Output */}
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider pl-0.5 flex items-center gap-1">
                      <span className="material-symbols-outlined text-xs text-purple-400">output</span> Output
                    </span>
                    <div className={`p-2.5 rounded-xl border font-mono text-xs whitespace-pre-wrap select-all shadow-inner overflow-auto max-h-40 ${
                      currentCase.status === 'pass'
                        ? "bg-[#18231c] text-[#34d399] border-[#2cbb5d]/30"
                        : currentCase.status === 'fail'
                        ? "bg-[#251618] text-rose-300 border-rose-500/30"
                        : "bg-[#181a22] text-cyan-300 border-cyan-500/30"
                    }`}>
                      {currentCase.got || JSON.stringify(currentCase, null, 2)}
                    </div>
                  </div>

                  {/* Expected */}
                  <div className="flex flex-col gap-1.5 min-w-0">
                    <span className="text-[11px] font-semibold text-gray-400 uppercase tracking-wider pl-0.5 flex items-center gap-1">
                      <span className="material-symbols-outlined text-xs text-emerald-400">check_box</span> Expected
                    </span>
                    {currentCase.expected ? (
                      <div className="p-2.5 bg-[#18181e] rounded-xl border border-[#27272a] font-mono text-xs text-emerald-300 whitespace-pre-wrap select-all shadow-inner overflow-auto max-h-40">
                        {currentCase.expected}
                      </div>
                    ) : (
                      <div className="p-2.5 bg-[#18181e]/60 rounded-xl border border-dashed border-[#27272a] font-sans text-xs text-zinc-400 italic whitespace-pre-wrap select-all shadow-inner overflow-auto max-h-40 flex flex-col gap-1">
                        <div className="flex items-center gap-1 text-cyan-400 font-semibold not-italic">
                          <span className="material-symbols-outlined text-[14px]">info</span> Unverified Case
                        </div>
                        <span>No expected output in expected.txt for this custom case. Add it in the expected.txt tab to enable automated verification!</span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <pre className="font-mono text-xs text-emerald-400 whitespace-pre-wrap">{JSON.stringify(result, null, 2)}</pre>
          )}
        </div>
      </div>
    );
  };

  return (
    <main className="flex-1 flex flex-col h-full overflow-hidden bg-[#09090B]">
      {/* Header */}
      <header className="h-11 border-b border-[#27272A] bg-[#121216] flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Futuristic Glowing Leeter Emblem */}
          <div className="flex items-center gap-2.5 mr-1 select-none">
            <div className="w-7 h-7 rounded-xl bg-gradient-to-tr from-cyan-500/20 via-emerald-500/20 to-blue-500/20 border border-cyan-400/60 flex items-center justify-center shadow-lg shadow-cyan-500/20 ring-1 ring-emerald-400/30">
              <span className="material-symbols-outlined text-cyan-300 text-[19px] drop-shadow-[0_0_8px_rgba(6,182,212,0.8)]">data_object</span>
            </div>
            <span className="font-extrabold tracking-tight text-sm text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-emerald-400 font-mono">Leeter</span>
          </div>

          {problems.length > 0 && (
            <div className="flex items-center gap-1.5">
              <div className="relative">
                <select 
                  value={problemDir} 
                  onChange={(e) => {
                    setProblemDir(e.target.value);
                    setTraceEvents([]);
                    setResult(null);
                  }}
                  className="bg-[#18181B] border border-[#27272A] hover:border-zinc-500 text-white font-mono text-xs rounded-lg focus:ring-0 focus:border-cyan-400 h-7 pl-2.5 pr-8 appearance-none cursor-pointer outline-none shadow-inner"
                >
                  {problems.map(p => (
                    <option key={p} value={p}>{p.replace('problems/', '')}</option>
                  ))}
                </select>
                <span className="material-symbols-outlined absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 text-[16px] pointer-events-none">expand_more</span>
              </div>
              <button
                onClick={handleDeleteCurrentProblem}
                title="Delete current problem folder from workspace"
                disabled={loading || problems.length === 0}
                className="bg-[#18181B] border border-[#27272A] hover:border-rose-500/50 hover:bg-rose-500/10 text-zinc-400 hover:text-rose-400 px-2 h-7 flex items-center justify-center rounded-lg transition-all shadow-inner disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[16px]">delete</span>
              </button>
            </div>
          )}
          <button 
            onClick={() => setShowFetchModal(true)}
            className="bg-[#18181B] border border-[#27272A] hover:border-cyan-500/50 hover:bg-cyan-500/10 text-white px-3 h-7 flex items-center gap-1.5 text-xs rounded-lg transition-all font-medium shadow-inner"
          >
            <span className="material-symbols-outlined text-[16px] text-cyan-400">cloud_download</span> Pull by ID
          </button>
        </div>

        <div className="flex items-center gap-3">
          <ActionBar 
            loading={loading}
            onRun={handleRun}
            onTrack={handleTrack}
          />
          <button
            onClick={() => setShowSettingsModal(true)}
            title="Configure Editor Font & Tab Indentation Settings"
            className="bg-[#18181B] border border-[#27272A] hover:border-zinc-500 hover:text-white text-zinc-400 px-3 h-7 flex items-center gap-1.5 text-xs rounded-lg transition-all font-medium"
          >
            <span className="material-symbols-outlined text-[16px] text-cyan-400">settings</span> Settings
          </button>
        </div>
      </header>

      {/* Split Pane Layout */}
      <div className="flex-1 flex min-h-0 overflow-hidden">
        {/* Left Column (Editor & Console) */}
        <div className="flex-1 flex flex-col min-w-0 min-h-0">
          
          {/* Editor Pane */}
          <div className="flex-1 flex flex-col min-h-0 min-w-0 bg-[#09090B] overflow-hidden">
            {/* Editor Tabs */}
            <div className="flex h-[34px] bg-[#121216] border-b border-[#27272A] overflow-x-auto no-scrollbar shrink-0">
              <div 
                onClick={() => setActiveTab("statement")}
                className={cn("flex items-center px-3.5 h-full font-mono text-xs cursor-pointer border-r border-[#27272A] transition-all select-none", 
                  activeTab === "statement" ? "bg-[#09090B] border-t-2 border-amber-400 text-white font-bold shadow-inner" : "border-t-2 border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-[#16161b]")}
              >
                <span className="material-symbols-outlined text-[15px] text-amber-400 mr-1.5">article</span> problem_statement.txt
              </div>
              <div 
                onClick={() => setActiveTab("code")}
                className={cn("flex items-center px-3.5 h-full font-mono text-xs cursor-pointer border-r border-[#27272A] transition-all select-none", 
                  activeTab === "code" ? "bg-[#09090B] border-t-2 border-cyan-400 text-white font-bold shadow-inner" : "border-t-2 border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-[#16161b]")}
              >
                <span className="material-symbols-outlined text-[15px] text-cyan-400 mr-1.5">code</span> solution.cpp
              </div>
              <div 
                onClick={() => setActiveTab("input")}
                className={cn("flex items-center px-3.5 h-full font-mono text-xs cursor-pointer border-r border-[#27272A] transition-all select-none", 
                  activeTab === "input" ? "bg-[#09090B] border-t-2 border-emerald-400 text-white font-bold shadow-inner" : "border-t-2 border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-[#16161b]")}
              >
                <span className="material-symbols-outlined text-[15px] text-emerald-400 mr-1.5">subject</span> input.txt
              </div>
              <div 
                onClick={() => setActiveTab("expected")}
                className={cn("flex items-center px-3.5 h-full font-mono text-xs cursor-pointer border-r border-[#27272A] transition-all select-none", 
                  activeTab === "expected" ? "bg-[#09090B] border-t-2 border-purple-400 text-white font-bold shadow-inner" : "border-t-2 border-transparent text-zinc-400 hover:text-zinc-200 hover:bg-[#16161b]")}
              >
                <span className="material-symbols-outlined text-[15px] text-purple-400 mr-1.5">fact_check</span> expected.txt
              </div>
            </div>
            
            {/* Editor Content with proper flex/scroll wrapper */}
            <div className="flex-1 min-h-0 overflow-hidden relative flex flex-col w-full">
              {activeTab === "statement" && (
                files["problem_statement.txt"] !== undefined ? (
                  <CodeViewer 
                    code={files["problem_statement.txt"] || "No problem statement loaded."} 
                    filename="problem_statement.txt" 
                    onChange={(newCode) => setFiles(prev => ({ ...prev, "problem_statement.txt": newCode }))}
                    onSave={() => handleSave("problem_statement.txt", files["problem_statement.txt"], apiClient.saveProblemStatement)}
                    fontFamily={editorFont}
                    fontSize={fontSize}
                    tabSize={tabSize}
                  />
                ) : <div className="h-full flex items-center justify-center text-zinc-500 text-xs font-mono">Loading problem statement...</div>
              )}
              {activeTab === "code" && (
                files["solution.cpp"] !== undefined ? (
                  <CodeViewer 
                    code={files['solution.cpp'] || ""} 
                    filename="solution.cpp" 
                    onChange={(newCode) => setFiles(prev => ({ ...prev, "solution.cpp": newCode }))}
                    onSave={() => handleSave("solution.cpp", files["solution.cpp"], apiClient.saveCode)}
                    breakpoints={breakpoints}
                    onBreakpointToggle={toggleBreakpoint}
                    fontFamily={editorFont}
                    fontSize={fontSize}
                    tabSize={tabSize}
                  />
                ) : <div className="h-full flex items-center justify-center text-zinc-500 text-xs font-mono">Loading solution.cpp...</div>
              )}
              {activeTab === "input" && (
                files["input.txt"] !== undefined ? (
                  <CodeViewer 
                    code={files["input.txt"]} 
                    filename="input.txt" 
                    onChange={(newCode) => setFiles(prev => ({ ...prev, "input.txt": newCode }))}
                    onSave={() => handleSave("input.txt", files["input.txt"], apiClient.saveTestCase)}
                    fontFamily={editorFont}
                    fontSize={fontSize}
                    tabSize={tabSize}
                  />
                ) : <div className="h-full flex items-center justify-center text-zinc-500 text-xs font-mono">Loading input.txt...</div>
              )}
              {activeTab === "expected" && (
                files["expected.txt"] !== undefined ? (
                  <CodeViewer 
                    code={files["expected.txt"]} 
                    filename="expected.txt" 
                    onChange={(newCode) => setFiles(prev => ({ ...prev, "expected.txt": newCode }))}
                    onSave={() => handleSave("expected.txt", files["expected.txt"], apiClient.saveExpected)}
                    fontFamily={editorFont}
                    fontSize={fontSize}
                    tabSize={tabSize}
                  />
                ) : <div className="h-full flex items-center justify-center text-zinc-500 text-xs font-mono">Loading expected.txt...</div>
              )}
            </div>
          </div>

          {/* Vertical Resizer Handle (Console Height) */}
          <div
            onMouseDown={handleStartResizeConsole}
            className="h-2.5 bg-[#121216] hover:bg-cyan-500/20 active:bg-cyan-500/30 border-t border-b border-[#27272A] cursor-row-resize flex items-center justify-center group transition-colors select-none flex-shrink-0 z-10"
            title="Drag vertically to resize Test Result Console"
          >
            <div className="w-10 h-1 bg-zinc-600 group-hover:bg-cyan-400 rounded-full transition-colors" />
          </div>

          {/* Console Pane (Bottom) */}
          <div 
            style={{ height: `${consoleHeight}px` }}
            className="border-t border-[#27272A] bg-[#09090B] flex flex-col flex-shrink-0 transition-[height] duration-0"
          >
            <div className="h-[30px] bg-[#121216] border-b border-[#27272A] flex items-center px-4 justify-between flex-shrink-0">
              <span className="font-bold tracking-wider text-[11px] text-gray-300 uppercase flex items-center gap-1.5">
                <span className="material-symbols-outlined text-cyan-400 text-sm font-bold">terminal</span>
                Test Result Console
              </span>
              <div className="flex gap-1.5">
                <span className="w-2 h-2 rounded-full bg-[#27272A]"></span>
                <span className="w-2 h-2 rounded-full bg-[#27272A]"></span>
                <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
              </div>
            </div>
            <div className="flex-1 min-h-0 overflow-auto">
              {error && (
                <div className="p-4">
                  <div className="text-red-400 bg-red-500/10 p-3.5 rounded-xl border border-red-500/20 font-mono text-xs shadow-sm">
                    <div className="font-bold text-sm mb-1.5 flex items-center gap-1.5">
                      <span className="material-symbols-outlined text-base">error</span>
                      [ERROR] {error.message}
                    </div>
                    {error.details && <pre className="mt-2.5 text-xs font-mono whitespace-pre-wrap opacity-90 bg-black/50 p-3 rounded-lg border border-red-500/20 overflow-auto">{error.details}</pre>}
                  </div>
                </div>
              )}
              {result && renderLeetCodeResult()}
              {!error && !result && (
                <div className="px-4 py-3.5 text-zinc-500 text-xs flex items-center gap-2 font-mono">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Ready to execute test cases or track loop iterations.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Horizontal Resizer Handle (Sidebar Width) */}
        <div
          onMouseDown={handleStartResizeSidebar}
          className="w-2.5 bg-[#121216] hover:bg-cyan-500/20 active:bg-cyan-500/30 border-l border-r border-[#27272A] cursor-col-resize flex flex-col items-center justify-center group transition-colors select-none flex-shrink-0 z-10"
          title="Drag horizontally to resize Loop Tracker panel"
        >
          <div className="w-1 h-10 bg-zinc-600 group-hover:bg-cyan-400 rounded-full transition-colors" />
        </div>

        {/* Right Column (Loop Tracker) */}
        <div 
          style={{ width: `${sidebarWidth}px` }}
          className="bg-[#09090B] border-l border-[#27272A] flex flex-col flex-shrink-0 min-h-0 transition-[width] duration-0"
        >
          <LoopTrackerViewer 
            events={traceEvents}
            selectedIteration={selectedIteration}
            onSelectIteration={setSelectedIteration}
            watchExprs={watchExpressions}
            onAddWatchExpr={(expr) => setWatchExpressions(prev => [...prev, expr])}
            onRemoveWatchExpr={(expr) => setWatchExpressions(prev => prev.filter(e => e !== expr))}
            selectedGutterLines={breakpoints}
            onClearGutterLines={() => setBreakpoints([])}
            loading={loading}
          />
        </div>
      </div>

      {/* Settings Modal */}
      {showSettingsModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121215] border border-[#27272A] rounded-2xl shadow-2xl p-6 w-[450px] text-gray-200 space-y-5">
            <div className="flex items-center justify-between border-b border-[#27272A] pb-3">
              <div className="flex items-center gap-2 text-white font-bold text-sm tracking-wide uppercase">
                <span className="material-symbols-outlined text-cyan-400">settings</span>
                Editor Preferences & Workspace
              </div>
              <button onClick={() => setShowSettingsModal(false)} className="text-zinc-500 hover:text-white transition-colors">
                <span className="material-symbols-outlined text-xl">close</span>
              </button>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-2 uppercase tracking-wider">Font Family</label>
              <select 
                value={editorFont} 
                onChange={(e) => {
                  setEditorFont(e.target.value);
                  localStorage.setItem("leeter_font", e.target.value);
                }}
                className="w-full bg-[#18181B] border border-[#27272A] rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 font-mono shadow-inner"
              >
                <option value='ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace'>System Monospace (Menlo / Consolas)</option>
                <option value='"JetBrains Mono", monospace'>JetBrains Mono</option>
                <option value='"Fira Code", monospace'>Fira Code</option>
                <option value='"SF Mono", monospace'>SF Mono</option>
                <option value='"Courier New", monospace'>Courier New</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-2 uppercase tracking-wider">Font Size ({fontSize}px)</label>
              <div className="grid grid-cols-3 gap-2">
                {[12, 13, 14, 15, 16, 18].map((size) => (
                  <button
                    key={size}
                    onClick={() => {
                      setFontSize(size);
                      localStorage.setItem("leeter_font_size", size.toString());
                    }}
                    className={cn("py-2 text-xs font-mono rounded-xl border transition-all shadow-sm", fontSize === size ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold shadow-cyan-500/10" : "bg-[#18181B] border-[#27272A] text-zinc-400 hover:text-white hover:bg-[#27272A]")}
                  >
                    {size}px
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-zinc-300 mb-2 uppercase tracking-wider">Tab Indentation Width</label>
              <div className="grid grid-cols-2 gap-2">
                {[2, 4].map((tab) => (
                  <button
                    key={tab}
                    onClick={() => {
                      setTabSize(tab);
                      localStorage.setItem("leeter_tab_size", tab.toString());
                    }}
                    className={cn("py-2 text-xs font-mono rounded-xl border transition-all shadow-sm", tabSize === tab ? "bg-cyan-500/20 border-cyan-400 text-cyan-300 font-bold shadow-cyan-500/10" : "bg-[#18181B] border-[#27272A] text-zinc-400 hover:text-white hover:bg-[#27272A]")}
                  >
                    {tab} Spaces
                  </button>
                ))}
              </div>
            </div>

            <div className="pt-3 border-t border-[#27272A]">
              <label className="block text-xs font-semibold text-rose-400 mb-2 uppercase tracking-wider flex items-center gap-1">
                <span className="material-symbols-outlined text-[16px]">warning_amber</span> Danger Zone
              </label>
              <button 
                onClick={handleResetAllProblems}
                disabled={loading}
                className="w-full py-2.5 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 hover:border-rose-500/60 text-rose-300 font-bold text-xs rounded-xl transition-all shadow-sm flex items-center justify-center gap-1.5 disabled:opacity-50"
              >
                <span className="material-symbols-outlined text-[16px]">delete_forever</span> Reset Workspace (Delete All Problems)
              </button>
            </div>

            <div className="flex justify-end pt-3 border-t border-[#27272A]">
              <button 
                onClick={() => setShowSettingsModal(false)}
                className="px-6 py-2 bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs rounded-xl transition-colors shadow-md shadow-cyan-500/20 uppercase tracking-wider"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fetch Modal */}
      {showFetchModal && (
        <div className="absolute inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#121215] border border-[#27272A] rounded-xl shadow-2xl p-6 w-96 text-gray-200">
            <div className="flex items-center gap-2 mb-2 text-white font-semibold text-base">
              <span className="material-symbols-outlined text-cyan-400">cloud_download</span>
              Pull LeetCode Problem
            </div>
            <p className="text-xs text-gray-400 mb-4 leading-relaxed">
              Enter the LeetCode problem ID (e.g., <strong className="text-cyan-300">1</strong>, <strong className="text-cyan-300">150</strong>) or paste the full problem URL.
            </p>
            <input 
              type="text" 
              value={fetchInput}
              onChange={e => setFetchInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleFetchSubmit()}
              placeholder="Problem ID (e.g. 1) or URL..."
              className="w-full bg-[#18181B] border border-[#27272A] rounded-lg px-3.5 py-2.5 text-xs mb-5 outline-none focus:border-cyan-500 text-white font-mono transition-colors shadow-inner"
              autoFocus
            />
            <div className="flex justify-end space-x-2.5">
              <button 
                onClick={() => setShowFetchModal(false)}
                className="px-4 py-2 text-xs font-medium hover:bg-[#27272A] text-gray-300 rounded-lg transition-colors border border-transparent"
                disabled={isFetching}
              >
                Cancel
              </button>
              <button 
                onClick={handleFetchSubmit}
                className="px-4 py-2 text-xs font-semibold bg-cyan-500 hover:bg-cyan-400 text-black rounded-lg transition-colors shadow-lg shadow-cyan-500/20 flex items-center gap-1.5 disabled:opacity-50"
                disabled={isFetching}
              >
                {isFetching ? (
                  <>
                    <span className="material-symbols-outlined text-sm animate-spin">progress_activity</span> Pulling...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-sm">download</span> Pull Problem
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
