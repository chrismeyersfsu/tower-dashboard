DOCKER_NAMESPACE ?= ansible

build-sdist:
	docker build -t ${DOCKER_NAMESPACE}/dashboard-sdist -f tools/Dockerfile.sdist .
	docker run -it -v $(PWD):/dashboard_devel --user=$(shell id -u) --workdir="/dashboard_devel" ${DOCKER_NAMESPACE}/dashboard-sdist python3 setup.py sdist

build:
	docker build -t ${DOCKER_NAMESPACE}/dashboard-dev -f tools/Dockerfile.dev .

build-prod: build-sdist
	docker build -t ${DOCKER_NAMESPACE}/dashboard-prod -f tools/Dockerfile.prod .

run:
	CURRENT_UID=$(shell id -u) docker-compose -f tools/docker-compose.dev.yml up --no-recreate

run-prod:
ifndef TOWERDASHBOARD_SETTINGS
	$(error TOWERDASHBOARD_SETTINGS must be defined)
endif
	CURRENT_UID=$(shell id -u) docker-compose -f tools/docker-compose.prod.yml up
