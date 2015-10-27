#    Copyright 2011 OpenStack Foundation
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


from proboscis import before_class
from proboscis import test
from proboscis.asserts import assert_equal
from proboscis.asserts import assert_raises

from trove import tests
from trove.scheduledtask.models import DBScheduledTaskType
from trove.tests.util import test_config
from trove.tests.util import create_dbaas_client
from trove.tests.util.users import Requirements
from trove.tests.util.check import TypeCheck
from troveclient.compat import exceptions

FAKE_MODE = test_config.values['fake_mode']
GROUP = "dbaas.api.mgmt.scheduledtasktypes"


@test(groups=[tests.DBAAS_API, GROUP])
class ScheduledTaskTypesTest(object):

    @before_class
    def setUp(self):
        self.user = test_config.users.find_user(Requirements(is_admin=True))
        self.client = create_dbaas_client(self.user)
        self.type = "test"
        DBScheduledTaskType.create(type="test", enabled=True,
                                   description="test")

    @test
    def test_scheduledtasktype_list(self):
        types = self.client.scheduledtasktypes.list()
        assert(len(types) > 0)
        for type in types:
            with TypeCheck('ScheduledTaskType', type) as check:
                check.has_field("type", basestring)
                check.has_field("description", basestring)
                check.has_field("enabled", bool)
                check.has_field("links", list)

    @test()
    def test_scheduledtasktype_disable(self):
        assert_raises(exceptions.NotFound,
                      self.client.scheduledtasktypes.disable, 'nonexistent')
        type_data = self.client.scheduledtasktypes.disable(self.type)
        assert_equal(type_data.enabled, False)

    @test(runs_after=[test_scheduledtasktype_disable])
    def test_scheduledtasktype_enable(self):
        assert_raises(exceptions.NotFound,
                      self.client.scheduledtasktypes.enable, 'nonexistent')
        type_data = self.client.scheduledtasktypes.enable(self.type)
        assert_equal(type_data.enabled, True)
