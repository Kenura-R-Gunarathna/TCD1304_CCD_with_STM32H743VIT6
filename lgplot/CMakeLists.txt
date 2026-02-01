# CMakeList.txt : CMake project for learnvcpkg, include source and define
# project specific logic here.
#
cmake_minimum_required (VERSION 3.10)

# Enable Hot Reload for MSVC compilers if supported.
if (POLICY CMP0141)
  cmake_policy(SET CMP0141 NEW)
  set(CMAKE_MSVC_DEBUG_INFORMATION_FORMAT "$<IF:$<AND:$<C_COMPILER_ID:MSVC>,$<CXX_COMPILER_ID:MSVC>>,$<$<CONFIG:Debug,RelWithDebInfo>:EditAndContinue>,$<$<CONFIG:Debug,RelWithDebInfo>:ProgramDatabase>>")
endif()

project ("lgplot")

find_package(imgui CONFIG REQUIRED)
find_package(implot CONFIG REQUIRED)
find_package(glfw3 CONFIG REQUIRED)
find_package(OpenGL REQUIRED)

# lgplot executable with modular structure
add_executable(lgplot 
    "src/main.cpp"
    "src/app_state.cpp"
    "src/console.cpp"
    "src/connection.cpp"
    "src/ui_panels.cpp"
)

target_include_directories(lgplot PRIVATE src)

target_link_libraries(lgplot PRIVATE 
    imgui::imgui
    implot::implot
    glfw
    OpenGL::GL
)

# Windows-specific settings
if(WIN32)
    target_link_libraries(lgplot PRIVATE ws2_32)
endif()

if (CMAKE_VERSION VERSION_GREATER 3.12)
  set_property(TARGET lgplot PROPERTY CXX_STANDARD 17)
endif()

