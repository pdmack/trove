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

from trove.common import cfg
from trove.common import exception
from trove.db import models as dbmodels
from trove.db import get_db_api
from trove.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
db_api = get_db_api()

valid_frequencies = [
    'hourly',
    'daily',
    'weekly',
    'monthly',
]


def persisted_models():
    return {
        'scheduledtasks': DBScheduledTask,
        'scheduledtasktypes': DBScheduledTaskType,
    }


def _validate_scheduled_task(**kwargs):
    args = dict(**kwargs)
    if 'type' in args:
        # this will throw a NotFound exception if it isn't a valid type
        DBScheduledTaskType.find_by(type=args['type'])
    if 'frequency' in args:
        if args['frequency'] not in valid_frequencies:
            raise exception.NotFound(
                "'%s' is not a valid scheduled task frequency"
                % args['frequency']
            )


class DBScheduledTask(dbmodels.DatabaseModelBase):

    _data_fields = [
        'id', 'tenant_id', 'instance_id', 'type', 'enabled',
        'name', 'frequency', 'window_start', 'window_end',
        'description', 'metadata',
    ]


class DBScheduledTaskType(dbmodels.DatabaseModelBase):

    _data_fields = ['type', 'description', 'enabled']


class ScheduledTask(object):

    def __init__(self, db_info):
        self.db_info = db_info

    @classmethod
    def load(cls, id, context=None):
        return cls(DBScheduledTask.find_by(id=id, context=context))

    @classmethod
    def create(cls, **kwargs):
        _validate_scheduled_task(**kwargs)
        return cls(DBScheduledTask.create(**kwargs))

    def delete(self):
        self.db_info.delete()

    def update(self, **kwargs):
        _validate_scheduled_task(**kwargs)
        self.db_info.update(**kwargs)
        return self

    @property
    def id(self):
        return self.db_info.id

    @property
    def tenant_id(self):
        return self.db_info.tenant_id

    @property
    def instance_id(self):
        return self.db_info.instance_id

    @property
    def type(self):
        return self.db_info.type

    @property
    def enabled(self):
        return self.db_info.enabled

    @property
    def name(self):
        return self.db_info.name

    @property
    def frequency(self):
        return self.db_info.frequency

    @property
    def window_start(self):
        return self.db_info.window_start

    @property
    def window_end(self):
        return self.db_info.window_end

    @property
    def description(self):
        return self.db_info.description

    @property
    def metadata(self):
        return self.db_info.metadata


class ScheduledTasks(object):

    def __init__(self, db_info):
        self.db_info = db_info

    @classmethod
    def load(cls, **kwargs):
        return cls(DBScheduledTask.find_all(**kwargs))

    def __iter__(self):
        for item in self.db_info:
            yield item


class ScheduledTaskType(object):

    def __init__(self, db_info):
        self.db_info = db_info

    @classmethod
    def load(cls, type):
        return cls(DBScheduledTaskType.find_by(type=type))

    @classmethod
    def create(cls, **kwargs):
        return cls(DBScheduledTask.create(**kwargs))

    def delete(self):
        self.db_info.delete()

    def update(self, **kwargs):
        self.db_info.update(**kwargs)
        return self

    @property
    def type(self):
        return self.db_info.type

    @property
    def description(self):
        return self.db_info.description

    @property
    def enabled(self):
        return self.db_info.enabled


class ScheduledTaskTypes(object):

    def __init__(self, db_info):
        self.db_info = db_info

    @classmethod
    def load(cls, **kwargs):
        return cls(DBScheduledTaskType.find_all(**kwargs))

    def __iter__(self):
        for item in self.db_info:
            yield item
