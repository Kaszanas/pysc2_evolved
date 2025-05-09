# Docker variables:
DOCKER_DIR = ./docker
DOCKER_FILE = $(DOCKER_DIR)/Dockerfile
DOCKER_FILE_DEV = $(DOCKER_DIR)/Dockerfile.dev
DOCKER_TAG = pysc2_evolved

# Python variables:
PYTHON_VERSION = 3.11



.PHONY: docker_build
docker_build: ## Builds the image containing all of the tools.
	@echo "Building the Dockerfile: $(DOCKER_FILE)"
	@echo "Using Python version: $(PYTHON_VERSION)"
	docker build \
		--build-arg="PYTHON_VERSION=$(PYTHON_VERSION)" \
		-f $(DOCKER_FILE) . \
		--tag=$(DOCKER_TAG) \
