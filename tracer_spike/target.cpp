#include <iostream>
#include <vector>

int main() {
    std::vector<int> fib;
    fib.push_back(0);
    fib.push_back(1);
    
    for (int i = 2; i < 5; ++i) {
        int next_val = fib[i - 1] + fib[i - 2];
        fib.push_back(next_val);
    }
    
    std::cout << "Fib[4] = " << fib.back() << std::endl;
    return 0;
}
