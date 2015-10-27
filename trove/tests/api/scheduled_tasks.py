# Copyright 2013 OpenStack Foundation
# Copyright 2013 Rackspace Hosting
# Copyright 2013 Hewlett-Packard Development Company, L.P.
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
#


from time import sleep
from datetime import datetime
from datetime import timedelta
from proboscis import after_class
from proboscis import before_class
from proboscis import test
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_is_not_none
from proboscis.asserts import assert_raises

from trove import tests
from trove.tests.api.instances import instance_info
from trove.tests.api.instances import VOLUME_SUPPORT
from trove.tests.util import create_dbaas_client
from trove.tests.util import test_config
from trove.tests.util.instance import create_instance_blocking
from trove.tests.util.instance import destroy_instance_blocking
from trove.tests.util.users import Requirements
from trove.tests.util.check import TypeCheck
from troveclient.compat import exceptions

GROUP = "dbaas.api.scheduled_tasks"


@test(groups=[tests.DBAAS_API, GROUP, tests.PRE_INSTANCES])
class ScheduledTasks(object):
    test_task = None
    test_task_type = "backup"

    @before_class
    def setUp(self):
        reqs = Requirements(is_admin=True)
        self.user = test_config.users.find_user(reqs)
        self.client = create_dbaas_client(self.user)
        volume = None
        if VOLUME_SUPPORT:
            volume = {'size': 1}

        self.instance = create_instance_blocking(self.client,
            name="Test Scheduled Task Instance",
            flavor_id=instance_info.dbaas_flavor_href,
            volume=volume,
            databases=[],
            users=[],
        )

        other_reqs = Requirements(is_admin=False)
        self.other_user = test_config.users.find_user(other_reqs)
        self.other_client = create_dbaas_client(self.other_user)

    @after_class
    def tearDown(self):
        destroy_instance_blocking(self.client, self.instance)

    @test
    def test_scheduledtask_create(self):
        now = datetime.now()
        params = {
            "name": "Test Task",
            "instance_id": self.instance.id,
            "description": "Testing",
            "type": self.test_task_type,
            "enabled": True,
            "frequency": "daily",
            "window_start": now,
            "window_end": now + timedelta(hours=1),
            "metadata": {
                "meta": "data",
                "i_am": "so meta!",
            },
        }
        self.test_task = self.client.scheduledtasks.create(**params)
        for key in params:
            assert_equal(getattr(self.test_task, key), params[key])

        assert_is_not_none(self.test_task.id)

        params['frequency'] = 'dodecahourly'
        assert_raises(exceptions.NotFound, self.client.scheduledtasks.create,
                      **params)

        params['type'] = 'nonexistent'
        assert_raises(exceptions.NotFound, self.client.scheduledtasks.create,
                      **params)

    @test(runs_after=[test_scheduledtask_create])
    def test_scheduledtask_list(self):
        scheduledtasks = self.client.instances.scheduledtasks(self.instance.id)
        for scheduledtask in scheduledtasks:
            with TypeCheck('ScheduledTask', scheduledtask) as check:
                check.has_field("id", basestring)
                check.has_field("name", basestring)
                check.has_field("instance_id", basestring)
                check.has_field("description", basestring)
                check.has_field("type", basestring)
                check.has_field("enabled", bool)
                check.has_field("frequency", basestring)
                check.has_field("window_start", basestring)
                check.has_field("window_end", basestring)

    @test(runs_after=[test_scheduledtask_create])
    def test_scheduledtask_get(self):
        assert_raises(exceptions.NotFound,
                      self.other_client.scheduledtasks.get,
                      id=self.test_task.id)
        scheduledtask = self.client.scheduledtasks.get(id=self.test_task.id)
        with TypeCheck('ScheduledTask', scheduledtask) as check:
            check.has_field("id", basestring)
            check.has_field("name", basestring)
            check.has_field("links", list)
        assert_equal(scheduledtask, self.test_task)

    @test(runs_after=[test_scheduledtask_create])
    def test_scheduledtask_update(self):
        assert_raises(exceptions.NotFound,
                      self.other_client.scheduledtasks.update,
                      id=self.test_task.id, name="Updated")
        scheduledtask = self.client.scheduledtasks.update(id=self.test_task.id,
                                                          name="Updated")
        assert_equal(scheduledtask.name, "Updated")
        assert_equal(scheduledtask.id, self.test_task.id)

    @test(runs_after=[test_scheduledtask_get, test_scheduledtask_list,
                      test_scheduledtask_update])
    def test_scheduledtask_delete(self):
        assert_raises(exceptions.NotFound,
                      self.other_client.scheduledtasks.delete,
                      id=self.test_task.id)
        self.client.scheduledtasks.delete(id=self.test_task.id)
        assert_raises(exceptions.NotFound,
                      self.client.scheduledtasks.get, self.test_task.id)
