# Build with Docker Desktop's built-in builder, never the globally active buildx builder
# (which may belong to another project and keep its own large cache).
export BUILDX_BUILDER := desktop-linux

COMPOSE   := docker compose
TOXIPROXY := http://localhost:8474
PSQL      := $(COMPOSE) exec -T postgres psql -U religuard -d postgres -v ON_ERROR_STOP=1 -q
DBS       := orders payments inventory

.PHONY: help up down reset proxies ps logs clean size prune

help:  ## Show available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

up:  ## Start the stack and wait until Toxiproxy answers
	$(COMPOSE) up -d --build --wait
	@for i in $$(seq 1 30); do curl -sf $(TOXIPROXY)/version >/dev/null && break; sleep 1; done
	@curl -sf $(TOXIPROXY)/version >/dev/null || (echo "Toxiproxy did not start" && exit 1)
	@$(MAKE) --no-print-directory proxies

down:  ## Stop the stack (database is in RAM, so its data is discarded)
	$(COMPOSE) down

reset:  ## Remove all toxics, re-enable all proxies, recreate the databases
	curl -sf -X POST $(TOXIPROXY)/reset
	@for db in $(DBS); do \
		echo "recreating database $$db"; \
		$(PSQL) -c "DROP DATABASE IF EXISTS $$db WITH (FORCE);" -c "CREATE DATABASE $$db;" || exit 1; \
	done

proxies:  ## List Toxiproxy proxies and their toxics
	@python3 infra/show_proxies.py $(TOXIPROXY)

ps:  ## Show container status
	$(COMPOSE) ps

logs:  ## Follow logs from all containers
	$(COMPOSE) logs -f

clean:  ## Stop the stack and remove this project's containers, networks, and images
	$(COMPOSE) down -v --rmi all --remove-orphans

size:  ## Show disk used by this project's images and volumes (budget: < 1 GB)
	@docker images --format '{{.Repository}}:{{.Tag}}\t{{.Size}}' | grep -E '^(religuard|postgres:16.4-alpine|ghcr.io/shopify/toxiproxy)' || true
	@docker volume ls -q --filter label=com.docker.compose.project=religuard | sed 's/^/volume: /'
	@docker system df --format '{{.Type}}: {{.Size}}' | grep -i 'build cache'

prune:  ## Remove this project's dangling images and the desktop-linux build cache (other builders untouched)
	docker image prune -f --filter label=com.docker.compose.project=religuard
	docker builder prune -f --builder $(BUILDX_BUILDER)
