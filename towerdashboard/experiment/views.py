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

import io
import flask
import os
import uuid
from datetime import date, datetime
from urllib.parse import parse_qs

from flask import (
    current_app,
    json,
)

from towerdashboard.app import db
from towerdashboard import github
from towerdashboard.jenkins import jenkins
from towerdashboard.data import base
from towerdashboard import common
from towerdashboard.common import set_freshness
from towerdashboard.models import (
    TestRun,
    TestResult,
    TestSuiteResult,
    Filter,
    TestRunReport,
)
from towerdashboard.serialize import (
    TestRunSchema,
    TestSuiteResultSchema,
    TestResultSchema,
    FilterSchema,
    TestRunReportSchema,
)

from junitparser import JUnitXml, Element, TestCase, Attr
from junitparser.junitparser import Skipped, Failure, Error

# parse junit xml from str instead of file
try:
    from lxml import etree
except ImportError:
    from xml.etree import ElementTree as etree
# Support old paths until we can update jenkins

from typing import List, Set, Dict, Tuple, Optional

from . import experiment


test_run_schema = TestRunSchema()
filter_schema = FilterSchema()
test_run_report_schema = TestRunReportSchema()


@experiment.route('/filters', methods=['GET'], strict_slashes=False)
def list_filter():
    filters = Filter.query.all()
    resp = {'results': [filter_schema.dump(r) for r in filters]}
    resp['count'] = len(resp['results'])
    return json.jsonify(resp)


@experiment.route('/filters/<id>', methods=['GET'], strict_slashes=False)
def get_filter():
    filter_obj = Filter.query.filter_by(id=id).first()
    return json.jsonify(filter_schema.dump(filter_obj))


@experiment.route('/filters/', methods=['POST'], strict_slashes=False)
def create_filter():
    deserialized_filter = filter_schema.load(flask.request.get_json())
    filter_obj = Filter(**deserialized_filter)
    db.session.add(filter_obj)
    db.session.commit()
    return json.jsonify(filter_schema.dump(filter_obj)), 201


@experiment.route('/filters/<id>', methods=['PATCH'], strict_slashes=False)
def patch_filter():
    deserialized_filter = filter_schema.load(flask.request.get_json())

    Filter.query.filter_by(id=id).update(deserialized_filter)
    db.session.commit()
    filter = Filter.query.filter_by(id=id).first()
    return json.jsonify(filter_schema.dump(filter)), 200


@experiment.route('/filters/<id>', methods=['DELETE'], strict_slashes=False)
def delete_filter():
    Filter.query.filter_by(id=id).first().delete()
    return '', 204


@experiment.route('/test_run_reports', methods=['GET'], strict_slashes=False)
def list_test_run_reports():
    reports = TestRunReport.query.all()
    resp = {'results': [test_run_report_schema.dump(r) for r in reports]}
    resp['count'] = len(resp['results'])
    return json.jsonify(resp)


@experiment.route('/test_run_reports/<id>', methods=['GET'], strict_slashes=False)
def get_test_run_report(id):
    report = TestRunReport.query.filter_by(id=id).first()

    search = parse_qs(report.filter.raw)
    test_runs = TestRun.search_params(search)

    resp = test_run_report_schema.dump(report)
    resp['test_runs'] = [test_run_schema.dump(tr) for tr in test_runs]
    return json.jsonify(resp)


@experiment.route('/test_run_reports', methods=['POST'], strict_slashes=False)
def create_test_run_report():
    deserialized_report = test_run_report_schema.load(flask.request.get_json())
    report = TestRunReport(**deserialized_report)
    db.session.add(report)
    db.session.commit()
    return json.jsonify(test_run_report_schema.dump(report)), 201


@experiment.route('/test_run_reports/<id>', methods=['PATCH'], strict_slashes=False)
def patch_test_run_report(id):
    deserialized_report = test_report_schema.load(flask.request.get_json())

    TestRunReport.query.filter_by(id=id).update(deserialized_report)
    db.session.commit()
    report = TestRunReport.query.filter_by(id=id).first()
    return json.jsonify(report_schema.dump(report)), 200


@experiment.route('/test_run_reports/<id>', methods=['DELETE'], strict_slashes=False)
def delete_report(id):
    TestRunReport.query.filter_by(id=id).first().delete()
    return '', 204


@jenkins.route('/import', methods=['POST'], strict_slashes=False)
def import_results():
    payload = flask.request.get_json()
    run_data = payload['run']
    # TODO: Verify data exists
    xml = JUnitXml.fromfile(io.StringIO(payload['data']))
    ts = datetime.utcnow()

    run_dict = {}

    class TestCaseBase(TestCase):
        file = Attr()
        line = Attr()

    def build_dict_out_of_properties(suite: Element, properties: List[str]):
        return {p: getattr(suite, p, None) for p in properties}

    suites = xml
    run_dict['params'] = run_data['params']

    test_run = TestRun(params=run_data['params'])
    db.session.add(test_run)
    db.session.flush()

    test_cases = []
    for suite in suites:
        suite_dict = build_dict_out_of_properties(suites, ['name', 'skipped', 'time', 'failures', 'tests'])


        for case in suite:
            test_suite = TestSuiteResult(name=suite_dict['name'],
                                         skipped=int(suite_dict['skipped']),
                                         duration=int(suite_dict['time']),
                                         failures=int(suite_dict['failures']),
                                         tests_total=int(suite_dict['tests']))
            test_run.test_suites.append(test_suite)
            db.session.add(test_suite)

            case = TestCaseBase.fromelem(case)
            case_dict = build_dict_out_of_properties(case, ['classname', 'file', 'line', 'name', 'time', 'system_err', 'system_out'])
            case_dict['failure_message'] = ''
            case_dict['result'] = 'unknown'
            case_dict['line'] = case_dict['line'] or -1
            if type(case.result) is Skipped:
                case_dict['result'] = 'skipped'
                case_dict['skipped_message'] = case.result.message
            elif type(case.result) is Failure:
                case_dict['result'] = 'failure'
                case_dict['failure_message'] = case.result.message
            elif type(case.result) is Error:
                case_dict['result'] = 'error'
                case_dict['failure_message'] = case.result.message

            test_cases.append(case_dict)
            test_result = TestResult(name=case_dict['name'],
                                     classname=case_dict['classname'],
                                     file=case_dict['file'],
                                     line=int(case_dict['line']),
                                     result=case_dict['result'],
                                     failure_msg=case_dict['failure_message'],
                                     system_err=case_dict['system_err'],
                                     system_out=case_dict['system_out'],
                                     duration=int(case_dict['time']))
            test_run.test_results.append(test_result)
            test_suite.test_results.append(test_result)
            db.session.add(test_result)

    db.session.commit()
    test_suite_schema = TestSuiteResultSchema()
    test_result_schema = TestResultSchema()
    return json.dumps({'test_run': TestRunSchema().dump(test_run),
                       'test_suites': [test_suite_schema.dump(suite) for suite in test_run.test_suites],
                       'test_results': [test_result_schema.dump(test) for test in test_run.test_results]})
