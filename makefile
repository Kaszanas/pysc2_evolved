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
		-v "$(PWD)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev

# Bazel variables (local builds use Bazelisk with version from .bazelversion):
BAZELISK ?= bazelisk
BAZEL_FLAGS =

.PHONY: bazel_build_converter
bazel_build_converter: ## Builds the C++ converter pybind11 extension inside the dev container.
	docker run --rm \
		-v "$(PWD)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev \
		bazel build //src/pysc2_evolved/env/converter/cc/python:converter \
			--output_base=/bazel-cache

.PHONY: bazel_build_converter_local
bazel_build_converter_local: ## Builds the C++ converter pybind11 extension locally via Bazelisk.
	$(BAZELISK) build $(BAZEL_FLAGS) //src/pysc2_evolved/env/converter/cc/python:converter

.PHONY: bazel_test_converter
bazel_test_converter: ## Runs all C++ converter unit tests inside the dev container.
	docker run --rm \
		-v "$(PWD)":/workspace \
		-v bazel-cache:/bazel-cache \
		$(DOCKER_TAG)-dev \
		bazel test //src/pysc2_evolved/env/converter/cc:all \
			--output_base=/bazel-cache \
			--test_output=errors

.PHONY: bazel_test_converter_local
bazel_test_converter_local: ## Runs all C++ converter unit tests locally via Bazelisk.
	$(BAZELISK) test $(BAZEL_FLAGS) //src/pysc2_evolved/env/converter/cc:all \
		--test_output=errors

.PHONY: bazel_build_all_local
bazel_build_all_local: ## Builds all Bazel targets locally via Bazelisk.
	$(BAZELISK) build $(BAZEL_FLAGS) //src/pysc2_evolved/...
