#pragma once
#include <iostream>
#include <string>
#include "printer.h"
#include "debug.h"
#include <cmath>

namespace lc_assert {
    inline int passed = 0;
    inline int failed = 0;
    
    template<typename T, typename U>
    void assert_eq(const T& result, const U& expected, const char* result_expr, const char* expected_expr) {
        if (result == expected) {
            passed++;
        } else {
            failed++;
            std::cerr << lc_debug::color_red() << "Assertion failed: " << result_expr << " == " << expected_expr << lc_debug::color_reset() << "\n";
            lc_debug::StderrRedirect redir;
            std::cout << "Expected: ";
            print(expected);
            std::cout << "Got     : ";
            print(result);
        }
    }
    
    inline void assert_near(double result, double expected, double epsilon, const char* result_expr, const char* expected_expr) {
        if (std::abs(result - expected) <= epsilon) {
            passed++;
        } else {
            failed++;
            std::cerr << lc_debug::color_red() << "Assertion failed: " << result_expr << " near " << expected_expr << lc_debug::color_reset() << "\n";
            std::cerr << "Expected: " << expected << "\nGot     : " << result << "\n";
        }
    }
    
    inline void assert_true(bool condition, const char* condition_expr) {
        if (condition) {
            passed++;
        } else {
            failed++;
            std::cerr << lc_debug::color_red() << "Assertion failed: " << condition_expr << lc_debug::color_reset() << "\n";
        }
    }
    
    inline void summary() {
        if (failed == 0) {
            std::cerr << lc_debug::color_gray() << "✓ " << passed << "/" << passed << " passed" << lc_debug::color_reset() << "\n";
        } else {
            std::cerr << lc_debug::color_red() << passed << "/" << (passed + failed) << " passed, " << failed << " failed" << lc_debug::color_reset() << "\n";
        }
    }
}

#define ASSERT_EQ(res, exp) lc_assert::assert_eq(res, exp, #res, #exp)
#define ASSERT_NEAR(res, exp, eps) lc_assert::assert_near(res, exp, eps, #res, #exp)
#define ASSERT_TRUE(cond) lc_assert::assert_true(cond, #cond)
