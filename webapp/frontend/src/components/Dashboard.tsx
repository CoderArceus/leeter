import { useState, useEffect } from "react";
import { apiClient } from "../api/client";

export function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await apiClient.getSummary();
        setSummary(data);
      } catch (err: any) {
        setError(err.message || "Failed to load summary");
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, []);

  if (loading) {
    return <div className="flex-1 flex items-center justify-center text-on-surface-variant">Loading Analytics...</div>;
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center space-y-4">
        <span className="material-symbols-outlined text-[48px] text-error opacity-80">error</span>
        <p className="text-error font-medium">{error}</p>
      </div>
    );
  }

  if (!summary || !summary.difficulty_counts) {
    return <div className="flex-1 flex items-center justify-center text-on-surface-variant p-8">No analytics data available.</div>;
  }

  return (
    <main className="flex-1 flex flex-col h-full bg-[#09090B] overflow-hidden">
      {/* Header */}
      <header className="h-panel-header-height flex items-center justify-between px-margin-sm border-b border-panel shrink-0 bg-level-1">
        <h1 className="font-headline text-[16px] font-semibold text-primary">Analytics</h1>
        <div className="flex items-center gap-margin-sm">
          <div className="flex items-center bg-[#09090B] border border-panel rounded-sm px-2 py-0.5">
            <span className="text-xs text-on-surface-variant mr-2">Range:</span>
            <select className="bg-transparent text-primary text-xs font-code-sm border-none p-0 focus:ring-0 cursor-pointer appearance-none outline-none">
              <option className="bg-level-1">All Time</option>
            </select>
            <span className="material-symbols-outlined text-[14px] text-on-surface-variant ml-1 pointer-events-none">expand_more</span>
          </div>
        </div>
      </header>

      {/* Canvas */}
      <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4 content-start">
        {/* Top Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Stat Card 1 */}
          <div className="bg-level-1 border border-panel p-3 flex flex-col justify-between h-[80px]">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Total Solved</span>
              <span className="material-symbols-outlined text-[16px] text-primary">task_alt</span>
            </div>
            <div className="flex items-baseline gap-2">
              <div className="font-code-md text-2xl text-primary font-semibold leading-none">{summary.total_solved}</div>
              <div className="text-xs text-on-surface-variant font-code-sm"><span className="text-on-surface-variant font-code-sm">/ {summary.total_problems}</span></div>
            </div>
          </div>
          
          {/* Stat Card 2 */}
          <div className="bg-level-1 border border-panel p-3 flex flex-col justify-between h-[80px]">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Current Streak</span>
              <span className="material-symbols-outlined text-[16px] text-primary">local_fire_department</span>
            </div>
            <div className="flex items-baseline gap-2">
              <div className="font-code-md text-2xl text-primary font-semibold leading-none">{summary.streak_days}<span className="text-sm font-body-sm text-on-surface-variant ml-1">d</span></div>
            </div>
          </div>

          {/* Stat Card 3 */}
          <div className="bg-level-1 border border-panel p-3 flex flex-col justify-between h-[80px]">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">Avg. Exec</span>
              <span className="material-symbols-outlined text-[16px] text-primary">speed</span>
            </div>
            <div className="flex items-baseline gap-2">
              <div className="font-code-md text-2xl text-primary font-semibold leading-none">{(summary.average_mean_ns / 1000000).toFixed(2)}<span className="text-sm font-body-sm text-on-surface-variant ml-1">ms</span></div>
            </div>
          </div>
        </div>

        {/* Difficulty Breakdown & Activity Map */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Difficulty Panel */}
          <div className="lg:col-span-1 bg-level-1 border border-panel flex flex-col">
            <div className="px-3 py-2 border-b border-panel">
              <h2 className="text-sm font-semibold text-primary">Breakdown</h2>
            </div>
            <div className="flex flex-col gap-3 p-3">
              <ProgressBar label="Easy" solved={summary.difficulty_counts.easy.solved} total={summary.difficulty_counts.easy.total} colorClass="bg-emerald-500" />
              <ProgressBar label="Medium" solved={summary.difficulty_counts.medium.solved} total={summary.difficulty_counts.medium.total} colorClass="bg-amber-500" />
              <ProgressBar label="Hard" solved={summary.difficulty_counts.hard.solved} total={summary.difficulty_counts.hard.total} colorClass="bg-rose-500" />
            </div>
          </div>

          {/* Recent Submissions List */}
          <div className="lg:col-span-2 bg-level-1 border border-panel flex flex-col">
            <div className="px-3 py-2 border-b border-panel flex justify-between items-center bg-level-2">
              <h2 className="text-sm font-semibold text-primary">Recent Submissions</h2>
              <a className="text-xs text-on-surface-variant hover:text-primary underline decoration-panel underline-offset-2" href="#">View All</a>
            </div>
            <div className="flex-1 overflow-x-auto">
              <table className="w-full text-left text-sm border-collapse whitespace-nowrap">
                <thead>
                  <tr className="border-b border-panel text-xs text-on-surface-variant bg-level-1">
                    <th className="py-1 px-3 font-normal w-1/2">Problem</th>
                    <th className="py-1 px-3 font-normal">Status</th>
                    <th className="py-1 px-3 font-normal">Runtime</th>
                    <th className="py-1 px-3 font-normal text-right">Time</th>
                  </tr>
                </thead>
                <tbody className="text-primary text-xs">
                  {/* Dummy Data matching HTML template */}
                  <tr className="border-b border-panel hover:bg-level-2 transition-colors cursor-pointer group">
                    <td className="py-1.5 px-3 group-hover:text-primary text-on-surface-variant">Two Sum</td>
                    <td className="py-1.5 px-3 text-emerald-500">Accepted</td>
                    <td className="py-1.5 px-3 font-code-sm">2ms</td>
                    <td className="py-1.5 px-3 text-right text-on-surface-variant font-code-sm">10m ago</td>
                  </tr>
                  <tr className="border-b border-panel hover:bg-level-2 transition-colors cursor-pointer group">
                    <td className="py-1.5 px-3 group-hover:text-primary text-on-surface-variant">Valid Parentheses</td>
                    <td className="py-1.5 px-3 text-rose-500">Wrong Answer</td>
                    <td className="py-1.5 px-3 font-code-sm">N/A</td>
                    <td className="py-1.5 px-3 text-right text-on-surface-variant font-code-sm">2h ago</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function ProgressBar({ label, solved, total, colorClass }: { label: string, solved: number, total: number, colorClass: string }) {
  const percentage = total > 0 ? (solved / total) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between items-end mb-1">
        <span className="text-xs text-primary">{label}</span>
        <span className="font-code-sm text-xs text-on-surface-variant">{solved}/{total}</span>
      </div>
      <div className="w-full h-1 bg-level-2">
        <div className={`h-full ${colorClass}`} style={{ width: `${percentage}%` }}></div>
      </div>
    </div>
  );
}
