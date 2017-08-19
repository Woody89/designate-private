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
import re
from oslo_config import cfg
from oslo_log import log as logging

from designate import exceptions
from designate import utils
from designate.api.v2.controllers import rest
from designate import objects
from designate.objects.adapters import DesignateAdapter
from designate.i18n import _LI


CONF = cfg.CONF


LOG = logging.getLogger(__name__)


class ViewController(rest.RestController):

    SORT_KEYS = ['id', 'name', 'tenant_id' , 'pool_id']

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('view_id')
    def get_one(self, view_id):
        """Get View"""
        # TODO(kiall): Validate we have a sane UUID for view_id
        
        
        request = pecan.request
        context = request.environ['context']
        view = self.central_api.get_view(context, view_id)

        LOG.info(_LI("Retrieved %(view)s"), {'view': view})

        view = DesignateAdapter.render(
            'API_v2',
            view,
            request=request)
        view_acls = self.central_api.find_view_acls(context, view['id'])
        acl_ids = []
        if len(view_acls) > 0:
            for view_acl in view_acls:
                acl_ids.append(view_acl['acl_id'])
                view['acl_ids'] = acl_ids
        else:
            view['acl_ids'] = acl_ids
        return view

    @pecan.expose(template='json:', content_type='application/json')
    def get_all(self, **params):
        """List Views"""
        request = pecan.request
        context = request.environ['context']

        marker, limit, sort_key, sort_dir = utils.get_paging_params(
                context, params, self.SORT_KEYS)

        # Extract any filter params.
        accepted_filters = ('name', 'pool_id', 'acl_id', 'tenant_id' )

        criterion = self._apply_filter_params(
            params, accepted_filters, {})
        views = self.central_api.find_views(
            context, criterion, marker, limit, sort_key, sort_dir)

        LOG.info(_LI("Retrieved %(views)s"), {'views': views})

        views = DesignateAdapter.render('API_v2', views, request=request)
        for view in views['views']:
            view_acls = self.central_api.find_view_acls(context, view['id'])
            acl_ids = []
            if len(view_acls) > 0:
                for view_acl in view_acls:
                    acl_ids.append(view_acl['acl_id'])
                    view['acl_ids'] = acl_ids
            else:
                view['acl_ids'] = acl_ids
        return views    

    @pecan.expose(template='json:', content_type='application/json')
    def post_all(self):
        """Create View"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']

        view = request.body_dict
        if not view.has_key('acl_ids'):
            raise exceptions.AclsIsNone
        if not re.search(u'^[_a-zA-Z0-9\u4e00-\u9fa5]+$', view['name']):
            raise exceptions.ParamsIsNotLegal
        acl_ids = view['acl_ids']
        if not isinstance(acl_ids, list):
            raise exceptions.AclidsMustBeList
        view.pop('acl_ids')
        view = DesignateAdapter.parse('API_v2', view, objects.View())
        view.validate()
        # Create the view
        view = self.central_api.create_view(context, view, acl_ids)
        view = view[0]
        LOG.info(_LI("Created %(view)s"), {'view': view})

        view = DesignateAdapter.render('API_v2', view, request=request)

        response.headers['Location'] = view['links']['self']
        view['acl_ids'] = acl_ids
        return view

    @pecan.expose(template='json:', content_type='application/json')
    @pecan.expose(template='json:', content_type='application/json-patch+json')
    @utils.validate_uuid('view_id')
    def patch_one(self, view_id):
        """Update View"""
        # TODO(kiall): This needs cleanup to say the least..
        request = pecan.request
        context = request.environ['context']
        body = request.body_dict
        response = pecan.response
        if not body.has_key('acl_ids'):
            raise exceptions.AclsIsNone
        acl_ids = body['acl_ids']
        if not isinstance(acl_ids, list):
            raise exceptions.AclidsMustBeList
        view = self.central_api.update_view(context, view_id, acl_ids)
        LOG.info(_LI("Updated %(view)s"), {'view': view})
        view = DesignateAdapter.render('API_v2', view, request=request)
        view['acl_ids'] = body['acl_ids']
        return view

    @pecan.expose(template='json:', content_type='application/json')
    @utils.validate_uuid('view_id')
    def delete_one(self, view_id):
        """Delete View"""
        request = pecan.request
        response = pecan.response
        context = request.environ['context']
        view = self.central_api.delete_view(context, view_id)

        LOG.info(_LI("Deleted %(view)s"), {'view': view})
        response.status_int = 202
#         return DesignateAdapter.render('API_v2', view, request=request)
        return response
