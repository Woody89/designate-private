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
from designate.objects import base


class ZdnsRecord(base.DictObjectMixin, base.PersistentObjectMixin,
             base.DesignateObject):
    # TODO(kiall): `hash` is an implementation detail of our SQLA driver,
    #              so we should remove it.
    
    FIELDS = {
        'name': {
            'schema': {
                'type': 'string',
            },
        },
        'ttl': {
            'schema': {
                'type': 'string',
            },
        },
        'rdata': {
            'schema': {
                'type': 'string',
            },
        },
        'type': {
            'schema': {
                'type': 'string',
            },
        },
        'klass': {
            'schema': {
                'type': 'string',
            },
        },
        'rr_id': {
            'schema': {
                'type': 'string',
            },
        },
        'action': {
            'schema': {
                'type': 'string',
            },
        },
    }

    STRING_KEYS = [
        'name'
    ]


class ZdnsRecordList(base.ListObjectMixin, base.DesignateObject):
    LIST_ITEM_TYPE = ZdnsRecord
