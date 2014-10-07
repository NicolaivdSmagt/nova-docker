# Copyright (C) 2014 Juniper Networks, Inc
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

from nova import utils
from nova.openstack.common import log as logging
from novadocker.virt.docker import network

from opencontrail_api import OpenContrailComputeApi

LOG = logging.getLogger(__name__)


class OpenContrailVIFDriver(object):
    def __init__(self):
        self._api = OpenContrailComputeApi()

    def plug(self, instance, vif):
        pass

    def attach(self, instance, vif, container_id):
        if_local_name = 'veth%s' % vif['id'][:8]
        if_remote_name = 'ns%s' % vif['id'][:8]

        undo_mgr = utils.UndoManager()

        try:
            utils.execute('ip', 'link', 'add', if_local_name, 'type', 'veth',
                          'peer', 'name', if_remote_name, run_as_root=True)
            undo_mgr.undo_with(lambda: utils.execute(
                'ip', 'link', 'delete', if_local_name, run_as_root=True))

            utils.execute('ip', 'link', 'set', if_remote_name, 'address',
                          vif['address'], run_as_root=True)
            utils.execute('ip', 'link', 'set', if_remote_name, 'netns',
                          container_id, run_as_root=True)

            self._api.add_port(instance['uuid'], vif['id'], if_local_name,
                               vif['address'],
                               project_id=instance['project_id'])
            utils.execute('ip', 'link', 'set', if_local_name, 'up',
                          run_as_root=True)
        except:
            LOG.exception("Failed to configure network")
            msg = _('Failed to setup the network, rolling back')
            undo_mgr.rollback_and_reraise(msg=msg, instance=instance)

        # TODO: attempt DHCP client; fallback to manual config if the
        # container doesn't have an working dhcpclient
        utils.execute('ip', 'netns', 'exec', container_id, 'dhclient',
                      if_remote_name, run_as_root=True)

    def unplug(self, instance, vif):
        try:
            self._api.delete_port(vif['id'])
        except Exception:
            LOG.exception(_("Delete port failed"), instance=instance)

        if_local_name = 'veth%s' % vif['id'][:8]
        utils.execute('ip', 'link', 'delete', if_local_name, run_as_root=True)
