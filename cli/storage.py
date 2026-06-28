import os
import json
from datetime import datetime, timedelta

def get_session_file():
    os.makedirs(os.path.expanduser("~/.lc"), exist_ok=True)
    return os.path.expanduser("~/.lc/session.json")

def load_session():
    filepath = get_session_file()
    if not os.path.exists(filepath):
        return {
            "streak": 0,
            "last_solve_date": None,
            "daily_goal": "3:1:1:1", # total:easy:medium:hard
            "recent_solves": []
        }
    with open(filepath, "r") as f:
        return json.load(f)

def save_session(session_data):
    filepath = get_session_file()
    with open(filepath, "w") as f:
        json.dump(session_data, f, indent=2)

def update_streak(session_data):
    today = datetime.now().strftime("%Y-%m-%d")
    last_solve = session_data.get("last_solve_date")
    
    if last_solve == today:
        pass # Already solved today, streak remains the same
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

def mark_problem_solved(problem_dir: str):
    problem_file = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(problem_file):
        return
        
    with open(problem_file, "r") as f:
        problem_data = json.load(f)
        
    if not problem_data.get("solved", False):
        problem_data["solved"] = True
        
        # update session
        session = load_session()
        session = update_streak(session)
        
        solve_entry = {
            "id": problem_data.get("id"),
            "slug": problem_data.get("slug"),
            "date": datetime.now().isoformat()
        }
        
        recent = session.get("recent_solves", [])
        recent.insert(0, solve_entry)
        session["recent_solves"] = recent[:50] # keep last 50
        
        save_session(session)
        
    with open(problem_file, "w") as f:
        json.dump(problem_data, f, indent=2)

def set_last_accessed_problem(problem_dir: str):
    session = load_session()
    session["last_accessed_problem"] = os.path.abspath(problem_dir)
    save_session(session)

def get_last_accessed_problem() -> str:
    session = load_session()
    return session.get("last_accessed_problem")
