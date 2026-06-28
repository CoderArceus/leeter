#pragma once
#include <vector>
#include <string>
#include <cstdlib>
#include "tree.h"
#include "list.h"

inline std::vector<int> randomVector(int n, int lo, int hi) {
    std::vector<int> res(n);
    for (int i = 0; i < n; ++i) res[i] = lo + rand() % (hi - lo + 1);
    return res;
}

inline std::vector<std::vector<int>> randomMatrix(int rows, int cols, int lo, int hi) {
    std::vector<std::vector<int>> res(rows, std::vector<int>(cols));
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < cols; ++j) {
            res[i][j] = lo + rand() % (hi - lo + 1);
        }
    }
    return res;
}

inline std::string randomString(int n, const std::string& charset) {
    std::string res(n, ' ');
    for (int i = 0; i < n; ++i) res[i] = charset[rand() % charset.size()];
    return res;
}

inline TreeNode* randomTree(int n, int lo, int hi) {
    if (n == 0) return nullptr;
    TreeNode* root = new TreeNode(lo + rand() % (hi - lo + 1));
    return root;
}

inline ListNode* randomLinkedList(int n, int lo, int hi) {
    ListNode dummy;
    ListNode* tail = &dummy;
    for (int i = 0; i < n; ++i) {
        tail->next = new ListNode(lo + rand() % (hi - lo + 1));
        tail = tail->next;
    }
    return dummy.next;
}
