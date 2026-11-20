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
