import os
import sys

# Add parent directory to sys.path to allow imports when run locally
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from cli.models import (
    ProblemIR, CppType, Primitive, Pointer, Vector, Array,
    OptionalType, Pair, TupleType, Map, Unknown, Method
)
from cli.runners.function import to_cpp_type

class StatefulClassRunner:
    def supports(self, ir: ProblemIR) -> bool:
        return ir.runner == "stateful_class"

    def capabilities(self, ir: ProblemIR) -> list:
        return ["run", "trace", "replay", "multiple_cases"]

    def generate(self, ir: ProblemIR, include_path: str = "../../include") -> str:
        s = ir.stateful_class
        lines = []
        lines.append(f'#include "{include_path}/lc.h"')
        lines.append('#include "../solution.cpp"')
        lines.append('')
        
        # Helper to convert python bool to c++ bool string
        lines.append('int main() {')
        lines.append('    while (has_input()) {')
        lines.append('        vector<string> ops = parse<vector<string>>();')
        lines.append('        expect_char(\'[\');')
        lines.append(f'        {s.name}* obj = nullptr;')
        lines.append('        cout << "[";')
        
        lines.append('        for (size_t i = 0; i < ops.size(); ++i) {')
        lines.append('            if (i > 0) { cout << ","; expect_char(\',\'); }')
        
        # Constructor dispatch
        lines.append(f'            if (ops[i] == "{s.name}") {{')
        lines.append('                expect_char(\'[\');')
        
        cons_args = []
        cons_json = []
        for i, param in enumerate(s.constructor):
            if i > 0: lines.append('                expect_char(\',\');')
            ctype = to_cpp_type(param.type)
            lines.append(f'                auto p{i} = parse<{ctype}>();')
            cons_args.append(f'p{i}')
            cons_json.append(f'to_json_string(p{i})')
            
        lines.append('                expect_char(\']\');')
        lines.append(f'                obj = new {s.name}({", ".join(cons_args)});')
        lines.append('                cout << "null";')
        
        # Build JSON array for args: "[" + to_json_string(p0) + "," + to_json_string(p1) + "]"
        if not cons_json:
            args_json_str = '"[]"'
        else:
            args_json_str = 'std::string("[") + ' + ' + "," + '.join(cons_json) + ' + "]"'
            
        lines.append(f'                get_trace_logger().method_call("{s.name}", {args_json_str});')
        lines.append('                get_trace_logger().method_return("null");')
        lines.append('                emit_snapshot(*obj);')
        lines.append('            }')
        
        for m in s.methods:
            if m.name == "to_snapshot":
                continue
                
            lines.append(f'            else if (ops[i] == "{m.name}") {{')
            lines.append('                expect_char(\'[\');')
            m_args = []
            m_json = []
            for i, param in enumerate(m.parameters):
                if i > 0: lines.append('                expect_char(\',\');')
                ctype = to_cpp_type(param.type)
                lines.append(f'                auto p{i} = parse<{ctype}>();')
                m_args.append(f'p{i}')
                m_json.append(f'to_json_string(p{i})')
            lines.append('                expect_char(\']\');')
            
            if not m_json:
                args_json_str = '"[]"'
            else:
                args_json_str = 'std::string("[") + ' + ' + "," + '.join(m_json) + ' + "]"'
                
            lines.append(f'                get_trace_logger().method_call("{m.name}", {args_json_str});')
            lines.append('                if (!obj) { cout << "null"; get_trace_logger().method_return("null"); continue; }')
            
            call_expr = f'obj->{m.name}({", ".join(m_args)})'
            if m.is_void:
                lines.append(f'                {call_expr};')
                lines.append('                cout << "null";')
                lines.append('                get_trace_logger().method_return("null");')
            else:
                lines.append(f'                auto res = {call_expr};')
                lines.append('                print_inline(res);')
                lines.append('                get_trace_logger().method_return(to_json_string(res));')
                
            lines.append('                emit_snapshot(*obj);')
            lines.append('            }')
            
        lines.append('        }')
        lines.append('        cout << "]" << endl;')
        lines.append('        expect_char(\']\');')
        lines.append('        if (obj) delete obj;')
        lines.append('    }')
        lines.append('    return 0;')
        lines.append('}')
        
        return "\n".join(lines) + "\n"
