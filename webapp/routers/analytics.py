from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from leeter_core.analytics import (
    get_stats_summary, search_problems, load_session,
    DifficultyCount, StatsSummary, SearchHit
)

router = APIRouter()

@router.get("/summary", response_model=StatsSummary)
def get_summary(problems_dir: Optional[str] = None):
    return get_stats_summary(problems_dir)

@router.get("/search", response_model=List[SearchHit])
def search(query: str, problems_dir: Optional[str] = None):
    return search_problems(query, problems_dir)

@router.get("/session")
def get_session():
    return load_session()
