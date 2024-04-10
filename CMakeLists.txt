# This CMake config hopefully makes it easier to compile.
# Ensure the CUDA Toolkit is available on your path. Then run:
#   For  GCC: `cmake -B build . && cmake --build build`
#   For MSVC: `cmake -B build . && cmake --build build --config Release`
# You can also use the following options and variables
#  - COMPUTE_BACKEND: Set to `cpu`, `cuda`, or `mps` to select the backend
#  - NO_CUBLASLT: Default OFF, will skip building/linking CUBLASLT support
#  - CUDA_VERSION: The expected CUDA version, for sanity checking. The actual version
#                  is whatever CMake finds on your path.
#  - COMPUTE_CAPABILITY: Which GPU Arch/Compute codes to provide to NVCC.
#                        Separate by semicolons, i.e. `-DCOMPUTE_CAPABILITY=89;90`
#                        Check your compute capability here: https://developer.nvidia.com/cuda-gpus
#  - PTXAS_VERBOSE: Pass the `-v` option to the PTX Assembler
cmake_minimum_required(VERSION 3.22.1)

project(bitsandbytes LANGUAGES CXX)

# If run without specifying a build type, default to using the Release configuration:
#    optimizing the generated binaries for performance and also adds the `-DNDEBUG` flag,
#    which turns off a bunch of asserts which seem to link to new symbols in libstdc++,
#    worsening our many_linux compliance..
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Define included source files
set(CPP_FILES csrc/common.cpp csrc/cpu_ops.cpp csrc/pythonInterface.c)
set(CUDA_FILES csrc/ops.hip.cpp csrc/kernels.hip.cpp)
# C++ sources are always included
list(APPEND SRC_FILES ${CPP_FILES})

set(COMPUTE_BACKEND "hip" CACHE STRING "The compute backend to use (cpu, hip)")
set_property(CACHE COMPUTE_BACKEND PROPERTY STRINGS cpu cuda mps hip)
option(PTXAS_VERBOSE "Pass through -v flag to PTX Assembler" OFF)

if(NOT DEFINED HIP_PATH)
    if(NOT DEFINED ENV{HIP_PATH})
        set(HIP_PATH "/opt/rocm/hip" CACHE PATH "Path to which HIP has been installed")
    else()
        set(HIP_PATH $ENV{HIP_PATH} CACHE PATH "Path to which HIP has been installed")
    endif()
endif()
message("HIP_PATH: " ${HIP_PATH})
set(CMAKE_MODULE_PATH "${HIP_PATH}/cmake" ${CMAKE_MODULE_PATH})
find_package(HIP REQUIRED)
if (HIP_FOUND)
  message(STATUS "Found HIP: " ${HIP_VERSION})
else()
  message(FATAL_ERROR "Could not find HIP")
endif()
find_package(rocthrust REQUIRED)
find_package(hipblas REQUIRED)
find_package(hipsparse REQUIRED)
find_package(rocrand REQUIRED)
find_package(hipblaslt REQUIRED)
# Search for rocm in common locations
list(APPEND CMAKE_PREFIX_PATH /opt/rocm/hip /opt/rocm /opt/rocm)
list(APPEND HIP_PATH /opt/rocm/llvm/bin/)
# Find HIP.
# The user may override AMDGPU_TARGETS defined in the HIP config file
# to select the AMDGPU archs to compile for.
# ex. set(AMDGPU_TARGETS "gfx803;gfx900;gfx906")
# Find OpenMP.
#find_package(OpenMP REQUIRED)
# Set compiler and linker.
if(NOT WIN32)
  set(CMAKE_CXX_COMPILER ${HIP_HIPCC_EXECUTABLE})
  set(CMAKE_CXX_LINKER   ${HIP_HIPCC_EXECUTABLE})
  set(CMAKE_CXXFLAGS -D__HIP_PLATFORM_AMD__)
  set(CMAKE_CFLAGS -D__HIP_PLATFORM_AMD__)
endif()
message("Current CMAKE_CXX_COMPILER (should show hipcc): " ${CMAKE_CXX_COMPILER})
message("Current CMAKE_CXX_LINKER (should show hipcc): " ${CMAKE_CXX_LINKER})

set(BNB_OUTPUT_NAME "bitsandbytes")

message(STATUS "Configuring ${PROJECT_NAME} (Backend: ${COMPUTE_BACKEND})")

if(${COMPUTE_BACKEND} STREQUAL "hip")
    set(BUILD_HIP on)
    set(BUILD_CUDA OFF)
    set(BUILD_MPS OFF)
    set(NO_CUBLASLT ON)
else()
    set(BUILD_CUDA OFF)
    set(BUILD_MPS OFF)
endif()


if(BUILD_HIP)
    list(APPEND SRC_FILES ${CUDA_FILES})
    # real name
    string(APPEND BNB_OUTPUT_NAME "_hip_nohipblaslt")
    add_compile_definitions(BUILD_HIP)
else()
    string(APPEND BNB_OUTPUT_NAME "_cpu")
    set(GPU_SOURCES)
endif()

if (BUILD_HIP)
    set_source_files_properties(${CPP_FILES} PROPERTIES LANGUAGE CXX)
    message("Working on: " ${CPP_FILES})
    add_library(bitsandbytes SHARED ${SRC_FILES})
    target_include_directories(bitsandbytes PRIVATE ${CMAKE_SOURCE_DIR} ${CMAKE_SOURCE_DIR}/include /opt/rocm/include/rocwmma)
    target_compile_features(bitsandbytes PUBLIC cxx_std_14)
    target_compile_definitions(bitsandbytes PUBLIC NO_CUBLASLT)
    target_include_directories(bitsandbytes PUBLIC csrc include)
    target_link_libraries(bitsandbytes PUBLIC hip::device roc::rocthrust roc::hipblas roc::hipsparse roc::rocrand roc::rocprim roc::hipblaslt ) 
else()
    set_source_files_properties(${CPP_FILES} PROPERTIES LANGUAGE CXX)
    add_library(bitsandbytes SHARED ${SRC_FILES})
    target_compile_features(bitsandbytes PUBLIC cxx_std_14)
    target_include_directories(bitsandbytes PUBLIC csrc include)
    target_link_libraries(bitsandbytes PUBLIC hip::device)
endif()

set_target_properties(bitsandbytes PROPERTIES OUTPUT_NAME ${BNB_OUTPUT_NAME})
set_target_properties(bitsandbytes PROPERTIES LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bitsandbytes")