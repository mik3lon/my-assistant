# Makefile to manage Django application locally

# Variables
# (No need for DOCKER_COMPOSE_FILE since we're not using Docker)

# Help command - auto-extracted from comments
help:
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Commands for Qdrant
up: ## Start the Qdrant container
	docker compose -f docker-compose.yaml up -d qdrant

down: ## Stop and remove the Qdrant container
	docker compose -f docker-compose.yaml down qdrant

restart: ## Restart the Qdrant container
	docker compose -f docker-compose.yaml down qdrant
	docker compose -f docker-compose.yaml up -d qdrant

logs: ## Follow the logs of the Qdrant container
	docker compose -f docker-compose.yaml logs -f qdrant

ps: ## List running containers
	docker compose -f docker-compose.yaml ps

clean: ## Remove containers, volumes, and images
	docker compose -f docker-compose.yaml down -v --rmi all

# Commands for Django
django-run: ## Run the Django development server locally
	python3 manage.py runserver

django-migrate: ## Apply database migrations for the Django application
	python3 manage.py migrate

django-shell: ## Open a shell in the Django application
	python3 manage.py shell

django-create-superuser: ## Create a superuser for the Django application
	python3 manage.py createsuperuser

.PHONY: up down restart logs ps clean help django-run django-migrate django-shell django-create-superuser
