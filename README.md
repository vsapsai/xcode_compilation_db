**xcode_compilation_db.py** creates [compilation database](http://clang.llvm.org/docs/JSONCompilationDatabase.html) compile_commands.json from Xcode projects.

It uses the same approach as `scan-build` in [Clang Static Analyzer](http://clang-analyzer.llvm.org/).  I.e. it replaces C and C++ compilers with `c_interposer.py` and `c_interposer.py`.  Then it invokes `xcodebuild` and aforementioned scripts intercept and store compilation commands.  `xcode_compilation_db.py` is used the following way:

`python xcode_compilation_db.py xcodebuild -scheme FooApp build`

Please note that the tool is new and untested.  Use it cautiously.

## Alternatives

[Bear](https://github.com/rizsotto/Bear) by László Nagy.  Main disadvantage for me is that it needs to be compiled.  I prefer a Python script.  And I haven't checked how it works with Xcode projects.

DTrace.  Sean Silva has [suggested to use DTrace](http://clang-developers.42468.n3.nabble.com/tooling-helper-td4028330.html) to generate compile_commands.json and there is even execsnoop example.  Unfortunately, on Mac OS X `curpsinfo->pr_psargs` [doesn't work](https://discussions.apple.com/thread/1980539).  You can try to inspect execve arguments directly with arg0, arg1, etc.  Brendan Gregg has written [a nice instruction](http://dtrace.org/blogs/brendan/2011/02/11/dtrace-pid-provider-arguments/) how to do this.  But arg1 is `char *const argv[]` and I haven't found any way to inspect null-terminated array.

[oclint/oclint-xcodebuild](https://github.com/oclint/oclint-xcodebuild).  It creates compile_commands.json by parsing `xcodebuild` output.  I have found it after creating `xcode_compilation_db.py` and haven't checked how it works.
