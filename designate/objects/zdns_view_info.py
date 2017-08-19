# Copyright (c) 2014 Rackspace Hosting
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
from designate import utils
from designate import exceptions
from designate.objects import base


class ZdnsViewInfo(base.DictObjectMixin, base.SoftDeleteObjectMixin,
           base.PersistentObjectMixin, base.DesignateObject):
    
    FIELDS = {
        'name': {
            'schema': {
                'type': 'string',
                'description': 'zdns_view name',
                'maxLength': 255,
            },
            'immutable': True,
        },
        'dns64s': {
            'schema': {
                'type': 'string',
            },
        },
        'owners': {
            'schema': {
                'type': 'string',
            },
        },
        'fail_forwarder': {
            'schema': {
                'type': 'string',
            },
        },
        'current_users': {
            'schema': {
                'type': 'string',
            },
        },
        'priority': {
            'schema': {
                'type': 'string',
            },
        },
        'query_source': {
            'schema': {
                'type': 'string',
            },
        },
        'href': {
            'schema': {
                'type': 'string',
            },
        },
        'zones': {
            'schema': {
                'type': 'string',
            },
        },
        'comment': {
            'schema': {
                'type': 'string',
            },
        },
    }

    STRING_KEYS = [
        'id', 'name', 'owners']




class ZdnsViewInfoList(base.ListObjectMixin, base.DesignateObject,
               base.PagedListObjectMixin):
    LIST_ITEM_TYPE = ZdnsViewInfo
