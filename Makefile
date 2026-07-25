BUILD_DIR := chrono/build

.PHONY: all run clean hooks format

all: $(BUILD_DIR)/sim

$(BUILD_DIR)/sim: chrono/CMakeLists.txt chrono/main.cpp
	cmake -GNinja -B $(BUILD_DIR) -S chrono -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
	cmake --build $(BUILD_DIR)

run: $(BUILD_DIR)/sim
	cd $(BUILD_DIR) && ./sim

clean:
	rm -rf $(BUILD_DIR)

hooks:
	pre-commit install --hook-type pre-commit --hook-type commit-msg

format:
	ruff format .
	ruff check --fix .
	find chrono \( -path 'chrono/vendor' -o -path 'chrono/build' \) -prune -o \( -name '*.cpp' -o -name '*.hpp' -o -name '*.h' \) -print0 | xargs -0 clang-format -i
	shfmt -i 4 -s -w .devcontainer/ docker/
