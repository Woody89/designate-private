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
from designate.objects.validation_error import ValidationError
from designate.objects.validation_error import ValidationErrorList




class Acl(base.DictObjectMixin, base.SoftDeleteObjectMixin,
           base.PersistentObjectMixin, base.DesignateObject):
    FIELDS = {
        'tenant_id': {
            'schema': {
                'type': 'string',
            },
            'immutable': True
        },
        'name': {
            'schema': {
                'type': 'string',
                'description': 'Acl name',
                'format': 'domainname',
                'maxLength': 255,
            },
            'immutable': True,
            'required': True
        },
        'pool_id': {
            'schema': {
                'type': 'string',
                'format': 'uuid',
            },
            'immutable': True,
        },
        'networks': {
            'schema': {
                'type': 'string',
                'format': 'ip-or-host',
            },
        },
    }

    STRING_KEYS = [
        'id', 'networks', 'name', 'pool_id'
    ]

    def _raise(self, errors):
        if len(errors) != 0:
            raise exceptions.InvalidObject(
                "Provided object does not match "
                "schema", errors=errors, object=self)

    def __hash__(self):
        return hash(self.id)


class AclList(base.ListObjectMixin, base.DesignateObject,
               base.PagedListObjectMixin):
    LIST_ITEM_TYPE = Acl
