cmake_minimum_required(VERSION 2.8)
include(RezBuild)

file(GLOB_RECURSE py_files "src/*.py")
rez_install_python(
    py
    FILES ${py_files}
    DESTINATION .
    LOCAL_SYMLINK
)

file(GLOB_RECURSE qss_files "src/*.qss")
rez_install_files(
    ${qss_files}
    DESTINATION .
    LOCAL_SYMLINK
)

file(GLOB bin_files "bin/*")
rez_install_files(
    ${bin_files}
    DESTINATION .
    EXECUTABLE
    LOCAL_SYMLINK
)
