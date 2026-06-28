import os
from cli.output import renderer

def cmd_clean(args):
    problem_dir = getattr(args, 'problem', None)
    
    def clean_dir(p_dir):
        build_dir = os.path.join(p_dir, "build")
        if os.path.exists(build_dir):
            import shutil
            shutil.rmtree(build_dir)
            renderer.success(f"Removed build/  ({os.path.relpath(p_dir)})")
            
    if getattr(args, 'all', False):
        problems_dir = os.path.abspath("problems")
        if os.path.exists(problems_dir):
            for d in os.listdir(problems_dir):
                p_dir = os.path.join(problems_dir, d)
                if os.path.isdir(p_dir) and os.path.exists(os.path.join(p_dir, "problem.json")):
                    clean_dir(p_dir)
    else:
        if problem_dir:
            clean_dir(problem_dir)
