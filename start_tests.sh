#!/bin/bash
set +x

cd /dashboard_devel
source /venv/bin/activate
pytest -v towerdashboard/tests
