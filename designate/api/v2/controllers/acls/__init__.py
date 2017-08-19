# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
# Author: Kiall Mac Innes <kiall@hpe.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import pecan
import json
from oslo_config import cfg
from oslo_log import log as logging
import re

from designate import exceptions
from designate import utils
from designate.api.v2.controllers import rest
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI



CONF = cfg.CONF


LOG = logging.getLogger(__name__)


class AclsController(rest.RestController):

    SORT_KEYS = ['id', 'pool_id', 'name', 'tenant_id', 'networks']


    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('acl_id')
    def get_one(self, acl_id):
        """Get acl"""
        # TODO(kiall): Validate we have a sane UUID for acl_id

        request = pecan.request
        context = request.environ['context']

        acl = self.central_api.get_acl(context, acl_id)

        LOG.info(_LI("Retrieved %(acl)s"), {'acl': acl})

        return DesignateAdapter.render(
            'API_v2',
            acl,
            request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List acls"""
        request = pecan.request
        context = request.environ['context']

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
            context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('name', 'pool_id', 'tenant_id', 'networks')

        criterion = self._apply_filter_params(
            params, accepted_filters, {})

        acls = self.central_api.find_acls(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(acls)s"), {'acls': acls})

        return DesignateAdapter.render('API_v2', acls, request=request)

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create Acl"""

        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        # l = len(request.body_dict)
        # if not l == '3':
        #     raise exceptions.InvalidObject

        acl = request.body_dict
        if not re.search(u'^[_a-zA-Z0-9\u4e00-\u9fa5]+$', acl['name']):
            raise exceptions.InvalidAclName
        acl = DesignateAdapter.parse('API_v2', acl, objects.Acl())
        # Create the zone
        acl = self.central_api.create_acl(context, acl)

        LOG.info(_LI("Created %(acl)s"), {'acl': acl})
        acl = DesignateAdapter.render('API_v2', acl, request=request)
        response.headers['Location'] = acl['links']['self']
        response.status_int=201
        return acl

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('acl_id')
    def delete_one(self, acl_id):
        """Delete acl"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        acl = self.central_api.delete_acl(context, acl_id)
        response.status_int = 202

        LOG.info(_LI("Deleted %(acl)s"), {'acl': acl})

        # return DesignateAdapter.render('API_v2', acl, request=request)
        return response

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('acl_id')
    def patch_one(self, acl_id):
        """Update acl"""
        # TODO(kiall): This needs cleanup to say the least..
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response

        # TODO(kiall): Validate we have a sane UUID for acl_id

        # Fetch the existing acl
        acl = self.central_api.get_acl(context, acl_id)
        if request.content_type == 'application/json-patch+json':
            raise NotImplemented('json-patch not implemented')
        else:
            acl = DesignateAdapter.parse('API_v2', body, acl)

        acl = self.central_api.update_acl(context, acl)

        LOG.info(_LI("Updated %(acl)s"), {'acl': acl})

        return DesignateAdapter.render('API_v2', acl, request=request)


    #def is_invalid(dict):
