import { cn } from "../lib/utils";

interface ActionBarProps {
  className?: string;
  onRun?: () => void;
  onTrack?: () => void;
  loading?: boolean;
}

export function ActionBar({ className, onRun, onTrack, loading }: ActionBarProps) {
  return (
    <div className={cn("flex border border-panel bg-[#09090B] divide-x divide-[#27272A] rounded-md overflow-hidden shadow-sm", className)}>
      <button
        onClick={onRun}
        disabled={loading}
        className="px-3 h-7 hover:bg-[#27272A] flex items-center gap-1.5 text-on-surface-variant hover:text-white transition-colors text-xs font-medium disabled:opacity-50"
      >
        <span className="material-symbols-outlined text-[15px] text-emerald-400">play_arrow</span> Run
      </button>
      <button
        onClick={onTrack}
        disabled={loading}
        className="px-3 h-7 hover:bg-[#27272A] flex items-center gap-1.5 text-on-surface-variant hover:text-white transition-colors text-xs font-medium disabled:opacity-50"
        title="Track loop iterations and variable mutations across time"
      >
        <span className="material-symbols-outlined text-[15px] text-cyan-400">radar</span> Track Elements
      </button>
      <button 
        className="px-3.5 h-7 bg-white text-black hover:bg-gray-200 transition-colors text-xs font-semibold flex items-center gap-1 disabled:opacity-50" 
        disabled={loading}
      >
        <span className="material-symbols-outlined text-[14px]">publish</span> Submit
      </button>
    </div>
  );
}
