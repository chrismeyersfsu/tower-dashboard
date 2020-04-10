import datetime

from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.types import PickleType
from sqlalchemy.ext.declarative import declarative_base

from towerdashboard.app import db


HybridType = PickleType() # sqlite
HybridType = HybridType.with_variant(HSTORE(), 'postgresql')

BigInt = db.Integer() # sqlite
BigInt = BigInt.with_variant(db.BigInteger(), 'postgresql')


class TestRun(db.Model):
    __tablename__ = 'test_run'

    id = db.Column(BigInt, primary_key=True)
    params = db.Column(HybridType)

    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    test_suites = db.relationship('TestSuiteResult', backref='test_run',
                                  cascade="all, delete-orphan", lazy="dynamic")
    test_results = db.relationship('TestResult', backref='test_run',
                                   cascade="all, delete-orphan", lazy="dynamic")

    @classmethod
    def search_params(cls, terms):
        term_keys = set(terms.keys())
        results = set()

        for obj in TestRun.query.all():
            if not term_keys.issubset(obj.params.keys()):
                continue

            found_all = True
            for k, v in terms.items():
                vs = v if isinstance(v, list) else [v]
                found = False
                for v in vs:
                    if obj.params[k] == v:
                        found = True
                        break
                if not found:
                    found_all = False
            if found_all:
                results.add(obj)
        return results


class TestSuiteResult(db.Model):
    __tablename__ = 'test_suite_result'

    id = db.Column(BigInt, primary_key=True)
    failures = db.Column(db.Integer)
    name = db.Column(db.String(1024))
    skipped = db.Column(db.Integer)
    tests_total = db.Column(db.Integer)
    duration = db.Column(db.Integer)

    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    test_run_id = db.Column(BigInt,
                            db.ForeignKey(TestRun.id,
                                          ondelete="CASCADE"),
                            nullable=False)

    test_results = db.relationship('TestResult', backref='test_suite',
                                   cascade="all, delete-orphan", lazy="dynamic")


class TestResult(db.Model):
    __tablename__ = 'test_result'

    id = db.Column(BigInt, primary_key=True)
    classname = db.Column(db.String(1024))
    file = db.Column(db.String(1024))
    line = db.Column(db.Integer)
    name = db.Column(db.String(1024))
    result = db.Column(db.String(64))
    system_err = db.Column(db.VARCHAR)
    system_out = db.Column(db.VARCHAR)
    failure_msg = db.Column(db.VARCHAR)
    duration = db.Column(db.Integer)

    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    test_suite_id = db.Column(BigInt,
                              db.ForeignKey(TestSuiteResult.id),
                              nullable=False)
    test_run_id = db.Column(BigInt,
                            db.ForeignKey(TestRun.id),
                            nullable=False)


class Filter(db.Model):
    id = db.Column(BigInt, primary_key=True)
    name = db.Column(db.String(1024))
    description = db.Column(db.String(1024))
    raw = db.Column(db.String(4096))
    test_run_reports = db.relationship('TestRunReport', backref='filter',
                                       lazy="dynamic")


class TestRunReport(db.Model):
    __table_name__ = 'test_run_report'

    id = db.Column(BigInt, primary_key=True)
    name = db.Column(db.String(1024))
    description = db.Column(db.String(1024))
    filter_id = db.Column(BigInt,
                          db.ForeignKey(Filter.id),
                          nullable=True)

