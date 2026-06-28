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
    std::stringstream ss;
    std::streambuf* old_cout = std::cout.rdbuf(ss.rdbuf());
    print_inline(val);
    std::cout.rdbuf(old_cout);
    return ss.str();
}

#include "trace.h"

using namespace std;
