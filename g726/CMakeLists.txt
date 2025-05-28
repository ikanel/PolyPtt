cmake_minimum_required(VERSION 3.30)
project(g726)
#add_executable(g726 main.cpp)
add_library(g726 SHARED main.cpp)

set(CMAKE_CXX_STANDARD 26)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(/opt/homebrew/Cellar/spandsp/0.0.6_3/include)
link_directories(/opt/homebrew/Cellar/spandsp/0.0.6_3/lib)
target_link_libraries(g726 /opt/homebrew/lib/libspandsp.dylib)

include_directories(/opt/homebrew/Cellar/libtiff/4.7.0/include)
link_directories(/opt/homebrew/Cellar/libtiff/4.7.0/lib)
#target_link_libraries(g726 /opt/homebrew/Cellar/libtiff)
