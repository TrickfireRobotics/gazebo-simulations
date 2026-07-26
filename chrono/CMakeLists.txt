cmake_minimum_required(VERSION 3.18)
project(trickfire_sim CXX)

set(CHRONO_DIR "/home/trickfire/chrono/build/cmake"
    CACHE PATH "Path to Chrono's cmake/ directory inside the build tree")

find_package(Chrono
    COMPONENTS Vehicle VSG
    HINTS "${CHRONO_DIR}"
    REQUIRED
)

add_executable(sim main.cpp)
target_compile_definitions(sim PRIVATE
    CHRONO_DATA_PATH="${CMAKE_SOURCE_DIR}/data/"
    CHRONO_VEHICLE_DATA_PATH="${CHRONO_VEHICLE_DATA_DIR}"
)
target_link_libraries(sim
    Chrono::Chrono_core
    Chrono::Chrono_vehicle
    Chrono::Chrono_vsg
    Chrono::Chrono_vehicle_vsg
)
set_target_properties(sim PROPERTIES CXX_STANDARD 17)
