cmake_minimum_required(VERSION 3.8)
project(arm_bringup)

find_package(ament_cmake REQUIRED)
find_package(arm_description REQUIRED)

install(
  PROGRAMS
    genesis/genesis_sim.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME genesis_sim
)

install(
  DIRECTORY
    launch/
  DESTINATION share/${PROJECT_NAME}/launch
)

install(
  DIRECTORY
    config/
  DESTINATION share/${PROJECT_NAME}/config
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
