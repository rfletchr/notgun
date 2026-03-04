cmake_minimum_required(VERSION 2.8)
include(RezBuild)

file(GLOB startup_files "startup/*.py")
rez_install_files(
    ${startup_files}
    DESTINATION .
    LOCAL_SYMLINK
)

file(GLOB_RECURSE python_files "src/*.py")
rez_install_python(
    py
    ${python_files}
    DESTINATION .
    LOCAL_SYMLINK
)
