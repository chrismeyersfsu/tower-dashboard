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
import sqlite3

from flask import (
    current_app,
    json,
)

import redis
from redis import Redis

from flask_caching import Cache

from flask_sqlalchemy import SQLAlchemy

from sqlalchemy.ext.declarative import declarative_base

from towerdashboard.raw_db import is_db_inited
from towerdashboard import (
    github,
)


root = flask.Blueprint('root', __name__)
db = SQLAlchemy()


def create_app():
    # Prevent circular import
    from towerdashboard.api import api # noqa
    from towerdashboard.commands import dashboard as dashboard_commands # noqa
    from towerdashboard.jenkins import jenkins # noqa
    from towerdashboard.experiment import experiment # noqa
    from towerdashboard import raw_db

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

    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////dashboard_data/towerdashboard.sqlite'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    raw_db.init_app(app)

    app.register_blueprint(root, cli_group=None)
    app.register_blueprint(jenkins)
    app.register_blueprint(api)
    app.register_blueprint(experiment)

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
    # FLASK_APP="app.py:app" flask dashboard <command>
    with app.app_context():
        app.cli.add_command(dashboard_commands.cmds)
    return app


def is_db_inited(db):
    engine = db.get_engine()
    res = engine.dialect.has_table(engine.connect(), "test_run")
    return res


@root.route('/', strict_slashes=False)
def index():
    return json.jsonify({"_status": "OK", "message": "Tower Dashboard: OK"})


@root.route("/api/health", strict_slashes=False)
def health():
    status = {
        "database": {"online": True, "inited": is_db_inited(db),},
        "redis": {"online": False,},
    }
    try:
        r = Redis("redis", socket_connect_timeout=1)
        r.ping()
        status["redis"]["online"] = True
    except redis.exceptions.ConnectionError:
        status["redis"]["online"] = False

    return json.jsonify(status)
