import os
import json
import asyncio
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
import subprocess
from typing import Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from leeter_core.exceptions import FileNotFoundInProblemError

router = APIRouter(tags=["workspace"])

def read_workspace_files(problem_dir: str) -> dict:
    sol_path = os.path.join(problem_dir, "solution.cpp")
    input_path = os.path.join(problem_dir, "input.txt")
    brute_path = os.path.join(problem_dir, "brute.cpp")
    files = {}
    
    if os.path.exists(sol_path):
        with open(sol_path, 'r') as f:
            files["solution.cpp"] = f.read()
            
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            files["input.txt"] = f.read()
    else:
        files["input.txt"] = ""
        
    if os.path.exists(brute_path):
        with open(brute_path, 'r') as f:
            files["brute.cpp"] = f.read()
    else:
        files["brute.cpp"] = "// Naive brute force solution for stress testing\n#include \"lc.h\"\n\nclass BruteSolution {\npublic:\n    // Add your brute force implementation here\n};\n"
        
    return files

from typing import List
from pydantic import BaseModel

class SaveRequest(BaseModel):
    problem_dir: str
    content: str

@router.post("/save")
async def save_file(req: SaveRequest):
    """Saves the provided content to solution.cpp in the specified problem directory."""
    problem_dir = os.path.abspath(req.problem_dir)
    sol_path = os.path.join(problem_dir, "solution.cpp")
    
    if not os.path.exists(problem_dir):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Problem directory not found")
        
    with open(sol_path, "w") as f:
        f.write(req.content)
        
    return {"status": "success"}

class FetchRequest(BaseModel):
    problem_id: str

@router.post("/fetch")
async def fetch_problem(req: FetchRequest):
    """Fetches a LeetCode problem by ID or URL and scaffolds it."""
    from leeter_core.fetch import get_title_slug_by_id, fetch_question_data
    from cli.scaffold import scaffold_problem
    import re
    
    # Extract ID if URL is provided
    # URLs look like: https://leetcode.com/problems/two-sum/
    val = req.problem_id.strip().lstrip('#').strip()
    if "leetcode.com/problems/" in val:
        match = re.search(r"leetcode\.com/problems/([^/]+)", val)
        if match:
            title_slug = match.group(1)
            # if we only have title slug, we can fetch directly
            data = fetch_question_data(title_slug)
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid LeetCode URL")
    else:
        title_slug = get_title_slug_by_id(val)
        data = fetch_question_data(title_slug)
        
    folder = scaffold_problem(data, force=False)
    # folder is like 'problems/1_two_sum'
    return {"status": "success", "folder": folder}

@router.get("/problems")
async def list_problems() -> List[str]:
    """Returns a list of all problem directories in the problems/ folder."""
    problems_dir = os.path.abspath("problems")
    if not os.path.exists(problems_dir):
        return []
    
    problems = []
    for d in os.listdir(problems_dir):
        if os.path.isdir(os.path.join(problems_dir, d)):
            problems.append(f"problems/{d}")
            
    return sorted(problems)

@router.get("/testcase")
async def get_testcase(problem_dir: str) -> str:
    """Returns the string contents of input.txt."""
    problem_dir = os.path.abspath(problem_dir)
    input_path = os.path.join(problem_dir, "input.txt")
    if os.path.exists(input_path):
        with open(input_path, 'r') as f:
            return f.read()
    return ""

@router.post("/testcase/save")
async def save_testcase(req: SaveRequest):
    """Saves the provided content to input.txt in the specified problem directory."""
    problem_dir = os.path.abspath(req.problem_dir)
    input_path = os.path.join(problem_dir, "input.txt")
    
    if not os.path.exists(problem_dir):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Problem directory not found")
        
    with open(input_path, "w") as f:
        f.write(req.content)
        
    return {"status": "success"}

@router.get("/brute")
async def get_brute(problem_dir: str) -> str:
    """Returns the string contents of brute.cpp. Returns a template if it doesn't exist."""
    problem_dir = os.path.abspath(problem_dir)
    brute_path = os.path.join(problem_dir, "brute.cpp")
    if os.path.exists(brute_path):
        with open(brute_path, 'r') as f:
            return f.read()
    return "// Naive brute force solution for stress testing\n#include \"lc.h\"\n\nclass BruteSolution {\npublic:\n    // Add your brute force implementation here\n};\n"

@router.post("/brute/save")
async def save_brute(req: SaveRequest):
    """Saves the provided content to brute.cpp in the specified problem directory."""
    problem_dir = os.path.abspath(req.problem_dir)
    brute_path = os.path.join(problem_dir, "brute.cpp")
    
    if not os.path.exists(problem_dir):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Problem directory not found")
        
    with open(brute_path, "w") as f:
        f.write(req.content)
        
    return {"status": "success"}

@router.get("/files")
async def get_files(problem_dir: str) -> Dict[str, str]:
    """
    Returns the current contents of solution.cpp and input.txt.
    """
    problem_dir = os.path.abspath(problem_dir)
    return read_workspace_files(problem_dir)

@router.get("/events")
async def workspace_events(request: Request, problem_dir: str):
    problem_dir = os.path.abspath(problem_dir)
    
    async def event_generator():
        q = asyncio.Queue()
        
        class Handler(FileSystemEventHandler):
            def on_modified(self, event):
                if event.is_directory:
                    return
                # We only care about solution.cpp, input.txt, and brute.cpp
                if event.src_path.endswith("solution.cpp") or event.src_path.endswith("input.txt") or event.src_path.endswith("brute.cpp"):
                    # Fire-and-forget an event into the asyncio loop
                    try:
                        loop = asyncio.get_event_loop()
                        loop.call_soon_threadsafe(q.put_nowait, True)
                    except Exception:
                        pass
                        
        observer = Observer()
        observer.schedule(Handler(), problem_dir, recursive=False)
        observer.start()
        
        try:
            # Send initial state
            data = read_workspace_files(problem_dir)
            yield f"data: {json.dumps(data)}\n\n"
            
            while True:
                if await request.is_disconnected():
                    break
                    
                # Wait for file change with a timeout to detect disconnects
                try:
                    await asyncio.wait_for(q.get(), timeout=1.0)
                    # Drain any burst of events
                    while not q.empty():
                        q.get_nowait()
                        
                    data = read_workspace_files(problem_dir)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    pass # Just loop to check is_disconnected
        finally:
            observer.stop()
            observer.join()
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.websocket("/replay/ws")
async def replay_websocket(websocket: WebSocket, problem_dir: str, breakpoints: str = "", watch_exprs: str = ""):
    await websocket.accept()
    
    problem_dir = os.path.abspath(problem_dir)
    sol_path = os.path.join(problem_dir, "solution.cpp")
    if not os.path.exists(sol_path):
        await websocket.send_json({"type": "error", "message": "solution.cpp not found"})
        await websocket.close()
        return

    # Parse breakpoints
    breakpoints_list = []
    if breakpoints:
        try:
            breakpoints_list = [int(x.strip()) for x in breakpoints.split(",") if x.strip()]
        except ValueError:
            pass
            
    # Parse watch expressions
    watch_exprs_list = []
    if watch_exprs:
        watch_exprs_list = [x.strip() for x in watch_exprs.split(",") if x.strip()]

    from cli.analyzer import run_pipeline_unified
    from cli.runners.function import FunctionRunner
    from cli.runners.stateful_class import StatefulClassRunner
    from cli.build import compile_replay
    from leeter_core.debugger import DebuggerWrapper
    
    with open(sol_path, 'r') as f:
        stub = f.read()
        
    ir, _ = run_pipeline_unified(stub)
    if ir.runner == "function":
        runner = FunctionRunner()
    elif ir.runner == "stateful_class":
        runner = StatefulClassRunner()
    else:
        await websocket.send_json({"type": "error", "message": f"Runner {ir.runner} not supported for replay."})
        await websocket.close()
        return
        
    include_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "include"))
    driver_code = runner.generate(ir, include_path=include_path)
    
    os.makedirs(os.path.join(problem_dir, "build"), exist_ok=True)
    driver_path = os.path.join(problem_dir, "build", "driver.cpp")
    with open(driver_path, 'w') as f:
        f.write(driver_code)
        
    if not compile_replay(problem_dir):
        await websocket.send_json({"type": "error", "message": "Compilation failed. Check terminal."})
        await websocket.close()
        return
        
    bin_path = os.path.join(problem_dir, "build", "solution_replay")
    input_file = os.path.join(problem_dir, 'input.txt')
    if not os.path.exists(input_file):
        open(input_file, 'w').close()
        
    # Instantiate native debugger wrapper
    debugger = DebuggerWrapper(bin_path, input_file)
    try:
        await debugger.start(breakpoints=breakpoints_list)
        
        # Send initial locals
        locals_dict = await debugger.get_locals(watch_exprs=watch_exprs_list if watch_exprs_list else None)
        await websocket.send_json({"locals": locals_dict})
    except Exception as e:
        print(f"Debugger error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": f"Debugger start failed: {str(e)}"})
            await websocket.close()
        except Exception:
            pass
        return

    async def read_ws():
        try:
            while True:
                data = await websocket.receive_json()
                if data.get("command") == "step":
                    try:
                        if breakpoints_list:
                            await debugger.continue_execution()
                        else:
                            await debugger.step()
                        
                        # Read dynamic watch expressions from payload if provided
                        dynamic_watch_exprs = data.get("watch_exprs")
                        if dynamic_watch_exprs and isinstance(dynamic_watch_exprs, list):
                            current_watch_exprs = [x.strip() for x in dynamic_watch_exprs if x.strip()]
                        else:
                            current_watch_exprs = watch_exprs_list

                        locals_dict = await debugger.get_locals(watch_exprs=current_watch_exprs if current_watch_exprs else None)
                        await websocket.send_json({"locals": locals_dict})
                    except Exception:
                        pass
        except WebSocketDisconnect:
            pass
        except Exception:
            pass
            
    # Run the loop to listen to websocket commands
    try:
        await read_ws()
    finally:
        debugger.stop()
        try:
            await websocket.close()
        except Exception:
            pass
