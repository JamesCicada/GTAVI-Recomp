@echo off
setlocal enableextensions

rem Configure, build, and test on Windows.
rem
rem Usage:
rem   scripts\build-windows.bat [Debug^|Release^|RelWithDebInfo^|MinSizeRel] [--clean]
rem
rem Defaults to Release. Finds vcvars64.bat with vswhere, so it works with any
rem Visual Studio edition or the Build Tools, from any shell. Nothing outside
rem this script's own environment is modified.

set "PF86=%ProgramFiles(x86)%"
set "CONFIG=Release"
set "CLEAN="
set "ROOT=%~dp0.."
set "BUILD_DIR=build\windows"

:parse_args
if "%~1"=="" goto :args_done
if /I "%~1"=="-h" goto :usage
if /I "%~1"=="--help" goto :usage
if /I "%~1"=="--clean" (
    set "CLEAN=1"
) else (
    set "CONFIG=%~1"
)
shift
goto :parse_args
:args_done

if /I not "%CONFIG%"=="Debug" if /I not "%CONFIG%"=="Release" if /I not "%CONFIG%"=="RelWithDebInfo" if /I not "%CONFIG%"=="MinSizeRel" (
    >&2 echo error: unknown configuration "%CONFIG%"
    >&2 echo        expected Debug, Release, RelWithDebInfo, or MinSizeRel
    exit /b 2
)

pushd "%ROOT%" >nul 2>&1
if errorlevel 1 (
    >&2 echo error: cannot enter repository root "%ROOT%"
    exit /b 1
)

rem Skip the toolchain search when already inside a developer environment.
where cl >nul 2>&1
if not errorlevel 1 goto :have_toolchain

set "VSWHERE=%PF86%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" set "VSWHERE=%ProgramFiles%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%VSWHERE%" (
    >&2 echo error: vswhere.exe not found.
    >&2 echo        Install Visual Studio or the Build Tools with the C++ workload,
    >&2 echo        or run this script from a Developer Command Prompt.
    goto :fail
)

set "VSPATH_FILE=%TEMP%\gtavi-vswhere-%RANDOM%.txt"
"%VSWHERE%" -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath > "%VSPATH_FILE%"
set "VSPATH="
set /p "VSPATH="<"%VSPATH_FILE%"
del "%VSPATH_FILE%" >nul 2>&1

if not defined VSPATH (
    >&2 echo error: no Visual Studio installation with the C++ workload was found.
    >&2 echo        Install the "Desktop development with C++" workload.
    goto :fail
)

set "VCVARS=%VSPATH%\VC\Auxiliary\Build\vcvars64.bat"
if not exist "%VCVARS%" (
    >&2 echo error: vcvars64.bat not found at "%VCVARS%"
    goto :fail
)

echo Environment:
echo   %VCVARS%
call "%VCVARS%" >nul
if errorlevel 1 (
    >&2 echo error: vcvars64.bat failed
    goto :fail
)

:have_toolchain
where cmake >nul 2>&1
if errorlevel 1 (
    >&2 echo error: cmake not found on PATH.
    >&2 echo        Install CMake, or add the Visual Studio CMake component to PATH.
    goto :fail
)

echo Compiler:
where cl

set "GENERATOR=-G Ninja"
where ninja >nul 2>&1
if errorlevel 1 (
    echo Ninja not found; falling back to the default Visual Studio generator.
    set "GENERATOR="
)

if defined CLEAN (
    echo Removing "%BUILD_DIR%"
    if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
)

echo.
echo Configuring %CONFIG%
cmake -S . -B "%BUILD_DIR%" %GENERATOR% -DCMAKE_BUILD_TYPE=%CONFIG% -DGTAVI_WARNINGS_AS_ERRORS=ON -DGTAVI_BUILD_TESTS=ON
if errorlevel 1 goto :fail

echo.
echo Building
cmake --build "%BUILD_DIR%" --config %CONFIG% --parallel
if errorlevel 1 goto :fail

echo.
echo Testing
ctest --test-dir "%BUILD_DIR%" -C %CONFIG% --output-on-failure --no-tests=error
if errorlevel 1 goto :fail

echo.
echo OK: %CONFIG% build and tests passed in "%BUILD_DIR%"
popd
exit /b 0

:fail
echo.
>&2 echo FAILED
popd
exit /b 1

:usage
echo Usage: scripts\build-windows.bat [Debug^|Release^|RelWithDebInfo^|MinSizeRel] [--clean]
echo.
echo   Debug, Release, RelWithDebInfo, MinSizeRel   configuration (default: Release)
echo   --clean                                     delete the build directory first
echo   -h, --help                                  show this message
echo.
echo Finds vcvars64.bat with vswhere, then configures, builds, and tests.
exit /b 0
