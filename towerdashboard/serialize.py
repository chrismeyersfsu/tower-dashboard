from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields
from towerdashboard.models import (
    TestRun,
    TestSuiteResult,
    TestResult,
    Filter,
    TestRunReport,
)


class TestRunSchema(SQLAlchemySchema):
    class Meta:
        model = TestRun
        load_instance = False

    id = auto_field()
    params = fields.Dict()
    created = auto_field()


class TestSuiteResultSchema(SQLAlchemySchema):
    class Meta:
        model = TestSuiteResult
        load_instance = False

    id = auto_field()
    failures = auto_field()
    name = auto_field()
    skipped = auto_field()
    tests_total = auto_field()
    duration = auto_field()
    created = auto_field()
    test_run_id = auto_field()


class TestResultSchema(SQLAlchemySchema):
    class Meta:
        model = TestResult
        load_instance = False

    id = auto_field()
    classname = auto_field()
    file = auto_field()
    line = auto_field()
    name = auto_field()
    result = auto_field()
    system_err = auto_field()
    system_out = auto_field()
    failure_msg = auto_field()
    duration = auto_field()
    created = auto_field()


class FilterSchema(SQLAlchemySchema):
    class Meta:
        model = Filter
        load_instance = False

    id = auto_field()
    name = auto_field()
    description = auto_field()
    raw = auto_field()


class TestRunReportSchema(SQLAlchemySchema):
    class Meta:
        model = TestRunReport
        load_instance = False

    id = auto_field()
    name = auto_field()
    description = auto_field()
    filter_id = auto_field()

