# Copyright 2015 Tesora Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from proboscis import test

from trove.tests.api.instances import GROUP_START_SIMPLE
from trove.tests.api.instances import WaitForGuestInstallationToFinish
from trove.tests.scenario.groups.test_group import TestGroup


GROUP = "scenario.cluster_actions_group"


@test(depends_on_groups=[GROUP_START_SIMPLE], groups=[GROUP],
      runs_after=[WaitForGuestInstallationToFinish])
class ClusterActionsGroup(TestGroup):

    def __init__(self):
        super(ClusterActionsGroup, self).__init__(
            'cluster_actions_runners', 'ClusterActionsRunner')

    @test
    def cluster_create(self):
        self.test_runner.run_cluster_create()

    @test(depends_on=[cluster_create])
    def test_cluster_communication(self):
        self.test_runner.run_cluster_communication()

    @test(depends_on=[cluster_create], runs_after=[test_cluster_communication])
    def cluster_delete(self):
        self.test_runner.run_cluster_delete()
