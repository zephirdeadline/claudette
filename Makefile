.PHONY: help install clean build run test

# Variables
PYTHON := python3
PIP := pip3
APP_NAME := claudette
MAIN_SCRIPT := main.py
DIST_DIR := dist
BUILD_DIR := build
SPEC_FILE := $(APP_NAME).spec

# Colors for terminal output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Claudette - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Install dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	$(PIP) install pyinstaller

clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	rm -rf $(DIST_DIR) $(BUILD_DIR) __pycache__ src/__pycache__
	rm -f $(SPEC_FILE)
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Clean complete!$(NC)"

build: clean ## Build distributable binary with PyInstaller
	@echo "$(GREEN)Building Claudette distributable...$(NC)"
	pyinstaller --onefile \
		--name $(APP_NAME) \
		--add-data "src:src" \
		--hidden-import=ollama \
		--hidden-import=rich \
		--hidden-import=prompt_toolkit \
		--hidden-import=yaml \
		--hidden-import=tiktoken \
		--hidden-import=colorama \
		--collect-all tiktoken \
		--collect-all rich \
		--collect-all prompt_toolkit \
		--clean \
		$(MAIN_SCRIPT)
	@echo "$(GREEN)Build complete! Binary located at: $(DIST_DIR)/$(APP_NAME)$(NC)"

build-debug: clean ## Build with debug console (useful for troubleshooting)
	@echo "$(GREEN)Building Claudette (debug mode)...$(NC)"
	pyinstaller --onefile \
		--name $(APP_NAME)-debug \
		--add-data "src:src" \
		--hidden-import=ollama \
		--hidden-import=rich \
		--hidden-import=prompt_toolkit \
		--hidden-import=yaml \
		--hidden-import=tiktoken \
		--hidden-import=colorama \
		--collect-all tiktoken \
		--collect-all rich \
		--collect-all prompt_toolkit \
		--debug all \
		$(MAIN_SCRIPT)
	@echo "$(GREEN)Debug build complete!$(NC)"

run: ## Run the application from source
	@echo "$(GREEN)Running Claudette from source...$(NC)"
	$(PYTHON) $(MAIN_SCRIPT)

run-dist: ## Run the built distributable
	@echo "$(GREEN)Running Claudette from distributable...$(NC)"
	@if [ -f "$(DIST_DIR)/$(APP_NAME)" ]; then \
		./$(DIST_DIR)/$(APP_NAME); \
	else \
		echo "$(RED)Error: Distributable not found. Run 'make build' first.$(NC)"; \
		exit 1; \
	fi

test: ## Test the built distributable
	@echo "$(GREEN)Testing distributable...$(NC)"
	@if [ -f "$(DIST_DIR)/$(APP_NAME)" ]; then \
		./$(DIST_DIR)/$(APP_NAME) --help; \
		echo "$(GREEN)Test complete!$(NC)"; \
	else \
		echo "$(RED)Error: Distributable not found. Run 'make build' first.$(NC)"; \
		exit 1; \
	fi

install-dist: build ## Build and install to /usr/local/bin
	@echo "$(GREEN)Installing Claudette to /usr/local/bin...$(NC)"
	sudo cp $(DIST_DIR)/$(APP_NAME) /usr/local/bin/
	sudo chmod +x /usr/local/bin/$(APP_NAME)
	@echo "$(GREEN)Installation complete! You can now run 'claudette' from anywhere.$(NC)"

uninstall-dist: ## Remove installed binary
	@echo "$(YELLOW)Removing Claudette from /usr/local/bin...$(NC)"
	sudo rm -f /usr/local/bin/$(APP_NAME)
	@echo "$(GREEN)Uninstall complete!$(NC)"

size: ## Show binary size
	@if [ -f "$(DIST_DIR)/$(APP_NAME)" ]; then \
		echo "$(GREEN)Binary size:$(NC)"; \
		du -h $(DIST_DIR)/$(APP_NAME); \
	else \
		echo "$(RED)Error: Distributable not found. Run 'make build' first.$(NC)"; \
	fi

all: install build test ## Install dependencies, build, and test

.DEFAULT_GOAL := help
