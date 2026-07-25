import uvicorn
import webbrowser
import threading
import time

def cmd_ui(args):
    def open_browser():
        time.sleep(1) # wait for server to start
        webbrowser.open("http://localhost:8000")
        
    print("Starting Leeter UI on http://localhost:8000...")
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run FastAPI programmatically
    uvicorn.run("webapp.main:app", host="127.0.0.1", port=8000, log_level="info")
