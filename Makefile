.PHONY: help install dev test lint format clean docker-build docker-up docker-down backup

help: ## Mostra esta mensagem de ajuda
	@echo "Comandos disponíveis:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências de produção
	pip install -r requirements.txt

dev: ## Instala dependências de desenvolvimento
	pip install -r requirements.txt
	pip install pre-commit black isort flake8 mypy bandit safety
	pre-commit install

test: ## Executa testes com cobertura
	pytest --cov=app --cov-report=html --cov-report=term-missing -v

test-fast: ## Executa testes sem cobertura (mais rápido)
	pytest -x --disable-warnings -q

test-watch: ## Executa testes em modo watch
	pytest-watch -- --maxfail=1

lint: ## Executa linters (flake8, mypy, bandit)
	@echo "Running Flake8..."
	flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203,W503
	@echo "\nRunning MyPy..."
	mypy app/ --ignore-missing-imports
	@echo "\nRunning Bandit..."
	bandit -r app/ -ll

format: ## Formata código com Black e isort
	black app/ tests/ scripts/ --line-length=120
	isort app/ tests/ scripts/ --profile black --line-length 120

security: ## Verifica vulnerabilidades
	safety check
	bandit -r app/ -f json -o security-report.json

run: ## Inicia servidor de desenvolvimento
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Inicia servidor de produção
	gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

migrate: ## Executa migrations
	alembic upgrade head

migrate-create: ## Cria nova migration
	alembic revision --autogenerate -m "$(msg)"

migrate-rollback: ## Rollback última migration
	alembic downgrade -1

init-auth: ## Inicializa sistema de autenticação
	python scripts/init_auth.py

backup: ## Executa backup manual
	./scripts/backup/backup.sh daily

restore: ## Restaura backup (uso: make restore file=backup.sql.gz)
	./scripts/backup/restore.sh $(file)

setup-cron: ## Configura backups automáticos
	./scripts/backup/setup_cron.sh

clean: ## Remove arquivos temporários
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov/ coverage.xml .coverage

docker-build: ## Builda imagem Docker
	docker build -t erp-api:latest .

docker-up: ## Sobe containers Docker
	docker-compose up -d

docker-down: ## Para containers Docker
	docker-compose down

docker-logs: ## Mostra logs dos containers
	docker-compose logs -f

docker-shell: ## Abre shell no container da API
	docker-compose exec api bash

db-shell: ## Abre shell no PostgreSQL
	docker-compose exec db psql -U postgres -d erp_db

redis-shell: ## Abre shell no Redis
	docker-compose exec redis redis-cli

pre-commit: ## Executa pre-commit hooks em todos os arquivos
	pre-commit run --all-files

coverage: ## Gera relatório de cobertura HTML
	pytest --cov=app --cov-report=html
	@echo "\nRelatório gerado em: htmlcov/index.html"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open htmlcov/index.html || true

docs: ## Gera documentação da API
	@echo "Acesse http://localhost:8000/docs para Swagger UI"
	@echo "Acesse http://localhost:8000/redoc para ReDoc"

check-deps: ## Verifica dependências desatualizadas
	pip list --outdated

update-deps: ## Atualiza dependências
	pip install --upgrade -r requirements.txt

freeze: ## Gera requirements.txt atualizado
	pip freeze > requirements.txt

all: format lint test ## Executa formatação, lint e testes
