import os
import sys
import json
from cli.storage import load_session, save_session

def cmd_session(args):
    session = load_session()
    
    if args.goal:
        try:
            parts = args.goal.split(":")
            if len(parts) != 4: raise ValueError
            [int(p) for p in parts] # validate integers
            session["daily_goal"] = args.goal
            save_session(session)
            print(f"Daily goal updated to {args.goal}")
        except Exception:
            print("Invalid goal format. Use 'total:easy:medium:hard' (e.g. 5:1:3:1)")
            sys.exit(1)
            
    print(f"\n--- Leeter Session ---")
    print(f"🔥 Current Streak: {session.get('streak', 0)} days")
    print(f"🎯 Daily Goal: {session.get('daily_goal')}")
    
    recent = session.get("recent_solves", [])
    if recent:
        print("\n🕒 Recent Solves:")
        for solve in recent[:5]:
            print(f"   - [{solve['id']}] {solve['slug']} (at {solve['date'][:10]})")
    else:
        print("\n🕒 Recent Solves: None yet!")
        
    print("\n💡 Suggested Problems:")
    problems_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "problems")
    
    unsolved = []
    if os.path.exists(problems_dir):
        for pdir in os.listdir(problems_dir):
            full_path = os.path.join(problems_dir, pdir)
            if not os.path.isdir(full_path): continue
            
            pjson_path = os.path.join(full_path, "problem.json")
            if not os.path.exists(pjson_path): continue
            
            with open(pjson_path, "r") as f:
                try:
                    data = json.load(f)
                    if not data.get("solved", False):
                        diff_str = data.get("difficulty", "Easy")
                        diff_val = 1 if diff_str == "Easy" else 2 if diff_str == "Medium" else 3
                        unsolved.append({
                            "id": data.get("id"),
                            "slug": data.get("slug"),
                            "difficulty": diff_str,
                            "diff_val": diff_val
                        })
                except Exception:
                    pass
                    
    unsolved.sort(key=lambda x: (x["diff_val"], x["id"]))
    
    if not unsolved:
        print("   No unsolved problems found! Run `leetcode fetch` to get more.")
    else:
        for p in unsolved[:5]:
            print(f"   - [{p['id']}] {p['slug']} ({p['difficulty']})")
    print()
