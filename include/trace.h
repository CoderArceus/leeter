#pragma once
#include <fstream>
#include <string>
#include <variant>
#include <vector>
#include <typeinfo>
#include "snapshot.h"

inline std::string escape_json_str(const std::string& s) {
    std::string res;
    for (char c : s) {
        if (c == '"') res += "\\\"";
        else if (c == '\\') res += "\\\\";
        else if (c == '\n') res += "\\n";
        else if (c == '\r') res += "\\r";
        else if (c == '\t') res += "\\t";
        else res += c;
    }
    return res;
}

inline std::string snapshot_to_json(const SnapshotValue& v) {
    if (std::holds_alternative<std::nullptr_t>(v.data)) return "null";
    if (std::holds_alternative<bool>(v.data)) return std::get<bool>(v.data) ? "true" : "false";
    if (std::holds_alternative<long long>(v.data)) return std::to_string(std::get<long long>(v.data));
    if (std::holds_alternative<double>(v.data)) return std::to_string(std::get<double>(v.data));
    if (std::holds_alternative<std::string>(v.data)) return "\"" + escape_json_str(std::get<std::string>(v.data)) + "\"";
    if (std::holds_alternative<SnapshotValue::Object>(v.data)) {
        std::string s = "{";
        bool first = true;
        for (const auto& kv : std::get<SnapshotValue::Object>(v.data)) {
            if (!first) s += ",";
            s += "\"" + escape_json_str(kv.first) + "\":" + snapshot_to_json(kv.second);
            first = false;
        }
        return s + "}";
    }
    if (std::holds_alternative<SnapshotValue::Array>(v.data)) {
        std::string s = "[";
        bool first = true;
        for (const auto& item : std::get<SnapshotValue::Array>(v.data)) {
            if (!first) s += ",";
            s += snapshot_to_json(item);
            first = false;
        }
        return s + "]";
    }
    return "null";
}

struct TraceLogger {
    std::ofstream out;
    bool first_event = true;
    
    TraceLogger() {
        out.open("build/trace.json");
        out << "[\n";
    }
    
    ~TraceLogger() {
        out << "\n]\n";
    }
    
    void _write_comma() {
        if (!first_event) out << ",\n";
        first_event = false;
    }
    
    void method_call(const std::string& name, const std::string& args_json) {
        _write_comma();
        out << "  {\"type\": \"method_call\", \"method\": \"" << escape_json_str(name) 
            << "\", \"args\": " << args_json << "}";
    }
    
    void method_return(const std::string& ret_json) {
        _write_comma();
        out << "  {\"type\": \"method_return\", \"return\": " << ret_json << "}";
    }
    
    void snapshot(const std::string& type_name, const SnapshotValue& val) {
        _write_comma();
        out << "  {\"type\": \"snapshot\", \"class\": \"" << escape_json_str(type_name) 
            << "\", \"data\": " << snapshot_to_json(val) << "}";
    }
    void user_snapshot(int line, const std::string& names, const std::string& values_json) {
        _write_comma();
        out << "  {\"type\": \"user_snapshot\", \"line\": " << line 
            << ", \"names\": \"" << escape_json_str(names) << "\", \"values\": " << values_json << "}";
    }
};

inline TraceLogger& get_trace_logger() {
    static TraceLogger logger;
    return logger;
}

inline void log_snapshot_event(const char* type_name, const SnapshotValue& val) {
    get_trace_logger().snapshot(type_name, val);
}

template<typename T>
inline void _build_snapshot_json(std::string& out, const T& val) {
    out += to_json_string(val);
}

template<typename T, typename... Args>
inline void _build_snapshot_json(std::string& out, const T& first, const Args&... rest) {
    out += to_json_string(first) + ", ";
    _build_snapshot_json(out, rest...);
}

template<typename... Args>
inline void log_user_snapshot(int line, const char* names, const Args&... args) {
    std::string values_json = "[";
    if constexpr (sizeof...(args) > 0) {
        _build_snapshot_json(values_json, args...);
    }
    values_json += "]";
    get_trace_logger().user_snapshot(line, names, values_json);
}

#ifdef TRACE_ENABLED
#define SNAPSHOT(...) log_user_snapshot(__LINE__, #__VA_ARGS__, __VA_ARGS__)
#else
#define SNAPSHOT(...)
#endif
