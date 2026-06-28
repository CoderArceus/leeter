import os
import shutil
import subprocess
from cli.output import renderer

def resolve_leeter_bin() -> str:
    if shutil.which("leeter"):
        return "leeter"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return f"python3 {os.path.join(script_dir, 'leeter.py')}"

def merge_tasks(existing: list, new_tasks: list) -> list:
    existing_by_label = {t.get("label"): i for i, t in enumerate(existing) if "label" in t}
    result = list(existing)
    for task in new_tasks:
        label = task["label"]
        entry = {k: v for k, v in task.items() if k != "id"}
        if label in existing_by_label:
            result[existing_by_label[label]] = entry
        else:
            result.append(entry)
    return result

def merge_keymap(existing: list, new_keymap: list) -> list:
    result = list(existing)
    for entry in new_keymap:
        if entry not in result:
            result.append(entry)
    return result

def check_gitignore(path: str):
    # Fallback gitignore checker
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            capture_output=True
        )
        if result.returncode == 0:
            rel = os.path.relpath(path)
            renderer.print(f"\n[Warning] {rel} is ignored in your .gitignore.")
            renderer.print(f"It is recommended to track {os.path.basename(path)} so tasks are shared across environments.")
            renderer.print(f"Consider adding: !{rel} to your .gitignore")
    except Exception:
        pass

def cmd_setup(args):
    editor = args.editor.lower()
    bin_cmd = resolve_leeter_bin()
    
    editors_to_run = [editor]
    if editor == "all":
        editors_to_run = ["zed", "vscode", "neovim", "emacs"]
        
    for ed in editors_to_run:
        try:
            if ed == "zed":
                from cli.setup_zed import setup_zed
                setup_zed(args, bin_cmd, merge_tasks, merge_keymap)
                if getattr(args, 'scope', 'project') == 'project' and not getattr(args, 'dry_run', False):
                    check_gitignore(os.path.abspath(".zed/tasks.json"))
            elif ed == "vscode":
                from cli.setup_vscode import setup_vscode
                setup_vscode(args, bin_cmd, merge_tasks, merge_keymap)
                if getattr(args, 'scope', 'project') == 'project' and not getattr(args, 'dry_run', False):
                    check_gitignore(os.path.abspath(".vscode/tasks.json"))
            elif ed == "neovim":
                from cli.setup_neovim import setup_neovim
                setup_neovim(args, bin_cmd, merge_tasks, merge_keymap)
            elif ed == "emacs":
                from cli.setup_emacs import setup_emacs
                setup_emacs(args, bin_cmd, merge_tasks, merge_keymap)
        except Exception as e:
            renderer.print(f"Failed to setup {ed}: {e}")

def maybe_bootstrap_zed_tasks(repo_root: str):
    # This function is retained for compatibility with fetch.py.
    # The specification upgrades it to handle all installed editors.
    detectors = {
        "zed":    (shutil.which("zed") or os.path.exists(os.path.expanduser("~/.config/zed")),
                   os.path.join(repo_root, ".zed", "tasks.json")),
        "vscode": (shutil.which("code"),
                   os.path.join(repo_root, ".vscode", "tasks.json")),
        "neovim": (shutil.which("nvim"),
                   os.path.join(repo_root, ".nvim.lua")),
        "emacs":  (shutil.which("emacs"),
                   os.path.join(repo_root, ".dir-locals.el")),
    }
    
    class DummyArgs:
        def __init__(self, editor):
            self.editor = editor
            self.scope = "project"
            self.dry_run = False
            self.keybindings = False
            
    prev_cwd = os.getcwd()
    os.chdir(repo_root)
    try:
        for editor, (detected, config_path) in detectors.items():
            if detected and not os.path.exists(config_path):
                cmd_setup(DummyArgs(editor))
                print(f"[leeter] {editor} auto-bootstrapped.")
    except Exception as e:
        print(f"[leeter] Failed to auto-bootstrap tasks: {e}")
    finally:
        os.chdir(prev_cwd)
