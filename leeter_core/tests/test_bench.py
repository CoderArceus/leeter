import os
import json
import pytest
from leeter_core.bench import bench_problem
from leeter_core.exceptions import ProblemNotFoundError, UnsupportedRunnerError, FileNotFoundInProblemError

def test_bench_missing_problem_json(tmp_path):
    with pytest.raises(ProblemNotFoundError):
        bench_problem(str(tmp_path))

def test_bench_unsupported_runner(tmp_path):
    (tmp_path / "problem.json").write_text(json.dumps({"runner": "interactive"}))
    with pytest.raises(UnsupportedRunnerError):
        bench_problem(str(tmp_path))

def test_bench_missing_input_txt(tmp_path, monkeypatch):
    (tmp_path / "problem.json").write_text(json.dumps({
        "runner": "function", "function": {"name": "foo", "return_type": {"kind": "Primitive", "name": "int"}, "parameters": []}
    }))
    (tmp_path / "solution.cpp").write_text("int foo() { return 0; }")
    
    # Mock compile_file to avoid actually running clang++ during the test
    import leeter_core.bench
    monkeypatch.setattr(leeter_core.bench, "compile_file", lambda src, bin, problem_dir: None)
    
    with pytest.raises(FileNotFoundInProblemError):
        bench_problem(str(tmp_path))
