import os
import sys
from cli.output import renderer

def cmd_open(args):
    if getattr(args, 'id', None):
        frontend_id = args.id
        problems_dir = os.path.abspath("problems")
        if not os.path.exists(problems_dir):
            renderer.error("problems/ directory not found.")
            sys.exit(1)
        candidates = [f for f in os.listdir(problems_dir) if os.path.isdir(os.path.join(problems_dir, f)) and f.startswith(str(frontend_id) + "_")]
        if not candidates:
            renderer.error(f"Folder for ID {frontend_id} not found in problems/.")
            sys.exit(1)
        folder = os.path.join("problems", candidates[0])
    else:
        folder = getattr(args, 'problem', None)
        if not folder:
            renderer.error("No active problem resolved.")
            sys.exit(1)
        
    slug = os.path.basename(folder).split('_', 1)[1] if '_' in os.path.basename(folder) else ""
    url = f"https://leetcode.com/problems/{slug}/" if slug else ""

    if not getattr(args, 'browser_only', False):
        editor = getattr(args, 'editor', None) or os.environ.get("EDITOR", "zed")
        os.system(f"{editor} {folder}")
        
    if url and not getattr(args, 'editor_only', False):
        os.system(f"open {url}")
