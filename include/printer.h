#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <queue>
#include <set>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include "tree.h"
#include "list.h"

template<typename T>
void print_inline(const T& value);

template<typename T>
struct Printer {
    static void print(const T& value) {
        std::cout << value;
    }
};

template<typename T>
void print(const T& value) {
    Printer<T>::print(value);
    std::cout << std::endl;
}

template<typename T>
void print_inline(const T& value) {
    Printer<T>::print(value);
}

// Specializations
template<>
struct Printer<bool> {
    static void print(bool value) {
        std::cout << (value ? "true" : "false");
    }
};

template<>
struct Printer<std::string> {
    static void print(const std::string& value) {
        std::cout << '"' << value << '"';
    }
};

template<typename T>
struct Printer<std::vector<T>> {
    static void print(const std::vector<T>& value) {
        std::cout << "[";
        for (size_t i = 0; i < value.size(); ++i) {
            if (i > 0) std::cout << ",";
            print_inline(value[i]);
        }
        std::cout << "]";
    }
};

template<typename A, typename B>
struct Printer<std::pair<A, B>> {
    static void print(const std::pair<A, B>& value) {
        std::cout << "[";
        print_inline(value.first);
        std::cout << ",";
        print_inline(value.second);
        std::cout << "]";
    }
};

template<typename T>
struct Printer<std::set<T>> {
    static void print(const std::set<T>& value) {
        std::cout << "[";
        bool first = true;
        for (const auto& v : value) {
            if (!first) std::cout << ",";
            print_inline(v);
            first = false;
        }
        std::cout << "]";
    }
};

template<typename K, typename V>
struct Printer<std::map<K, V>> {
    static void print(const std::map<K, V>& value) {
        std::cout << "[";
        bool first = true;
        for (const auto& kv : value) {
            if (!first) std::cout << ",";
            std::cout << "[";
            print_inline(kv.first);
            std::cout << ",";
            print_inline(kv.second);
            std::cout << "]";
            first = false;
        }
        std::cout << "]";
    }
};

template<typename T, typename Hash, typename Eq, typename Alloc>
struct Printer<std::unordered_set<T, Hash, Eq, Alloc>> {
    static void print(const std::unordered_set<T, Hash, Eq, Alloc>& value) {
        std::cout << "[";
        bool first = true;
        for (const auto& v : value) {
            if (!first) std::cout << ",";
            print_inline(v);
            first = false;
        }
        std::cout << "]";
    }
};

template<typename K, typename V, typename Hash, typename Eq, typename Alloc>
struct Printer<std::unordered_map<K, V, Hash, Eq, Alloc>> {
    static void print(const std::unordered_map<K, V, Hash, Eq, Alloc>& value) {
        std::cout << "[";
        bool first = true;
        for (const auto& kv : value) {
            if (!first) std::cout << ",";
            std::cout << "[";
            print_inline(kv.first);
            std::cout << ",";
            print_inline(kv.second);
            std::cout << "]";
            first = false;
        }
        std::cout << "]";
    }
};

template<>
struct Printer<TreeNode*> {
    static void print(TreeNode* root) {
        if (!root) {
            std::cout << "[]";
            return;
        }
        std::cout << "[";
        std::queue<TreeNode*> q;
        q.push(root);
        std::vector<std::string> res;
        while (!q.empty()) {
            TreeNode* curr = q.front();
            q.pop();
            if (curr) {
                res.push_back(std::to_string(curr->val));
                q.push(curr->left);
                q.push(curr->right);
            } else {
                res.push_back("null");
            }
        }
        while (!res.empty() && res.back() == "null") {
            res.pop_back();
        }
        for (size_t i = 0; i < res.size(); ++i) {
            if (i > 0) std::cout << ",";
            std::cout << res[i];
        }
        std::cout << "]";
    }
};

template<>
struct Printer<ListNode*> {
    static void print(ListNode* head) {
        std::cout << "[";
        while (head) {
            std::cout << head->val;
            if (head->next) std::cout << ",";
            head = head->next;
        }
        std::cout << "]";
    }
};
