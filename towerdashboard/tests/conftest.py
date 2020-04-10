import tempfile
import os

import pytest
import sqlite3

from towerdashboard.app import create_app
from towerdashboard.app import db
from towerdashboard import raw_db


@pytest.fixture
def app():
    app = create_app()
    db_fd, app.config["SQLITE_PATH"] = tempfile.mkstemp()
    db_fd_raw, db_raw_path = tempfile.mkstemp()

    db.init_app(app)
    raw_db.init_app(app)
    raw_db.init_db(app)
    yield app

    os.close(db_fd)
    os.unlink(app.config["SQLITE_PATH"])

    os.close(db_fd_raw)
    os.unlink(db_raw_path)


@pytest.fixture
def client(app):
    app.testing = True
    with app.test_client() as client:
        yield client
