import argparse
import os
import sys

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.output import configure_renderer, renderer
from cli.storage import set_last_accessed_problem, get_last_accessed_problem

# Command handlers
from cli.run import cmd_run
from cli.debug import cmd_debug
from cli.clean import cmd_clean
from cli.new import cmd_new
from cli.auth import cmd_auth
from cli.open import cmd_open
from cli.fetch import cmd_fetch
from cli.replay import cmd_replay
from cli.stress import cmd_stress
from cli.bench import cmd_bench
from cli.session import cmd_session
from cli.stats import cmd_stats, cmd_search
from cli.note import cmd_note
from cli.paste import cmd_paste
from cli.migrate import cmd_migrate
from cli.setup import cmd_setup

def resolve_problem_dir(args_problem: str) -> str:
    if args_problem:
        path = os.path.abspath(args_problem)
        if os.path.isdir(path) and os.path.exists(os.path.join(path, "problem.json")):
            set_last_accessed_problem(path)
            return path
        problems_dir = os.path.abspath("problems")
        if os.path.exists(problems_dir):
            candidates = [f for f in os.listdir(problems_dir) if f.startswith(f"{args_problem}_")]
            if candidates:
                path = os.path.join(problems_dir, candidates[0])
                set_last_accessed_problem(path)
                return path
        renderer.error("Problem not found.", f"Could not resolve problem from argument: {args_problem}")
        sys.exit(1)

    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "problem.json")):
        set_last_accessed_problem(cwd)
        return cwd
        
    last_accessed = get_last_accessed_problem()
    if last_accessed and os.path.exists(os.path.join(last_accessed, "problem.json")):
        return last_accessed

    renderer.error(
        "No active problem.",
        "",
        "Run from inside a problem folder, or pass --problem <id>."
    )
    sys.exit(1)

def main():
    global_parser = argparse.ArgumentParser(add_help=False)
    global_parser.add_argument("--problem", type=str, help="Override active problem resolution", default=argparse.SUPPRESS)
    global_parser.add_argument("--json", action="store_true", help="Machine-readable output", default=argparse.SUPPRESS)
    global_parser.add_argument("--no-color", action="store_true", help="Disable ANSI color codes", default=argparse.SUPPRESS)
    global_parser.add_argument("--quiet", action="store_true", help="Suppress all output except errors and results", default=argparse.SUPPRESS)
    global_parser.add_argument("--verbose", action="store_true", help="Show full pipeline stage output", default=argparse.SUPPRESS)
    global_parser.add_argument("--version", action="store_true", help="Print framework version and exit", default=argparse.SUPPRESS)
    
    parser = argparse.ArgumentParser(description="Leeter CLI", parents=[global_parser])
    subparsers = parser.add_subparsers(dest="command")
    
    fetch_parser = subparsers.add_parser("fetch", parents=[global_parser])
    fetch_parser.add_argument("id", type=str)
    fetch_parser.add_argument("--lang", type=str, default="cpp")
    fetch_parser.add_argument("--force", action="store_true")
    fetch_parser.add_argument("--no-analyze", action="store_true")
    
    run_parser = subparsers.add_parser("run", parents=[global_parser])
    run_parser.add_argument("--case", type=int)
    run_parser.add_argument("--no-compile", action="store_true")
    run_parser.add_argument("--timeout", type=int, default=5)
    run_parser.add_argument("--input", type=str, default="input.txt")
    
    debug_parser = subparsers.add_parser("debug", parents=[global_parser])
    debug_parser.add_argument("--no-sanitize", action="store_true")
    debug_parser.add_argument("--input", type=str, default="input.txt")
    
    new_parser = subparsers.add_parser("new", parents=[global_parser])
    new_parser.add_argument("name", type=str, nargs="?")
    new_parser.add_argument("--difficulty", type=str, choices=["easy", "medium", "hard"])
    new_parser.add_argument("--runner", type=str, choices=["function", "stateful", "interactive"])
    new_parser.add_argument("--id", type=int)
    
    replay_parser = subparsers.add_parser("replay", parents=[global_parser])
    replay_parser.add_argument("--case", type=int, default=0)
    replay_parser.add_argument("--op", type=int, default=0)
    replay_parser.add_argument("--raw", action="store_true")
    
    bench_parser = subparsers.add_parser("bench", parents=[global_parser])
    bench_parser.add_argument("--iters", type=int, default=1000)
    bench_parser.add_argument("--warmup", type=int, default=10)
    bench_parser.add_argument("--compare", action="store_true")
    bench_parser.add_argument("--input", type=str, default="input.txt")
    
    stress_parser = subparsers.add_parser("stress", parents=[global_parser])
    stress_parser.add_argument("--iters", type=int, default=1000)
    stress_parser.add_argument("--seed", type=int)
    stress_parser.add_argument("--timeout", type=int, default=2)
    
    subparsers.add_parser("paste", parents=[global_parser])
    
    open_parser = subparsers.add_parser("open", parents=[global_parser])
    open_parser.add_argument("id", type=str, nargs="?")
    open_parser.add_argument("--browser-only", action="store_true")
    open_parser.add_argument("--editor-only", action="store_true")
    open_parser.add_argument("--editor", type=str)
    
    subparsers.add_parser("note", parents=[global_parser])
    
    search_parser = subparsers.add_parser("search", parents=[global_parser])
    search_parser.add_argument("query", type=str, nargs="?", default="")
    search_parser.add_argument("--tag", type=str)
    search_parser.add_argument("--difficulty", type=str, choices=["easy", "medium", "hard"])
    search_parser.add_argument("--solved", action="store_true")
    search_parser.add_argument("--unsolved", action="store_true")
    search_parser.add_argument("--limit", type=int, default=20)
    
    stats_parser = subparsers.add_parser("stats", parents=[global_parser])
    stats_parser.add_argument("--by-tag", action="store_true")
    stats_parser.add_argument("--by-difficulty", action="store_true", default=True)
    stats_parser.add_argument("--since", type=str)
    
    session_parser = subparsers.add_parser("session", parents=[global_parser])
    session_parser.add_argument("--goal", type=str)
    session_parser.add_argument("--reset", action="store_true")
    
    auth_parser = subparsers.add_parser("auth", parents=[global_parser])
    auth_parser.add_argument("cookie", type=str, nargs="?")
    auth_parser.add_argument("--check", action="store_true")
    
    migrate_parser = subparsers.add_parser("migrate", parents=[global_parser])
    migrate_parser.add_argument("--apply", action="store_true")
    migrate_parser.add_argument("--from", dest="from_ver", type=int)
    
    clean_parser = subparsers.add_parser("clean", parents=[global_parser])
    clean_parser.add_argument("--all", action="store_true")
    
    setup_parser = subparsers.add_parser("setup", parents=[global_parser])
    setup_parser.add_argument("editor", type=str, choices=["zed", "vscode", "neovim", "emacs", "all"])
    setup_parser.add_argument("--scope", type=str, choices=["project", "global"], default="project")
    setup_parser.add_argument("--keybindings", action="store_true")
    setup_parser.add_argument("--dry-run", action="store_true")
    
    args = parser.parse_args()
    
    if not hasattr(args, 'problem'): args.problem = None
    if not hasattr(args, 'json'): args.json = False
    if not hasattr(args, 'no_color'): args.no_color = False
    if not hasattr(args, 'quiet'): args.quiet = False
    if not hasattr(args, 'verbose'): args.verbose = False
    if not hasattr(args, 'help'): args.help = False
    if not hasattr(args, 'version'): args.version = False

    if getattr(args, 'help', False):
        parser.print_help()
        sys.exit(0)
    
    if getattr(args, 'version', False):
        print("Leeter CLI v1.0")
        sys.exit(0)
        
    configure_renderer(args.json, args.no_color, args.quiet, args.verbose)
    
    if not args.command:
        parser.print_help()
        sys.exit(0)
        
    # Active problem resolution before dispatching
    needs_problem = ["run", "debug", "replay", "stress", "bench", "note", "paste"]
    if args.command in needs_problem:
        args.problem = resolve_problem_dir(getattr(args, 'problem', None))
    elif args.command == "clean" and not getattr(args, 'all', False):
        args.problem = resolve_problem_dir(getattr(args, 'problem', None))
    elif args.command == "open" and not getattr(args, 'id', None):
        args.problem = resolve_problem_dir(getattr(args, 'problem', None))
        
    if args.command == "run":
        cmd_run(args)
    elif args.command == "new":
        cmd_new(args)
    elif args.command == "auth":
        cmd_auth(args)
    elif args.command == "fetch":
        cmd_fetch(args)
    elif args.command == "open":
        cmd_open(args)
    elif args.command == "paste":
        cmd_paste(args)
    elif args.command == "replay":
        cmd_replay(args)
    elif args.command == "stress":
        cmd_stress(args)
    elif args.command == "bench":
        cmd_bench(args)
    elif args.command == "session":
        cmd_session(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "note":
        cmd_note(args)
    elif args.command == "migrate":
        cmd_migrate(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "debug":
        cmd_debug(args)
    elif args.command == "setup":
        cmd_setup(args)

if __name__ == "__main__":
    main()
