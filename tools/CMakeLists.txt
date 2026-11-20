add_executable(gtavi_probe probe/main.cpp)

target_link_libraries(gtavi_probe PRIVATE gtavi::core gtavi_warnings)
