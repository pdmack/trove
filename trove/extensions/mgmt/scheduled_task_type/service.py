# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation
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


from trove.common import wsgi
from trove.common.auth import admin_context
from trove.openstack.common import log as logging
from trove.openstack.common.gettextutils import _
from trove.scheduledtask import models
from trove.scheduledtask import views

LOG = logging.getLogger(__name__)


class ScheduledTaskTypeController(wsgi.Controller):
    """Controller for scheduled task type functionality"""

    @admin_context
    def enable(self, req, tenant_id, id):
        """Enable a specific scheduled task type globally

        This global switch is the default enabled state for all scheduled tasks
        of a particular type.  Note that tasks can be individually disabled,
        but both the task and its type must be enabled for it to run.
        """
        LOG.info(_("Enabled scheduled task type '%(id)s' by tenant '%(ten)s'")
                 % {"id": id, "ten": tenant_id})

        task_type = models.ScheduledTaskType.load(id)
        task_type.update(enabled=True)
        view = views.ScheduledTaskTypeView(task_type, req)
        return wsgi.Result(view.data(), 200)

    @admin_context
    def disable(self, req, tenant_id, id):
        """Disable a specific scheduled task type globally

        This global switch will disable any scheduled tasks of this type from
        running in the entire system.  Individual tasks enabled setting is
        ignored if the type has been disabled.
        """
        LOG.info(_("Disabled scheduled task type '%(id)s' by tenant '%(ten)s'")
                 % {"id": id, "ten": tenant_id})

        task_type = models.ScheduledTaskType.load(id)
        task_type.update(enabled=False)
        view = views.ScheduledTaskTypeView(task_type, req)
        return wsgi.Result(view.data(), 200)
