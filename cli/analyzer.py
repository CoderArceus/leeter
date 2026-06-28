import re
from typing import Tuple, List, Optional
import sys
import os

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cli.models import (
    ProblemIR, FunctionStruct, StatefulClassStruct, InteractiveStruct,
    Method, Parameter, CppType, Primitive, Pointer, Vector, Array,
    OptionalType, Pair, TupleType, Map, Unknown, RunnerKind,
    DetectionResult, DetectionAlternative, Capability,
    PipelineSignal, Continue, NeedInput, Warn, Fail
)

def parse_cpp_type(raw: str) -> CppType:
    raw = re.sub(r'\s+', ' ', raw).strip()
    raw = raw.replace('const ', '').replace('&', '').strip()
    raw = raw.replace(' *', '*')
    
    if raw in ["int", "long", "long long", "double", "bool", "string", "void", "std::string"]:
        return Primitive(raw.replace("std::", ""))
    if raw in ["TreeNode*", "ListNode*"]:
        return Pointer(raw)
    
    m = re.match(r'^vector\s*<\s*(.+)\s*>$', raw)
    if m:
        return Vector(parse_cpp_type(m.group(1)))
        
    return Unknown(raw)

def parse_params(args_raw: str) -> List[Parameter]:
    params = []
    if args_raw.strip():
        # Split by comma but respect nested brackets
        args = []
        depth = 0
        curr = ""
        for char in args_raw:
            if char == '<': depth += 1
            elif char == '>': depth -= 1
            elif char == ',' and depth == 0:
                args.append(curr)
                curr = ""
                continue
            curr += char
        if curr: args.append(curr)

        for arg in args:
            arg = arg.strip()
            # type name
            parts = arg.rsplit(' ', 1)
            if len(parts) == 2:
                ptype, pname = parts
                params.append(Parameter(pname.strip(), parse_cpp_type(ptype)))
            else:
                pass
    return params

class StubAnalyzer:
    def analyze(self, stub: str, ir: ProblemIR) -> Tuple[ProblemIR, PipelineSignal]:
        # FunctionRunner (Solution class)
        if "class Solution {" in stub:
            m = re.search(r'class Solution\s*\{.*?(?:public:)?(.*?)\};', stub, re.DOTALL)
            if m:
                body = m.group(1)
                body = body.replace('public:', '').replace('private:', '').replace('protected:', '')
                # exclude constructors/destructors by looking for return type
                for line in body.split('}'):
                    sig_m = re.search(r'([a-zA-Z0-9_<>:\*]+(?:(?:\s+|&|\*)[a-zA-Z0-9_<>:\*]+)*)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)', line)
                    if sig_m:
                        ret_type_raw = sig_m.group(1)
                        name = sig_m.group(2)
                        args_raw = sig_m.group(3)
                        
                        ret_type = parse_cpp_type(ret_type_raw)
                        ir.function = FunctionStruct(
                            name=name,
                            return_type=ret_type,
                            parameters=parse_params(args_raw)
                        )
                        break
            return ir, Continue()
            
        # InteractiveRunner (extends something)
        m = re.search(r'class Solution\s*:\s*public\s+([a-zA-Z0-9_]+)', stub)
        if m:
            ir.interactive = InteractiveStruct(oracle_class=m.group(1), mock_interface=m.group(1))
            return ir, Continue()
            
        # StatefulClassRunner
        m = re.search(r'class\s+([a-zA-Z0-9_]+)\s*\{', stub)
        if m:
            class_name = m.group(1)
            body_m = re.search(r'class\s+' + class_name + r'\s*\{.*?(?:public:)?(.*?)\};', stub, re.DOTALL)
            if body_m:
                body = body_m.group(1)
                body = body.replace('public:', '').replace('private:', '').replace('protected:', '')
                methods = []
                constructor_params = []
                # Simple extraction
                for line in body.split('}'):
                    # look for constructor
                    cons_m = re.search(class_name + r'\s*\((.*?)\)', line)
                    if cons_m and not 'return' in line:
                        constructor_params = parse_params(cons_m.group(1))
                        continue
                        
                    # look for methods
                    sig_m = re.search(r'([a-zA-Z0-9_<>:\*]+(?:(?:\s+|&|\*)[a-zA-Z0-9_<>:\*]+)*)\s+([a-zA-Z0-9_]+)\s*\((.*?)\)', line)
                    if sig_m:
                        ret = parse_cpp_type(sig_m.group(1))
                        name = sig_m.group(2)
                        if name == class_name: continue # constructor caught by method regex
                        params = parse_params(sig_m.group(3))
                        methods.append(Method(name=name, return_type=ret, parameters=params, is_void=isinstance(ret, Primitive) and ret.name == 'void'))
                
                # Check ambiguity
                if len(methods) == 1 and not constructor_params:
                    # Ambiguous! Could be FunctionRunner without Solution class or StatefulClassRunner with 1 method.
                    pass # handled by resolver
                    
                ir.stateful_class = StatefulClassStruct(
                    name=class_name,
                    constructor=constructor_params,
                    methods=methods
                )
            return ir, Continue()
            
        return ir, Continue()

class RunnerResolver:
    def analyze(self, ir: ProblemIR) -> Tuple[ProblemIR, PipelineSignal]:
        if ir.function:
            ir.runner = RunnerKind.FUNCTION
            ir.runner_detection = DetectionResult(candidate=RunnerKind.FUNCTION, evidence=["Solution class present"])
            return ir, Continue()
            
        if ir.interactive:
            ir.runner = RunnerKind.INTERACTIVE
            ir.runner_detection = DetectionResult(candidate=RunnerKind.INTERACTIVE, evidence=["Inherits from base class"])
            return ir, Continue()
            
        if ir.stateful_class:
            if len(ir.stateful_class.methods) == 1 and not ir.stateful_class.constructor:
                # Ambiguous
                ir.runner_detection = DetectionResult(
                    ambiguous=True,
                    alternatives=[
                        DetectionAlternative(RunnerKind.FUNCTION, ["Single method"]),
                        DetectionAlternative(RunnerKind.STATEFUL_CLASS, ["Class not named Solution"])
                    ]
                )
                return ir, NeedInput("Unable to determine runner automatically.\nChoose runner [1/2]:")
            
            ir.runner = RunnerKind.STATEFUL_CLASS
            ir.runner_detection = DetectionResult(candidate=RunnerKind.STATEFUL_CLASS, evidence=["Constructor and methods present"])
            return ir, Continue()
            
        return ir, Fail("Could not resolve runner")

class TypeAnalyzer:
    def _check_type(self, t: CppType, signals: List[PipelineSignal]):
        if isinstance(t, Unknown):
            signals.append(Warn(f"Unsupported type: {t.raw}"))
        elif isinstance(t, Vector):
            self._check_type(t.inner, signals)

    def analyze(self, ir: ProblemIR) -> Tuple[ProblemIR, PipelineSignal]:
        signals = []
        if ir.function:
            self._check_type(ir.function.return_type, signals)
            for p in ir.function.parameters:
                self._check_type(p.type, signals)
        
        if signals:
            return ir, signals[0] # Just return first warning
        return ir, Continue()

class CapabilityAnalyzer:
    def analyze(self, ir: ProblemIR) -> Tuple[ProblemIR, PipelineSignal]:
        caps = [Capability.RUN, Capability.TRACE]
        if ir.runner == RunnerKind.FUNCTION:
            caps.extend([Capability.MULTIPLE_CASES, Capability.BENCHMARK, Capability.STRESS_TEST])
        elif ir.runner == RunnerKind.STATEFUL_CLASS:
            caps.extend([Capability.REPLAY, Capability.MULTIPLE_CASES])
        
        ir.capabilities = caps
        return ir, Continue()

def run_pipeline(stub: str, mock_input: str = None) -> Tuple[ProblemIR, List[PipelineSignal]]:
    ir = ProblemIR()
    signals = []
    
    stages = [
        StubAnalyzer(),
        RunnerResolver(),
        TypeAnalyzer(),
        CapabilityAnalyzer()
    ]
    
    for stage in stages:
        ir, sig = stage.analyze(ir if isinstance(stage, RunnerResolver) else (stub if isinstance(stage, StubAnalyzer) else ir))
        
        # In StubAnalyzer, we passed stub, but it returns IR.
        # Wait, the signature of analyze varies! Let's unify.
        pass

    return ir, signals

# Unified run_pipeline
def run_pipeline_unified(stub: str) -> Tuple[ProblemIR, List[PipelineSignal]]:
    ir = ProblemIR()
    history = []
    
    ir, sig = StubAnalyzer().analyze(stub, ir)
    history.append(sig)
    
    ir, sig = RunnerResolver().analyze(ir)
    history.append(sig)
    if isinstance(sig, NeedInput):
        # Pause pipeline in real usage; for tests we just return it
        return ir, history
        
    ir, sig = TypeAnalyzer().analyze(ir)
    history.append(sig)
    
    ir, sig = CapabilityAnalyzer().analyze(ir)
    history.append(sig)
    
    return ir, history
