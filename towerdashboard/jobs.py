#!/bin/env python3

import json

from towerdashboard import app as APP
from towerdashboard import db


def refresh_github_branches():
    print("Running refresh_github_branches()")
    app = APP.create_app()
    app.cache.delete_memoized(app.github.get_branches)
    app.cache.delete_memoized(app.github.get_test_plan_url)
    app.cache.delete_memoized(app.github.get_project_by_name)
    app.cache.delete_memoized(app.github.get_issues_information)

    branches = app.github.get_branches()

    db_access = db.get_db(app)
    versions_query = "SELECT * FROM tower_versions"
    versions = db_access.execute(versions_query).fetchall()
    versions = db.format_fetchall(versions)
    for version in versions:
        if "devel" not in version["version"].lower():
            _version = version["version"].lower().replace(" ", "_")
            _res = [branch for branch in branches if branch.startswith(_version)]
            _res.sort()
            milestone_name = _res[-1]
            version["next_release"] = _res[-1]
            version["next_release"] = version["next_release"].replace("release_", "")
        else:
            version["next_release"] = app.config.get("DEVEL_VERSION_NAME", "undef")
            milestone_name = "release_{}".format(version["next_release"])

        app.github.get_test_plan_url(version["next_release"])
        project_number = app.github.get_project_by_name(
            "Ansible Tower {}".format(version["next_release"])
        )["number"]
        if project_number:
            project = f"ansible/{project_number}"
            app.github.get_issues_information(project)
            app.github.get_issues_information(project, "label:state:needs_test")
