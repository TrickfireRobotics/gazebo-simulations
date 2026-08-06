BUILD_DIR := ./build

.PHONY: all run clean

all: $(BUILD_DIR)/sim

$(BUILD_DIR)/sim: ./CMakeLists.txt ./main.cpp
	cmake -GNinja -B $(BUILD_DIR) -S . -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
	cmake --build $(BUILD_DIR)

run: $(BUILD_DIR)/sim
	cd $(BUILD_DIR) && ./sim

clean:
	rm -rf $(BUILD_DIR)
