from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional
from leeter_core.stress import stress_test

router = APIRouter()

class StressRequest(BaseModel):
    problem_dir: str
    iterations: int = 1000
    seed: Optional[int] = None
    timeout: int = 2

class StressResponse(BaseModel):
    status: str
    payload: Dict[str, Any]

from fastapi.concurrency import run_in_threadpool

@router.post("/", response_model=StressResponse)
async def stress_problem_endpoint(req: StressRequest):
    result = await run_in_threadpool(stress_test, req.problem_dir, req.iterations, req.seed, req.timeout)
    return StressResponse(
        status="pass",
        payload={"passed_iterations": result.passed_iterations}
    )
