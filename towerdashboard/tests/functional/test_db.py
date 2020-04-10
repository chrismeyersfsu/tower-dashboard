import pytest
import mock

from towerdashboard.raw_db import is_db_inited


def test_after_init(app):
    assert True == is_db_inited(app)

    # TODO: Maybe more assertionns about schema in DB
