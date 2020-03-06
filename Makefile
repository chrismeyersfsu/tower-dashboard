build:
	docker build -t ansible/dashboard -f tools/Dockerfile .

run:
	CURRENT_UID=$(shell id -u) docker-compose -f tools/docker-compose.yml up --no-recreate
