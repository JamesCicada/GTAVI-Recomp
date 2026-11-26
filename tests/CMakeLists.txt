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
