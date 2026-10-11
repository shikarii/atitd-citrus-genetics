cmake_minimum_required(VERSION 3.18)
project(citrus_native LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# --- CPU architecture: Intel i7-6700K (Skylake) ---
if(MSVC)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} /arch:AVX2 /O2 /fp:fast")
else()
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -mavx2 -mfma -msse4.2 -march=skylake -O3 -ffast-math")
endif()

# --- pybind11 ---
find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(pybind11 CONFIG REQUIRED)

# --- Optional CUDA ---
include(CheckLanguage)
check_language(CUDA)
if(CMAKE_CUDA_COMPILER)
    enable_language(CUDA)
    set(CMAKE_CUDA_STANDARD 17)
    set(CMAKE_CUDA_STANDARD_REQUIRED ON)
    set(CITRUS_CUDA_ENABLED ON)
    add_definitions(-DCITRUS_CUDA_ENABLED)
    message(STATUS "CUDA enabled: ${CMAKE_CUDA_COMPILER}")
else()
    set(CITRUS_CUDA_ENABLED OFF)
    message(STATUS "CUDA not found, building CPU-only")
endif()

# --- Source files ---
set(CORE_SOURCES
    src/model.cpp
    src/avx2.cpp
    src/dispatch.cpp
    src/bindings.cpp
)

if(CITRUS_CUDA_ENABLED)
    set(CUDA_SOURCES
        cuda/trait_rows.cu
        cuda/scan_parent.cu
        cuda/loglik.cu
    )
    pybind11_add_module(_citrus_native ${CORE_SOURCES} ${CUDA_SOURCES})
    target_link_libraries(_citrus_native PRIVATE CUDA::cudart)
else()
    pybind11_add_module(_citrus_native ${CORE_SOURCES})
endif()

target_include_directories(_citrus_native PRIVATE include)

# --- Install to Python package ---
install(TARGETS _citrus_native
    LIBRARY DESTINATION ${Python3_SITEARCH}/citrus_genetics/core
)
