cmake_minimum_required(VERSION 3.5)

project(models_and_worlds)

find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY
    models/
  DESTINATION share/${PROJECT_NAME}/models
)

install(
  DIRECTORY
    worlds/
  DESTINATION share/${PROJECT_NAME}/worlds
)

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.sh.in")

ament_package()
