execute_process(
  COMMAND ${EMULATOR} "${PROBE}" --to-posix [[D:\Data\app0]] --mount d:/games//ps5/ --mount D:/ignored
    --to-windows /games/ps5/Data/app0 --to-posix [[C:\Games]]
  RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE errors)
if(NOT result STREQUAL "0")
  message(FATAL_ERROR "Custom mount translation failed (${result}): ${errors}")
endif()
foreach(expected IN ITEMS [[D:\Data\app0 -> /games/ps5/Data/app0]]
                         [[/games/ps5/Data/app0 -> D:\Data\app0]] [[C:\Games -> /mnt/c/Games]])
  string(FIND "${output}" "${expected}" match_at)
  if(match_at LESS 0)
    message(FATAL_ERROR "Missing translation '${expected}' in: ${output}")
  endif()
endforeach()

execute_process(COMMAND ${EMULATOR} "${PROBE}" --mount D:relative --to-posix [[D:\Data]]
  RESULT_VARIABLE result OUTPUT_QUIET ERROR_VARIABLE errors)
if(NOT result STREQUAL "2" OR NOT errors MATCHES "invalid mount")
  message(FATAL_ERROR "Invalid mount did not produce the expected error (${result}): ${errors}")
endif()
