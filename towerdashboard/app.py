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
from datetime import datetime

from flask_caching import Cache

from redis import Redis
from rq_scheduler import Scheduler

from towerdashboard import db
from towerdashboard.jenkins import jenkins
from towerdashboard import jobs
from towerdashboard import github


root = flask.Blueprint('root', __name__)


def start_background_scheduled_jobs(logger):
    scheduler = Scheduler(connection=Redis('redis'))
    for j in scheduler.get_jobs():
        scheduler.cancel(j)

    scheduler.schedule(scheduled_time=datetime.utcnow(),
                       func=jobs.refresh_github_branches,
                       interval=120, repeat=3, ttl=15, result_ttl=20)


def create_app(start_background_scheduled_jobs=False):

    app = flask.Flask(__name__)
    if os.environ.get('TOWERDASHBOARD_SETTINGS'):
        app.config.from_envvar('TOWERDASHBOARD_SETTINGS')
    else:
        app.config.from_object('towerdashboard.settings.settings')
    if not app.config.get('GITHUB_TOKEN'):
        raise RuntimeError('GITHUB_TOKEN setting must be specified')
    if not app.config.get('TOWERQA_REPO'):
        raise RuntimeError('TOWERQA_REPO setting must be specified')

    app.register_blueprint(root)
    app.register_blueprint(jenkins)
    db.init_app(app)

    cache = Cache(config={
        'CACHE_TYPE': 'redis',
        'CACHE_REDIS_URL': 'redis://redis:6379/6',
        'CACHE_KEY_PREFIX': 'towerdashboard',
    })

    cache.init_app(app)
    app.cache = cache
    app.github = github.GithubQuery(app.logger,
                                    cache,
                                    github_token=app.config.get('GITHUB_TOKEN'),
                                    towerqa_repo=app.config.get('TOWERQA_REPO'))

    # HACK: So that background tasks do not restart the scheduler
    if start_background_scheduled_jobs:
        start_background_scheduled_jobs(app.logger)
    return app


@root.route('/', strict_slashes=False)
def index():
    return flask.Response(
        json.dumps({'_status': 'OK', 'message': 'Tower Dasbhoard: OK'}),
        status=200,
        content_type='application/json'
    )


@root.route('/init-db', strict_slashes=False)
def init_db():
    if db.init_db():
        msg = 'Database initialized'
    else:
        msg = 'Database alaready initialized'

    return flask.Response(
        json.dumps({'_status': 'OK', 'message': msg}),
        status=200,
        content_type='application/json'
    )
