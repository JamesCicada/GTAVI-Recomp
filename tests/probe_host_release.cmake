cmake_minimum_required(VERSION 3.21)

if(CMAKE_HOST_WIN32)
  set(expected_platform windows)
  execute_process(COMMAND cmd /d /c ver OUTPUT_VARIABLE version COMMAND_ERROR_IS_FATAL ANY)
  # ver may include a fourth component. The probe reports major.minor.build.
  string(REGEX MATCH "[0-9]+\\.[0-9]+\\.[0-9]+" expected "${version}")
else()
  set(expected_platform linux)
  execute_process(COMMAND uname -r OUTPUT_VARIABLE expected
    OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
endif()

execute_process(COMMAND "${PROBE}" OUTPUT_VARIABLE output COMMAND_ERROR_IS_FATAL ANY)
string(REGEX MATCH "(^|\n)os version:[ \t]+([^\r\n]+)" field "${output}")
if(NOT expected OR NOT field OR NOT "${CMAKE_MATCH_2}" STREQUAL "${expected}")
  message(FATAL_ERROR "Expected the native OS release '${expected}' in the probe output:\n${output}")
endif()

if(NOT output MATCHES "(^|\n)platform:[ \t]+${expected_platform}(\r?\n|$)")
  message(FATAL_ERROR "Expected platform '${expected_platform}' in the probe output:\n${output}")
endif()
