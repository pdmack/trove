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
from trove.tests.scenario.groups import backup_group
from trove.tests.scenario.groups import instance_actions_group
from trove.tests.scenario.groups import replication_group
from trove.tests.scenario.groups.test_group import TestGroup


GROUP = "scenario.instance_delete_group"


@test(depends_on_groups=[GROUP_START_SIMPLE], groups=[GROUP],
      runs_after_groups=[backup_group.GROUP_BACKUP, replication_group.GROUP,
                         instance_actions_group.GROUP])
class InstanceDeleteGroup(TestGroup):

    def __init__(self):
        super(InstanceDeleteGroup, self).__init__(
            'instance_delete_runners', 'InstanceDeleteRunner')

    @test
    def instance_delete(self):
        self.test_runner.run_instance_delete()
