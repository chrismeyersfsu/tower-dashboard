#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2019 Red Hat, Inc.
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


import requests

API_GITHUB = "https://api.github.com"


def markcache(func, *args, **kwargs):
    setattr(func, "__markcache", True)
    return func


class GithubQuery:
    def __init__(self, logger, cache, github_token=None, towerqa_repo=None):
        if not github_token:
            raise ValueError("github_token required")
        if not towerqa_repo:
            raise ValueError("towerqa_repo required")

        self.logger = logger
        self.cache = cache
        self.github_token = github_token
        self.towerqa_repo = towerqa_repo

        # cache all functions
        for attr, value in self.__class__.__dict__.items():
            if callable(value) and hasattr(value, "__markcache"):
                setattr(self, attr, cache.memoize(timeout=360)(getattr(self, attr)))

    def get_cache_functions(self):
        funcs = []
        for attr, value in self.__class__.__dict__.items():
            if callable(value) and hasattr(value, "__markcache"):
                funcs.append(getattr(self, attr))
        return funcs

    def github_request(self, url):
        res = requests.get(
            url,
            headers={
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.inertia-preview+json",
            },
        )
        if res.status_code != 200:
            self.logger.warn(
                f"github request returned {res.status_code} for url {url} and reason {res.content}"
            )
            if res.status_code == 403:
                raise RuntimeError("Rate limit exceeded")

        return res

    @markcache
    def get_project_by_name(self, name):
        url = f"{API_GITHUB}/orgs/ansible/projects"
        projects = self.github_request(url).json()
        projects = [proj for proj in projects if proj["name"] == name]
        if projects:
            return projects[0]
        else:
            return {"name": name, "number": None}

    @markcache
    def get_branches(self):
        url = f"{API_GITHUB}/repos/{self.towerqa_repo}/branches"
        response = self.github_request(url)
        # example of github response.link
        # {'next': {'url': 'https://api.github.com/repositories/12570480/branches?page=2',
        # 'rel': 'next'},
        # 'last': {'url': 'https://api.github.com/repositories/12570480/branches?page=2',
        # 'rel': 'last'}}
        branches = response.json()
        while "next" in response.links:
            response = self.github_request(response.links["next"]["url"])
            branches.extend(response.json())
        return [branch["name"] for branch in branches]

    @markcache
    def get_test_plan_url(self, version):
        url = f"{API_GITHUB}/repos/{self.towerqa_repo}/contents/docs/test_plans/release_validation/testplan-{version}.md"
        res = self.github_request(url)

        if res.status_code == 200:
            return f"https://github.com/{self.towerqa_repo}/blob/devel/docs/test_plans/release_validation/testplan-{version}.md"

        return ""

    @markcache
    def get_issues_information(self, project, custom_query=None):
        url = f"{API_GITHUB}/search/issues?q=is:open+is:issue+project:{project}"
        if custom_query:
            url += f"+{custom_query}"
        return self.github_request(url).json()
