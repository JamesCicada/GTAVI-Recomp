# Shared warning configuration.
#
# Usage: target_link_libraries(<target> PRIVATE gtavi_warnings)
#
# The interface target keeps warning flags out of public headers and lets every
# target opt in with a single line.

add_library(gtavi_warnings INTERFACE)

if(MSVC)
  target_compile_options(
    gtavi_warnings
    INTERFACE /W4 # High warning level.
              /permissive- # Conform to the standard, not MSVC extensions.
              /utf-8 # Source and execution charset are UTF-8.
              /Zc:__cplusplus # Report the real __cplusplus value.
              /Zc:preprocessor # Standard-conforming preprocessor.
              /EHsc # Standard C++ exception model.
  )
  if(GTAVI_WARNINGS_AS_ERRORS)
    target_compile_options(gtavi_warnings INTERFACE /WX)
  endif()
else()
  target_compile_options(
    gtavi_warnings
    INTERFACE -Wall
              -Wextra
              -Wpedantic
              -Wshadow
              -Wnon-virtual-dtor
              -Wold-style-cast
              -Wcast-align
              -Wunused
              -Woverloaded-virtual
              -Wdouble-promotion
              -Wformat=2
              -Wconversion
              -Wsign-conversion
  )
  if(GTAVI_WARNINGS_AS_ERRORS)
    target_compile_options(gtavi_warnings INTERFACE -Werror)
  endif()
endif()
