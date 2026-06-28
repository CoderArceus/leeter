#pragma once
#include <iostream>
#include <string>
#include <vector>
#include <cctype>
#include <stdexcept>
#include <queue>
#include "tree.h"
#include "list.h"

inline void skip_whitespace() {
    int c;
    while ((c = std::cin.peek()) != EOF && std::isspace(c)) {
        std::cin.get();
    }
}

inline bool has_input() {
    skip_whitespace();
    return std::cin.peek() != EOF;
}

inline void expect_char(char expected) {
    skip_whitespace();
    int c = std::cin.get();
    if (c != expected) {
        throw std::runtime_error(std::string("Expected '") + expected + "', got '" + (char)c + "'");
    }
}

inline bool match_char(char expected) {
    skip_whitespace();
    if (std::cin.peek() == expected) {
        std::cin.get();
        return true;
    }
    return false;
}

template<typename T>
struct Parser {
    static T parse();
};

template<typename T>
inline T parse() {
    return Parser<T>::parse();
}

template<>
struct Parser<int> {
    static int parse() {
        skip_whitespace();
        int val;
        std::cin >> val;
        return val;
    }
};

template<>
struct Parser<long long> {
    static long long parse() {
        skip_whitespace();
        long long val;
        std::cin >> val;
        return val;
    }
};

template<>
struct Parser<double> {
    static double parse() {
        skip_whitespace();
        double val;
        std::cin >> val;
        return val;
    }
};

template<>
struct Parser<bool> {
    static bool parse() {
        skip_whitespace();
        std::string s;
        while (std::isalpha(std::cin.peek())) {
            s += (char)std::cin.get();
        }
        if (s == "true") return true;
        if (s == "false") return false;
        throw std::runtime_error("Invalid boolean");
    }
};

template<>
struct Parser<std::string> {
    static std::string parse() {
        skip_whitespace();
        expect_char('"');
        std::string s;
        int c;
        while ((c = std::cin.get()) != EOF && c != '"') {
            if (c == '\\') {
                int next = std::cin.get();
                if (next == 'n') s += '\n';
                else if (next == 't') s += '\t';
                else s += (char)next;
            } else {
                s += (char)c;
            }
        }
        return s;
    }
};

template<typename T>
struct Parser<std::vector<T>> {
    static std::vector<T> parse() {
        expect_char('[');
        std::vector<T> res;
        skip_whitespace();
        if (match_char(']')) {
            return res;
        }
        while (true) {
            res.push_back(::parse<T>());
            skip_whitespace();
            if (match_char(']')) {
                break;
            }
            expect_char(',');
        }
        return res;
    }
};

inline std::string parse_raw_token() {
    skip_whitespace();
    std::string s;
    int c;
    while ((c = std::cin.peek()) != EOF && c != ',' && c != ']' && !std::isspace(c)) {
        s += (char)std::cin.get();
    }
    return s;
}

template<>
struct Parser<TreeNode*> {
    static TreeNode* parse() {
        expect_char('[');
        skip_whitespace();
        if (match_char(']')) return nullptr;

        std::vector<TreeNode*> nodes;
        std::string token = parse_raw_token();
        if (token == "null" || token == "NULL") {
            return nullptr;
        }
        TreeNode* root = new TreeNode(std::stoi(token));
        nodes.push_back(root);
        
        int head = 0;
        bool isLeft = true;
        
        while (true) {
            skip_whitespace();
            if (match_char(']')) break;
            expect_char(',');
            
            token = parse_raw_token();
            if (token != "null" && token != "NULL") {
                TreeNode* node = new TreeNode(std::stoi(token));
                nodes.push_back(node);
                if (isLeft) {
                    nodes[head]->left = node;
                } else {
                    nodes[head]->right = node;
                }
            }
            
            if (!isLeft) {
                head++;
            }
            isLeft = !isLeft;
        }
        return root;
    }
};

template<>
struct Parser<ListNode*> {
    static ListNode* parse() {
        expect_char('[');
        skip_whitespace();
        if (match_char(']')) return nullptr;
        
        ListNode* dummy = new ListNode();
        ListNode* tail = dummy;
        
        while (true) {
            std::string token = parse_raw_token();
            tail->next = new ListNode(std::stoi(token));
            tail = tail->next;
            
            skip_whitespace();
            if (match_char(']')) break;
            expect_char(',');
        }
        ListNode* head = dummy->next;
        delete dummy;
        return head;
    }
};
