import os
import sys
import json
import glob

CURRENT_FRAMEWORK_VERSION = 2

def migrate_problem(problem_dir: str):
    problem_file = os.path.join(problem_dir, "problem.json")
    if not os.path.exists(problem_file):
        return
        
    try:
        with open(problem_file, "r") as f:
            problem_data = json.load(f)
    except Exception as e:
        print(f"Error reading {problem_file}: {e}")
        return
        
    version = problem_data.get("framework_version", 1)
    
    if version == CURRENT_FRAMEWORK_VERSION:
        return
        
    if version > CURRENT_FRAMEWORK_VERSION:
        print(f"Error: {problem_dir} has framework_version {version} which is newer than current {CURRENT_FRAMEWORK_VERSION}. Aborting to prevent corruption.")
        sys.exit(1)
        
    # Migration 1 -> 2
    if version == 1:
        # In version 2, we added benchmark_history, solved, solve_time_ms, notes if they don't exist
        if "benchmark_history" not in problem_data:
            problem_data["benchmark_history"] = []
        if "solved" not in problem_data:
            problem_data["solved"] = False
        if "solve_time_ms" not in problem_data:
            problem_data["solve_time_ms"] = None
        if "notes" not in problem_data:
            problem_data["notes"] = ""
            
        problem_data["framework_version"] = 2
        print(f"Migrated {problem_dir} to version 2.")
        version = 2
        
    with open(problem_file, "w") as f:
        json.dump(problem_data, f, indent=2)

def cmd_migrate(args):
    problems_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "problems")
    if not os.path.exists(problems_dir):
        print("No problems directory found.")
        return
        
    problem_dirs = [os.path.join(problems_dir, d) for d in os.listdir(problems_dir) if os.path.isdir(os.path.join(problems_dir, d))]
    
    print(f"Scanning {len(problem_dirs)} problems for migration...")
    for pdir in problem_dirs:
        migrate_problem(pdir)
        
    print("Migration complete.")
