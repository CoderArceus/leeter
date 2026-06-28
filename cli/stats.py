import os
import json

def get_all_problems():
    problems_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "problems")
    problems = []
    if os.path.exists(problems_dir):
        for pdir in os.listdir(problems_dir):
            full_path = os.path.join(problems_dir, pdir)
            if not os.path.isdir(full_path): continue
            
            pjson_path = os.path.join(full_path, "problem.json")
            if not os.path.exists(pjson_path): continue
            
            with open(pjson_path, "r") as f:
                try:
                    data = json.load(f)
                    problems.append((full_path, data))
                except Exception:
                    pass
    return problems

def cmd_stats(args):
    problems = get_all_problems()
    
    solved = {"Easy": 0, "Medium": 0, "Hard": 0}
    total = {"Easy": 0, "Medium": 0, "Hard": 0}
    benchmarks = []
    
    for path, data in problems:
        diff = data.get("difficulty", "Easy")
        if diff not in total: diff = "Easy"
        
        total[diff] += 1
        if data.get("solved", False):
            solved[diff] += 1
            
        bh = data.get("benchmark_history", [])
        if bh:
            benchmarks.append(bh[-1]["mean_ns"]) # use latest
            
    print("\n--- Leeter Statistics ---")
    print("📊 Solved / Total")
    print(f"  Easy:   {solved['Easy']:3d} / {total['Easy']:3d}")
    print(f"  Medium: {solved['Medium']:3d} / {total['Medium']:3d}")
    print(f"  Hard:   {solved['Hard']:3d} / {total['Hard']:3d}")
    print(f"  TOTAL:  {sum(solved.values()):3d} / {sum(total.values()):3d}")
    
    if benchmarks:
        avg_mean_ns = sum(benchmarks) / len(benchmarks)
        print(f"\n⚡ Average Solution Time: {avg_mean_ns/1000.0:.2f} µs")
    print()

def cmd_search(args):
    query = args.query.lower()
    problems = get_all_problems()
    
    print(f"\n🔍 Searching for '{query}'...")
    found = 0
    
    for path, data in problems:
        title = data.get("title", "").lower()
        slug = data.get("slug", "").lower()
        tags = [t.lower() for t in data.get("tags", [])]
        
        match = False
        if query in title or query in slug:
            match = True
        if any(query in tag for tag in tags):
            match = True
            
        readme_path = os.path.join(path, "README.md")
        if not match and os.path.exists(readme_path):
            with open(readme_path, "r") as f:
                if query in f.read().lower():
                    match = True
                    
        if match:
            found += 1
            status = "✅" if data.get("solved", False) else "❌"
            print(f"  {status} [{data.get('id')}] {data.get('title')} ({data.get('difficulty')})")
            
    if found == 0:
        print("  No matches found.")
    print()
