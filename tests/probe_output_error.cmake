# A short report fits in the C stdio buffer. The write error may only surface
# when the process flushes its output before exiting.
execute_process(COMMAND "${PROBE}" --to-posix [[D:\Data]] OUTPUT_FILE "/dev/full"
  RESULT_VARIABLE status ERROR_VARIABLE errors)
if(NOT status STREQUAL "1" OR NOT errors MATCHES "could not write probe output")
  message(FATAL_ERROR "Expected an output error, got status ${status}: ${errors}")
endif()
