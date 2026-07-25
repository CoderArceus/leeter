import clang.cindex

def test_parse():
    try:
        # Sometimes Config.set_library_file('/Library/Developer/CommandLineTools/usr/lib/libclang.dylib') is needed
        # but let's try default first
        index = clang.cindex.Index.create()
        tu = index.parse("problems/1_two_sum/solution.cpp", args=["-std=c++20"])
        for d in tu.diagnostics:
            print(d)
        print("Success:", tu.spelling)
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    test_parse()
