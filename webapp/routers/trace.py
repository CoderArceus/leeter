from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List
from leeter_core.tracer.engine import trace_problem
from fastapi.concurrency import run_in_threadpool

router = APIRouter(tags=["trace"])

class TraceRequest(BaseModel):
    problem_dir: str
    test_case_input: Optional[str] = None
    breakpoints: Optional[List[int]] = None
    watch_exprs: Optional[List[str]] = None

@router.post("/")
async def run_trace(req: TraceRequest) -> List[dict]:
    # Let exceptions bubble up to the global handlers in main.py
    return await run_in_threadpool(
        trace_problem,
        req.problem_dir,
        req.test_case_input,
        req.breakpoints,
        req.watch_exprs
    )
