import json

from datetime import date, datetime
from towerdashboard import db


def form_tower_query(tower):
    if "devel" == tower:
        return 'SELECT id FROM tower_versions WHERE code = "devel"'
    else:
        return 'SELECT id FROM tower_versions WHERE code = "%s"' % tower[0:3]


def set_freshness(items, key, duration=2, discard_old=False):
    for item in items:
        if item.get(key):
            if type(item[key]) is date:
                delta = date.today() - item[key]
            else:
                delta = datetime.now() - datetime.strptime(
                    item[key], "%Y-%m-%d %H:%M:%S"
                )
            item["freshness"] = delta.days
    if discard_old:
        items = [x for x in items if x["freshness"] < duration]

    return items


def check_payload(payload, required_keys):
    missing_keys = []
    for key in required_keys:
        if key not in payload:
            missing_keys.append(key)
    if missing_keys:
        return flask.Response(
            json.dumps(
                {
                    "Error": "Missing required keys/value pairs for {}".format(
                        missing_keys
                    )
                }
            ),
            status=400,
            content_type="application/json",
        )


def integration_tests(flask):
    if flask.request.method == "GET":
        db_access = db.get_db(flask.current_app)
        tower_query = ""
        failed_on = "2000-01-01"
        for arg in flask.request.args:
            if arg == "failed_on":
                failed_on = flask.request.args.get(arg)
                try:
                    failed_on = str(datetime.strptime(failed_on, "%Y-%m-%d").date())
                except ValueError:
                    return flask.Response(
                        json.dumps(
                            {"Error": "Failed on should be a string like 2020-01-01"}
                        ),
                        status=400,
                        content_type="application/json",
                    )
            if arg == "tower":
                tower_query = form_tower_query(flask.request.args.get(arg))
            if arg not in ["failed_on", "tower"]:
                return flask.Response(
                    json.dumps(
                        {"Error": 'only able to filter on "failed on" or "tower" field'}
                    ),
                    status=400,
                    content_type="application/json",
                )
        if tower_query:
            fetch_query = (
                'SELECT * FROM integration_tests WHERE tower_id = (%s) AND created_at >= date("%s")'
                % (tower_query, failed_on)
            )
        else:
            fetch_query = (
                'SELECT * FROM integration_tests WHERE created_at >= date("%s")'
                % (failed_on)
            )
        print(fetch_query)
        test_results = db_access.execute(fetch_query).fetchall()
        test_results = db.format_fetchall(test_results)
        return flask.Response(
            json.dumps(test_results, default=str),
            status=200,
            content_type="application/json",
        )
    else:
        payload = flask.request.json
        required_keys = [
            "name",
            "tower",
            "deploy",
            "platform",
            "bundle",
            "tls",
            "fips",
            "ansible",
            "status",
            "url",
        ]
        check_payload(payload, required_keys)
        tower_query = form_tower_query(payload["tower"])
        tests = payload["name"]
        for test in tests:
            condition = (
                'test_name = "%s" AND tower_id = (%s) AND deploy = "%s" AND platform = "%s" AND'
                ' tls = "%s" AND fips = "%s" AND bundle = "%s" AND ansible = "%s"'
                % (
                    test,
                    tower_query,
                    payload["deploy"],
                    payload["platform"],
                    payload["tls"],
                    payload["fips"],
                    payload["bundle"],
                    payload["ansible"],
                )
            )
            job_query = "SELECT * FROM integration_tests WHERE %s" % (condition)
            db_access = db.get_db(flask.current_app)
            existing = db_access.execute(job_query).fetchall()
            existing = db.format_fetchall(existing)
            if existing:
                failing_since_query = (
                    "SELECT failing_since FROM integration_tests WHERE %s" % (condition)
                )
                failing_since = db_access.execute(failing_since_query).fetchall()
                failing_since = db.format_fetchall(failing_since)
                failing_since = failing_since[0]["failing_since"]
                delete_query = "DELETE FROM integration_tests WHERE  %s" % (condition)
                db_access.execute(delete_query)
            else:
                failing_since = date.today()
            insert_query = (
                "INSERT INTO integration_tests (test_name, tower_id, deploy, "
                "platform, bundle, tls, fips, ansible, status, url, failing_since) "
                'VALUES ("%s", (%s), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s")'
                % (
                    test,
                    tower_query,
                    payload["deploy"],
                    payload["platform"],
                    payload["bundle"],
                    payload["tls"],
                    payload["fips"],
                    payload["ansible"],
                    payload["status"],
                    payload["url"],
                    failing_since,
                )
            )
            db_access.execute(insert_query)
            db_access.commit()

        return flask.Response(
            json.dumps({"Inserted": "ok"}), status=201, content_type="application/json"
        )


def sign_off_jobs(flask):
    if flask.request.method == "GET":
        tower_query = ""
        for arg in flask.request.args:
            if arg == "tower":
                tower_query = form_tower_query(flask.request.args.get(arg))
            else:
                return flask.Response(
                    json.dumps({"Error": "only able to filter on tower versions"}),
                    status=400,
                    content_type="application/json",
                )
        if tower_query:
            job_query = "SELECT * FROM sign_off_jobs WHERE tower_id = (%s)" % (
                tower_query
            )
        else:
            job_query = "SELECT * FROM sign_off_jobs"

        db_access = db.get_db(flask.current_app)
        res = db_access.execute(job_query).fetchall()
        sign_off_jobs = db.format_fetchall(res)

        return flask.Response(
            json.dumps(sign_off_jobs), status=200, content_type="application/json"
        )
    else:
        payload = flask.request.json
        required_keys = [
            "tower",
            "component",
            "deploy",
            "platform",
            "tls",
            "fips",
            "bundle",
            "ansible",
            "url",
            "status",
        ]

        check_payload(payload, required_keys)
        tower_query = form_tower_query(payload["tower"])
        condition = (
            'tower_id = (%s) AND component = "%s" AND deploy = "%s" AND platform = "%s" AND'
            ' tls = "%s" AND fips = "%s" AND bundle = "%s" AND ansible = "%s"'
            % (
                tower_query,
                payload["component"],
                payload["deploy"],
                payload["platform"],
                payload["tls"],
                payload["fips"],
                payload["bundle"],
                payload["ansible"],
            )
        )
        job_query = "SELECT id FROM sign_off_jobs WHERE %s" % (condition)

        db_access = db.get_db(flask.current_app)
        existing = db_access.execute(job_query).fetchall()
        existing = db.format_fetchall(existing)
        if existing:
            _update_query = (
                'UPDATE sign_off_jobs SET status = "%s", url = "%s", created_at = "%s" WHERE id = (%s)'
                % (payload["status"], payload["url"], datetime.now(), job_query)
            )
            db_access.execute(_update_query)
            return_info_query = (
                "SELECT display_name, created_at FROM sign_off_jobs WHERE id = (%s)"
                % (job_query)
            )
            res = db_access.execute(return_info_query).fetchall()
            updated_job = db.format_fetchall(res)
        else:
            job = "component_{}_platform_{}_deploy_{}_tls_{}_fips_{}_bundle_{}_ansible_{}".format(
                payload["component"],
                payload["platform"],
                payload["deploy"],
                payload["tls"],
                payload["fips"],
                payload["bundle"],
                payload["ansible"],
            )
            tls_statement = "(TLS Enabled)" if payload["tls"] == "yes" else ""
            fips_statement = "(FIPS Enabled)" if payload["fips"] == "yes" else ""
            bundle_statement = (
                "(Bundle installer)" if payload["bundle"] == "yes" else ""
            )
            display_name = "{} {} {} {} {} {} w/ ansible {}".format(
                payload["platform"],
                payload["deploy"],
                payload["component"].replace("_", " "),
                tls_statement,
                fips_statement,
                bundle_statement,
                payload["ansible"],
            )
            display_name = display_name.title()
            insert_query = (
                "INSERT INTO sign_off_jobs (tower_id, job, display_name, component, platform, deploy, "
                'tls, fips, bundle, ansible, status, url) VALUES ((%s), "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s", "%s");\n'
                % (
                    tower_query,
                    job,
                    display_name,
                    payload["component"],
                    payload["platform"],
                    payload["deploy"],
                    payload["tls"],
                    payload["fips"],
                    payload["bundle"],
                    payload["ansible"],
                    payload["status"],
                    payload["url"],
                )
            )
            db_access.execute(insert_query)
        db_access.commit()

        if existing:
            return flask.Response(
                json.dumps({"OK": "Updated"}),
                status=200,
                content_type="application/json",
            )
        else:
            return flask.Response(
                json.dumps({"OK": "Inserted"}),
                status=200,
                content_type="application/json",
            )


def tower_versions(flask):
    db_access = db.get_db(flask.current_app)

    versions = db_access.execute("SELECT * FROM tower_versions").fetchall()
    versions = db.format_fetchall(versions)

    return flask.Response(
        json.dumps(versions), status=200, content_type="application/json"
    )


def ansible_versions(flask):
    db_access = db.get_db(flask.current_app)

    versions = db_access.execute("SELECT * FROM ansible_versions").fetchall()
    versions = db.format_fetchall(versions)

    return flask.Response(
        json.dumps(versions), status=200, content_type="application/json"
    )


def os_versions(flask):
    db_access = db.get_db(flask.current_app)

    versions = db_access.execute("SELECT * FROM os_versions").fetchall()
    versions = db.format_fetchall(versions)

    return flask.Response(
        json.dumps(versions), status=200, content_type="application/json"
    )
