#!/usr/bin/env python3
import subprocess
import sys
import time
import os
import signal

def main():
    print("Starting Leeter DX Stack...")
    
    is_windows = os.name == 'nt'
    
    kwargs = {}
    if is_windows:
        kwargs['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs['preexec_fn'] = os.setsid
        
    # 1. Start FastAPI backend
    backend = subprocess.Popen(
        ["uvicorn", "webapp.main:app", "--reload"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        **kwargs
    )
    
    # 2. Start Vite frontend
    frontend = subprocess.Popen(
        ["npm", "run", "dev", "--prefix", "webapp/frontend"],
        stdout=sys.stdout,
        stderr=sys.stderr,
        **kwargs
    )
    
    try:
        # Keep main thread alive waiting for processes
        while backend.poll() is None and frontend.poll() is None:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nShutting down Leeter DX Stack...")
    finally:
        # Graceful cleanup
        if is_windows:
            os.kill(backend.pid, signal.CTRL_BREAK_EVENT)
            os.kill(frontend.pid, signal.CTRL_BREAK_EVENT)
        else:
            try:
                os.killpg(os.getpgid(backend.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                os.killpg(os.getpgid(frontend.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
                
        backend.wait()
        frontend.wait()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
