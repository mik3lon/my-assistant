# Makefile to manage Docker Compose for Qdrant

# Variables
DOCKER_COMPOSE_FILE = docker-compose.yaml

# Help command - auto-extracted from comments
help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Commands
up: ## Start the Qdrant container
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d

down: ## Stop and remove the Qdrant container
	docker compose -f $(DOCKER_COMPOSE_FILE) down

restart: ## Restart the Qdrant container
	docker compose -f $(DOCKER_COMPOSE_FILE) down
	docker compose -f $(DOCKER_COMPOSE_FILE) up -d

logs: ## Follow the logs of the Qdrant container
	docker compose -f $(DOCKER_COMPOSE_FILE) logs -f

ps: ## List running containers
	docker compose -f $(DOCKER_COMPOSE_FILE) ps

clean: ## Remove containers, volumes, and images
	docker compose -f $(DOCKER_COMPOSE_FILE) down -v --rmi all

.PHONY: up down restart logs ps clean help
