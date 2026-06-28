import os
import sys

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cli.models import (
    ProblemIR, CppType, Primitive, Pointer, Vector, Array,
    OptionalType, Pair, TupleType, Map, Unknown
)

def to_cpp_type(t: CppType) -> str:
    if isinstance(t, Primitive): return t.name
    if isinstance(t, Pointer): return t.name
    if isinstance(t, Vector): return f"vector<{to_cpp_type(t.inner)}>"
    if isinstance(t, Array): return f"array<{to_cpp_type(t.inner)}, {t.size}>"
    if isinstance(t, OptionalType): return f"optional<{to_cpp_type(t.inner)}>"
    if isinstance(t, Pair): return f"pair<{to_cpp_type(t.first)}, {to_cpp_type(t.second)}>"
    if isinstance(t, TupleType): return f"tuple<{', '.join(to_cpp_type(x) for x in t.elements)}>"
    if isinstance(t, Map): return f"map<{to_cpp_type(t.key)}, {to_cpp_type(t.value)}>"
    if isinstance(t, Unknown): return t.raw
    return "Unknown"

class FunctionRunner:
    def supports(self, ir: ProblemIR) -> bool:
        return ir.runner == "function"

    def capabilities(self, ir: ProblemIR) -> list:
        # Should match CapabilityAnalyzer from Milestone 2
        return ["run", "benchmark", "stress_test", "multiple_cases", "trace"]

    def generate(self, ir: ProblemIR, include_path: str = "../../include", solution_file: str = "solution.cpp", mode: str = "run") -> str:
        f = ir.function
        lines = []
        lines.append(f'#include "{include_path}/lc.h"')
        if mode == "bench":
            lines.append('#include <chrono>')
        lines.append(f'#include "../{solution_file}"')
        lines.append('')
        lines.append('int main() {')
        
        if mode == "bench":
            param_names = []
            for i, param in enumerate(f.parameters):
                ctype = to_cpp_type(param.type)
                lines.append(f'    auto p{i} = parse<{ctype}>();')
                param_names.append(f'p{i}')
            args = ", ".join(param_names)
            
            lines.append('    Solution sol;')
            lines.append('    for (int i = 0; i < 10; ++i) {')
            if isinstance(f.return_type, Primitive) and f.return_type.name == "void":
                lines.append(f'        sol.{f.name}({args});')
            else:
                lines.append(f'        volatile auto _ = sol.{f.name}({args});')
            lines.append('    }')
            
            lines.append('    vector<long long> times;')
            lines.append('    for (int i = 0; i < 1000; ++i) {')
            clone_args = []
            for i in range(len(f.parameters)):
                lines.append(f'        auto c{i} = p{i};')
                clone_args.append(f'c{i}')
            cargs = ", ".join(clone_args)
            
            lines.append('        auto start = std::chrono::high_resolution_clock::now();')
            if isinstance(f.return_type, Primitive) and f.return_type.name == "void":
                lines.append(f'        sol.{f.name}({cargs});')
            else:
                lines.append(f'        volatile auto _ = sol.{f.name}({cargs});')
            lines.append('        auto end = std::chrono::high_resolution_clock::now();')
            lines.append('        times.push_back(std::chrono::duration_cast<std::chrono::nanoseconds>(end - start).count());')
            lines.append('    }')
            lines.append('    print(times);')
        else:
            lines.append('    while (has_input()) {')
            
            param_names = []
            for i, param in enumerate(f.parameters):
                if isinstance(param.type, Unknown):
                    lines.append(f'        // auto p{i} = parse<{param.type.raw}>(); // Unsupported type')
                    lines.append(f'        #error "Unsupported type: {param.type.raw}"')
                else:
                    ctype = to_cpp_type(param.type)
                    lines.append(f'        auto p{i} = parse<{ctype}>();')
                param_names.append(f'p{i}')
                
            lines.append('')
            lines.append('        Solution sol;')
            
            args = ", ".join(param_names)
            
            # Trace method call
            lines.append('#ifdef TRACE_ENABLED')
            lines.append('        std::string _args_json = "[";')
            for i, p in enumerate(param_names):
                if i > 0: lines.append('        _args_json += ", ";')
                lines.append(f'        _args_json += to_json_string({p});')
            lines.append('        _args_json += "]";')
            lines.append(f'        get_trace_logger().method_call("{f.name}", _args_json);')
            lines.append('#endif')
            
            if isinstance(f.return_type, Primitive) and f.return_type.name == "void":
                lines.append(f'        sol.{f.name}({args});')
                lines.append('        cout << "null\\n";') # Need to print null for void
                lines.append('#ifdef TRACE_ENABLED')
                lines.append('        get_trace_logger().method_return("null");')
                lines.append('#endif')
            elif isinstance(f.return_type, Unknown):
                lines.append(f'        // auto result = sol.{f.name}({args}); // Unsupported return type')
                lines.append(f'        #error "Unsupported return type: {f.return_type.raw}"')
            else:
                lines.append(f'        auto result = sol.{f.name}({args});')
                lines.append('        print(result);')
                lines.append('#ifdef TRACE_ENABLED')
                lines.append('        get_trace_logger().method_return(to_json_string(result));')
                lines.append('#endif')
                
            lines.append('    }')
            
        lines.append('    return 0;')
        lines.append('}')
        
        return "\n".join(lines) + "\n"
