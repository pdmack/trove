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

from datetime import datetime
from distutils.util import strtobool

from trove.common import cfg
from trove.common import exception
from trove.common import wsgi
from trove.scheduledtask import models
from trove.scheduledtask import views
from trove.openstack.common import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)
DT_FMT = '%Y-%m-%dT%H:%M:%S.%fZ'


class ScheduledTaskController(wsgi.Controller):

    def create(self, req, body, tenant_id):
        LOG.info(_("Creating a scheduled task for tenant '%s'") % tenant_id)
        LOG.info(_("req : '%s'\n\n") % req)
        LOG.info(_("body : '%s'\n\n") % body)

        data = body['scheduledtask']

        # sigh, XML can't do booleans properly without a schema
        if 'enabled' in data:
            data['enabled'] = strtobool(str(data['enabled']))

        data['window_start'] = datetime.strptime(data['window_start'], DT_FMT)
        data['window_end'] = datetime.strptime(data['window_end'], DT_FMT)
        if data.get('metadata'):
            data['metadata'] = json.dumps(data['metadata'])

        context = req.environ[wsgi.CONTEXT_KEY]
        data['tenant_id'] = context.tenant

        scheduled_task = models.ScheduledTask.create(**data)
        return wsgi.Result(views.
                           ScheduledTaskView(scheduled_task, req).data(), 200)

    def show(self, req, tenant_id, id):
        LOG.info(_("Showing scheduled task '%(id)s' for tenant '%(tenant)s'")
                 % {"id": id, "tenant": tenant_id})
        LOG.info(_("req : '%s'\n\n") % req)

        context = req.environ[wsgi.CONTEXT_KEY]
        scheduledtask = models.ScheduledTask.load(id, context=context)
        view = views.ScheduledTaskView(scheduledtask, req)
        return wsgi.Result(view.data(), 200)

    def update(self, req, body, tenant_id, id):
        LOG.info(_("Updating scheduled task '%(id)s' for tenant '%(tenant)s'")
                 % {"id": id, "tenant": tenant_id})
        LOG.info(_("req : '%s'\n\n") % req)
        LOG.info(_("body : '%s'\n\n") % body)

        data = body['scheduledtask']

        # sigh, XML can't do booleans properly without a schema
        if 'enabled' in data:
            data['enabled'] = strtobool(str(data['enabled']))

        if data.get('window_start'):
            data['window_start'] = datetime.strptime(data['window_start'],
                                                     DT_FMT)
        if data.get('window_end'):
            data['window_end'] = datetime.strptime(data['window_end'], DT_FMT)

        if data.get('metadata'):
            data['metadata'] = json.dumps(data['metadata'])

        if (data.get('tenant_id') or data.get('instance_id')
                or data.get('type')):
            raise exception.Forbidden("Cannot migrate a scheduled task.")

        context = req.environ[wsgi.CONTEXT_KEY]

        scheduledtask = models.ScheduledTask.load(id, context=context)
        scheduledtask.update(**data)
        view = views.ScheduledTaskView(scheduledtask, req)
        return wsgi.Result(view.data(), 200)

    def delete(self, req, tenant_id, id):
        LOG.info(_("Deleting scheduled task '%(id)s' for tenant '%(tenant)s'")
                 % {"id": id, "tenant": tenant_id})
        LOG.info(_("req : '%s'\n\n") % req)

        context = req.environ[wsgi.CONTEXT_KEY]
        models.ScheduledTask.load(id, context=context).delete()
        return wsgi.Result(None, 202)

    def type_index(self, req, tenant_id):
        LOG.info(_("Listing scheduled task types for tenant '%s'") % tenant_id)
        LOG.info(_("req : '%s'\n\n") % req)

        scheduledtasktypes = models.ScheduledTaskTypes.load()
        view = views.ScheduledTaskTypesView(scheduledtasktypes, req)
        return wsgi.Result(view.data(), 200)
