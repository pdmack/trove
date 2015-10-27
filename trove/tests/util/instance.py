# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright (c) 2011 OpenStack Foundation
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


from trove.common.utils import poll_until
from troveclient.compat import exceptions

def create_instance_blocking(client, **kwargs):
    instance = client.instances.create(**kwargs)

    def verify_activation():
        refresh = client.instances.get(instance.id)
        if refresh.status == "ACTIVE":
            return True
        return False
    poll_until(verify_activation)
    return client.instances.get(instance.id)

def destroy_instance_blocking(client, instance):
    client.instances.delete(instance.id)
    def verify_destruction():
        try:
            client.instances.get(instance.id)
        except exceptions.NotFound:
            return True
        return False
    poll_until(verify_destruction)
