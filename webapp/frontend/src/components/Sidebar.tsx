import { Link, useLocation } from "react-router-dom";
import { cn } from "../lib/utils";

export function Sidebar({ className }: { className?: string }) {
  const location = useLocation();

  return (
    <nav className={cn("bg-surface-container-low border-r border-panel w-14 flex flex-col h-full py-2 flex-shrink-0 z-10", className)}>
      <div className="px-2 pb-4 flex flex-col items-center gap-1">
        <img 
          className="w-8 h-8 rounded-full border border-panel object-cover" 
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuBx7vs3M2DOyMykrvGYeYE_-0q9l6gPReKe7XY9mKORqKCn4QDHcJjMW3Clz8ztqjrdQZNjdnjWsGzT12U4dbUeZCX7AVrDv8Jrkdci8UwyOKLwsWHOvD8wNF9Jsw-wGuCBeedm6t0W-QRNRaozCuY5xvNoR2q9sBqYWSZbK4zAPmWrm46QJ0DrmV_xhWcHWXF6shMR4fDKLXiwIS9WnBul5dGN9WV6D6Rv0OyRqqtxUN_KHbEclh6djEpVRfVFxUy9u8MEqTaZtG-L" 
          alt="User Profile" 
          title="Leeter IDE"
        />
      </div>
      <div className="flex-1 overflow-y-auto mt-4">
        <ul className="flex flex-col items-center gap-2">
          <Link to="/" title="Problem Workspace" className={cn(
            "w-10 h-10 flex items-center justify-center cursor-pointer rounded-r-sm transition-colors border-l-2",
            location.pathname === "/" 
              ? "bg-surface-container-highest border-primary text-primary" 
              : "text-on-surface-variant hover:bg-surface-container-high border-transparent"
          )}>
            <span className="material-symbols-outlined text-[20px]">code</span>
          </Link>
        </ul>
      </div>
      <div className="mt-auto flex flex-col items-center">
        <ul className="flex flex-col border-t border-panel pt-2 w-full items-center gap-2">
          <li className="text-on-surface-variant hover:bg-surface-container-high w-10 h-10 flex items-center justify-center cursor-pointer transition-colors border-l-2 border-transparent rounded-r-sm" title="Settings">
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </li>
        </ul>
      </div>
    </nav>
  );
}
