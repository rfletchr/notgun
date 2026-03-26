cmake_minimum_required(VERSION 2.8)
include(RezBuild)

file(GLOB_RECURSE py_files "src/notgun/*.py")
rez_install_python(
    py
    FILES ${py_files}
    DESTINATION .
    LOCAL_SYMLINK
)

file(GLOB_RECURSE img_files "src/notgun/*.png")
rez_install_files(
    ${img_files}
    DESTINATION .
)

file(GLOB bin_files "bin/*")
rez_install_files(
    ${bin_files}
    DESTINATION .
    EXECUTABLE
)