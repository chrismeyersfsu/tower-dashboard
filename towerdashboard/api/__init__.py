#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018 Red Hat, Inc.
#
# Licensed under the Apache License, Version 2.0 (the 'License'); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import flask
import json
import requests

from datetime import date, datetime
from flask import current_app
from towerdashboard import db
from towerdashboard import github
from towerdashboard import common
from towerdashboard.common import set_freshness


api = flask.Blueprint("api", __name__, url_prefix="/api")


@api.route("/", strict_slashes=False)
def index():
    return flask.Response(
        json.dumps({"_status": "OK", "message": "Tower Dashboard: API."}),
        status=200,
        content_type="application/json",
    )


@api.route("/ansible_versions", strict_slashes=False)
def ansible_versions():
    return common.ansible_versions(flask)


@api.route("/os_versions", strict_slashes=False)
def os_versions():
    return common.os_versions(flask)


@api.route("/tower_versions", strict_slashes=False)
def tower_versions():
    return common.tower_versions(flask)


@api.route("/sign_off_jobs", strict_slashes=False, methods=["POST", "GET"])
def sign_off_jobs():
    return common.sign_off_jobs(flask)


@api.route("/integration_tests", strict_slashes=False, methods=["POST", "GET"])
def integration_tests():
    return common.integration_tests(flask)


@api.route("/pipeline_results", strict_slashes=False, methods=["POST"])
def results():
    return common.results(flask)
