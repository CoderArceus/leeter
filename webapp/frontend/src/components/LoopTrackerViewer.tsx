import React, { useState } from "react";

export interface TrackEvent {
  line: number;
  iteration: number;
  vars: Record<string, string>;
  source?: "native" | "debugger";
}

interface LoopTrackerViewerProps {
  events: TrackEvent[];
  selectedIteration: number | null;
  onSelectIteration: (index: number | null) => void;
  watchExprs: string[];
  onAddWatchExpr: (expr: string) => void;
  onRemoveWatchExpr: (expr: string) => void;
  selectedGutterLines?: number[];
  onClearGutterLines?: () => void;
  loading?: boolean;
}

export const LoopTrackerViewer: React.FC<LoopTrackerViewerProps> = ({
  events,
  selectedIteration,
  onSelectIteration,
  watchExprs,
  onAddWatchExpr,
  onRemoveWatchExpr,
  selectedGutterLines = [],
  onClearGutterLines,
  loading = false,
}) => {
  const [newWatch, setNewWatch] = useState("");
  const [searchFilter, setSearchFilter] = useState("");

  const handleAddWatch = (e: React.FormEvent) => {
    e.preventDefault();
    if (newWatch.trim() && !watchExprs.includes(newWatch.trim())) {
      onAddWatchExpr(newWatch.trim());
      setNewWatch("");
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#09090b] text-gray-200 overflow-hidden font-sans">
      {/* Top Banner */}
      <div className="px-3.5 py-2.5 border-b border-[#27272a] flex items-center justify-between bg-[#121215]">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-cyan-400 text-lg animate-pulse">radar</span>
          <span className="font-semibold text-xs tracking-wider uppercase text-gray-200">Loop & Element Tracker</span>
          {events.length > 0 && (
            <span className="px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 font-mono font-bold">
              {events.length} {events.length === 1 ? "iteration" : "iterations"}
            </span>
          )}
        </div>
      </div>

      {/* Target Loop from Gutter Selection Panel */}
      <div className="p-3 border-b border-[#27272a] bg-[#0e0e11] space-y-2.5">
        <div>
          <div className="text-[10px] font-semibold tracking-wider text-gray-400 uppercase mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1 text-cyan-400">
              <span className="material-symbols-outlined text-sm">my_location</span> 1. TARGET LOOP FROM GUTTER
            </span>
            {selectedGutterLines.length > 0 && onClearGutterLines && (
              <button onClick={onClearGutterLines} className="text-[10px] text-gray-500 hover:text-red-400 transition-colors">
                Clear
              </button>
            )}
          </div>
          {selectedGutterLines.length > 0 ? (
            <div className="flex flex-wrap gap-1.5">
              {selectedGutterLines.map((line) => (
                <span key={line} className="inline-flex items-center gap-1 px-2.5 py-1 bg-cyan-500/10 border border-cyan-500/30 text-cyan-300 rounded text-xs font-mono font-medium shadow-sm">
                  <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                  Line {line} Selected
                </span>
              ))}
            </div>
          ) : (
            <div className="text-xs text-zinc-500 bg-[#141417] p-2 rounded border border-[#27272a]/70 italic flex items-center gap-1.5">
              <span className="material-symbols-outlined text-[15px] text-zinc-400">touch_app</span>
              Click any line number in the code gutter to target a loop.
            </div>
          )}
        </div>

        {/* Define Elements to Track */}
        <div className="pt-2 border-t border-[#27272a]/50">
          <div className="text-[10px] font-semibold tracking-wider text-gray-400 uppercase mb-1.5 flex items-center justify-between">
            <span className="flex items-center gap-1 text-emerald-400">
              <span className="material-symbols-outlined text-sm">tune</span> 2. DEFINE ELEMENTS TO TRACK
            </span>
            <span className="text-[10px] text-gray-500">Press enter to add</span>
          </div>
          <form onSubmit={handleAddWatch} className="flex gap-2">
            <input
              type="text"
              placeholder="e.g. i, nums[i], left, right, m"
              value={newWatch}
              onChange={(e) => setNewWatch(e.target.value)}
              className="flex-1 bg-[#18181b] border border-[#27272a] rounded px-2.5 py-1.5 text-xs text-gray-100 font-mono placeholder-gray-500 focus:outline-none focus:border-emerald-500 transition-colors"
            />
            <button
              type="submit"
              className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-black font-semibold rounded text-xs transition-colors flex items-center justify-center shadow-sm"
            >
              Add Element
            </button>
          </form>
          {watchExprs.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2.5">
              {watchExprs.map((expr) => (
                <span
                  key={expr}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#1c1c22] border border-emerald-500/30 text-emerald-300 rounded text-xs font-mono shadow-sm"
                >
                  {expr}
                  <button
                    onClick={() => onRemoveWatchExpr(expr)}
                    className="hover:text-red-400 ml-0.5 font-bold text-xs leading-none transition-colors"
                  >
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Search and Filter */}
      {events.length > 0 && (
        <div className="px-3 py-2 border-b border-[#27272a] bg-[#121216] flex items-center gap-2">
          <span className="material-symbols-outlined text-gray-500 text-sm">search</span>
          <input
            type="text"
            placeholder="Filter tracked variables..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="w-full bg-transparent text-xs text-gray-300 placeholder-gray-600 focus:outline-none font-mono"
          />
          {searchFilter && (
            <button
              onClick={() => setSearchFilter("")}
              className="text-gray-500 hover:text-gray-300 text-xs"
            >
              Clear
            </button>
          )}
        </div>
      )}

      {/* Main Iteration Timeline Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2.5">
        {loading && (
          <div className="flex flex-col items-center justify-center h-48 text-gray-400 gap-3">
            <span className="material-symbols-outlined animate-spin text-cyan-400 text-3xl">progress_activity</span>
            <div className="text-center">
              <span className="text-xs font-medium text-gray-200 block">Executing zero-code tracking...</span>
              <span className="text-[11px] text-gray-500 mt-0.5 block">Monitoring element mutations across iterations</span>
            </div>
          </div>
        )}

        {!loading && events.length === 0 && (
          <div className="mt-4 border border-dashed border-[#27272a] rounded-xl p-5 bg-[#121215] text-center max-w-sm mx-auto shadow-inner">
            <div className="w-12 h-12 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto mb-3">
              <span className="material-symbols-outlined text-2xl">track_changes</span>
            </div>
            <h3 className="text-sm font-semibold text-white mb-2">Zero-Code Loop Tracking</h3>
            <p className="text-xs text-gray-400 leading-relaxed mb-4">
              Track how element values mutate across outer loop iterations <strong className="text-cyan-300">without injecting macros or modifying your source code</strong>.
            </p>
            <div className="text-left bg-[#16161a] p-3 rounded-lg border border-[#27272a] space-y-2.5 text-xs text-gray-300 font-sans">
              <div className="flex items-start gap-2">
                <span className="w-5 h-5 rounded-full bg-cyan-500/20 text-cyan-300 font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5">1</span>
                <div>
                  <strong className="text-white block">Select Loop in Gutter</strong>
                  <span className="text-gray-400 text-[11px]">Click the line number next to your loop in the code editor.</span>
                </div>
              </div>
              <div className="flex items-start gap-2 pt-2 border-t border-[#27272a]/60">
                <span className="w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-300 font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5">2</span>
                <div>
                  <strong className="text-white block">Define Elements Above</strong>
                  <span className="text-gray-400 text-[11px]">Add any variable or array element name (e.g., <code className="text-emerald-300 bg-black/50 px-1 py-0.5 rounded">nums[i]</code>).</span>
                </div>
              </div>
              <div className="flex items-start gap-2 pt-2 border-t border-[#27272a]/60">
                <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-300 font-bold text-[11px] flex items-center justify-center shrink-0 mt-0.5">3</span>
                <div>
                  <strong className="text-white block">Hit Track Elements</strong>
                  <span className="text-gray-400 text-[11px]">Click <strong className="text-cyan-400">Track Elements</strong> in the top action bar to inspect every iteration diff!</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {!loading && events.length > 0 && events.map((ev, index) => {
          const prevEv = index > 0 ? events[index - 1] : null;
          const isSelected = selectedIteration === index;

          // Filter vars by search
          const entries = Object.entries(ev.vars).filter(([k]) => 
            k.toLowerCase().includes(searchFilter.toLowerCase())
          );

          // Check if any variable changed in this iteration
          let hasMutations = false;
          if (prevEv) {
            for (const [key, val] of Object.entries(ev.vars)) {
              if (prevEv.vars[key] !== val) {
                hasMutations = true;
                break;
              }
            }
          } else {
            hasMutations = true;
          }

          return (
            <div
              key={index}
              onClick={() => onSelectIteration(isSelected ? null : index)}
              className={`border rounded-xl transition-all cursor-pointer overflow-hidden shadow-sm ${
                isSelected
                  ? "border-cyan-500 bg-[#18181e] shadow-md shadow-cyan-500/10 ring-1 ring-cyan-500"
                  : "border-[#27272a] bg-[#141418] hover:bg-[#18181c]"
              }`}
            >
              {/* Iteration Header */}
              <div className="px-3.5 py-2 border-b border-[#27272a]/70 flex items-center justify-between bg-[#1a1a20]/60">
                <div className="flex items-center gap-2.5">
                  <span className="px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 flex items-center justify-center font-mono text-xs font-bold shadow-inner">
                    #{ev.iteration}
                  </span>
                  <span className="text-xs font-semibold text-gray-100">
                    Iteration {ev.iteration}
                  </span>
                  <span className="text-[11px] text-gray-400 font-mono bg-black/30 px-1.5 py-0.5 rounded border border-white/5">
                    Line {ev.line}
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  {hasMutations && index > 0 && (
                    <span className="px-2 py-0.5 rounded text-[10px] bg-amber-500/15 text-amber-300 font-semibold border border-amber-500/30 tracking-wide">
                      ⚡ MUTATED
                    </span>
                  )}
                  <span className="px-2 py-0.5 rounded text-[10px] bg-cyan-500/10 text-cyan-400 font-medium border border-cyan-500/20">
                    {ev.source === "debugger" ? "LLDB Harvester" : "Zero-Code Track"}
                  </span>
                </div>
              </div>

              {/* Variables Mutation Table */}
              <div className="p-3 font-mono text-xs space-y-1.5">
                {entries.length === 0 && (
                  <div className="py-1 text-gray-500 text-[11px] italic">No elements matching filter.</div>
                )}
                {entries.map(([varName, currentVal]) => {
                  const prevVal = prevEv ? prevEv.vars[varName] : undefined;
                  const isChanged = prevVal !== undefined && prevVal !== currentVal;
                  const isNew = prevVal === undefined;

                  if (isChanged) {
                    return (
                      <div
                        key={varName}
                        className="py-2.5 px-3 rounded-lg bg-cyan-500/10 border border-cyan-500/30 flex flex-col gap-2 shadow-sm"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white select-all flex items-center gap-1.5 text-xs">
                            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
                            {varName}
                          </span>
                          <span className="text-[10px] uppercase font-semibold tracking-wider px-1.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300">
                            Mutated
                          </span>
                        </div>
                        <div className="flex items-center gap-2.5 text-xs font-mono bg-black/30 p-2 rounded border border-white/5 flex-wrap">
                          <span className="text-rose-300 line-through text-xs bg-rose-500/15 px-2 py-0.5 rounded border border-rose-500/30">
                            {prevVal}
                          </span>
                          <span className="material-symbols-outlined text-sm text-cyan-400 font-extrabold">
                            arrow_forward
                          </span>
                          <span className="text-cyan-200 font-extrabold bg-cyan-500/25 px-2.5 py-0.5 rounded border border-cyan-400 shadow-sm text-xs">
                            {currentVal}
                          </span>
                        </div>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={varName}
                      className="py-2 px-2.5 rounded-lg flex items-center justify-between gap-3 text-gray-300 hover:bg-[#1b1b22] transition-colors border border-transparent"
                    >
                      <span className="font-semibold text-gray-400 shrink-0 select-all text-xs">
                        {varName}
                      </span>
                      <div className="flex items-center text-right">
                        {isNew && index > 0 ? (
                          <span className="text-emerald-300 bg-emerald-500/15 px-2 py-0.5 rounded border border-emerald-500/30 text-xs font-mono">
                            {currentVal} <span className="text-[10px] text-emerald-400 opacity-80">(new)</span>
                          </span>
                        ) : (
                          <span className="text-gray-200 select-all bg-black/20 px-2 py-0.5 rounded border border-white/5 text-xs font-mono">
                            {currentVal}
                          </span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
