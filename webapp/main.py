from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from webapp.routers import run, bench, stress, analytics, trace, workspace
from leeter_core.exceptions import (
    ProblemNotFoundError, FileNotFoundInProblemError,
    UnsupportedRunnerError, CompilationError,
    BenchmarkExecutionError, RuntimeError_,
    TimeLimitExceeded, StressMismatchError
)

app = FastAPI(title="Leeter API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
@app.exception_handler(ProblemNotFoundError)
@app.exception_handler(FileNotFoundInProblemError)
async def not_found_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(UnsupportedRunnerError)
async def bad_request_handler(request: Request, exc: UnsupportedRunnerError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})

@app.exception_handler(CompilationError)
async def compilation_error_handler(request: Request, exc: CompilationError):
    return JSONResponse(status_code=500, content={"detail": str(exc), "stderr": exc.stderr})

@app.exception_handler(BenchmarkExecutionError)
@app.exception_handler(RuntimeError_)
async def execution_error_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc), "raw_output": exc.raw_output})

@app.exception_handler(TimeLimitExceeded)
async def timeout_handler(request: Request, exc: TimeLimitExceeded):
    return JSONResponse(status_code=408, content={"detail": str(exc), "timeout_sec": exc.timeout_sec})

@app.exception_handler(StressMismatchError)
async def stress_mismatch_handler(request: Request, exc: StressMismatchError):
    return JSONResponse(status_code=200, content={
        "status": "fail",
        "payload": {
            "found_at_iteration": exc.iteration,
            "seed": exc.seed,
            "input": exc.input_data,
            "solution_output": exc.solution_output,
            "brute_output": exc.brute_output
        }
    })

# Mount Routers
app.include_router(run.router, prefix="/api/run", tags=["run"])
app.include_router(bench.router, prefix="/api/bench", tags=["bench"])
app.include_router(stress.router, prefix="/api/stress", tags=["stress"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(trace.router, prefix="/api/trace", tags=["trace"])
app.include_router(workspace.router, prefix="/api/workspace", tags=["workspace"])

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount the React dist/ directory for assets
dist_dir = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(dist_dir, "assets")), name="assets")

    # Catch-all route to serve index.html for React Router
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        index_path = os.path.join(dist_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return JSONResponse(status_code=404, content={"detail": "Not found"})
