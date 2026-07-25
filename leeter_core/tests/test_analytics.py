import os
import json
import pytest
from leeter_core.analytics import get_stats_summary, search_problems

@pytest.fixture
def mock_problems_dir(tmp_path):
    p1 = tmp_path / "1_two_sum"
    p1.mkdir()
    (p1 / "problem.json").write_text(json.dumps({
        "id": 1, "title": "Two Sum", "difficulty": "Easy", "solved": True, "slug": "two-sum", "tags": ["array", "hash-table"]
    }))
    p2 = tmp_path / "2_add_two_numbers"
    p2.mkdir()
    (p2 / "problem.json").write_text(json.dumps({
        "id": 2, "title": "Add Two Numbers", "difficulty": "Medium", "solved": False, "slug": "add-two-numbers",
        "benchmark_history": [{"mean_ns": 1500000}]
    }))
    return str(tmp_path)

def test_get_stats_summary(mock_problems_dir):
    summary = get_stats_summary(mock_problems_dir)
    assert summary.total_problems == 2
    assert summary.total_solved == 1
    assert summary.easy.solved == 1
    assert summary.easy.total == 1
    assert summary.medium.solved == 0
    assert summary.medium.total == 1
    assert summary.avg_benchmark_ns == 1500000.0

def test_search_problems(mock_problems_dir):
    hits = search_problems("two", mock_problems_dir)
    assert len(hits) == 2
    
    hits = search_problems("array", mock_problems_dir)
    assert len(hits) == 1
    assert hits[0].id == 1
