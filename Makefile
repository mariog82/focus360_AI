
install:
	pip install -r requirements.txt

test:
	./scripts/run_tests.sh

security:
	./scripts/devsecops_scan.sh

up:
	docker compose up --build

down:
	docker compose down
