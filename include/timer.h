#pragma once
#include <iostream>
#include <chrono>
#include <string>

class Timer {
    std::chrono::time_point<std::chrono::high_resolution_clock> start_time;
public:
    void start() {
        start_time = std::chrono::high_resolution_clock::now();
    }
    void stop() {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        std::cerr << "[timer] " << duration.count() / 1000.0 << " ms\n";
    }
};

class ScopeTimer {
    std::string label;
    std::chrono::time_point<std::chrono::high_resolution_clock> start_time;
public:
    ScopeTimer(std::string label) : label(label) {
        start_time = std::chrono::high_resolution_clock::now();
    }
    ~ScopeTimer() {
        auto end_time = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end_time - start_time);
        std::cerr << "[timer] " << label << ": " << duration.count() / 1000.0 << " ms\n";
    }
};
