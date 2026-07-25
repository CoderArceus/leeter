#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <sstream>
#include <map>
#include <cctype>
#include "printer.h"

namespace lc_tracker {
    inline std::vector<std::string> split_var_names(const std::string& names_str) {
        std::vector<std::string> names;
        std::string cur;
        int depth = 0;
        bool in_string = false;
        char quote_char = 0;

        for (char c : names_str) {
            if (in_string) {
                cur += c;
                if (c == quote_char) {
                    in_string = false;
                }
                continue;
            }
            if (c == '"' || c == '\'') {
                in_string = true;
                quote_char = c;
                cur += c;
                continue;
            }
            if (c == '(' || c == '[' || c == '{') {
                depth++;
            } else if (c == ')' || c == ']' || c == '}') {
                depth--;
            } else if (c == ',' && depth == 0) {
                while (!cur.empty() && std::isspace(cur.front())) cur.erase(0, 1);
                while (!cur.empty() && std::isspace(cur.back())) cur.pop_back();
                names.push_back(cur);
                cur.clear();
                continue;
            }
            cur += c;
        }
        while (!cur.empty() && std::isspace(cur.front())) cur.erase(0, 1);
        while (!cur.empty() && std::isspace(cur.back())) cur.pop_back();
        if (!cur.empty()) names.push_back(cur);
        return names;
    }

    template<typename... Args>
    void record_track(int line, const char* names_str, const Args&... args) {
        static std::map<int, int> iteration_counts;
        int iter = ++iteration_counts[line];
        
        std::vector<std::string> names = split_var_names(names_str);
        std::vector<std::string> values;
        
        auto encode_val = [](const auto& val) {
            std::stringstream ss;
            {
                auto old_buf = std::cout.rdbuf(ss.rdbuf());
                print_inline(val);
                std::cout.rdbuf(old_buf);
            }
            return ss.str();
        };
        
        (values.push_back(encode_val(args)), ...);
        
        std::cerr << "@@LEETER_TRACK@@:{\"line\": " << line << ", \"iteration\": " << iter << ", \"vars\": {";
        for (size_t i = 0; i < names.size() && i < values.size(); ++i) {
            if (i > 0) std::cerr << ", ";
            std::string val = values[i];
            std::string escaped;
            for (char c : val) {
                if (c == '\"') escaped += "\\\"";
                else if (c == '\\') escaped += "\\\\";
                else if (c == '\n') escaped += "\\n";
                else if (c == '\r') escaped += "\\r";
                else if (c == '\t') escaped += "\\t";
                else escaped += c;
            }
            std::cerr << "\"" << names[i] << "\": \"" << escaped << "\"";
        }
        std::cerr << "}}\n";
    }
}

#define TRACK(...) \
    lc_tracker::record_track(__LINE__, #__VA_ARGS__, __VA_ARGS__)
