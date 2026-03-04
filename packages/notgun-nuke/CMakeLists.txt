cmake_minimum_required(VERSION 2.8)
include(RezBuild)

file(GLOB startup_files "startup/*.py")
rez_install_files(
    ${startup_files}
    DESTINATION startup
    LOCAL_SYMLINK
)
