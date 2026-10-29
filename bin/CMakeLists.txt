function(add_search_executable target_name source_file system_lib extra_include)
  add_executable(${target_name} ${source_file})
  target_include_directories(${target_name} PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}"
    ${extra_include}
  )
  target_link_libraries(${target_name} PRIVATE argparse ${system_lib})
  target_compile_options(${target_name}
    PRIVATE "-lineinfo"
    PRIVATE "-O2" "-g"
  )
endfunction()

# GustANN and FlashANNS: include their own self-contained src/<system>/
# (which contains shared/ internally)
add_search_executable(gustann_search gustann_search.cu gustann_lib
  "${PROJECT_SOURCE_DIR}/src/gustann")
add_search_executable(gustann_search_pw1 gustann_search.cu gustann_pw1_lib
  "${PROJECT_SOURCE_DIR}/src/gustann")
add_search_executable(probe_gustann_search_pw1 gustann_search.cu
  gustann_probe_pw1_lib "${PROJECT_SOURCE_DIR}/src/gustann")
add_search_executable(flashanns_search flashanns_search.cu flashanns_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(probe_flashanns_search flashanns_search.cu flashanns_probe_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(flashanns_search_pw1 flashanns_search.cu flashanns_pw1_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(flashanns_search_pw2 flashanns_search.cu flashanns_pw2_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(flashanns_search_pw3 flashanns_search.cu flashanns_pw3_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(flashanns_search_pw4 flashanns_search.cu flashanns_pw4_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(probe_flashanns_search_pw1 flashanns_search.cu flashanns_probe_pw1_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(probe_flashanns_search_pw2 flashanns_search.cu flashanns_probe_pw2_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(probe_flashanns_search_pw3 flashanns_search.cu flashanns_probe_pw3_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")
add_search_executable(probe_flashanns_search_pw4 flashanns_search.cu flashanns_probe_pw4_lib
  "${PROJECT_SOURCE_DIR}/src/flashanns")

# GPipeANN: uses top-level src/ (shared/ is public)
add_search_executable(gpipeann_search gpipeann_search.cu gpipeann_lib
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search gpipeann_search.cu gpipeann_probe_lib
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw1_q1 gpipeann_search.cu gpipeann_lib_pw1_q1
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw1_q2 gpipeann_search.cu gpipeann_lib_pw1_q2
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw1_q4 gpipeann_search.cu gpipeann_lib_pw1_q4
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw1_q8 gpipeann_search.cu gpipeann_lib_pw1_q8
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw2_q1 gpipeann_search.cu gpipeann_lib_pw2_q1
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw2_q2 gpipeann_search.cu gpipeann_lib_pw2_q2
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw2_q3 gpipeann_search.cu gpipeann_lib_pw2_q3
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw2_q4 gpipeann_search.cu gpipeann_lib_pw2_q4
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(gpipeann_search_pw4_q1 gpipeann_search.cu gpipeann_lib_pw4_q1
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw1_q1 gpipeann_search.cu gpipeann_probe_lib_pw1_q1
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw1_q2 gpipeann_search.cu gpipeann_probe_lib_pw1_q2
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw1_q4 gpipeann_search.cu gpipeann_probe_lib_pw1_q4
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw1_q8 gpipeann_search.cu gpipeann_probe_lib_pw1_q8
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw2_q1 gpipeann_search.cu gpipeann_probe_lib_pw2_q1
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw2_q2 gpipeann_search.cu gpipeann_probe_lib_pw2_q2
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw2_q3 gpipeann_search.cu gpipeann_probe_lib_pw2_q3
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw2_q4 gpipeann_search.cu gpipeann_probe_lib_pw2_q4
  "${PROJECT_SOURCE_DIR}/src")
add_search_executable(probe_gpipeann_search_pw4_q1 gpipeann_search.cu gpipeann_probe_lib_pw4_q1
  "${PROJECT_SOURCE_DIR}/src")

add_executable(search_setup_test
  common/search_setup_test.cpp)
set_source_files_properties(common/search_setup_test.cpp PROPERTIES LANGUAGE CUDA)
target_include_directories(search_setup_test PRIVATE
  "${CMAKE_CURRENT_SOURCE_DIR}"
  "${PROJECT_SOURCE_DIR}/src")
target_link_libraries(search_setup_test
  PRIVATE argparse spdlog shared_index_lib shared_io_lib)
target_compile_options(search_setup_test
  PRIVATE "-O2" "-g")

# ----------------------------------------------------------------------------
# Strawman ablation binaries (gated on GPIPEANN_BUILD_STRAWMEN).
# These exist only to defend the §Key Idea section by quantifying strawman
# design alternatives.
# ----------------------------------------------------------------------------
if (GPIPEANN_BUILD_STRAWMEN)
  add_search_executable(strawmen_static_dispatch strawmen_static_dispatch.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch
    strawmen_static_dispatch.cu gpipeann_probe_lib "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw1_q1
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw1_q1
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw1_q2
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw1_q2
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw1_q4
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw1_q4
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw1_q8
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw1_q8
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw2_q1
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw2_q1
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw2_q2
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw2_q2
    "${PROJECT_SOURCE_DIR}/src")
  add_search_executable(probe_strawmen_static_dispatch_pw4_q1
    strawmen_static_dispatch.cu gpipeann_probe_lib_pw4_q1
    "${PROJECT_SOURCE_DIR}/src")

  add_search_executable(strawmen_early_exit strawmen_early_exit.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")

  add_search_executable(strawmen_barrier strawmen_barrier.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")
  target_compile_definitions(strawmen_barrier PRIVATE GPIPEANN_BUILD_STRAWMEN)

  add_search_executable(strawmen_pq_in_smem strawmen_pq_in_smem.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")
  target_compile_definitions(strawmen_pq_in_smem PRIVATE GPIPEANN_BUILD_STRAWMEN)

  add_search_executable(strawmen_pq_in_gmem strawmen_pq_in_gmem.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")
  target_compile_definitions(strawmen_pq_in_gmem PRIVATE GPIPEANN_BUILD_STRAWMEN)

  add_search_executable(strawmen_naive_block_multi_query strawmen_naive_block_multi_query.cu
    gpipeann_lib "${PROJECT_SOURCE_DIR}/src")
  target_compile_definitions(strawmen_naive_block_multi_query PRIVATE GPIPEANN_BUILD_STRAWMEN)
endif()

if (GPIPEANN_ENABLE_SPDK)
  add_executable(spdk_write spdk_write.cpp)
  target_link_libraries(spdk_write PRIVATE shared_common_lib shared_spdk_wrapper)

  add_executable(spdk_read_probe spdk_read_probe.cpp)
  target_link_libraries(spdk_read_probe PRIVATE shared_common_lib shared_spdk_wrapper)
endif()
