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
import os
import logging
from datetime import datetime

from flask import (
    current_app,
    json,
)

import redis
from redis import Redis

from flask_caching import Cache

from towerdashboard.jenkins import jenkins
from towerdashboard.api import api
from towerdashboard.commands import dashboard as dashboard_commands
from towerdashboard import (
    db,
    jobs,
    github,
)


root = flask.Blueprint("root", __name__)


def create_app():

    app = flask.Flask(__name__)
    app.logger.setLevel(logging.INFO)
    if os.environ.get("TOWERDASHBOARD_SETTINGS"):
        app.config.from_envvar("TOWERDASHBOARD_SETTINGS")
    else:
        app.config.from_object("towerdashboard.settings.settings")
    if not app.config.get("GITHUB_TOKEN"):
        raise RuntimeError("GITHUB_TOKEN setting must be specified")
    if not app.config.get("TOWERQA_REPO"):
        raise RuntimeError("TOWERQA_REPO setting must be specified")

    app.register_blueprint(root, cli_group=None)
    app.register_blueprint(jenkins)
    app.register_blueprint(api)
    db.init_app(app)

    cache = Cache(
        config={
            "CACHE_TYPE": "redis",
            "CACHE_REDIS_URL": "redis://redis:6379/6",
            "CACHE_KEY_PREFIX": "towerdashboard",
        }
    )

    cache.init_app(app)
    app.cache = cache
    app.github = github.GithubQuery(
        app.logger,
        cache,
        github_token=app.config.get("GITHUB_TOKEN"),
        towerqa_repo=app.config.get("TOWERQA_REPO"),
    )

    # Command line commands
    # FLASK_APP="app.py:create_app()" flask dashboard <command>
    app.cli.add_command(dashboard_commands.cmds)
    return app


@root.route("/", strict_slashes=False)
def index():
    return json.jsonify({"_status": "OK", "message": "Tower Dashboard: OK"})


@root.route("/api/health", strict_slashes=False)
def health():
    status = {
        "database": {"online": True, "inited": db.is_db_inited(current_app),},
        "redis": {"online": False,},
    }
    try:
        r = Redis("redis", socket_connect_timeout=1)
        r.ping()
        status["redis"]["online"] = True
    except redis.exceptions.ConnectionError:
        status["redis"]["online"] = False

    return json.jsonify(status)
