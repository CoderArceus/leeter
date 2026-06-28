import os
import json
import re

# Add parent directory to sys.path to allow imports when run locally
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.analyzer import run_pipeline_unified
from cli.models import NeedInput, RunnerKind

def generate_input_txt(example_testcases):
    # exampleTestcases usually comes in as a string separated by newlines
    # For multiple cases, we might want to split them by double newlines or something.
    # The framework expects one case per blank-line block.
    # Usually example_testcases is just newline separated variables per testcase,
    # and multiple test cases are concatenated. LeetCode sends them with \n.
    # This might require some heuristics, but let's just write what they give us directly,
    # replacing the separator if needed. LeetCode usually sends variables separated by \n
    # and test cases might not have blank lines between them. Wait, exampleTestcases is
    # just a string of values separated by \n. It's hard to split perfectly without types.
    # For now, just write it exactly, maybe with an extra blank line between them if we can guess it.
    # Actually, LeetCode's raw exampleTestcases string is usually just variables separated by \n.
    # If a problem has 3 variables, every 3 lines is a test case.
    # Without types, we can't easily insert blank lines accurately here, but we will just output as-is for now,
    # or we can rely on the fact that the user might have to fix it, but `input.txt` is an example.
    
    # Actually, looking at the spec: "one test case per blank-line block".
    # Since we can't easily parse it perfectly here without knowing parameter count, 
    # we'll just dump it as is, or we could just dump it.
    
    return example_testcases

def scaffold_problem(data, force=False):
    frontend_id = data.get('questionFrontendId', '0')
    title_slug = data.get('titleSlug', 'unknown')
    
    folder_name = f"{frontend_id}_{title_slug}".replace("-", "_")
    folder_path = os.path.join("problems", folder_name)
    
    # In case there are non-alphanumeric chars (should be fine for slug)
    os.makedirs(folder_path, exist_ok=True)
    
    # 1. Write solution.cpp (idempotent)
    sol_path = os.path.join(folder_path, "solution.cpp")
    if not os.path.exists(sol_path) or force:
        snippets = data.get('codeSnippets', [])
        cpp_snippet = next((s for s in snippets if s.get('langSlug') == 'cpp'), None)
        code = cpp_snippet.get('code', 'class Solution {};') if cpp_snippet else 'class Solution {};'
        with open(sol_path, 'w') as f:
            f.write(code)
    else:
        with open(sol_path, 'r') as f:
            code = f.read()

    # 2. Run Analyzer
    ir, signals = run_pipeline_unified(code)
    
    for sig in signals:
        if isinstance(sig, NeedInput):
            # Prompt user if interactive
            from cli.output import renderer
            import sys
            
            choice = ""
            if not renderer.use_json and not renderer.quiet and sys.stdin.isatty():
                print(f"Ambiguous Runner Detection: {sig.prompt}")
                try:
                    choice = input("> ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\n[Warning] Interactive prompt failed. Defaulting...")
                    choice = ""
            else:
                renderer.print("[Warning] Ambiguous runner detected in non-interactive mode. Defaulting...")
            
            if "Multiple methods detected" in sig.prompt:
                try:
                    idx = int(choice) - 1
                    ir.function = ir.candidate_functions[idx]
                except:
                    ir.function = ir.candidate_functions[-1]
                ir.runner = RunnerKind.FUNCTION
                ir.capabilities = ["run", "trace", "multiple_cases", "benchmark", "stress_test"]
            else:
                if choice == "1":
                    ir.runner = RunnerKind.FUNCTION
                    ir.capabilities = ["run", "trace", "multiple_cases", "benchmark", "stress_test"]
                else:
                    ir.runner = RunnerKind.STATEFUL_CLASS
                    ir.capabilities = ["run", "trace", "replay", "multiple_cases"]
    
    # 3. Write problem.json
    problem_json_path = os.path.join(folder_path, "problem.json")
    # preserve existing data like solved, etc if they exist
    existing_data = {}
    if os.path.exists(problem_json_path):
        try:
            with open(problem_json_path, 'r') as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    out_dict = ir.to_dict()
    out_dict['framework_version'] = 2
    out_dict['id'] = frontend_id
    out_dict['slug'] = title_slug
    out_dict['title'] = data.get('title', 'Unknown')
    out_dict['difficulty'] = data.get('difficulty', 'Unknown')
    
    # restore stateful fields
    for k in ['solved', 'solve_time_ms', 'notes', 'benchmark_history']:
        if k in existing_data:
            out_dict[k] = existing_data[k]
            
    with open(problem_json_path, 'w') as f:
        json.dump(out_dict, f, indent=2)

    # 4. Write input.txt (idempotent)
    input_path = os.path.join(folder_path, "input.txt")
    if not os.path.exists(input_path) or force:
        tc = data.get('exampleTestcases', '')
        # Try to inject blank lines if we know the number of parameters
        if ir.function and ir.function.parameters:
            param_count = len(ir.function.parameters)
            if param_count > 0:
                lines = tc.split('\n')
                formatted_tc = ""
                for i, line in enumerate(lines):
                    formatted_tc += line + "\n"
                    if (i + 1) % param_count == 0 and (i + 1) != len(lines):
                        formatted_tc += "\n"
                tc = formatted_tc
                
        with open(input_path, 'w') as f:
            f.write(tc)

    # 5. Write README.md
    readme_path = os.path.join(folder_path, "README.md")
    
    content = data.get('content', '')
    # Simple HTML strip for markdown (very rudimentary, maybe beautifulsoup is better, but trying to avoid deps)
    # The content is usually HTML. We'll leave it as HTML/Markdown mix because markdown supports HTML
    
    title = data.get('title', 'Unknown')
    difficulty = data.get('difficulty', 'Unknown')
    url = f"https://leetcode.com/problems/{title_slug}/"
    
    readme_content = f"# {frontend_id}. {title}\n\n"
    readme_content += f"**Difficulty:** {difficulty}\n"
    readme_content += f"**URL:** [{url}]({url})\n\n"
    readme_content += f"{content}\n"
    
    # Preserve My Notes section if exists
    notes_section = "\n---\n## My Notes\n\n"
    if os.path.exists(readme_path):
        with open(readme_path, 'r') as f:
            existing_readme = f.read()
            if "\n---\n## My Notes" in existing_readme:
                notes_section = "\n---\n## My Notes" + existing_readme.split("\n---\n## My Notes")[1]
                
    with open(readme_path, 'w') as f:
        f.write(readme_content + notes_section)
        
    return folder_path
