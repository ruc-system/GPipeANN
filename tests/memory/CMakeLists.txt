cmake_minimum_required(VERSION 3.18)
project(QuiverMemoryTests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
enable_testing()
get_filename_component(QUIVER_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../.." ABSOLUTE)
find_package(Threads REQUIRED)

# Compile the production loaders directly: no CUDA, SPDK, or DiskANN toolchain.
foreach(system IN ITEMS shared gustann flashanns)
  if (system STREQUAL "shared")
    set(include_root "${QUIVER_ROOT}/src")
  else()
    set(include_root "${QUIVER_ROOT}/src/${system}")
  endif()
  set(io_root "${include_root}/shared/io")
  add_executable(${system}_mem_loader_test
    "${io_root}/mem_loader_test.cpp" "${io_root}/mem_loader.cpp")
  target_include_directories(${system}_mem_loader_test PRIVATE "${include_root}")
  target_link_libraries(${system}_mem_loader_test PRIVATE Threads::Threads)
  add_test(NAME ${system}_mem_loader COMMAND ${system}_mem_loader_test)
  set_tests_properties(${system}_mem_loader PROPERTIES TIMEOUT 30 LABELS "memory;host")
endforeach()
add_executable(flashanns_traced_file_loader_test
  "${QUIVER_ROOT}/src/flashanns/shared/io/mem_loader_test.cpp"
  "${QUIVER_ROOT}/src/flashanns/shared/io/mem_loader.cpp")
target_compile_definitions(flashanns_traced_file_loader_test PRIVATE FLASHANNS_LATENCY_PROBE)
target_include_directories(flashanns_traced_file_loader_test PRIVATE "${QUIVER_ROOT}/src/flashanns")
target_link_libraries(flashanns_traced_file_loader_test PRIVATE Threads::Threads)
add_test(NAME flashanns_traced_file_loader COMMAND flashanns_traced_file_loader_test)
set_tests_properties(flashanns_traced_file_loader PROPERTIES TIMEOUT 30 LABELS "memory;host")

set(QUIVER_MEMORY_SEARCH_BINARY "" CACHE FILEPATH "SPDK-disabled quiver_search for GPU tests")
option(QUIVER_MEMORY_ENTRY_TESTS "Run opt-in synthetic entry-node diagnostics" OFF)
option(QUIVER_MEMORY_EXTENDED_TESTS "Require multi-sector and per-query ef features" OFF)
if (QUIVER_MEMORY_EXTENDED_TESTS AND NOT QUIVER_MEMORY_SEARCH_BINARY)
  message(FATAL_ERROR "Extended tests require QUIVER_MEMORY_SEARCH_BINARY")
endif()

set(QUIVER_MEMORY_BASELINE_BIN_DIR "" CACHE PATH "Directory containing baseline search binaries")
if (QUIVER_MEMORY_BASELINE_BIN_DIR)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  foreach(engine IN ITEMS flashanns gustann)
    if (NOT EXISTS "${QUIVER_MEMORY_BASELINE_BIN_DIR}/${engine}_search")
      message(FATAL_ERROR "Missing ${engine}_search in QUIVER_MEMORY_BASELINE_BIN_DIR")
    endif()
    foreach(dtype IN ITEMS uint8 int8 float)
      add_test(NAME memory_search_${engine}_${dtype}
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
          --binary "${QUIVER_MEMORY_BASELINE_BIN_DIR}/${engine}_search"
          --engine "${engine}" --data-type "${dtype}"
          --output-dir "${CMAKE_BINARY_DIR}/search-${engine}-${dtype}")
      set_tests_properties(memory_search_${engine}_${dtype} PROPERTIES
        TIMEOUT 240 LABELS "memory;gpu;baseline" RUN_SERIAL TRUE)
    endforeach()
  endforeach()
endif()
if (QUIVER_MEMORY_SEARCH_BINARY)
  if (NOT EXISTS "${QUIVER_MEMORY_SEARCH_BINARY}")
    message(FATAL_ERROR "QUIVER_MEMORY_SEARCH_BINARY does not exist")
  endif()
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  foreach(dtype IN ITEMS uint8 int8 float)
    add_test(NAME memory_search_${dtype}
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
        --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type "${dtype}"
        --output-dir "${CMAKE_BINARY_DIR}/search-${dtype}")
    set_tests_properties(memory_search_${dtype} PROPERTIES
      TIMEOUT 240 LABELS "memory;gpu" RUN_SERIAL TRUE)
  endforeach()
  if (QUIVER_MEMORY_ENTRY_TESTS)
    add_test(NAME memory_search_entry_query
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
        --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type uint8 --entry-query
        --output-dir "${CMAKE_BINARY_DIR}/search-entry-query")
    set_tests_properties(memory_search_entry_query PROPERTIES
      TIMEOUT 240 LABELS "memory;gpu;regression" RUN_SERIAL TRUE)
    foreach(dtype IN ITEMS uint8 int8 float)
      add_test(NAME memory_search_nav_entry_${dtype}
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
          --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type "${dtype}"
          --navigation --entry-query
          --output-dir "${CMAKE_BINARY_DIR}/search-nav-entry-${dtype}")
      set_tests_properties(memory_search_nav_entry_${dtype} PROPERTIES
        TIMEOUT 240 LABELS "memory;gpu;regression" RUN_SERIAL TRUE)
    endforeach()
    add_test(NAME memory_search_large_topk
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
        --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type float
        --node-count 64 --topk 33 --entry-query
        --output-dir "${CMAKE_BINARY_DIR}/search-large-topk")
    set_tests_properties(memory_search_large_topk PROPERTIES
      TIMEOUT 240 LABELS "memory;gpu;regression" RUN_SERIAL TRUE)
  endif()
  add_test(NAME memory_search_override_index
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
      --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type float --override-index
      --output-dir "${CMAKE_BINARY_DIR}/search-override")
  set_tests_properties(memory_search_override_index PROPERTIES
    TIMEOUT 240 LABELS "memory;gpu;regression" RUN_SERIAL TRUE)
  if (QUIVER_MEMORY_EXTENDED_TESTS)
    add_test(NAME memory_search_per_query_ef
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
        --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type uint8 --per-query-ef
        --output-dir "${CMAKE_BINARY_DIR}/search-per-query-ef")
    add_test(NAME memory_search_multisector
      COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/search.py"
        --binary "${QUIVER_MEMORY_SEARCH_BINARY}" --data-type float
        --dimensions 1536 --per-query-ef
        --output-dir "${CMAKE_BINARY_DIR}/search-multisector")
    set_tests_properties(memory_search_per_query_ef memory_search_multisector PROPERTIES
      TIMEOUT 240 LABELS "memory;gpu;extended" RUN_SERIAL TRUE)
  endif()
endif()
