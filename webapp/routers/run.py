from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from leeter_core.build import run_problem_pipeline

router = APIRouter()

class RunRequest(BaseModel):
    problem_dir: str
    timeout_sec: int = 5

class CaseResultModel(BaseModel):
    index: int
    status: str
    got: str
    expected: Optional[str] = None

class RunStatsModel(BaseModel):
    passed: int
    failed: int
    total: int
    run_ms: float
    binary_kb: float

class RunPayloadModel(BaseModel):
    cases: List[CaseResultModel]
    stats: RunStatsModel

class RunResponse(BaseModel):
    status: str
    payload: RunPayloadModel

from fastapi.concurrency import run_in_threadpool

@router.post("/", response_model=RunResponse)
async def run_problem_endpoint(req: RunRequest):
    result = await run_in_threadpool(run_problem_pipeline, req.problem_dir, req.timeout_sec)
    
    cases = [CaseResultModel(index=c.index, status=c.status, got=c.got, expected=c.expected) for c in result.cases]
    stats = RunStatsModel(
        passed=result.passed,
        failed=result.failed,
        total=result.total,
        run_ms=result.run_ms,
        binary_kb=result.binary_kb
    )
    
    status_str = "fail" if result.failed > 0 else ("pass" if result.passed == result.total and result.total > 0 else "unverified")
    return RunResponse(
        status=status_str,
        payload=RunPayloadModel(cases=cases, stats=stats)
    )

