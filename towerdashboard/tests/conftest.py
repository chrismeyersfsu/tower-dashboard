import tempfile
import os

import pytest

from towerdashboard.app import create_app
from towerdashboard import db

@pytest.fixture
def app():
    app = create_app()
    db_fd, app.config['SQLITE_PATH'] = tempfile.mkstemp(dir='/dashboard_data/')

    db.init_app(app)
    db.init_db(app)
    yield app

    os.close(db_fd)
    os.unlink(app.config['SQLITE_PATH'])

@pytest.fixture
def client(app):
    app.testing = True
    with app.test_client() as client:
        yield client
