# Copyright 2013 UnitedStack Inc.
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

import datetime

import pecan
from pecan import rest
import wsme
from wsme import types as wtypes
import wsmeext.pecan as wsme_pecan

from magnum.api.controllers import base
from magnum.api.controllers import link
from magnum.api.controllers.v1 import collection
from magnum.api.controllers.v1 import types
from magnum.api.controllers.v1 import utils as api_utils
from magnum.common import exception
from magnum import objects


class NodePatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/node_uuid']


class Node(base.APIBase):
    """API representation of a node.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a node.
    """

    _node_uuid = None

    def _get_node_uuid(self):
        return self._node_uuid

    def _set_node_uuid(self, value):
        if value and self._node_uuid != value:
            try:
                # FIXME(comstud): One should only allow UUID here, but
                # there seems to be a bug in that tests are passing an
                # ID. See bug #1301046 for more details.
                node = objects.Node.get(pecan.request.context, value)
                self._node_uuid = node.uuid
                # NOTE(lucasagomes): Create the node_id attribute on-the-fly
                #                    to satisfy the api -> rpc object
                #                    conversion.
                self.node_id = node.id
            except exception.NodeNotFound as e:
                # Change error code because 404 (NotFound) is inappropriate
                # response for a POST request to create a Node
                e.code = 400  # BadRequest
                raise e
        elif value == wtypes.Unset:
            self._node_uuid = wtypes.Unset

    uuid = types.uuid
    """Unique UUID for this node"""

    type = wtypes.text
    """Type of this node"""

    image_id = wtypes.text
    """The image name or UUID to use as a base image for this node"""

    ironic_node_id = wtypes.text
    """The Ironic node ID associated with this node"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link and associated node links"""

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.Node.fields)
        # NOTE(lucasagomes): node_uuid is not part of objects.Node.fields
        #                    because it's an API-only attribute
        fields.append('node_uuid')
        for field in fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

        # NOTE(lucasagomes): node_id is an attribute created on-the-fly
        # by _set_node_uuid(), it needs to be present in the fields so
        # that as_dict() will contain node_id field when converting it
        # before saving it in the database.
        self.fields.append('node_id')
        setattr(self, 'node_uuid', kwargs.get('node_id', wtypes.Unset))

    @staticmethod
    def _convert_with_links(node, url, expand=True):
        if not expand:
            node.unset_fields_except(['uuid', 'name', 'type', 'image_id',
                                     'ironic_node_id'])

        # never expose the node_id attribute
        node.node_id = wtypes.Unset

        node.links = [link.Link.make_link('self', url,
                                          'nodes', node.uuid),
                      link.Link.make_link('bookmark', url,
                                          'nodes', node.uuid,
                                          bookmark=True)
                     ]
        return node

    @classmethod
    def convert_with_links(cls, rpc_node, expand=True):
        node = Node(**rpc_node.as_dict())
        return cls._convert_with_links(node, pecan.request.host_url, expand)

    @classmethod
    def sample(cls, expand=True):
        sample = cls(uuid='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
                     name='example',
                     type='virt',
                     image_id='Fedora-k8s',
                     node_count=1,
                     created_at=datetime.datetime.utcnow(),
                     updated_at=datetime.datetime.utcnow())
        # NOTE(lucasagomes): node_uuid getter() method look at the
        # _node_uuid variable
        sample._node_uuid = '7ae81bb3-dec3-4289-8d6c-da80bd8001ae'
        return cls._convert_with_links(sample, 'http://localhost:9511', expand)


class NodeCollection(collection.Collection):
    """API representation of a collection of nodes."""

    nodes = [Node]
    """A list containing nodes objects"""

    def __init__(self, **kwargs):
        self._type = 'nodes'

    @staticmethod
    def convert_with_links(rpc_nodes, limit, url=None, expand=False, **kwargs):
        collection = NodeCollection()
        collection.nodes = [Node.convert_with_links(p, expand)
                            for p in rpc_nodes]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection

    @classmethod
    def sample(cls):
        sample = cls()
        sample.nodes = [Node.sample(expand=False)]
        return sample


class NodesController(rest.RestController):
    """REST controller for Nodes."""

    from_nodes = False
    """A flag to indicate if the requests to this controller are coming
    from the top-level resource Nodes."""

    _custom_actions = {
        'detail': ['GET'],
    }

    def _get_nodes_collection(self, marker, limit,
                              sort_key, sort_dir, expand=False,
                              resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.Node.get_by_uuid(pecan.request.context,
                                                  marker)

        nodes = objects.Node.list(pecan.request.context, limit,
                                marker_obj, sort_key=sort_key,
                                sort_dir=sort_dir)

        return NodeCollection.convert_with_links(nodes, limit,
                                                url=resource_url,
                                                expand=expand,
                                                sort_key=sort_key,
                                                sort_dir=sort_dir)

    @wsme_pecan.wsexpose(NodeCollection, types.uuid,
                         types.uuid, int, wtypes.text, wtypes.text)
    def get_all(self, node_uuid=None, marker=None, limit=None,
                sort_key='id', sort_dir='asc'):
        """Retrieve a list of nodes.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        return self._get_nodes_collection(marker, limit, sort_key,
                                         sort_dir)

    @wsme_pecan.wsexpose(NodeCollection, types.uuid,
                         types.uuid, int, wtypes.text, wtypes.text)
    def detail(self, node_uuid=None, marker=None, limit=None,
                sort_key='id', sort_dir='asc'):
        """Retrieve a list of nodes with detail.

        :param node_uuid: UUID of a node, to get only nodes for that node.
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        # NOTE(lucasagomes): /detail should only work agaist collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "nodes":
            raise exception.HTTPNotFound

        expand = True
        resource_url = '/'.join(['nodes', 'detail'])
        return self._get_nodes_collection(marker, limit,
                                         sort_key, sort_dir, expand,
                                         resource_url)

    @wsme_pecan.wsexpose(Node, types.uuid)
    def get_one(self, node_uuid):
        """Retrieve information about the given node.

        :param node_uuid: UUID of a node.
        """
        if self.from_nodes:
            raise exception.OperationNotPermitted

        rpc_node = objects.Node.get_by_uuid(pecan.request.context, node_uuid)
        return Node.convert_with_links(rpc_node)

    @wsme_pecan.wsexpose(Node, body=Node, status_code=201)
    def post(self, node):
        """Create a new node.

        :param node: a node within the request body.
        """
        if self.from_nodes:
            raise exception.OperationNotPermitted

        new_node = objects.Node(pecan.request.context,
                                **node.as_dict())
        new_node.create()
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('nodes', new_node.uuid)
        return Node.convert_with_links(new_node)

    @wsme.validate(types.uuid, [NodePatchType])
    @wsme_pecan.wsexpose(Node, types.uuid, body=[NodePatchType])
    def patch(self, node_uuid, patch):
        """Update an existing node.

        :param node_uuid: UUID of a node.
        :param patch: a json PATCH document to apply to this node.
        """
        if self.from_nodes:
            raise exception.OperationNotPermitted

        rpc_node = objects.Node.get_by_uuid(pecan.request.context, node_uuid)
        try:
            node_dict = rpc_node.as_dict()
            # NOTE(lucasagomes):
            # 1) Remove node_id because it's an internal value and
            #    not present in the API object
            # 2) Add node_uuid
            node_dict['node_uuid'] = node_dict.pop('node_id', None)
            node = Node(**api_utils.apply_jsonpatch(node_dict, patch))
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.Node.fields:
            try:
                patch_val = getattr(node, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if rpc_node[field] != patch_val:
                rpc_node[field] = patch_val

        rpc_node.save()
        return Node.convert_with_links(rpc_node)

    @wsme_pecan.wsexpose(None, types.uuid, status_code=204)
    def delete(self, node_uuid):
        """Delete a node.

        :param node_uuid: UUID of a node.
        """
        if self.from_nodes:
            raise exception.OperationNotPermitted

        rpc_node = objects.Node.get_by_uuid(pecan.request.context,
                                            node_uuid)
        rpc_node.destroy()
