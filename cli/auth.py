import os
import json
from cli.output import renderer

def cmd_auth(args):
    os.makedirs(os.path.expanduser("~/.lc"), exist_ok=True)
    session_file = os.path.expanduser("~/.lc/session.json")
    if getattr(args, 'check', False):
        with open(session_file, 'r') as f:
            data = json.load(f)
            if "cookie" in data:
                renderer.success("Authenticated.")
            else:
                renderer.error("Not authenticated.")
    else:
        with open(session_file, 'w') as f:
            json.dump({"cookie": getattr(args, 'cookie', '')}, f)
        renderer.success("Session cookie saved to ~/.lc/session.json")
