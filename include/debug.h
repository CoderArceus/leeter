#pragma once
#include <iostream>
#include <string>
#include <unistd.h>
#include "printer.h"

#define LC_DEBUG_LEVEL_INFO 0
#define LC_DEBUG_LEVEL_WARN 1
#define LC_DEBUG_LEVEL_ERROR 2

#ifndef LC_DEBUG_LEVEL
#define LC_DEBUG_LEVEL LC_DEBUG_LEVEL_INFO
#endif

#ifdef LC_NO_DEBUG
#define dbg(...)
#define trace(...)
#define watch(...)
#else

namespace lc_debug {
    struct StderrRedirect {
        std::streambuf* old;
        StderrRedirect() {
            old = std::cout.rdbuf(std::cerr.rdbuf());
        }
        ~StderrRedirect() {
            std::cout.rdbuf(old);
        }
    };

    inline bool is_color_enabled() {
        static bool enabled = isatty(STDERR_FILENO);
        return enabled;
    }

    inline const char* color_gray() { return is_color_enabled() ? "\033[90m" : ""; }
    inline const char* color_yellow() { return is_color_enabled() ? "\033[33m" : ""; }
    inline const char* color_red() { return is_color_enabled() ? "\033[31m" : ""; }
    inline const char* color_reset() { return is_color_enabled() ? "\033[0m" : ""; }

    template<typename T>
    void print_dbg_args(const T& val) {
        StderrRedirect redir;
        print_inline(val);
        std::cout << "\n";
    }

    template<typename T, typename... Args>
    void print_dbg_args(const T& val, Args... args) {
        StderrRedirect redir;
        print_inline(val);
        std::cout << "\n";
        print_dbg_args(args...);
    }
}

#define dbg(...) \
    do { \
        std::cerr << lc_debug::color_gray() << "[debug] " << #__VA_ARGS__ << " = " << lc_debug::color_reset(); \
        lc_debug::print_dbg_args(__VA_ARGS__); \
    } while(0)

#define trace(...) \
    do { \
        std::cerr << lc_debug::color_gray() << "[trace] " << #__VA_ARGS__ << " = " << lc_debug::color_reset(); \
        lc_debug::print_dbg_args(__VA_ARGS__); \
    } while(0)

#define watch(vec) \
    do { \
        std::cerr << lc_debug::color_gray() << "[watch] " << #vec << " = " << lc_debug::color_reset(); \
        lc_debug::print_dbg_args(vec); \
    } while(0)

#endif
