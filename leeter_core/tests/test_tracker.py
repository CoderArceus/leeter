import os
import pytest
from leeter_core.tracer.engine import trace_problem

def test_tracker_zero_code_gutter():
    prob_dir = "problems/1_two_sum"
    if not os.path.exists(prob_dir):
        pytest.skip("Two sum problem directory not found for tracking verification")
        
    # Verify that solution.cpp is unmodified and has no TRACK macros
    sol_path = os.path.join(prob_dir, "solution.cpp")
    with open(sol_path, "r") as f:
        content = f.read()
    assert "TRACK" not in content, "solution.cpp should remain pristine without embedded macros!"

    # Simulate user clicking Line 8 in gutter and defining watch elements in UI
    events = trace_problem(
        prob_dir,
        breakpoints=[8],
        watch_exprs=["i", "nums[i]", "complement", "m"]
    )
    assert isinstance(events, list)
    assert len(events) > 0
    first_ev = events[0]
    assert "iteration" in first_ev
    assert "vars" in first_ev
    assert "i" in first_ev["vars"]
    assert "nums[i]" in first_ev["vars"]
    assert "complement" in first_ev["vars"]
    assert first_ev["vars"]["i"] == "0"
