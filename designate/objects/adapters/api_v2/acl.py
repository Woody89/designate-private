# Copyright 2014 Hewlett-Packard Development Company, L.P.
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

from designate.objects.adapters.api_v2 import base
from designate import objects


class AclAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.Acl

    MODIFICATIONS = {
        'fields': {
            "id": {},
            "pool_id": {'read_only': False
                        },
            "tenant_id": {},
            "name": {
                'immutable': True,
            },
            "networks":{
                'read_only': False
            },
        },
        'options': {
            'links': True,
            'resource_name': 'acl',
            'collection_name': 'acls',
        }
    }

#     @classmethod
#     def _parse_object(cls, values, object, *args, **kwargs):
#  
#         if 'masters' in values:
#  
#             object.masters = objects.adapters.DesignateAdapter.parse(
#                 cls.ADAPTER_FORMAT,
#                 values['masters'],
#                 objects.AclMasterList(),
#                 *args, **kwargs)
#  
#             del values['masters']
#  
#         if 'attributes' in values:
#  
#             object.attributes = objects.adapters.DesignateAdapter.parse(
#                 cls.ADAPTER_FORMAT,
#                 values['attributes'],
#                 objects.AclAttributeList(),
#                 *args, **kwargs)
#  
#             del values['attributes']
#  
#         return super(AclAPIv2Adapter, cls)._parse_object(
#             values, object, *args, **kwargs)


class AclListAPIv2Adapter(base.APIv2Adapter):

    ADAPTER_OBJECT = objects.AclList

    MODIFICATIONS = {
        'options': {
            'links': True,
            'resource_name': 'acl',
            'collection_name': 'acls',
        }
    }
