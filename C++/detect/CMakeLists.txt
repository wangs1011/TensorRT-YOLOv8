cmake_minimum_required(VERSION 3.10)

project(yolov8_detect)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g -fPIC -O3 -std=c++11 -fopenmp")
add_definitions(-std=c++11)
add_definitions(-DAPI_EXPORTS)
set(CMAKE_CXX_STANDARD 11)
set(CMAKE_BUILD_TYPE release)

# include and link dirs of cuda and tensorrt, you need adapt them if yours are different
# CUDA
find_package(CUDA REQUIRED)
message(STATUS "Find CUDA include at ${CUDA_INCLUDE_DIRS}")
message(STATUS "Find CUDA libraries: ${CUDA_LIBRARIES}")

# TensorRT
set(TENSORRT_ROOT /usr/local/TensorRT-8.5.1.7)
find_path(TENSORRT_INCLUDE_DIR NvInfer.h
        HINTS ${TENSORRT_ROOT} PATH_SUFFIXES include/)
message(STATUS "Found TensorRT headers at ${TENSORRT_INCLUDE_DIR}")
find_library(TENSORRT_LIBRARY_INFER nvinfer
        HINTS ${TENSORRT_ROOT} ${TENSORRT_BUILD} ${CUDA_TOOLKIT_ROOT_DIR}
        PATH_SUFFIXES lib lib64 lib/x64)
find_library(TENSORRT_LIBRARY_ONNXPARSER nvonnxparser
        HINTS  ${TENSORRT_ROOT} ${TENSORRT_BUILD} ${CUDA_TOOLKIT_ROOT_DIR}
        PATH_SUFFIXES lib lib64 lib/x64)
set(TENSORRT_LIBRARY ${TENSORRT_LIBRARY_INFER} ${TENSORRT_LIBRARY_ONNXPARSER})
message(STATUS "Find TensorRT libs: ${TENSORRT_LIBRARY}")

# OpenCV
set(OpenCV_DIR /home/clib/opencv-3.4.0/build/)
find_package(OpenCV REQUIRED)
message(STATUS "Find OpenCV include at ${OpenCV_INCLUDE_DIRS}")
message(STATUS "Find OpenCV libraries: ${OpenCV_LIBRARIES}")

# CURL
find_package(CURL REQUIRED)
message(STATUS "Find CURL include at ${CURL_INCLUDE_DIRS}")
message(STATUS "Find CURL libraries: ${CURL_LIBRARIES}")

# 添加CMake模块路径
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/Modules/")

# 查找hiredis
find_package(hiredis REQUIRED)

# 如果找到了hiredis，则添加它的头文件和库
if(HIREDIS_FOUND)
    message(STATUS "Find hiredis include at ${HIREDIS_INCLUDE_DIRS}")
    message(STATUS "Find hiredis libraries: ${HIREDIS_LIBRARIES}")
else()
    message(FATAL_ERROR "hiredis not found")
endif()

# ============ yolo infer shared lib ============
include_directories(${PROJECT_SOURCE_DIR}/include ${CUDA_INCLUDE_DIRS} ${TENSORRT_INCLUDE_DIR} ${OpenCV_INCLUDE_DIRS} ${CURL_INCLUDE_DIRS} ${HIREDIS_INCLUDE_DIRS})
file(GLOB_RECURSE SRCS ${PROJECT_SOURCE_DIR}/src/*.cpp ${PROJECT_SOURCE_DIR}/src/*.cu)
cuda_add_library(yolo_infer SHARED ${SRCS})
target_link_libraries(yolo_infer ${OpenCV_LIBRARIES} ${CUDA_LIBRARIES} ${TENSORRT_LIBRARY} ${CURL_LIBRARIES} ${HIREDIS_LIBRARIES} )

# ======== main execute file ========
add_executable(main ${PROJECT_SOURCE_DIR}/main.cpp)
target_link_libraries(main yolo_infer)