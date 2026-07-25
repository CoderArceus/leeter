import unittest
import os
import json
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cli.analyzer import run_pipeline_unified
from cli.models import NeedInput, Warn

class TestAnalyzer(unittest.TestCase):
    def test_two_sum(self):
        stub = """
class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertEqual(ir.runner, "function")
        self.assertIsNotNone(ir.function)
        self.assertEqual(ir.function.name, "twoSum")
        self.assertEqual(ir.function.return_type.to_dict()["kind"], "Vector")
        self.assertEqual(len(ir.function.parameters), 2)
        self.assertEqual(ir.function.parameters[0].name, "nums")

    def test_lru_cache(self):
        stub = """
class LRUCache {
public:
    LRUCache(int capacity) {
        
    }
    
    int get(int key) {
        
    }
    
    void put(int key, int value) {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertEqual(ir.runner, "stateful_class")
        self.assertIsNotNone(ir.stateful_class)
        self.assertEqual(ir.stateful_class.name, "LRUCache")
        self.assertEqual(len(ir.stateful_class.constructor), 1)
        self.assertEqual(len(ir.stateful_class.methods), 2)

    def test_guess_number(self):
        stub = """
class Solution : public GuessGame {
public:
    int guessNumber(int n) {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertEqual(ir.runner, "interactive")
        self.assertEqual(ir.interactive.oracle_class, "GuessGame")

    def test_nested_iterator(self):
        stub = """
class NestedIterator {
public:
    NestedIterator(vector<NestedInteger> &nestedList) {
        
    }
    
    int next() {
        
    }
    
    bool hasNext() {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertEqual(ir.runner, "stateful_class")
        
    def test_ambiguous(self):
        stub = """
class Mystery {
public:
    int solve(int n) {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertTrue(any(isinstance(sig, NeedInput) for sig in history))
        
    def test_exotic_types(self):
        stub = """
class Solution {
public:
    void solve(MyCustomType t) {
        
    }
};
"""
        ir, history = run_pipeline_unified(stub)
        self.assertEqual(ir.runner, "function")
        self.assertTrue(any(isinstance(sig, Warn) for sig in history))
        self.assertEqual(ir.function.parameters[0].type.to_dict()["kind"], "Unknown")

if __name__ == "__main__":
    unittest.main()
