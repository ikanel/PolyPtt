cmake_minimum_required(VERSION 3.20)
project(g726)
#add_executable(g726 main.cpp)
add_library(g726 SHARED main.cpp)

set(CMAKE_CXX_STANDARD 26)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(/usr/include/spandsp/)
link_directories(/usr/lib/aarch64-linux-gnu/)
target_link_libraries(g726 /usr/lib/aarch64-linux-gnu/libspandsp.so)

#Raspberry pi settings
#include_directories(/usr/include/spandsp/)
#link_directories(/usr/lib/aarch64-linux-gnu/)
#target_link_libraries(g726 /usr/lib/aarch64-linux-gnu/libspandsp.so)

include_directories(/opt/homebrew/Cellar/libtiff/4.7.0/include)
link_directories(/opt/homebrew/Cellar/libtiff/4.7.0/lib)

#Raspberry pi settings
#include_directories(/usr/include/aarch64-linux-gnu/)
#link_directories(/usr/lib/aarch64-linux-gnu/)

