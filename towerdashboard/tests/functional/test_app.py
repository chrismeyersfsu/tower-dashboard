import pytest


from towerdashboard import app as app_module

def test_create_app(app):
    assert app.cache
    assert app.github
    assert app.cli
    assert app.db


class TestRootEndpoints():
    def test_endpoint_root(self, client):
        resp = client.get('/').get_json()
        assert 'OK' == resp['_status']
        assert 'Tower Dashboard: OK' == resp['message']


    def test_health(self, client):
        resp = client.get('/api/health').get_json()
        assert True == resp['database']['online']
        assert True == resp['database']['inited']

