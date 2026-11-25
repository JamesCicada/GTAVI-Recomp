# U+4E57 has a backslash as its second byte in code page 936. U+1F600
# cannot be represented at all in the common legacy Windows code pages.
set(windows [[D:\Music\乗-😀]])
set(posix "/library/音/Music/乗-😀")
execute_process(
  COMMAND "${PROBE}" --mount "D:/library/音" --to-posix "${windows}" --to-windows "${posix}"
  ENCODING UTF-8 RESULT_VARIABLE result OUTPUT_VARIABLE output ERROR_VARIABLE errors)
if(NOT result STREQUAL "0")
  message(FATAL_ERROR "Unicode path translation failed (${result}): ${errors}")
endif()
foreach(line IN ITEMS "${windows} -> ${posix}\n" "${posix} -> ${windows}\n")
  string(FIND "${output}" "${line}" position)
  if(position LESS 0)
    message(FATAL_ERROR "Missing translation '${line}' in: ${output}")
  endif()
endforeach()

execute_process(COMMAND "${PROBE}" --mount "D:乗-😀"
  ENCODING UTF-8 RESULT_VARIABLE result OUTPUT_QUIET ERROR_VARIABLE errors)
string(FIND "${errors}" "invalid mount: D:乗-😀" position)
if(NOT result STREQUAL "2" OR position LESS 0)
  message(FATAL_ERROR "Unicode usage diagnostic failed (${result}): ${errors}")
endif()
