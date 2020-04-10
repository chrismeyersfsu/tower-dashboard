import json
import os
import jenkins
import time
import click
from datetime import datetime
from requests import Request
import requests

import redis
from redis import Redis

from flask import current_app
from flask.cli import AppGroup

from rq_scheduler import Scheduler

from towerdashboard import app as APP
from towerdashboard.models import(
    TestRun,
)
from towerdashboard.app import db


cmds = AppGroup("dashboard")


def wait_for(func, retries=60):
    count = 0
    while True:
        res = func()
        if res:
            return True
        if count < retries:
            count += 1
            time.sleep(1)
        else:
            break
    return False


@cmds.command("wait_for_services")
def wait_for_services():
    def get_services_health():
        try:
            res = requests.get("http://web/api/health")
            if res.status_code != 200:
                return False
            health = res.json()
            return health["database"]["online"] and health["redis"]["online"]
        except requests.exceptions.ConnectionError as e:
            current_app.logger.warn(f"Failed to get health {e}")
            return False

    return wait_for(get_services_health)


@cmds.command("wait_for_redis")
def wait_for_redis():
    def get_health():
        try:
            res = requests.get("http://web/api/health")
            if res.status_code != 200:
                return False
            health = res.json()
            return health["redis"]["online"]
        except requests.exceptions.ConnectionError as e:
            current_app.logger.warn(f"Failed to get health {e}")
            return False

    return wait_for(get_health)


@cmds.command("reset_db")
def reset_db():
    db.drop_all()
    init_db()


@cmds.command("init_db")
def init_db():
    db.create_all()
    db.session.commit()
    res = True
    if res:
        current_app.logger.info("Initialized Database")
    else:
        current_app.logger.info("Database already initialized")

@cmds.command("init_query")
def init_query():
    request.post('http://web/experiment/query', data={})

@cmds.command("create_schedules")
def create_schedules():
    scheduler = Scheduler(connection=Redis('redis'))
    for j in scheduler.get_jobs():
        scheduler.cancel(j)

    '''
    scheduler.schedule(scheduled_time=datetime.utcnow(),
                       func=crawl_jenkins_jobs,
                       interval=120, repeat=None, result_ttl=120)
    '''

