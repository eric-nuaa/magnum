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


class BayModelPatchType(types.JsonPatchType):

    @staticmethod
    def mandatory_attrs():
        return ['/baymodel_uuid']


class BayModel(base.APIBase):
    """API representation of a baymodel.

    This class enforces type checking and value constraints, and converts
    between the internal object model and the API representation of a baymodel.
    """

    _baymodel_uuid = None

    def _get_baymodel_uuid(self):
        return self._baymodel_uuid

    def _set_baymodel_uuid(self, value):
        if value and self._baymodel_uuid != value:
            try:
                # FIXME(comstud): One should only allow UUID here, but
                # there seems to be a bug in that tests are passing an
                # ID. See bug #1301046 for more details.
                baymodel = objects.BayModel.get(pecan.request.context, value)
                self._baymodel_uuid = baymodel.uuid
                self.baymodel_id = baymodel.id
            except exception.BayModelNotFound as e:
                # Change error code because 404 (NotFound) is inappropriate
                # response for a POST request to create a BayModel
                e.code = 400  # BadRequest
                raise e
        elif value == wtypes.Unset:
            self._baymodel_uuid = wtypes.Unset

    uuid = types.uuid
    """Unique UUID for this baymodel"""

    name = wtypes.text
    """The name of the bay model"""

    image_id = wtypes.text
    """The image name or UUID to use as a base image for this baymodel"""

    flavor_id = wtypes.text
    """The flavor of this bay model"""

    dns_nameserver = wtypes.text
    """The DNS nameserver address"""

    keypair_id = wtypes.text
    """The name or id of the nova ssh keypair"""

    external_network_id = wtypes.text
    """The external network to attach the Bay"""

    links = wsme.wsattr([link.Link], readonly=True)
    """A list containing a self link and associated baymodel links"""

    def __init__(self, **kwargs):
        self.fields = []
        fields = list(objects.BayModel.fields)
        fields.append('baymodel_uuid')
        for field in fields:
            # Skip fields we do not expose.
            if not hasattr(self, field):
                continue
            self.fields.append(field)
            setattr(self, field, kwargs.get(field, wtypes.Unset))

        # NOTE(lucasagomes): baymodel_id is an attribute created on-the-fly
        # by _set_baymodel_uuid(), it needs to be present in the fields so
        # that as_dict() will contain baymodel_id field when converting it
        # before saving it in the database.
        self.fields.append('baymodel_id')
        setattr(self, 'baymodel_uuid', kwargs.get('baymodel_id', wtypes.Unset))

    @staticmethod
    def _convert_with_links(baymodel, url, expand=True):
        if not expand:
            baymodel.unset_fields_except(['uuid', 'name', 'type', 'image_id',
                                     'ironic_baymodel_id'])

        # never expose the baymodel_id attribute
        baymodel.baymodel_id = wtypes.Unset

        baymodel.links = [link.Link.make_link('self', url,
                                          'baymodels', baymodel.uuid),
                      link.Link.make_link('bookmark', url,
                                          'baymodels', baymodel.uuid,
                                          bookmark=True)
                     ]
        return baymodel

    @classmethod
    def convert_with_links(cls, rpc_baymodel, expand=True):
        baymodel = BayModel(**rpc_baymodel.as_dict())
        return cls._convert_with_links(baymodel, pecan.request.host_url,
                                       expand)

    @classmethod
    def sample(cls, expand=True):
        sample = cls(uuid='27e3153e-d5bf-4b7e-b517-fb518e17f34c',
                     name='example',
                     type='virt',
                     image_id='Fedora-k8s',
                     baymodel_count=1,
                     created_at=datetime.datetime.utcnow(),
                     updated_at=datetime.datetime.utcnow())
        # NOTE(lucasagomes): baymodel_uuid getter() method look at the
        # _baymodel_uuid variable
        sample._baymodel_uuid = '7ae81bb3-dec3-4289-8d6c-da80bd8001ae'
        return cls._convert_with_links(sample, 'http://localhost:9511', expand)


class BayModelCollection(collection.Collection):
    """API representation of a collection of baymodels."""

    baymodels = [BayModel]
    """A list containing baymodels objects"""

    def __init__(self, **kwargs):
        self._type = 'baymodels'

    @staticmethod
    def convert_with_links(rpc_baymodels, limit, url=None, expand=False,
                           **kwargs):
        collection = BayModelCollection()
        collection.baymodels = [BayModel.convert_with_links(p, expand)
                            for p in rpc_baymodels]
        collection.next = collection.get_next(limit, url=url, **kwargs)
        return collection

    @classmethod
    def sample(cls):
        sample = cls()
        sample.baymodels = [BayModel.sample(expand=False)]
        return sample


class BayModelsController(rest.RestController):
    """REST controller for BayModels."""

    from_baymodels = False
    """A flag to indicate if the requests to this controller are coming
    from the top-level resource BayModels."""

    _custom_actions = {
        'detail': ['GET'],
    }

    def _get_baymodels_collection(self, marker, limit,
                              sort_key, sort_dir, expand=False,
                              resource_url=None):

        limit = api_utils.validate_limit(limit)
        sort_dir = api_utils.validate_sort_dir(sort_dir)

        marker_obj = None
        if marker:
            marker_obj = objects.BayModel.get_by_uuid(pecan.request.context,
                                                  marker)

        baymodels = objects.BayModel.list(pecan.request.context, limit,
                                marker_obj, sort_key=sort_key,
                                sort_dir=sort_dir)

        return BayModelCollection.convert_with_links(baymodels, limit,
                                                url=resource_url,
                                                expand=expand,
                                                sort_key=sort_key,
                                                sort_dir=sort_dir)

    @wsme_pecan.wsexpose(BayModelCollection, types.uuid,
                         types.uuid, int, wtypes.text, wtypes.text)
    def get_all(self, baymodel_uuid=None, marker=None, limit=None,
                sort_key='id', sort_dir='asc'):
        """Retrieve a list of baymodels.

        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        return self._get_baymodels_collection(marker, limit, sort_key,
                                         sort_dir)

    @wsme_pecan.wsexpose(BayModelCollection, types.uuid,
                         types.uuid, int, wtypes.text, wtypes.text)
    def detail(self, baymodel_uuid=None, marker=None, limit=None,
                sort_key='id', sort_dir='asc'):
        """Retrieve a list of baymodels with detail.

        :param baymodel_uuid: UUID of a baymodel, to get only baymodels for
               that baymodel.
        :param marker: pagination marker for large data sets.
        :param limit: maximum number of resources to return in a single result.
        :param sort_key: column to sort results by. Default: id.
        :param sort_dir: direction to sort. "asc" or "desc". Default: asc.
        """
        # NOTE(lucasagomes): /detail should only work agaist collections
        parent = pecan.request.path.split('/')[:-1][-1]
        if parent != "baymodels":
            raise exception.HTTPNotFound

        expand = True
        resource_url = '/'.join(['baymodels', 'detail'])
        return self._get_baymodels_collection(marker, limit,
                                         sort_key, sort_dir, expand,
                                         resource_url)

    @wsme_pecan.wsexpose(BayModel, types.uuid)
    def get_one(self, baymodel_uuid):
        """Retrieve information about the given baymodel.

        :param baymodel_uuid: UUID of a baymodel.
        """
        if self.from_baymodels:
            raise exception.OperationNotPermitted

        rpc_baymodel = objects.BayModel.get_by_uuid(pecan.request.context,
            baymodel_uuid)
        return BayModel.convert_with_links(rpc_baymodel)

    @wsme_pecan.wsexpose(BayModel, body=BayModel, status_code=201)
    def post(self, baymodel):
        """Create a new baymodel.

        :param baymodel: a baymodel within the request body.
        """
        if self.from_baymodels:
            raise exception.OperationNotPermitted

        new_baymodel = objects.BayModel(pecan.request.context,
                                **baymodel.as_dict())
        new_baymodel.create()
        # Set the HTTP Location Header
        pecan.response.location = link.build_url('baymodels',
                                  new_baymodel.uuid)
        return BayModel.convert_with_links(new_baymodel)

    @wsme.validate(types.uuid, [BayModelPatchType])
    @wsme_pecan.wsexpose(BayModel, types.uuid, body=[BayModelPatchType])
    def patch(self, baymodel_uuid, patch):
        """Update an existing baymodel.

        :param baymodel_uuid: UUID of a baymodel.
        :param patch: a json PATCH document to apply to this baymodel.
        """
        if self.from_baymodels:
            raise exception.OperationNotPermitted

        rpc_baymodel = objects.BayModel.get_by_uuid(pecan.request.context,
            baymodel_uuid)
        try:
            baymodel_dict = rpc_baymodel.as_dict()
            # NOTE(lucasagomes):
            # 1) Remove baymodel_id because it's an internal value and
            #    not present in the API object
            # 2) Add baymodel_uuid
            baymodel_dict['baymodel_uuid'] = baymodel_dict.pop('baymodel_id',
                                             None)
            baymodel = BayModel(**api_utils.apply_jsonpatch(baymodel_dict,
                patch))
        except api_utils.JSONPATCH_EXCEPTIONS as e:
            raise exception.PatchError(patch=patch, reason=e)

        # Update only the fields that have changed
        for field in objects.BayModel.fields:
            try:
                patch_val = getattr(baymodel, field)
            except AttributeError:
                # Ignore fields that aren't exposed in the API
                continue
            if patch_val == wtypes.Unset:
                patch_val = None
            if rpc_baymodel[field] != patch_val:
                rpc_baymodel[field] = patch_val

        rpc_baymodel.save()
        return BayModel.convert_with_links(rpc_baymodel)

    @wsme_pecan.wsexpose(None, types.uuid, status_code=204)
    def delete(self, baymodel_uuid):
        """Delete a baymodel.

        :param baymodel_uuid: UUID of a baymodel.
        """
        if self.from_baymodels:
            raise exception.OperationNotPermitted

        rpc_baymodel = objects.BayModel.get_by_uuid(pecan.request.context,
                                            baymodel_uuid)
        rpc_baymodel.destroy()
