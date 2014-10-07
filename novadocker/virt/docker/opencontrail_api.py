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

from nova_contrail_vif.gen_py.instance_service import InstanceService

import uuid
import thrift
from thrift.protocol import TBinaryProtocol
from thrift.transport import TTransport


class OpenContrailComputeApi(object):
    def __init__(self):
        self._client = None

    def _rpc_client_instance(self):
        """ Return an RPC client connection """
        import thrift.transport.TSocket as TSocket
        socket = TSocket.TSocket('127.0.0.1', 9090)
        try:
            transport = TTransport.TFramedTransport(socket)
            transport.open()
        except thrift.transport.TTransport.TTransportException:
            logging.error('Connection failure')
            return None
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        return InstanceService.Client(protocol)

    def _uuid_from_string(self, idstr):
        """ Convert an uuid into an array of integers """
        if not idstr:
            return None
        hexstr = uuid.UUID(idstr).hex
        return [int(hexstr[i:i+2], 16) for i in range(32) if i % 2 == 0]

    def add_port(self, vm_uuid, vif_uuid, interface_name, mac_address,
                 project_id=None):
        if self._client is None:
            self._client = self._rpc_client_instance()

        from nova_contrail_vif.gen_py.instance_service import ttypes
        data = ttypes.Port(
            self._uuid_from_string(vif_uuid),
            self._uuid_from_string(vm_uuid),
            interface_name,
            '0.0.0.0',
            [0] * 16,
            mac_address)

        self._client.AddPort([data])

    def delete_port(self, vif_uuid):
        if self._client is None:
            self._client = self._rpc_client_instance()

        self._client.DeletePort(self._uuid_from_string(vif_uuid))
