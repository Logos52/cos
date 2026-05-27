# Makefile for CosURLHandler.app
#
# Convenience targets for developers who like `make`.
# All heavy lifting lives in build.sh (single source of truth for the bundle recipe).
#
# Targets:
#   make              — build the .app
#   make clean        — remove build artifacts
#   make install      — build + copy to ~/Applications + register scheme
#   make test         — quick smoke test of the binary (CLI mode)
#
# Requires: Xcode Command Line Tools

.PHONY: all build clean install test help

BUILD_DIR := build
APP := $(BUILD_DIR)/CosURLHandler.app

all: build

build:
	@./build.sh

clean:
	@./build.sh --clean

install:
	@./build.sh --install

test: build
	@echo "Testing CLI mode of the built binary..."
	"$(APP)/Contents/MacOS/CosURLHandler" --version
	"$(APP)/Contents/MacOS/CosURLHandler" --help | head -8
	@echo ""
	@echo "To actually exercise URL handling (will launch Ghostty/Terminal):"
	@echo "  open 'cos://brief'"
	@echo "  \"$(APP)/Contents/MacOS/CosURLHandler\" 'cos://research?ticker=NVDA'"

help:
	@echo "CosURLHandler Makefile"
	@echo ""
	@echo "  make build     Build CosURLHandler.app"
	@echo "  make clean     Remove build/ directory"
	@echo "  make install   Build and install to ~/Applications (recommended one-time step)"
	@echo "  make test      Build + smoke-test the CLI entrypoint"
	@echo ""
	@echo "See build.sh and macos-helper/README.md for details."