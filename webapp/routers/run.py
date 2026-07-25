from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from leeter_core.build import run_problem_pipeline

router = APIRouter()

class RunRequest(BaseModel):
    problem_dir: str
    timeout_sec: int = 5

class CaseResultModel(BaseModel):
    index: int
    status: str
    got: str

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
    
    cases = [CaseResultModel(index=c.index, status=c.status, got=c.got) for c in result.cases]
    stats = RunStatsModel(
        passed=result.passed,
        failed=result.failed,
        total=result.total,
        run_ms=result.run_ms,
        binary_kb=result.binary_kb
    )
    
    return RunResponse(
        status="pass" if result.failed == 0 else "fail",
        payload=RunPayloadModel(cases=cases, stats=stats)
    )
