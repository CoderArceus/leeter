#pragma once
#include <iostream>
#include <vector>
#include <string>
#include <map>
#include <set>
#include <queue>
#include <stack>
#include <algorithm>
#include <cmath>
#include <unordered_map>
#include <unordered_set>

#include "tree.h"
#include "list.h"
#include "parser.h"
#include "printer.h"
#include "debug.h"
#include "timer.h"
#include "assert.h"
#include "snapshot.h"
#include "random.h"

#include <sstream>
template<typename T>
std::string to_json_string(const T& val) {
    struct StdoutRedirect {
        std::streambuf* old;
        StdoutRedirect(std::streambuf* buf) { old = std::cout.rdbuf(buf); }
        ~StdoutRedirect() { std::cout.rdbuf(old); }
    };
    std::stringstream ss;
    StdoutRedirect redir(ss.rdbuf());
    print_inline(val);
    return ss.str();
}

#include "trace.h"

using namespace std;
