#pragma once
#include <map>
#include <vector>
#include <string>
#include <variant>
#include <iostream>
#include <type_traits>

struct SnapshotValue {
    using Object  = std::map<std::string, SnapshotValue>;
    using Array   = std::vector<SnapshotValue>;
    using Variant = std::variant<std::nullptr_t, bool, long long, double, std::string, Object, Array>;
    Variant data;
    
    SnapshotValue() : data(nullptr) {}
    SnapshotValue(std::nullptr_t) : data(nullptr) {}
    SnapshotValue(bool v) : data(v) {}
    SnapshotValue(long long v) : data(v) {}
    SnapshotValue(int v) : data((long long)v) {}
    SnapshotValue(double v) : data(v) {}
    SnapshotValue(const std::string& v) : data(v) {}
    SnapshotValue(const char* v) : data(std::string(v)) {}
    SnapshotValue(const Object& v) : data(v) {}
    SnapshotValue(const Array& v) : data(v) {}
};

// SFINAE check for to_snapshot
template <typename T, typename = void>
struct has_to_snapshot : std::false_type {};

template <typename T>
struct has_to_snapshot<T, std::void_t<decltype(to_snapshot(std::declval<T>()))>> : std::true_type {};

void log_snapshot_event(const char* type_name, const SnapshotValue& val);

template <typename T>
void emit_snapshot(const T& obj) {
    if constexpr (has_to_snapshot<T>::value) {
        SnapshotValue val = to_snapshot(obj);
        log_snapshot_event(typeid(T).name(), val);
    }
}
