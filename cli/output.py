import json
import sys
import os

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    DIM = '\033[2m'
    RESET = '\033[0m'

class Renderer:
    def __init__(self, use_json: bool = False, no_color: bool = False, quiet: bool = False, verbose: bool = False):
        self.use_json = use_json
        # Disable color if no_color is set, or if not a tty
        self.no_color = no_color or not sys.stdout.isatty()
        self.quiet = quiet
        self.verbose = verbose
        
    def _color(self, text: str, color: str) -> str:
        if self.no_color:
            return text
        return f"{color}{text}{Colors.RESET}"

    def print(self, *args, **kwargs):
        """Standard print, suppressed if --quiet or --json"""
        if not self.use_json and not self.quiet:
            print(*args, **kwargs)
            
    def print_verbose(self, *args, **kwargs):
        if not self.use_json and self.verbose:
            print(*args, **kwargs)

    def success(self, msg: str):
        if not self.use_json and not self.quiet:
            print(f"  {self._color('✓', Colors.GREEN)} {msg}")

    def error(self, msg: str, detail: str = "", remediation: str = ""):
        if not self.use_json:
            print(f"  {self._color('✗', Colors.RED)} {msg}\n")
            if detail:
                print(f"  {detail}\n")
            if remediation:
                print(f"  {remediation}\n")
            
    def emit_error(self, command: str, problem: dict, stage: str, message: str, raw: str = "", exit_code: int = 5):
        if self.use_json:
            payload = {
                "command": command,
                "problem": problem,
                "status": "error",
                "payload": {
                    "stage": stage,
                    "message": message,
                    "raw": raw
                }
            }
            sys.stdout.write(json.dumps(payload) + "\n")
        else:
            self.error(message, raw)
        sys.exit(exit_code)
        
    def emit_success(self, command: str, problem: dict, payload: dict, status: str = "pass"):
        if self.use_json:
            out = {
                "command": command,
                "problem": problem,
                "status": status,
                "payload": payload
            }
            sys.stdout.write(json.dumps(out) + "\n")
            
renderer = Renderer()

def configure_renderer(use_json=False, no_color=False, quiet=False, verbose=False):
    global renderer
    renderer.use_json = use_json
    renderer.no_color = no_color or not sys.stdout.isatty()
    renderer.quiet = quiet
    renderer.verbose = verbose
