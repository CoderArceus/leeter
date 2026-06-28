#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <queue>

struct TreeNode {
    int val;
    TreeNode *left;
    TreeNode *right;
    TreeNode() : val(0), left(nullptr), right(nullptr) {}
    TreeNode(int x) : val(x), left(nullptr), right(nullptr) {}
    TreeNode(int x, TreeNode *left, TreeNode *right) : val(x), left(left), right(right) {}
};

inline void print_inorder(TreeNode* root) {
    if (!root) return;
    print_inorder(root->left);
    std::cout << root->val << " ";
    print_inorder(root->right);
}

inline void print_preorder(TreeNode* root) {
    if (!root) return;
    std::cout << root->val << " ";
    print_preorder(root->left);
    print_preorder(root->right);
}

inline void print_postorder(TreeNode* root) {
    if (!root) return;
    print_postorder(root->left);
    print_postorder(root->right);
    std::cout << root->val << " ";
}

inline void print_levelorder(TreeNode* root) {
    if (!root) return;
    std::queue<TreeNode*> q;
    q.push(root);
    while (!q.empty()) {
        TreeNode* curr = q.front();
        q.pop();
        if (curr) {
            std::cout << curr->val << " ";
            q.push(curr->left);
            q.push(curr->right);
        } else {
            std::cout << "null ";
        }
    }
}

inline void free_tree(TreeNode* root) {
    if (!root) return;
    free_tree(root->left);
    free_tree(root->right);
    delete root;
}

inline void print_tree(TreeNode* root, std::string prefix = "", bool isLeft = false, bool isRoot = true) {
    if (root == nullptr) return;
    std::cout << prefix;
    if (!isRoot) {
        std::cout << (isLeft ? "├── " : "└── ");
    }
    std::cout << root->val << std::endl;
    print_tree(root->left, prefix + (isRoot ? "" : (isLeft ? "│   " : "    ")), true, false);
    print_tree(root->right, prefix + (isRoot ? "" : (isLeft ? "│   " : "    ")), false, false);
}
