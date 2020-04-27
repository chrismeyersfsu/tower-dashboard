#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Red Hat, Inc.
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
import requests

from datetime import date, datetime
from operator import itemgetter
from flask import (
    current_app,
    json,
)
from towerdashboard import db
from towerdashboard import github
from towerdashboard.jenkins import jenkins
from towerdashboard.data import base
from towerdashboard import common
from towerdashboard.common import set_freshness

# Support old paths until we can update jenkins


@jenkins.route("/integration_tests", strict_slashes=False, methods=["POST", "GET"])
def integration_tests():
    current_app.logger.warning(
        "Sending request to /jenkins/integration_tests is DEPRECATED and will be removed in a future release"
    )
    return common.integration_tests(flask)


@jenkins.route("/sign_off_jobs", strict_slashes=False, methods=["POST", "GET"])
def sign_off_jobs():
    current_app.logger.warning(
        "Sending request to /jenkins/sign_off_jobs is DEPRECATED and will be removed in a future release"
    )
    return common.sign_off_jobs(flask)


@jenkins.route("/os-versions", strict_slashes=False, methods=["GET"])
def os_versions():
    current_app.logger.warning(
        "Sending request to /jenkins/os-versions is DEPRECATED and will be removed in a future release"
    )
    return common.os_versions(flask)


@jenkins.route("/ansible-versions", strict_slashes=False, methods=["GET"])
def ansible_versions():
    current_app.logger.warning(
        "Sending request to /jenkins/ansible-versions is DEPRECATED and will be removed in a future release"
    )
    return common.ansible_versions(flask)


@jenkins.route("/tower-versions", strict_slashes=False, methods=["GET"])
def tower_versions():
    current_app.logger.warning(
        "Sending request to /jenkins/tower-versions is DEPRECATED and will be removed in a future release"
    )
    return common.tower_versions(flask)


@jenkins.route("/results", strict_slashes=False, methods=["POST"])
def results():
    current_app.logger.warning(
        "Sending request to /jenkins/results is DEPRECATED and will be removed in a future release"
    )
    return common.results(flask)


def serialize_issues(project):
    total_count = current_app.github.get_issues_information(project)["total_count"]
    result = current_app.github.get_issues_information(
        project, "label:state:needs_test"
    )

    needs_test_issues = []
    for issue in result["items"]:
        needs_test_issues.append(
            {
                "title": issue["title"],
                "url": issue["html_url"],
                "updated_at": datetime.strptime(
                    issue["updated_at"], "%Y-%m-%dT%H:%M:%SZ"
                ).strftime("%b %-d %Y, %X"),
                "assignee": ", ".join([i["login"] for i in issue["assignees"]]),
            }
        )

    return {
        "count": total_count,
        "html_url": "https://github.com/issues?q=is:open+is:issue+project:{}".format(
            project
        ),
        "needs_test_count": len(needs_test_issues),
        "needs_test_issues": needs_test_issues,
        "needs_test_html_url": "https://github.com/issues?q=is:open+is:issue+project:{}+label:state:needs_test".format(
            project
        ),
    }


@jenkins.route("/integration_test_results", strict_slashes=False)
def integration_test_results():
    db_access = db.get_db(current_app)
    versions_query = "SELECT * FROM tower_versions"
    versions = db_access.execute(versions_query).fetchall()
    versions = db.format_fetchall(versions)
    branches = current_app.github.get_branches()

    for version in versions:
        print(version)
        if "devel" not in version["version"].lower():
            _version = version["version"].lower().replace(" ", "_")
            _res = [branch for branch in branches if branch.startswith(_version)]
            _res.sort()
            version["next_release"] = _res[-1]
            version["next_release"] = version["next_release"].replace("release_", "")
        else:
            version["next_release"] = current_app.config.get(
                "DEVEL_VERSION_NAME", "undef"
            )

    failed_on = ""
    for arg in flask.request.args:
        if arg == "failed_on":
            failed_on = flask.request.args.get(arg)
        else:
            return flask.Response(
                json.dumps({"Error": 'only able to filter on "failed on" field'}),
                status=400,
                content_type="application/json",
            )
    fetch_query = "SELECT * FROM integration_tests"
    integration_test_results = db_access.execute(fetch_query).fetchall()
    integration_test_results = db.format_fetchall(integration_test_results)
    integration_test_results = set_freshness(
        integration_test_results, "created_at", duration=1
    )
    integration_test_results = sorted(
        integration_test_results, key=lambda i: i["created_at"], reverse=True
    )

    if failed_on == "today":
        integration_test_results = [
            i for i in integration_test_results if i["freshness"] < 1
        ]

    return flask.render_template(
        "jenkins/integration_test_results.html",
        versions=versions,
        integration_test_results=integration_test_results,
    )


@jenkins.route("/releases", strict_slashes=False)
def releases():
    db_access = db.get_db(current_app)

    versions_query = "SELECT * FROM tower_versions"
    versions = db_access.execute(versions_query).fetchall()
    versions = db.format_fetchall(versions)

    results_query = 'SELECT tv.id, tv.version, av.version as "ansible", ov.version as "os", ov.description as "os_description", res.status, res.created_at as "res_created_at", res.url FROM tower_versions tv JOIN tower_os toos ON tv.id = toos.tower_id JOIN os_versions ov on toos.os_id = ov.id AND ov.version != "OpenShift" AND ov.version != "Artifacts" JOIN tower_ansible ta ON tv.id = ta.tower_id JOIN ansible_versions av ON av.id = ta.ansible_id LEFT JOIN results res ON (res.tower_id = tv.id AND res.os_id = ov.id AND res.ansible_id = av.id) ORDER BY tv.version, ov.id, av.id'
    results = db_access.execute(results_query).fetchall()
    results = db.format_fetchall(results)

    misc_query = 'SELECT tv.id, tv.version, ov.version as "os", ov.description as "os_description", res.status, res.created_at as "res_created_at", res.url FROM tower_versions tv JOIN tower_os toos ON tv.id = toos.tower_id JOIN os_versions ov on toos.os_id = ov.id AND (ov.version == "OpenShift" OR ov.version == "Artifacts") LEFT JOIN results res ON (res.tower_id = tv.id AND res.os_id = ov.id) ORDER BY tv.version, ov.id'
    misc_results = db_access.execute(misc_query).fetchall()
    misc_results = db.format_fetchall(misc_results)

    sign_off_jobs_query = "SELECT * from sign_off_jobs;"
    sign_off_jobs = db_access.execute(sign_off_jobs_query).fetchall()
    sign_off_jobs = db.format_fetchall(sign_off_jobs)

    unstable_jobs_query = 'SELECT * from sign_off_jobs WHERE status = "UNSTABLE";'
    unstable_jobs = db_access.execute(unstable_jobs_query).fetchall()
    unstable_jobs = db.format_fetchall(unstable_jobs)

    failed_jobs_query = 'SELECT * from sign_off_jobs WHERE status = "FAILURE";'
    failed_jobs = db_access.execute(failed_jobs_query).fetchall()
    failed_jobs = db.format_fetchall(failed_jobs)

    results = set_freshness(results, "res_created_at")
    sign_off_jobs = set_freshness(sign_off_jobs, "created_at")
    unstable_jobs = set_freshness(unstable_jobs, "created_at", discard_old=True)
    failed_jobs = set_freshness(failed_jobs, "created_at", discard_old=True)
    misc_results = set_freshness(misc_results, "res_created_at")

    branches = current_app.github.get_branches()

    for version in versions:
        if "devel" not in version["version"].lower():
            _version = version["version"].lower().replace(" ", "_")
            _res = [branch for branch in branches if branch.startswith(_version)]
            _res.sort()
            milestone_name = _res[-1]
            version["next_release"] = _res[-1]
            version["next_release"] = version["next_release"].replace("release_", "")
        else:
            version["next_release"] = current_app.config.get(
                "DEVEL_VERSION_NAME", "undef"
            )
            milestone_name = "release_{}".format(version["next_release"])

        version["next_release_test_plan"] = current_app.github.get_test_plan_url(
            version["next_release"]
        )
        project = current_app.github.get_project_by_name(
            "Ansible Tower {}".format(version["next_release"])
        )
        project_number = project["number"]
        if project_number:
            version["project"] = "https://github.com/orgs/ansible/projects/{}".format(
                project_number
            )
            version["issues"] = serialize_issues("ansible/{}".format(project_number))
            for issue in version["issues"]["needs_test_issues"]:
                issue["qe_or_not"] = any(
                    item.strip() in base.QE_ASSIGNEE
                    for item in issue["assignee"].split(",")
                )
            version["issues"]["needs_test_issues"].sort(key=itemgetter("qe_or_not"))

    return flask.render_template(
        "jenkins/releases.html",
        versions=versions,
        results=results,
        misc_results=misc_results,
        sign_off_jobs=sign_off_jobs,
        unstable_jobs=unstable_jobs,
        failed_jobs=failed_jobs,
    )
