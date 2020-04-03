#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2018-2019 Red Hat, Inc.
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
import itertools


ANSIBLE_VERSIONS = [
    {"name": "devel"},
    {"name": "stable-2.9"},
    {"name": "stable-2.8"},
    {"name": "stable-2.7"},
]

OS_VERSIONS = [
    {"name": "rhel-8.1-x86_64", "desc": "RHEL 8.1", "family": "RHEL"},
    {"name": "rhel-8.0-x86_64", "desc": "RHEL 8.0", "family": "RHEL"},
    {"name": "rhel-7.7-x86_64", "desc": "RHEL 7.7", "family": "RHEL"},
    {"name": "rhel-7.6-x86_64", "desc": "RHEL 7.6", "family": "RHEL"},
    {"name": "rhel-7.5-x86_64", "desc": "RHEL 7.5", "family": "RHEL"},
    {"name": "rhel-7.4-x86_64", "desc": "RHEL 7.4", "family": "RHEL"},
    {
        "name": "centos-7.latest-x86_64",
        "desc": "CentOS Latest",
        "family": "RHEL",
    },  # noqa
    {"name": "ol-7.6-x86_64", "desc": "Oracle Linux 7.6", "family": "RHEL"},
    {"name": "ubuntu-16.04-x86_64", "desc": "Ubuntu 16.04", "family": "Ubuntu"},  # noqa
    {"name": "ubuntu-14.04-x86_64", "desc": "Ubuntu 14.04", "family": "Ubuntu"},  # noqa
    {"name": "OpenShift", "desc": "OpenShift", "family": "misc"},  # noqa
    {"name": "Artifacts", "desc": "Artifacts", "family": "misc"},  # noqa
]

# Taken from: https://access.redhat.com/support/policy/updates/ansible-tower
#
TOWER_VERSIONS = [
    {
        "name": "In Development",
        "code": "devel",
        "general_availability": None,
        "end_of_full_support": None,
        "end_of_maintenance_support": None,
        "end_of_life": None,
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1F6qSF6x_CVrfAQc8zDaScDTM7eESFujQvq9Cc7mMv0M/edit#gid=166211985",
    },
    {
        "name": "Release 3.6",
        "code": "3.6",
        "general_availability": "2019-11-14",
        "end_of_full_support": "2020-05-14",
        "end_of_maintenance_support": "2020-11-14",
        "end_of_life": "2021-05-14",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1NNTN-SBM23UQPZAH9HylKhYQBAoyIsDcTlvl_ItDzHs/edit#gid=762158314",
    },
    {
        "name": "Release 3.5",
        "code": "3.5",
        "general_availability": "2019-05-29",
        "end_of_full_support": "2019-10-29",
        "end_of_maintenance_support": "2020-05-29",
        "end_of_life": "2020-10-29",
        "spreadsheet_url": "https://docs.google.com/spreadsheets/d/1Vo1lyIx_33Ad7TPqzO19NAe501CRcX0HTA0Rgepm5j0/",
    },
    {
        "name": "Release 3.4",
        "code": "3.4",
        "general_availability": "2019-01-09",
        "end_of_full_support": "2019-07-09",
        "end_of_maintenance_support": "2020-01-09",
        "end_of_life": "2020-07-09",
        "spreadsheet_url": None,
    },
    {
        "name": "Release 3.3",
        "code": "3.3",
        "general_availability": "2018-09-12",
        "end_of_full_support": "2019-03-12",
        "end_of_maintenance_support": "2019-09-12",
        "end_of_life": "2020-03-12",
        "spreadsheet_url": None,
    },
]

TOWER_OS = [
    {"tower": "In Development", "os": "rhel-8.1-x86_64"},
    {"tower": "In Development", "os": "rhel-8.0-x86_64"},
    {"tower": "In Development", "os": "rhel-7.7-x86_64"},
    {"tower": "In Development", "os": "rhel-7.6-x86_64"},
    {"tower": "In Development", "os": "rhel-7.5-x86_64"},
    {"tower": "In Development", "os": "rhel-7.4-x86_64"},
    {"tower": "In Development", "os": "centos-7.latest-x86_64"},
    {"tower": "In Development", "os": "ol-7.6-x86_64"},
    {"tower": "In Development", "os": "OpenShift"},
    {"tower": "In Development", "os": "Artifacts"},
    {"tower": "Release 3.6", "os": "rhel-8.1-x86_64"},
    {"tower": "Release 3.6", "os": "rhel-8.0-x86_64"},
    {"tower": "Release 3.6", "os": "rhel-7.7-x86_64"},
    {"tower": "Release 3.6", "os": "rhel-7.6-x86_64"},
    {"tower": "Release 3.6", "os": "rhel-7.5-x86_64"},
    {"tower": "Release 3.6", "os": "rhel-7.4-x86_64"},
    {"tower": "Release 3.6", "os": "centos-7.latest-x86_64"},
    {"tower": "Release 3.6", "os": "ol-7.6-x86_64"},
    {"tower": "Release 3.6", "os": "OpenShift"},
    {"tower": "Release 3.6", "os": "Artifacts"},
    {"tower": "Release 3.5", "os": "rhel-8.1-x86_64"},
    {"tower": "Release 3.5", "os": "rhel-8.0-x86_64"},
    {"tower": "Release 3.5", "os": "rhel-7.7-x86_64"},
    {"tower": "Release 3.5", "os": "rhel-7.6-x86_64"},
    {"tower": "Release 3.5", "os": "rhel-7.5-x86_64"},
    {"tower": "Release 3.5", "os": "rhel-7.4-x86_64"},
    {"tower": "Release 3.5", "os": "centos-7.latest-x86_64"},
    {"tower": "Release 3.5", "os": "ol-7.6-x86_64"},
    {"tower": "Release 3.5", "os": "ubuntu-16.04-x86_64"},
    {"tower": "Release 3.5", "os": "OpenShift"},
    {"tower": "Release 3.5", "os": "Artifacts"},
    {"tower": "Release 3.4", "os": "rhel-7.7-x86_64"},
    {"tower": "Release 3.4", "os": "rhel-7.6-x86_64"},
    {"tower": "Release 3.4", "os": "rhel-7.5-x86_64"},
    {"tower": "Release 3.4", "os": "rhel-7.4-x86_64"},
    {"tower": "Release 3.4", "os": "centos-7.latest-x86_64"},
    {"tower": "Release 3.4", "os": "ol-7.6-x86_64"},
    {"tower": "Release 3.4", "os": "ubuntu-16.04-x86_64"},
    {"tower": "Release 3.4", "os": "OpenShift"},
    {"tower": "Release 3.4", "os": "Artifacts"},
    {"tower": "Release 3.3", "os": "rhel-7.7-x86_64"},
    {"tower": "Release 3.3", "os": "rhel-7.6-x86_64"},
    {"tower": "Release 3.3", "os": "rhel-7.5-x86_64"},
    {"tower": "Release 3.3", "os": "rhel-7.4-x86_64"},
    {"tower": "Release 3.3", "os": "centos-7.latest-x86_64"},
    {"tower": "Release 3.3", "os": "ol-7.6-x86_64"},
    {"tower": "Release 3.3", "os": "ubuntu-16.04-x86_64"},
    {"tower": "Release 3.3", "os": "ubuntu-14.04-x86_64"},
    {"tower": "Release 3.3", "os": "OpenShift"},
    {"tower": "Release 3.3", "os": "Artifacts"},
]

TOWER_ANSIBLE = [
    {"tower": "In Development", "ansible": "devel"},
    {"tower": "In Development", "ansible": "stable-2.9"},
    {"tower": "In Development", "ansible": "stable-2.8"},
    {"tower": "In Development", "ansible": "stable-2.7"},
    {"tower": "Release 3.6", "ansible": "devel"},
    {"tower": "Release 3.6", "ansible": "stable-2.9"},
    {"tower": "Release 3.6", "ansible": "stable-2.8"},
    {"tower": "Release 3.6", "ansible": "stable-2.7"},
    {"tower": "Release 3.5", "ansible": "devel"},
    {"tower": "Release 3.5", "ansible": "stable-2.9"},
    {"tower": "Release 3.5", "ansible": "stable-2.8"},
    {"tower": "Release 3.5", "ansible": "stable-2.7"},
    {"tower": "Release 3.4", "ansible": "devel"},
    {"tower": "Release 3.4", "ansible": "stable-2.9"},
    {"tower": "Release 3.4", "ansible": "stable-2.8"},
    {"tower": "Release 3.4", "ansible": "stable-2.7"},
    {"tower": "Release 3.3", "ansible": "devel"},
    {"tower": "Release 3.3", "ansible": "stable-2.9"},
    {"tower": "Release 3.3", "ansible": "stable-2.8"},
    {"tower": "Release 3.3", "ansible": "stable-2.7"},
]

RESULTS = [
    #     {'release': 'release_3.3.2', 'os': 'rhel-7.6-x86_64', 'ansible': 'stable-2.7', 'status': 'SUCCESS', 'job_id': 12},
    #     {'release': 'release_3.3.2', 'os': 'rhel-7.5-x86_64', 'ansible': 'stable-2.6', 'status': 'SUCCESS', 'job_id': 13},
    #     {'release': 'release_3.3.2', 'os': 'rhel-7.4-x86_64', 'ansible': 'stable-2.5', 'status': 'SUCCESS', 'job_id': 16},
    #     {'release': 'release_3.2.9', 'os': 'rhel-7.6-x86_64', 'ansible': 'stable-2.7', 'status': 'SUCCESS', 'job_id': 19},
    #     {'release': 'release_3.2.9', 'os': 'rhel-7.5-x86_64', 'ansible': 'stable-2.7', 'status': 'SUCCESS', 'job_id': 20},
    #     {'release': 'release_3.2.9', 'os': 'rhel-7.4-x86_64', 'ansible': 'stable-2.7', 'status': 'SUCCESS', 'job_id': 24},
    #     {'release': 'release_3.2.9', 'os': 'centos-7.latest-x86_64', 'ansible': 'stable-2.7', 'status': 'FAILURE', 'job_id': 24},
]

QE_assignee = [
    "appuk",
    "squidboylan",
    "dsesami",
    "kdelee",
    "elyezer",
    "fpjrh",
    "jneedle",
    "unlikelyzero",
    "nixocio",
    "one-t",
    "Spredzy",
]
