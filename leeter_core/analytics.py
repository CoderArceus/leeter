# leeter_core/analytics.py
"""Core analytics and storage functionality – pure library.

Extracted from cli/stats.py and cli/storage.py.  No print() calls, no
renderer dependency.  Returns plain dicts/dataclasses that the CLI
wrapper or FastAPI router can format however they want.

Public API
----------
get_all_problems(problems_dir) -> list[tuple[str, dict]]
    Scan the problems/ directory and return (path, problem_data) tuples.

get_stats_summary(problems_dir) -> StatsSummary
    Aggregate solved/total counts by difficulty and avg benchmark time.

search_problems(problems_dir, query) -> list[SearchHit]
    Full-text search across title, slug, tags, and README.

load_session() -> dict
    Load the user session from ~/.lc/session.json.

save_session(session_data) -> None
    Persist the session to ~/.lc/session.json.

update_streak(session_data) -> dict
    Update the daily-solve streak in *session_data* and return it.

mark_problem_solved(problem_dir) -> None
    Set ``solved=True`` in problem.json and update the session streak.

set_last_accessed_problem(problem_dir) -> None
get_last_accessed_problem() -> str | None
"""

import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# ── Result data classes ──────────────────────────────────────────────────

@dataclass
class DifficultyCount:
    solved: int = 0
    total: int = 0


@dataclass
class StatsSummary:
    """Aggregate statistics across all problems."""
    easy: DifficultyCount = field(default_factory=DifficultyCount)
    medium: DifficultyCount = field(default_factory=DifficultyCount)
    hard: DifficultyCount = field(default_factory=DifficultyCount)
    total_solved: int = 0
    total_problems: int = 0
    avg_benchmark_ns: Optional[float] = None


@dataclass
class SearchHit:
    """One matching problem from a search query."""
    path: str
    id: Optional[int] = None
    title: str = ""
    difficulty: str = ""
    solved: bool = False


# ── Problem scanning ─────────────────────────────────────────────────────

def get_all_problems(
    problems_dir: Optional[str] = None,
) -> List[Tuple[str, dict]]:
    """Scan *problems_dir* and return ``(path, problem_data)`` tuples.

    If *problems_dir* is ``None``, falls back to ``<repo>/problems/``
    relative to this file's location (matching the original CLI behaviour).
    """
    if problems_dir is None:
        problems_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "problems",
        )

    problems: List[Tuple[str, dict]] = []
    if not os.path.exists(problems_dir):
        return problems

    for pdir in os.listdir(problems_dir):
        full_path = os.path.join(problems_dir, pdir)
        if not os.path.isdir(full_path):
            continue

        pjson_path = os.path.join(full_path, "problem.json")
        if not os.path.exists(pjson_path):
            continue

        try:
            with open(pjson_path, "r") as f:
                data = json.load(f)
            problems.append((full_path, data))
        except Exception:
            pass

    return problems


# ── Aggregate stats ──────────────────────────────────────────────────────

def get_stats_summary(
    problems_dir: Optional[str] = None,
) -> StatsSummary:
    """Compute solved/total counts by difficulty and average benchmark time."""
    problems = get_all_problems(problems_dir)

    solved: Dict[str, int] = {"Easy": 0, "Medium": 0, "Hard": 0}
    total: Dict[str, int] = {"Easy": 0, "Medium": 0, "Hard": 0}
    benchmarks: List[float] = []

    for _path, data in problems:
        diff = data.get("difficulty", "Easy")
        if diff not in total:
            diff = "Easy"

        total[diff] += 1
        if data.get("solved", False):
            solved[diff] += 1

        bh = data.get("benchmark_history", [])
        if bh:
            benchmarks.append(bh[-1]["mean_ns"])  # latest run

    avg_ns = (sum(benchmarks) / len(benchmarks)) if benchmarks else None

    return StatsSummary(
        easy=DifficultyCount(solved=solved["Easy"], total=total["Easy"]),
        medium=DifficultyCount(solved=solved["Medium"], total=total["Medium"]),
        hard=DifficultyCount(solved=solved["Hard"], total=total["Hard"]),
        total_solved=sum(solved.values()),
        total_problems=sum(total.values()),
        avg_benchmark_ns=avg_ns,
    )


# ── Search ───────────────────────────────────────────────────────────────

def search_problems(
    query: str,
    problems_dir: Optional[str] = None,
) -> List[SearchHit]:
    """Return problems whose title, slug, tags, or README contain *query*."""
    query_lower = query.lower()
    problems = get_all_problems(problems_dir)
    hits: List[SearchHit] = []

    for path, data in problems:
        title = data.get("title", "").lower()
        slug = data.get("slug", "").lower()
        tags = [t.lower() for t in data.get("tags", [])]

        match = False
        if query_lower in title or query_lower in slug:
            match = True
        if any(query_lower in tag for tag in tags):
            match = True

        readme_path = os.path.join(path, "README.md")
        if not match and os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                if query_lower in f.read().lower():
                    match = True

        if match:
            hits.append(SearchHit(
                path=path,
                id=data.get("id"),
                title=data.get("title", ""),
                difficulty=data.get("difficulty", ""),
                solved=data.get("solved", False),
            ))

    return hits


# ── Session / streak persistence ─────────────────────────────────────────

def _get_session_file() -> str:
    os.makedirs(os.path.expanduser("~/.lc"), exist_ok=True)
    return os.path.expanduser("~/.lc/session.json")


def load_session() -> dict:
    """Load the user session from ``~/.lc/session.json``."""
    filepath = _get_session_file()
    if not os.path.exists(filepath):
        return {
            "streak": 0,
            "last_solve_date": None,
            "daily_goal": "3:1:1:1",  # total:easy:medium:hard
            "recent_solves": [],
        }
    with open(filepath, "r") as f:
        return json.load(f)


def save_session(session_data: dict) -> None:
    """Persist the session to ``~/.lc/session.json``."""
    filepath = _get_session_file()
    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=2)


def update_streak(session_data: dict) -> dict:
    """Update the daily-solve streak in *session_data* (mutates in-place)."""
    today = datetime.now().strftime("%Y-%m-%d")
    last_solve = session_data.get("last_solve_date")

    if last_solve == today:
        pass  # Already solved today
    elif last_solve is None:
        session_data["streak"] = 1
        session_data["last_solve_date"] = today
    else:
        last_date = datetime.strptime(last_solve, "%Y-%m-%d")
        curr_date = datetime.strptime(today, "%Y-%m-%d")
        if (curr_date - last_date).days == 1:
            session_data["streak"] += 1
        else:
            session_data["streak"] = 1
        session_data["last_solve_date"] = today

    return session_data


def mark_problem_solved(problem_dir: str) -> None:
    """Set ``solved=True`` in problem.json and update the session streak."""
    problem_file = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(problem_file):
        return

    with open(problem_file, "r") as f:
        problem_data = json.load(f)

    if not problem_data.get("solved", False):
        problem_data["solved"] = True

        session = load_session()
        session = update_streak(session)

        solve_entry = {
            "id": problem_data.get("id"),
            "slug": problem_data.get("slug"),
            "date": datetime.now().isoformat(),
        }

        recent = session.get("recent_solves", [])
        recent.insert(0, solve_entry)
        session["recent_solves"] = recent[:50]  # keep last 50

        save_session(session)

    with open(problem_file, "w") as f:
        json.dump(problem_data, f, indent=2)


def set_last_accessed_problem(problem_dir: str) -> None:
    session = load_session()
    session["last_accessed_problem"] = os.path.abspath(problem_dir)
    save_session(session)


def get_last_accessed_problem() -> Optional[str]:
    session = load_session()
    return session.get("last_accessed_problem")
