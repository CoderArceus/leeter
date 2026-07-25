from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any
from leeter_core.bench import bench_problem

router = APIRouter()

class BenchRequest(BaseModel):
    problem_dir: str
    iterations: int = 1000

class BenchResponse(BaseModel):
    status: str
    payload: Dict[str, Any]

from fastapi.concurrency import run_in_threadpool

@router.post("/", response_model=BenchResponse)
async def bench_problem_endpoint(req: BenchRequest):
    stats = await run_in_threadpool(bench_problem, req.problem_dir, req.iterations)
    return BenchResponse(
        status="pass",
        payload={
            "iterations": stats["iterations"],
            "mean_ms": round(stats["mean_ns"] / 1_000_000.0, 2),
            "median_ms": round(stats["median_ns"] / 1_000_000.0, 2),
            "p95_ms": round(stats["p95_ns"] / 1_000_000.0, 2),
            "p99_ms": round(stats["p99_ns"] / 1_000_000.0, 2),
            "stddev_ms": round(stats["stddev_ns"] / 1_000_000.0, 2),
        }
    )
