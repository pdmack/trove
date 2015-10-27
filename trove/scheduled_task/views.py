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

import json
from trove.common.views import create_links
DT_FMT = '%Y-%m-%dT%H:%M:%S.%fZ'


class ScheduledTaskView(object):

    def __init__(self, scheduledtask, req=None):
        self.scheduledtask = scheduledtask
        self.req = req

    def data(self):
        task_view = {
            "id": self.scheduledtask.id,
            "tenant_id": self.scheduledtask.tenant_id,
            "instance_id": self.scheduledtask.instance_id,
            "type": self.scheduledtask.type,
            "enabled": self.scheduledtask.enabled,
            "name": self.scheduledtask.name,
            "frequency": self.scheduledtask.frequency,
            "window_start": self.scheduledtask.window_start.strftime(DT_FMT),
            "window_end": self.scheduledtask.window_end.strftime(DT_FMT),
            "description": self.scheduledtask.description,
            "metadata": {},
            "links": self._build_links(),
        }

        if self.scheduledtask.metadata:
            task_view['metadata'] = json.loads(self.scheduledtask.metadata)

        return {"scheduledtask": task_view}

    def _build_links(self):
        return create_links("scheduledtasks", self.req,
                            self.scheduledtask.id)


class ScheduledTasksView(object):

    def __init__(self, scheduledtasks, req=None):
        self.scheduledtasks = scheduledtasks
        self.req = req

    def data(self):
        data = []
        for scheduledtask in self.scheduledtasks:
            task_view = ScheduledTaskView(scheduledtask, req=self.req)
            task_data = task_view.data()['scheduledtask']
            data.append(task_data)
        return {'scheduledtasks': data}


class ScheduledTaskTypeView(object):

    def __init__(self, scheduledtasktype, req=None):
        self.scheduledtasktype = scheduledtasktype
        self.req = req

    def data(self):
        type_view = {
            "type": self.scheduledtasktype.type,
            "description": self.scheduledtasktype.description,
            "enabled": self.scheduledtasktype.enabled,
            "links": self._build_links(),
        }

        return {"scheduledtasktype": type_view}

    def _build_links(self):
        return create_links("scheduledtasktypes", self.req,
                            self.scheduledtasktype.type)


class ScheduledTaskTypesView(object):

    def __init__(self, scheduledtasktypes, req=None):
        self.scheduledtasktypes = scheduledtasktypes
        self.req = req

    def data(self):
        data = []
        for scheduledtasktype in self.scheduledtasktypes:
            type_view = ScheduledTaskTypeView(scheduledtasktype, req=self.req)
            type_data = type_view.data()['scheduledtasktype']
            data.append(type_data)
        return {'scheduledtasktypes': data}
