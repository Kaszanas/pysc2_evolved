# Docker variables:
DOCKER_DIR = ./docker
DOCKER_FILE = $(DOCKER_DIR)/Dockerfile
DOCKER_FILE_DEV = $(DOCKER_DIR)/Dockerfile.dev
DOCKER_TAG = pysc2_evolved

# Python variables:
PYTHON_VERSION = 3.11



.PHONY: docker_build
docker_build: ## Builds the runtime Docker image.
	@echo "Building the Dockerfile: $(DOCKER_FILE)"
	@echo "Using Python version: $(PYTHON_VERSION)"
	docker build \
		--build-arg="PYTHON_VERSION=$(PYTHON_VERSION)" \
		-f $(DOCKER_FILE) . \
		--tag=$(DOCKER_TAG)

.PHONY: docker_build_dev
docker_build_dev: ## Builds the dev image with Bazelisk + pinned Bazel (from .bazelversion).
	@echo "Building the dev Dockerfile: $(DOCKER_FILE_DEV)"
	docker build \
		-f $(DOCKER_FILE_DEV) . \
		--tag=$(DOCKER_TAG)-dev

.PHONY: docker_run_dev
docker_run_dev: ## Runs the dev container, mounting the repo as /workspace.
	docker run --rm -it \
		-v "$(CURDIR)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev

# Bazel variables (local builds use Bazelisk with version from .bazelversion):
BAZELISK ?= bazelisk
BAZEL_FLAGS =

.PHONY: bazel_build_converter
bazel_build_converter: ## Builds the C++ converter pybind11 extension inside the dev container.
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev \
		bazel --output_base=/bazel-cache \
		build //src/pysc2_evolved/env/converter/cc/python:converter

.PHONY: bazel_build_converter_local
bazel_build_converter_local: ## Builds the C++ converter pybind11 extension locally via Bazelisk.
	$(BAZELISK) build $(BAZEL_FLAGS) \
	//src/pysc2_evolved/env/converter/cc/python:converter

.PHONY: bazel_test_converter
bazel_test_converter: ## Runs all C++ converter unit tests inside the dev container.
	docker run --rm \
		-v "$(CURDIR)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev \
		bazel --output_base=/bazel-cache test \
		//src/pysc2_evolved/env/converter/cc:all \
		--test_output=errors

.PHONY: bazel_test_converter_local
bazel_test_converter_local: ## Runs all C++ converter unit tests locally via Bazelisk.
	$(BAZELISK) test $(BAZEL_FLAGS) //src/pysc2_evolved/env/converter/cc:all \
		--test_output=errors

.PHONY: bazel_build_all_local
bazel_build_all_local: ## Builds all Bazel targets locally via Bazelisk.
	$(BAZELISK) build $(BAZEL_FLAGS) //src/pysc2_evolved/...

.PHONY: bazel_build_uint8_lookup_local
bazel_build_uint8_lookup_local: ## Builds the uint8_lookup pybind11 extension locally via Bazelisk.
	$(BAZELISK) build $(BAZEL_FLAGS) \
	//src/pysc2_evolved/env/converter/cc/game_data/python:uint8_lookup

.PHONY: bazel_build_extensions_local
bazel_build_extensions_local: bazel_build_converter_local bazel_build_uint8_lookup_local ## Builds both pybind11 extensions (converter + uint8_lookup) locally via Bazelisk.

# Wheel packaging
# EXT must be set by the caller: "so" on Linux/macOS, "pyd" on Windows.
# Example: make copy_extensions_local EXT=so
.PHONY: copy_extensions_local
copy_extensions_local: ## Copies compiled extensions from bazel-bin into the source tree (local builds). Requires EXT=so|pyd.
	cp bazel-bin/src/pysc2_evolved/env/converter/cc/python/converter.$(EXT) \
	   src/pysc2_evolved/env/converter/cc/python/converter.$(EXT)
	cp bazel-bin/src/pysc2_evolved/env/converter/cc/game_data/python/uint8_lookup.$(EXT) \
	   src/pysc2_evolved/env/converter/cc/game_data/python/uint8_lookup.$(EXT)

# EXT must be set by the caller: "so" on Linux/macOS, "pyd" on Windows.
# Example: make stage_extensions_local EXT=so
.PHONY: stage_extensions_local
stage_extensions_local: ## Copies compiled extensions from bazel-bin into cc-dist/ for CI artifact upload. Requires EXT=so|pyd.
	mkdir -p cc-dist
	cp bazel-bin/src/pysc2_evolved/env/converter/cc/python/converter.$(EXT) \
	   cc-dist/converter.$(EXT)
	cp bazel-bin/src/pysc2_evolved/env/converter/cc/game_data/python/uint8_lookup.$(EXT) \
	   cc-dist/uint8_lookup.$(EXT)

# EXT must be set by the caller: "so" on Linux/macOS, "pyd" on Windows.
# SRCDIR must be set to the directory containing the pre-built extensions.
# Example: make place_extensions_local EXT=so SRCDIR=cc-dist
.PHONY: place_extensions_local
place_extensions_local: ## Places pre-built extensions from SRCDIR into the source tree (CI packaging). Requires EXT=so|pyd SRCDIR=path.
	cp $(SRCDIR)/converter.$(EXT) \
	   src/pysc2_evolved/env/converter/cc/python/converter.$(EXT)
	cp $(SRCDIR)/uint8_lookup.$(EXT) \
	   src/pysc2_evolved/env/converter/cc/game_data/python/uint8_lookup.$(EXT)

.PHONY: build_wheel_local
build_wheel_local: ## Builds a platform-specific wheel via uv.
	uv build --wheel

# Wheel verification targets:
.PHONY: smoke_test_local
smoke_test_local: ## Verifies pybind11 extensions are importable and execute C++ code.
	uv run --no-project python scripts/smoke_test_converter.py

.PHONY: install_wheel_local
install_wheel_local: ## Installs the wheel from dist/ into the current Python environment.
	uv pip install dist/*.whl

.PHONY: verify_wheel_local
verify_wheel_local: install_wheel_local smoke_test_local ## Installs wheel from dist/ and runs smoke test.
