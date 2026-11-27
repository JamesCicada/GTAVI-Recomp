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
  set(probe_args "-DPROBE=$<TARGET_FILE:gtavi_probe>")
  if(CMAKE_CROSSCOMPILING)
    # The CMake test scripts launch the probe themselves.
    list(APPEND probe_args "-DEMULATOR=$<TARGET_GENEX_EVAL:gtavi_probe,$<TARGET_PROPERTY:gtavi_probe,CROSSCOMPILING_EMULATOR>>")
  endif()
  add_test(NAME gtavi_probe_unicode
    COMMAND ${CMAKE_COMMAND} ${probe_args} -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_unicode.cmake)
  add_test(NAME gtavi_probe_mounts
    COMMAND ${CMAKE_COMMAND} ${probe_args} -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_mounts.cmake)
endif()

if(TARGET gtavi_probe AND NOT CMAKE_CROSSCOMPILING)
  if(CMAKE_HOST_SYSTEM_NAME MATCHES "^(Linux|Windows)$")
    add_test(NAME gtavi_probe_host_release
      COMMAND ${CMAKE_COMMAND} -DPROBE=$<TARGET_FILE:gtavi_probe> -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_host_release.cmake)
  else()
    add_test(NAME gtavi_probe_unsupported_host
      COMMAND ${CMAKE_COMMAND} -DPROBE=$<TARGET_FILE:gtavi_probe> -P ${CMAKE_CURRENT_SOURCE_DIR}/probe_unsupported_host.cmake)
  endif()
endif()
