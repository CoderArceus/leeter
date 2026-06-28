import json
from dataclasses import dataclass, field, asdict, is_dataclass
from typing import List, Dict, Optional, Union, Any

class CppType:
    def to_dict(self) -> dict:
        d = {"kind": self.__class__.__name__}
        for k, v in self.__dict__.items():
            if isinstance(v, CppType):
                d[k] = v.to_dict()
            elif isinstance(v, list) and all(isinstance(x, CppType) for x in v):
                d[k] = [x.to_dict() for x in v]
            else:
                d[k] = v
        return d

    @staticmethod
    def from_dict(d: dict) -> 'CppType':
        if not d: return Unknown("empty")
        kind = d.get("kind")
        if kind == "Primitive": return Primitive(d["name"])
        if kind == "Pointer": return Pointer(d["name"])
        if kind == "Vector": return Vector(CppType.from_dict(d["inner"]))
        if kind == "Array": return Array(CppType.from_dict(d["inner"]), d["size"])
        if kind == "OptionalType": return OptionalType(CppType.from_dict(d["inner"]))
        if kind == "Pair": return Pair(CppType.from_dict(d["first"]), CppType.from_dict(d["second"]))
        if kind == "TupleType": return TupleType([CppType.from_dict(x) for x in d["elements"]])
        if kind == "Map": return Map(CppType.from_dict(d["key"]), CppType.from_dict(d["value"]))
        if kind == "Unknown": return Unknown(d["raw"])
        return Unknown(str(d))

@dataclass
class Primitive(CppType):
    name: str

@dataclass
class Pointer(CppType):
    name: str

@dataclass
class Vector(CppType):
    inner: CppType

@dataclass
class Array(CppType):
    inner: CppType
    size: int

@dataclass
class OptionalType(CppType):
    inner: CppType

@dataclass
class Pair(CppType):
    first: CppType
    second: CppType

@dataclass
class TupleType(CppType):
    elements: List[CppType]

@dataclass
class Map(CppType):
    key: CppType
    value: CppType

@dataclass
class Unknown(CppType):
    raw: str

class RunnerKind:
    FUNCTION = "function"
    STATEFUL_CLASS = "stateful_class"
    INTERACTIVE = "interactive"

class Capability:
    RUN = "run"
    BENCHMARK = "benchmark"
    STRESS_TEST = "stress_test"
    MULTIPLE_CASES = "multiple_cases"
    TRACE = "trace"
    REPLAY = "replay"

@dataclass
class DetectionAlternative:
    candidate: str
    evidence: List[str]

@dataclass
class DetectionResult:
    candidate: Optional[str] = None
    evidence: List[str] = field(default_factory=list)
    ambiguous: bool = False
    alternatives: List[DetectionAlternative] = field(default_factory=list)

@dataclass
class Parameter:
    name: str
    type: CppType

    def to_dict(self):
        return {"name": self.name, "type": self.type.to_dict()}

    @staticmethod
    def from_dict(d):
        return Parameter(d["name"], CppType.from_dict(d["type"]))

@dataclass
class Method:
    name: str
    return_type: CppType
    parameters: List[Parameter]
    is_void: bool

    def to_dict(self):
        return {
            "name": self.name,
            "return_type": self.return_type.to_dict(),
            "parameters": [p.to_dict() for p in self.parameters],
            "is_void": self.is_void
        }

    @staticmethod
    def from_dict(d):
        return Method(
            d["name"],
            CppType.from_dict(d["return_type"]),
            [Parameter.from_dict(p) for p in d.get("parameters", [])],
            d["is_void"]
        )

@dataclass
class FunctionStruct:
    name: str
    return_type: CppType
    parameters: List[Parameter]

    def to_dict(self):
        return {
            "name": self.name,
            "return_type": self.return_type.to_dict(),
            "parameters": [p.to_dict() for p in self.parameters]
        }

    @staticmethod
    def from_dict(d):
        return FunctionStruct(
            d["name"],
            CppType.from_dict(d["return_type"]),
            [Parameter.from_dict(p) for p in d.get("parameters", [])]
        )

@dataclass
class StatefulClassStruct:
    name: str
    constructor: List[Parameter]
    methods: List[Method]

    def to_dict(self):
        return {
            "name": self.name,
            "constructor": [p.to_dict() for p in self.constructor],
            "methods": [m.to_dict() for m in self.methods]
        }

    @staticmethod
    def from_dict(d):
        return StatefulClassStruct(
            d["name"],
            [Parameter.from_dict(p) for p in d.get("constructor", [])],
            [Method.from_dict(m) for m in d.get("methods", [])]
        )

@dataclass
class InteractiveStruct:
    oracle_class: str
    mock_interface: str

    def to_dict(self):
        return asdict(self)

    @staticmethod
    def from_dict(d):
        return InteractiveStruct(**d)

@dataclass
class ProblemIR:
    id: int = 0
    title: str = ""
    difficulty: str = ""
    url: str = ""
    tags: List[str] = field(default_factory=list)
    acceptance_rate: float = 0.0

    runner: Optional[str] = None
    runner_detection: Optional[DetectionResult] = None

    function: Optional[FunctionStruct] = None
    stateful_class: Optional[StatefulClassStruct] = None
    interactive: Optional[InteractiveStruct] = None

    input_format: Optional[str] = None
    output_format: Optional[str] = None

    examples: List[Dict[str, str]] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)

    hints: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    related_problems: List[int] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    notes: str = ""
    solved: bool = False
    solve_time_ms: Optional[int] = None
    benchmark_history: List[Any] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        if self.runner_detection:
            d["runner_detection"] = asdict(self.runner_detection)
        if self.function:
            d["function"] = self.function.to_dict()
        if self.stateful_class:
            d["stateful_class"] = self.stateful_class.to_dict()
        if self.interactive:
            d["interactive"] = self.interactive.to_dict()
        d["framework_version"] = 2
        return d

    @staticmethod
    def from_dict(d: dict) -> 'ProblemIR':
        ir = ProblemIR()
        for k, v in d.items():
            if k == "framework_version": continue
            if k == "function" and v:
                ir.function = FunctionStruct.from_dict(v)
            elif k == "stateful_class" and v:
                ir.stateful_class = StatefulClassStruct.from_dict(v)
            elif k == "interactive" and v:
                ir.interactive = InteractiveStruct.from_dict(v)
            elif k == "runner_detection" and v:
                alts = [DetectionAlternative(**a) for a in v.get("alternatives", [])]
                ir.runner_detection = DetectionResult(
                    candidate=v.get("candidate"),
                    evidence=v.get("evidence", []),
                    ambiguous=v.get("ambiguous", False),
                    alternatives=alts
                )
            elif hasattr(ir, k):
                setattr(ir, k, v)
        return ir

class PipelineSignal:
    pass

@dataclass
class Continue(PipelineSignal):
    pass

@dataclass
class NeedInput(PipelineSignal):
    prompt: str

@dataclass
class Warn(PipelineSignal):
    message: str

@dataclass
class Fail(PipelineSignal):
    reason: str
