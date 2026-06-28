import os
from cli.build import compile_debug, execute_debug

def cmd_debug(args):
    problem_dir = args.problem
    if compile_debug(problem_dir, not getattr(args, 'no_sanitize', False)):
        execute_debug(problem_dir, getattr(args, 'input', 'input.txt'))
