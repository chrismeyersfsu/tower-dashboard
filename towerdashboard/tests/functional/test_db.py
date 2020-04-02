import pytest
import mock

from towerdashboard import db


def test_after_init(app):
    assert True == db.is_db_inited(app)

    # TODO: Maybe more assertionns about schema in DB
