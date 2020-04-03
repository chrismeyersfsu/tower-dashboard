import pytest


class TestApiEndpoints:
    @pytest.mark.parametrize(
        "endpoint", ["/api/ansible_versions/", "/jenkins/ansible-versions/"]
    )
    def test_ansible_versions(self, client, endpoint):
        resp = client.get(endpoint).get_json()
        versions = [v["version"] for v in resp]
        assert "devel" in versions
        assert "stable-2.9" in versions
        assert "stable-2.8" in versions
        assert "stable-2.7" in versions

    @pytest.mark.parametrize("endpoint", ["/api/os_versions/", "/jenkins/os-versions/"])
    def test_os_versions(self, client, endpoint):
        resp = client.get(endpoint).get_json()
        oses = [(v["family"], v["description"], v["version"]) for v in resp]
        assert ("RHEL", "RHEL 7.4", "rhel-7.4-x86_64") in oses
        assert ("RHEL", "RHEL 7.5", "rhel-7.5-x86_64") in oses
        assert ("RHEL", "RHEL 7.6", "rhel-7.6-x86_64") in oses
        assert ("RHEL", "RHEL 7.7", "rhel-7.7-x86_64") in oses
        assert ("RHEL", "RHEL 8.0", "rhel-8.0-x86_64") in oses
        assert ("RHEL", "RHEL 8.1", "rhel-8.1-x86_64") in oses
        assert ("RHEL", "CentOS Latest", "centos-7.latest-x86_64") in oses
        assert ("misc", "OpenShift", "OpenShift") in oses
        assert ("misc", "Artifacts", "Artifacts") in oses

    @pytest.mark.parametrize(
        "endpoint", ["/api/sign_off_jobs/", "/jenkins/sign_off_jobs/"]
    )
    def test_sign_off_jobs_invalid(self, client, endpoint):
        resp = client.post(
            endpoint, json={"bad": "key"}, content_type="application/json"
        )
        assert resp.status_code == 400
        for item in ["tower", "deploy", "bundle", "tls", "fips", "status", "url"]:
            assert item in str(resp.data)

    @pytest.mark.parametrize(
        "endpoint", ["/api/sign_off_jobs/", "/jenkins/sign_off_jobs/"]
    )
    def test_sign_off_jobs_valid(self, client, endpoint):
        resp = client.post(
            endpoint,
            json={
                "tower": "devel",
                "url": "https://your.job.runner.com/job/1",
                "component": "install",
                "status": "FAILURE",
                "tls": "yes",
                "fips": "no",
                "bundle": "no",
                "deploy": "standalone",
                "platform": "rhel-7.7-x86_64",
                "ansible": "devel",
            },
            content_type="application/json",
        )
        assert resp.status_code == 200
        resp = client.get("/api/sign_off_jobs/").get_json()
        jobs = " ".join([j["job"] for j in resp])
        assert (
            "component_install_platform_rhel-7.7-x86_64_deploy_standalone_tls_yes_fips_no_bundle_no_ansible_devel"
            in jobs
        )

    @pytest.mark.parametrize(
        "endpoint", ["/api/integration_tests/", "/jenkins/integration_tests/"]
    )
    def test_integration_tests_invalid(self, client, endpoint):
        resp = client.post(
            endpoint, json={"ansible": "devel"}, content_type="application/json",
        )
        assert resp.status_code == 400
        for item in [
            "name",
            "tower",
            "deploy",
            "bundle",
            "tls",
            "fips",
            "status",
            "url",
        ]:
            assert item in str(resp.data)

    @pytest.mark.parametrize(
        "endpoint", ["/api/integration_tests/", "/jenkins/integration_tests/"]
    )
    def test_integration_tests_valid(self, client, endpoint):
        resp = client.post(
            endpoint,
            json={
                "name": "test_name",
                "tower": "devel",
                "url": "https://your.job.runner.com/job/1",
                "status": "FAILURE",
                "tls": "yes",
                "fips": "no",
                "bundle": "no",
                "deploy": "standalone",
                "platform": "rhel-7.7-x86_64",
                "ansible": "devel",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201

    @pytest.mark.parametrize(
        "endpoint", ["/api/pipeline_results/", "/jenkins/results/"]
    )
    def test_pipeline_results_valid(self, client, endpoint):
        resp = client.post(
            endpoint,
            json={
                "name": "test_name",
                "tower": "devel",
                "os": "rhel-7.7-x86_64",
                "url": "https://your.job.runner.com/job/1",
                "status": "FAILURE",
                "ansible": "devel",
            },
            content_type="application/json",
        )
        assert resp.status_code == 201
