build:
	docker build -t ansible/dashboard -f tools/Dockerfile .

run:
	PYTHONUNBUFFERED=0 CURRENT_UID=$(shell id -u) docker-compose -f tools/docker-compose.yml up --no-recreate
