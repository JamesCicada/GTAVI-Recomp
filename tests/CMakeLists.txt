add_executable(
  gtavi_tests
  main.cpp
  error_tests.cpp
  log_tests.cpp
  path_tests.cpp
  platform_tests.cpp
)

target_link_libraries(gtavi_tests PRIVATE gtavi::core gtavi_warnings)

add_test(NAME gtavi_tests COMMAND gtavi_tests)

if(TARGET gtavi_probe AND CMAKE_HOST_SYSTEM_NAME STREQUAL "Linux"
   AND NOT CMAKE_CROSSCOMPILING AND EXISTS "/dev/full")
  add_test(NAME gtavi_probe_output_error
    COMMAND ${CMAKE_COMMAND} -DPROBE=$<TARGET_FILE:gtavi_probe> -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_output_error.cmake)
endif()

if(TARGET gtavi_probe)
  add_test(NAME gtavi_probe_unicode
    COMMAND ${CMAKE_COMMAND} -DPROBE=$<TARGET_FILE:gtavi_probe> -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_unicode.cmake)
  add_test(NAME gtavi_probe_mounts
    COMMAND ${CMAKE_COMMAND} -DPROBE=$<TARGET_FILE:gtavi_probe> -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_mounts.cmake)
endif()
