import React, { useRef } from "react";
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


interface CodeViewerProps {
  className?: string;
  code: string;
  filename?: string;
  onChange?: (newCode: string) => void;
  onSave?: () => void;
  breakpoints?: number[];
  onBreakpointToggle?: (line: number) => void;
}

export function CodeViewer({ className, code, filename = "solution.cpp", onChange, onSave, breakpoints = [], onBreakpointToggle }: CodeViewerProps) {
  const gutterRef = useRef<HTMLDivElement>(null);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    if (gutterRef.current) {
      gutterRef.current.scrollTop = e.currentTarget.scrollTop;
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      if (onSave) onSave();
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
      // Highlight numbers, arrays, brackets cleanly for input files
      grammar = Prism.languages.json || Prism.languages.markdown;
      languageName = "json";
    }

    try {
      return Prism.highlight(codeText, grammar, languageName);
    } catch {
      return codeText;
    }
  };

  return (
    <div className={cn("flex-1 flex overflow-hidden font-code-sm text-code-sm leading-[22px] bg-[#09090B]", className)}>
      {/* Line Numbers & Gutter Tracking Target */}
      <div 
        ref={gutterRef}
        className="w-13 text-right pr-2.5 py-1 text-[#444748] select-none flex flex-col bg-[#141417] border-r border-[#27272A] overflow-hidden relative font-mono text-[11px] flex-shrink-0"
        title="Click in gutter to select loop or target statement for tracking"
      >
        {code.split('\n').map((_, i) => {
          const line = i + 1;
          const isSelected = breakpoints.includes(line);
          return (
            <div 
              key={i} 
              className={cn(
                "flex items-center justify-end cursor-pointer hover:text-gray-200 group h-[22px] transition-colors pl-4 relative",
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
              <span className="leading-[22px]">{line}</span>
            </div>
          );
        })}
      </div>
      {/* Syntax Highlighted Code Editor */}
      <div 
        className="flex-1 overflow-auto bg-[#0b0b0e] min-h-0"
        onScroll={handleScroll}
        onKeyDown={handleKeyDown}
      >
        <Editor
          value={code}
          onValueChange={(newCode: string) => onChange && onChange(newCode)}
          highlight={getSyntaxHighlight}
          padding={4}
          style={{
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
            fontSize: 12,
            lineHeight: "22px",
            minHeight: "100%",
            backgroundColor: "transparent",
            color: "#e2e8f0"
          }}
          textareaClassName="focus:outline-none select-text"
        />
      </div>
    </div>
  );
}
