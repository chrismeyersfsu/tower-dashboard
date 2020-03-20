DOCKER_NAMESPACE ?= ansible

build-sdist:
	# HACK: move towerdashboard.egg-info because building the sdist will
	# require creating a directory with the same name.
	docker build -t ${DOCKER_NAMESPACE}/dashboard-sdist -f tools/Dockerfile.sdist .
	mv towerdashboard.egg-info towerdashboard.egg-info.bak || true
	docker run -it -v $(PWD):/dashboard_devel --user=$(shell id -u) --workdir="/dashboard_devel" ${DOCKER_NAMESPACE}/dashboard-sdist python3 setup.py sdist
	rm -rf towerdashboard.egg-info
	mv towerdashboard.egg-info.bak towerdashboard.egg-info

build:
	docker build -t ${DOCKER_NAMESPACE}/dashboard-dev -f tools/Dockerfile.dev .

build-prod: build-sdist
	docker build -t ${DOCKER_NAMESPACE}/dashboard-prod -f tools/Dockerfile.prod .

run:
	mkdir -p /tmp/dashboard_data/uwsgi
	CURRENT_UUID=$(shell id -u) TOWERDASHBOARD_SETTINGS=../settings.py docker-compose -f tools/docker-compose.dev.yml up --no-recreate

run-prod:
	TOWERDASHBOARD_SETTINGS=/etc/tower-dashboard/settings_docker.py docker-compose -f tools/docker-compose.prod.yml up

uwsgi-dev:
	/venv/bin/uwsgi -s /var/run/uwsgi/uwsgi.sock \
		--vacuum --processes=5 --harakiri=120 --no-orphans --master \
		--max-requests=1000 --lazy-apps -b 32768 --chmod-socket=666 --virtualenv=/venv/ \
		--mount="/dashboard_devel=towerdashboard.app:create_app()" --py-autoreload=1
