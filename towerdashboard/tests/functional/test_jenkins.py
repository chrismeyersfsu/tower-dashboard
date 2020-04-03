class TestJenkinsEndpoints:
    def test_ansible_versions(self, client):
        resp = client.get("/jenkins/ansible-versions").get_json()
        versions = [v["version"] for v in resp]
        assert "devel" in versions
        assert "stable-2.9" in versions
        assert "stable-2.8" in versions
        assert "stable-2.7" in versions

    def test_os_versions(self, client):
        resp = client.get("/jenkins/os-versions").get_json()
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
