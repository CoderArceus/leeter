import os
import json
import pytest
from leeter_core.stress import stress_test
from leeter_core.exceptions import ProblemNotFoundError, UnsupportedRunnerError, FileNotFoundInProblemError

def test_stress_missing_problem_json(tmp_path):
    with pytest.raises(ProblemNotFoundError):
        stress_test(str(tmp_path))

def test_stress_unsupported_runner(tmp_path):
    (tmp_path / "problem.json").write_text(json.dumps({"runner": "stateful_class"}))
    with pytest.raises(UnsupportedRunnerError):
        stress_test(str(tmp_path))

def test_stress_missing_brute_cpp(tmp_path, monkeypatch):
    (tmp_path / "problem.json").write_text(json.dumps({
        "runner": "function", "function": {"name": "foo", "return_type": {"kind": "Primitive", "name": "int"}, "parameters": []}
    }))
    
    # Mock compile_file
    import leeter_core.stress
    monkeypatch.setattr(leeter_core.stress, "compile_file", lambda src, bin, problem_dir: None)
    
    with pytest.raises(FileNotFoundInProblemError):
        stress_test(str(tmp_path))
