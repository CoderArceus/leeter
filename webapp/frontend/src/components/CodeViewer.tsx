import React, { useRef, useState } from "react";
import { cn } from "../lib/utils";
import EditorComponent from "react-simple-code-editor";
import PrismImport from "prismjs";
import "prismjs/components/prism-clike";
import "prismjs/components/prism-c";
import "prismjs/components/prism-cpp";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-json";
import "prismjs/themes/prism-tomorrow.css";

const Editor = (EditorComponent as any).default || EditorComponent;
const Prism = (PrismImport as any).default || PrismImport || (window as any).Prism;

interface HistoryState {
  undoStack: string[];
  redoStack: string[];
  lastEditTime: number;
}
const fileHistories: Record<string, HistoryState> = {};

function getHistory(filename: string): HistoryState {
  if (!fileHistories[filename]) {
    fileHistories[filename] = { undoStack: [], redoStack: [], lastEditTime: 0 };
  }
  return fileHistories[filename];
}

interface CodeViewerProps {
  className?: string;
  code: string;
  filename?: string;
  onChange?: (newCode: string) => void;
  onSave?: () => void;
  breakpoints?: number[];
  onBreakpointToggle?: (line: number) => void;
  fontFamily?: string;
  fontSize?: number;
  tabSize?: number;
}

export function CodeViewer({ 
  className, 
  code, 
  filename = "solution.cpp", 
  onChange, 
  onSave, 
  breakpoints = [], 
  onBreakpointToggle,
  fontFamily = 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
  fontSize = 13,
  tabSize = 4
}: CodeViewerProps) {
  const gutterRef = useRef<HTMLDivElement>(null);
  const [isSaved, setIsSaved] = useState(false);
  const computedLineHeight = Math.max(20, Math.round(fontSize * 1.6));

  const hist = getHistory(filename);
  const canUndo = hist.undoStack.length > 0;
  const canRedo = hist.redoStack.length > 0;

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const handleCodeChange = (newCode: string) => {
    if (newCode === code) return;
    const now = Date.now();
    // Record undo step if paused for >500ms, stack is empty, or large edit occurred
    if (now - hist.lastEditTime > 500 || hist.undoStack.length === 0 || Math.abs(newCode.length - code.length) > 5) {
      hist.undoStack.push(code);
    }
    hist.redoStack = [];
    hist.lastEditTime = now;
    if (isSaved) setIsSaved(false);
    if (onChange) onChange(newCode);
  };

  const handleUndo = () => {
    if (hist.undoStack.length === 0) return;
    const prevCode = hist.undoStack.pop()!;
    hist.redoStack.push(code);
    hist.lastEditTime = 0;
    if (isSaved) setIsSaved(false);
    if (onChange) onChange(prevCode);
  };

  const handleRedo = () => {
    if (hist.redoStack.length === 0) return;
    const nextCode = hist.redoStack.pop()!;
    hist.undoStack.push(code);
    hist.lastEditTime = 0;
    if (isSaved) setIsSaved(false);
    if (onChange) onChange(nextCode);
  };

  const handleManualSave = () => {
    if (onSave) {
      onSave();
      setIsSaved(true);
      setTimeout(() => setIsSaved(false), 2500);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if ((e.ctrlKey || e.metaKey) && (e.key === 's' || e.key === 'S')) {
      e.preventDefault();
      handleManualSave();
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'z' || e.key === 'Z')) {
      e.preventDefault();
      if (e.shiftKey) {
        handleRedo();
      } else {
        handleUndo();
      }
    } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || e.key === 'Y')) {
      e.preventDefault();
      handleRedo();
    }
  };

  const getSyntaxHighlight = (codeText: string) => {
    let grammar = Prism.languages.cpp;
    let languageName = "cpp";

    if (filename.endsWith(".md") || filename.endsWith(".markdown")) {
      grammar = Prism.languages.markdown;
      languageName = "markdown";
    } else if (filename.endsWith(".json")) {
      grammar = Prism.languages.json;
      languageName = "json";
    } else if (filename.endsWith(".txt")) {
      grammar = Prism.languages.markdown || Prism.languages.json;
      languageName = "markdown";
    }

    try {
      return Prism.highlight(codeText, grammar, languageName);
    } catch {
      return codeText;
    }
  };

  const isProblemStatement = filename === "problem_statement.txt";

  return (
    <div className={cn("flex-1 flex flex-col min-h-0 w-full h-full overflow-hidden bg-[#09090B]", className)}>
      {/* Integrated Editor Toolbar (Undo / Redo / Save Code) */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-[#141418] border-b border-[#27272A] shrink-0 text-xs text-gray-400 select-none">
        <div className="flex items-center gap-2">
          <span className="font-mono text-zinc-300 font-semibold">{filename}</span>
          <span className="text-[10px] bg-[#272730] px-2 py-0.5 rounded text-gray-400 font-sans uppercase tracking-wider font-semibold">
            {filename.endsWith(".cpp") ? "C++ Solution" : filename === "problem_statement.txt" ? "Problem Statement" : filename === "expected.txt" ? "Expected Output" : "Testcase Input"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <button 
            onClick={handleUndo} 
            disabled={!canUndo}
            title="Undo (⌘Z / Ctrl+Z)"
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#1f1f26] hover:bg-[#2c2c36] disabled:opacity-40 disabled:hover:bg-[#1f1f26] disabled:cursor-not-allowed text-zinc-200 text-[11px] font-sans font-medium transition-colors border border-[#3f3f4e]/40 shadow-sm"
          >
            <span className="material-symbols-outlined text-[14px]">undo</span> Undo
          </button>
          <button 
            onClick={handleRedo} 
            disabled={!canRedo}
            title="Redo (⌘Shift+Z / Ctrl+Y)"
            className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#1f1f26] hover:bg-[#2c2c36] disabled:opacity-40 disabled:hover:bg-[#1f1f26] disabled:cursor-not-allowed text-zinc-200 text-[11px] font-sans font-medium transition-colors border border-[#3f3f4e]/40 shadow-sm"
          >
            <span className="material-symbols-outlined text-[14px]">redo</span> Redo
          </button>
          <div className="h-4 w-[1px] bg-[#27272A] mx-1" />
          <button 
            onClick={handleManualSave}
            title="Save File (⌘S / Ctrl+S)"
            className={cn(
              "flex items-center gap-1.5 px-3 py-1 rounded font-sans text-[11px] font-semibold transition-all border shadow-sm select-none",
              isSaved 
                ? "bg-[#182a20] text-[#34d399] border-[#2cbb5d]/40 shadow-[#2cbb5d]/10" 
                : "bg-gradient-to-r from-cyan-600 to-teal-600 text-white border-cyan-400/30 hover:from-cyan-500 hover:to-teal-500 shadow-cyan-500/10"
            )}
          >
            <span className="material-symbols-outlined text-[14px]">
              {isSaved ? "check_circle" : "save"}
            </span>
            {isSaved ? "Saved" : "Save Code"}
          </button>
        </div>
      </div>

      {/* Editor & Gutter Container */}
      <div className="flex-1 flex min-h-0 min-w-0 w-full h-full overflow-hidden bg-[#0b0b0e]">
        {/* Line Numbers & Gutter Tracking Target (Hidden for problem statement text for better readability) */}
        {!isProblemStatement && (
          <div 
            ref={gutterRef}
            className="w-13 text-right pr-2.5 py-1 text-[#444748] select-none flex flex-col bg-[#141417] border-r border-[#27272A] overflow-hidden relative font-mono flex-shrink-0"
            title="Click in gutter to select loop or target statement for tracking"
          >
            {code.split('\n').map((_, i) => {
              const line = i + 1;
              const isSelected = breakpoints.includes(line);
              return (
                <div 
                  key={i} 
                  style={{ height: `${computedLineHeight}px`, lineHeight: `${computedLineHeight}px`, fontSize: `${Math.max(11, fontSize - 2)}px`, fontFamily }}
                  className={cn(
                    "flex items-center justify-end cursor-pointer hover:text-gray-200 group transition-colors pl-4 relative",
                    isSelected && "text-cyan-400 font-bold hover:text-cyan-300 bg-cyan-500/10"
                  )}
                  onClick={() => onBreakpointToggle && onBreakpointToggle(line)}
                >
                  <div className={cn(
                    "w-2.5 h-2.5 rounded-full absolute left-1.5 transition-all flex items-center justify-center",
                    isSelected 
                      ? "bg-cyan-400 shadow-sm shadow-cyan-400 opacity-100 scale-100 ring-2 ring-cyan-400/20 animate-pulse" 
                      : "bg-cyan-500/30 opacity-0 group-hover:opacity-100 scale-90"
                  )} />
                  <span style={{ lineHeight: `${computedLineHeight}px` }}>{line}</span>
                </div>
              );
            })}
          </div>
        )}
        {/* Syntax Highlighted Code Editor */}
        <div 
          className="flex-1 min-w-0 min-h-0 overflow-auto h-full w-full bg-[#0b0b0e]"
          onScroll={handleScroll}
          onKeyDown={handleKeyDown}
        >
          <Editor
            value={code}
            onValueChange={(newCode: string) => handleCodeChange(newCode)}
            highlight={getSyntaxHighlight}
            padding={12}
            tabSize={tabSize}
            insertSpaces={true}
            style={{
              fontFamily: fontFamily,
              fontSize: fontSize,
              lineHeight: `${computedLineHeight}px`,
              tabSize: tabSize,
              minHeight: "100%",
              backgroundColor: "transparent",
              color: "#e2e8f0",
              whiteSpace: isProblemStatement ? "pre-wrap" : "pre",
              wordBreak: isProblemStatement ? "break-word" : "normal"
            }}
            textareaClassName="focus:outline-none select-text"
          />
        </div>
      </div>
    </div>
  );
}
