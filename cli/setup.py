import json
import os
import shutil
import subprocess
import sys
import textwrap

# ---------------------------------------------------------------------------
# Canonical task manifest
# ---------------------------------------------------------------------------

LEETER_TASKS = [
    {
        "id": "run",
        "label": "Leeter: Run",
        "command": "run",
        "cwd": "problem_dir",
        "new_terminal": False,
    },
    {
        "id": "debug",
        "label": "Leeter: Debug",
        "command": "debug",
        "cwd": "problem_dir",
        "new_terminal": True,
    },
    {
        "id": "bench",
        "label": "Leeter: Bench",
        "command": "bench --iters 500",
        "cwd": "problem_dir",
        "new_terminal": False,
    },
    {
        "id": "stress",
        "label": "Leeter: Stress",
        "command": "stress --iters 200",
        "cwd": "problem_dir",
        "new_terminal": False,
    },
    {
        "id": "replay",
        "label": "Leeter: Replay",
        "command": "replay",
        "cwd": "problem_dir",
        "new_terminal": True,
    },
    {
        "id": "paste",
        "label": "Leeter: Paste",
        "command": "paste",
        "cwd": "problem_dir",
        "new_terminal": False,
    },
    {
        "id": "fetch",
        "label": "Leeter: Fetch Problem",
        "command": "fetch",
        "cwd": "repo_root",
        "new_terminal": True,
    },
    {
        "id": "session",
        "label": "Leeter: Session",
        "command": "session",
        "cwd": "repo_root",
        "new_terminal": False,
    },
    {
        "id": "stats",
        "label": "Leeter: Stats",
        "command": "stats",
        "cwd": "repo_root",
        "new_terminal": False,
    },
]

# Default keybinding map: task id -> key chord (used by Zed + VSCode backends)
DEFAULT_KEYBINDINGS = {
    "run":    ("ctrl-shift-r", "ctrl+shift+r"),   # (zed, vscode)
    "debug":  ("ctrl-shift-d", "ctrl+shift+d"),
    "bench":  ("ctrl-shift-b", "ctrl+shift+b"),
    "stress": ("ctrl-shift-t", "ctrl+shift+t"),
    "replay": ("ctrl-shift-p", "ctrl+shift+p"),
}

# Neovim/Emacs key suffix map: task id -> letter after <leader>l / C-c l
MODAL_KEYS = {
    "run":    "r",
    "debug":  "d",
    "bench":  "b",
    "stress": "t",
    "replay": "p",
    "paste":  "v",
    "fetch":  "f",
    "session": "s",
    "stats":  "a",
}


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------

def resolve_leeter_bin() -> str:
    """Return 'leeter' if on PATH, else absolute python3 path to leeter.py."""
    if shutil.which("leeter"):
        return "leeter"
    # __file__ is cli/setup.py; leeter.py lives in the same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    leeter_py = os.path.join(script_dir, "leeter.py")
    return f"python3 {leeter_py}"


def repo_root() -> str:
    """Return the git repo root, or cwd if not in a git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return os.getcwd()


def write_file(path: str, content: str, dry_run: bool):
    """Write content to path, creating parent dirs as needed."""
    if dry_run:
        print(f"[dry-run] Would write: {path}")
        print(textwrap.indent(content[:400] + ("..." if len(content) > 400 else ""), "    "))
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"[leeter] Written: {os.path.relpath(path)}")


def check_gitignore(path: str):
    """Warn if path is covered by .gitignore."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", path],
            capture_output=True
        )
        if result.returncode == 0:
            rel = os.path.relpath(path)
            dirname = os.path.dirname(rel)
            basename = os.path.basename(rel)
            print(f"\n[Warning] {rel} is ignored in your .gitignore.")
            print(f"It is recommended to track {basename} so tasks are shared across environments.")
            print(f"Consider adding: !{dirname}/{basename}  to your .gitignore\n")
    except FileNotFoundError:
        pass  # git not available


def merge_json_tasks(existing: list, new_tasks: list) -> list:
    """Overwrite existing Leeter tasks by label, append new ones, preserve others."""
    leeter_labels = {t["label"] for t in new_tasks}
    # Remove stale Leeter entries (keeps user's own tasks)
    result = [t for t in existing if t.get("label") not in leeter_labels]
    result.extend(new_tasks)
    return result


# ---------------------------------------------------------------------------
# Zed backend
# ---------------------------------------------------------------------------

def setup_zed(args):
    bin_ = resolve_leeter_bin()
    root = repo_root()

    if args.scope == "global":
        config_dir = os.path.expanduser("~/.config/zed")
        tasks_path = os.path.join(config_dir, "tasks.json")
        keymap_path = os.path.join(config_dir, "keymap.json")
    else:
        config_dir = os.path.join(root, ".zed")
        tasks_path = os.path.join(config_dir, "tasks.json")
        keymap_path = os.path.join(config_dir, "keymap.json")

    # Build task entries (no "id" field — Zed doesn't support it)
    cwd_map = {"problem_dir": "$ZED_DIRNAME", "repo_root": "$ZED_WORKTREE_ROOT"}
    tasks = []
    for t in LEETER_TASKS:
        tasks.append({
            "label": t["label"],
            "command": f"{bin_} {t['command']}",
            "cwd": cwd_map[t["cwd"]],
            "reveal": "always",
            "use_new_terminal": t["new_terminal"],
            "allow_concurrent_runs": False,
        })

    # Merge with existing
    existing = []
    if os.path.exists(tasks_path):
        try:
            with open(tasks_path) as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    merged = merge_json_tasks(existing, tasks)
    header = "// AUTO-GENERATED by `leeter setup zed`. Re-run to update.\n"
    content = header + json.dumps(merged, indent=4)
    write_file(tasks_path, content, args.dry_run)

    if not args.dry_run and args.scope == "project":
        check_gitignore(tasks_path)

    # Keybindings
    if args.keybindings:
        bindings = {}
        for task_id, (zed_key, _) in DEFAULT_KEYBINDINGS.items():
            label = next((t["label"] for t in LEETER_TASKS if t["id"] == task_id), None)
            if label:
                bindings[zed_key] = ["task::Spawn", {"task_name": label}]

        keymap_entry = [{"context": "Workspace", "bindings": bindings}]

        existing_km = []
        if os.path.exists(keymap_path):
            try:
                with open(keymap_path) as f:
                    existing_km = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        # Remove stale Leeter context block if present, then append fresh one
        existing_km = [
            block for block in existing_km
            if not (isinstance(block, dict) and
                    any(k.startswith("ctrl-shift-") for k in block.get("bindings", {})))
        ]
        existing_km.extend(keymap_entry)

        km_header = "// Optional keybindings for Zed. Run `leeter setup zed --keybindings` to apply.\n"
        write_file(keymap_path, km_header + json.dumps(existing_km, indent=4), args.dry_run)

    print(f"[leeter] Zed setup complete ({args.scope}).")


# ---------------------------------------------------------------------------
# VSCode backend
# ---------------------------------------------------------------------------

def setup_vscode(args):
    bin_ = resolve_leeter_bin()
    root = repo_root()

    if args.scope == "global":
        print("[leeter] VSCode has no global tasks file. Use --scope project (default).")
        print("         Keybindings are always written globally.")

    tasks_path = os.path.join(root, ".vscode", "tasks.json")

    cwd_map = {"problem_dir": "${fileDirname}", "repo_root": "${workspaceFolder}"}
    tasks = []
    for t in LEETER_TASKS:
        entry = {
            "label": t["label"],
            "type": "shell",
            "command": f"{bin_} {t['command']}",
            "options": {"cwd": cwd_map[t["cwd"]]},
            "problemMatcher": [],
            "presentation": {
                "reveal": "always",
                "panel": "new" if t["new_terminal"] else "shared",
                "clear": not t["new_terminal"],
            },
        }
        if t["id"] == "run":
            entry["group"] = {"kind": "build", "isDefault": True}
        tasks.append(entry)

    # Merge with existing
    existing_tasks = []
    if os.path.exists(tasks_path):
        try:
            with open(tasks_path) as f:
                data = json.load(f)
                existing_tasks = data.get("tasks", [])
        except (json.JSONDecodeError, OSError):
            pass

    merged = merge_json_tasks(existing_tasks, tasks)
    output = {"version": "2.0.0", "tasks": merged}
    header = "// AUTO-GENERATED by `leeter setup vscode`. Re-run to update.\n"
    write_file(tasks_path, header + json.dumps(output, indent=4), args.dry_run)
    check_gitignore(tasks_path)

    # Keybindings (always global for VSCode)
    if args.keybindings:
        if sys.platform == "darwin":
            kb_path = os.path.expanduser(
                "~/Library/Application Support/Code/User/keybindings.json"
            )
        elif sys.platform == "win32":
            kb_path = os.path.join(os.environ.get("APPDATA", ""), "Code", "User", "keybindings.json")
        else:
            kb_path = os.path.expanduser("~/.config/Code/User/keybindings.json")

        new_bindings = []
        for task_id, (_, vscode_key) in DEFAULT_KEYBINDINGS.items():
            label = next((t["label"] for t in LEETER_TASKS if t["id"] == task_id), None)
            if label:
                new_bindings.append({
                    "key": vscode_key,
                    "command": "workbench.action.tasks.runTask",
                    "args": label,
                })

        existing_kb = []
        if os.path.exists(kb_path):
            try:
                with open(kb_path) as f:
                    existing_kb = json.load(f)
            except (json.JSONDecodeError, OSError):
                pass

        leeter_args = {b["args"] for b in new_bindings}
        existing_kb = [b for b in existing_kb if b.get("args") not in leeter_args]
        existing_kb.extend(new_bindings)

        header = "// Leeter keybindings appended by `leeter setup vscode --keybindings`.\n"
        write_file(kb_path, header + json.dumps(existing_kb, indent=4), args.dry_run)

    print(f"[leeter] VSCode setup complete.")


# ---------------------------------------------------------------------------
# Neovim backend
# ---------------------------------------------------------------------------

def setup_neovim(args):
    bin_ = resolve_leeter_bin()
    root = repo_root()

    if args.scope == "global":
        out_path = os.path.expanduser("~/.config/nvim/leeter.lua")
        load_note = (
            "-- Add to your init.lua:  require('leeter')\n"
            "-- (This file was written to your Neovim config directory)\n"
        )
    else:
        out_path = os.path.join(root, ".nvim.lua")
        load_note = (
            "-- Auto-loaded by Neovim when vim.o.exrc = true (add to init.lua).\n"
        )

    keymaps = []
    for t in LEETER_TASKS:
        key = MODAL_KEYS.get(t["id"])
        if not key:
            continue
        cwd_expr = (
            "vim.fn.expand('%:p:h')"
            if t["cwd"] == "problem_dir"
            else "vim.fn.systemlist('git rev-parse --show-toplevel')[1]"
        )
        keymaps.append(
            f'  vim.keymap.set("n", prefix .. "{key}", '
            f'function() run("{bin_} {t["command"]}", {cwd_expr}) end, '
            f'{{ desc = "{t["label"]}" }})'
        )

    keymaps_str = "\n".join(keymaps)

    lua = textwrap.dedent(f"""\
        -- Leeter Neovim Integration
        -- AUTO-GENERATED by `leeter setup neovim`. Re-run to update.
        {load_note}
        local M = {{}}

        local function run(cmd, cwd)
          local buf = vim.api.nvim_create_buf(false, true)
          local width  = math.floor(vim.o.columns * 0.8)
          local height = math.floor(vim.o.lines   * 0.7)
          vim.api.nvim_open_win(buf, true, {{
            relative = "editor",
            width    = width,
            height   = height,
            col      = math.floor((vim.o.columns - width)  / 2),
            row      = math.floor((vim.o.lines   - height) / 2),
            style    = "minimal",
            border   = "rounded",
            title    = " " .. cmd .. " ",
          }})
          vim.fn.termopen(cmd, {{ cwd = cwd }})
          vim.keymap.set("n", "q", "<cmd>close<cr>", {{ buffer = buf }})
        end

        function M.setup(opts)
          opts = opts or {{}}
          local prefix = opts.prefix or "<leader>l"
        {keymaps_str}

          -- which-key label (no-op if not installed)
          local ok, wk = pcall(require, "which-key")
          if ok then
            wk.register({{ l = {{ name = "Leeter" }} }}, {{ prefix = "<leader>" }})
          end

          vim.notify("[leeter] Neovim integration loaded. " .. prefix .. " + r/d/b/t/p/v/f/s/a", vim.log.levels.INFO)
        end

        return M
    """)

    write_file(out_path, lua, args.dry_run)

    if not args.dry_run:
        # Check exrc if project-local
        if args.scope == "project":
            try:
                result = subprocess.run(
                    ["nvim", "--headless", "--noplugin", "-c",
                     "lua io.write(tostring(vim.o.exrc))", "-c", "qa"],
                    capture_output=True, text=True, timeout=5
                )
                if "false" in result.stdout:
                    print("[Warning] vim.o.exrc is not enabled.")
                    print("          Add `vim.o.exrc = true` to your init.lua so Neovim")
                    print("          auto-loads .nvim.lua when you open this project.")
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
        else:
            print("[leeter] Add  require('leeter').setup()  to your init.lua to activate.")

    print(f"[leeter] Neovim setup complete ({args.scope}).")


# ---------------------------------------------------------------------------
# Emacs backend
# ---------------------------------------------------------------------------

def setup_emacs(args):
    bin_ = resolve_leeter_bin()
    root = repo_root()

    if args.scope == "global":
        out_path = os.path.expanduser("~/.config/emacs/leeter.el")
        # Attempt to append (load ...) to init.el
        _maybe_append_emacs_load(out_path, args.dry_run)
    else:
        out_path = os.path.join(root, ".dir-locals.el")

    keybindings_forms = []
    for t in LEETER_TASKS:
        key = MODAL_KEYS.get(t["id"])
        if not key:
            continue
        use_root = t["cwd"] == "repo_root"
        keybindings_forms.append(
            f'      (define-key map (kbd "{key}") '
            f"(lambda () (interactive) (leeter--run \"{bin_} {t['command']}\" {'t' if use_root else 'nil'})))"
            f"  ; {t['label']}"
        )

    keybindings_str = "\n".join(keybindings_forms)

    if args.scope == "global":
        # Standalone .el file — proper defun style
        el = textwrap.dedent(f"""\
            ;;; leeter.el --- Leeter IDE integration for Emacs
            ;; AUTO-GENERATED by `leeter setup emacs`. Re-run to update.

            (defgroup leeter nil
              "Leeter LeetCode framework integration."
              :group 'tools)

            (defcustom leeter-prefix "C-c l"
              "Key prefix for Leeter commands."
              :type 'string
              :group 'leeter)

            (defun leeter--run (cmd &optional use-repo-root)
              "Run CMD via compile-mode, optionally from repo root."
              (let ((default-directory
                      (if use-repo-root
                          (or (locate-dominating-file default-directory ".git")
                              default-directory)
                        default-directory)))
                (compile cmd)))

            (defun leeter-setup-keys ()
              "Bind Leeter commands under `leeter-prefix`."
              (let ((map (make-sparse-keymap)))
            {keybindings_str}
                (global-set-key (kbd leeter-prefix) map)))

            (leeter-setup-keys)

            (provide 'leeter)
            ;;; leeter.el ends here
        """)
    else:
        # .dir-locals.el — eval form, project-scoped
        el = textwrap.dedent(f"""\
            ;;; .dir-locals.el --- Leeter project integration
            ;;; AUTO-GENERATED by `leeter setup emacs`. Re-run to update.
            ;;; Emacs will ask you to approve this file on first load.
            ;;; Select "!" to permanently allow it for this project.

            ((nil . ((eval . (progn
              (defun leeter--run (cmd &optional use-repo-root)
                "Run CMD via compile-mode, optionally from repo root."
                (let ((default-directory
                        (if use-repo-root
                            (or (locate-dominating-file default-directory ".git")
                                default-directory)
                          default-directory)))
                  (compile cmd)))

              (defvar leeter--map (make-sparse-keymap))
            {keybindings_str}
              (global-set-key (kbd "C-c l") leeter--map)
              (message "[leeter] Emacs integration loaded. C-c l + r/d/b/t/p/v/f/s/a"))))))
        """)

    write_file(out_path, el, args.dry_run)

    if not args.dry_run and args.scope == "project":
        check_gitignore(out_path)
        print("[leeter] Emacs will prompt to approve .dir-locals.el on first file open.")
        print("         Select '!' to permanently allow it for this project.")

    print(f"[leeter] Emacs setup complete ({args.scope}).")


def _maybe_append_emacs_load(leeter_el_path: str, dry_run: bool):
    """Try to append (load ...) to the user's Emacs init file."""
    candidates = [
        os.path.expanduser("~/.config/emacs/init.el"),
        os.path.expanduser("~/.emacs.d/init.el"),
        os.path.expanduser("~/.emacs"),
    ]
    init_file = next((p for p in candidates if os.path.exists(p)), None)
    load_form = f'\n(load "{leeter_el_path}" t)\n'

    if init_file:
        with open(init_file) as f:
            content = f.read()
        if leeter_el_path not in content:
            if dry_run:
                print(f"[dry-run] Would append (load ...) to {init_file}")
            else:
                with open(init_file, "a") as f:
                    f.write(load_form)
                print(f"[leeter] Appended (load ...) to {init_file}")
    else:
        print(f"[leeter] Could not find Emacs init file.")
        print(f"         Manually add this to your init.el:")
        print(f'         (load "{leeter_el_path}" t)')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def maybe_bootstrap_zed_tasks(repo_root: str):
    """
    Called by fetch.py on success to automatically bootstrap an editor if not already configured.
    """
    class DummyArgs:
        def __init__(self, editor):
            self.editor = editor
            self.scope = "project"
            self.dry_run = False
            self.keybindings = False

    detectors = {
        "zed":    lambda: shutil.which("zed") or os.path.exists(os.path.expanduser("~/.config/zed")),
        "vscode": lambda: shutil.which("code") or shutil.which("code-insiders"),
        "neovim": lambda: shutil.which("nvim"),
        "emacs":  lambda: shutil.which("emacs"),
    }
    
    editors = [e for e in detectors if detectors[e]()]
    for editor in editors:
        # Avoid bootstrapping if already done
        if editor == "zed" and os.path.exists(os.path.join(repo_root, ".zed", "tasks.json")): continue
        if editor == "vscode" and os.path.exists(os.path.join(repo_root, ".vscode", "tasks.json")): continue
        if editor == "neovim" and os.path.exists(os.path.join(repo_root, ".nvim.lua")): continue
        if editor == "emacs" and os.path.exists(os.path.join(repo_root, ".dir-locals.el")): continue
        
        try:
            cmd_setup(DummyArgs(editor))
        except Exception as e:
            print(f"[leeter] Failed to auto-bootstrap {editor}: {e}")

def cmd_setup(args):
    editors = (
        ["zed", "vscode", "neovim", "emacs"]
        if args.editor == "all"
        else [args.editor]
    )

    # When "all", only run backends where the editor is detected
    if args.editor == "all":
        detectors = {
            "zed":    lambda: shutil.which("zed") or os.path.exists(os.path.expanduser("~/.config/zed")),
            "vscode": lambda: shutil.which("code") or shutil.which("code-insiders"),
            "neovim": lambda: shutil.which("nvim"),
            "emacs":  lambda: shutil.which("emacs"),
        }
        editors = [e for e in editors if detectors[e]()]
        if not editors:
            print("[leeter] No supported editors detected. Install Zed, VSCode, Neovim, or Emacs first.")
            return
        print(f"[leeter] Detected editors: {', '.join(editors)}")

    dispatch = {
        "zed":    setup_zed,
        "vscode": setup_vscode,
        "neovim": setup_neovim,
        "emacs":  setup_emacs,
    }

    for editor in editors:
        print(f"\n--- {editor} ---")
        dispatch[editor](args)
