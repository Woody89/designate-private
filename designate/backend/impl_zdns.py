# coding=utf-8

# Copyright 2014 eBay Inc.
#
# Author: Ron Rickard <rrickard@ebay.com>
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

"""
Bind 9 backend. Create and delete zones by executing rndc
"""


import json
from oslo_log import log as logging
from oslo_config import cfg
from oslo_log import helpers as log_helpers
import requests
from designate.backend import base
from designate.exceptions import ZdnsErrMessage


LOG = logging.getLogger(__name__)
CONF = cfg.CONF
CFG_GROUP = 'backend:cms'


class CMSBackend(base.Backend):
    __plugin_name__ = 'cms'

    __backend_status__ = 'integrated'

    @log_helpers.log_method_call
    def __init__(self, target):
        super(CMSBackend, self).__init__(target)
        self.cms_ip = self.options.get('cms_ip')
        self.cms_port = self.options.get('cms_port')
        self.cms_username = self.options.get('cms_username')
        self.cms_password = self.options.get('cms_password')
        self.cms_owners = self.options.get('cms_owners').split(",")
        self.cms_slaves = self.options.get('cms_slaves')

    def get_client(self):
        return ZdnsClient(
            cms_ip=self.cms_ip,
            cms_port=self.cms_port,
            cms_username=self.cms_username,
            cms_password=self.cms_password,
        )

    @log_helpers.log_method_call
    def create_zone(self, context, zone, view_name):
        LOG.debug('Create Zone')
        data = {
            "name":zone.name,
            "owners":self.cms_owners,
            "default_ttl":zone.ttl,
            "slaves":self.cms_slaves,
            "renewal":"yes",
            "current_user":self.cms_username}
        client = self.get_client()
        endpoint = "/views/%s/zones" % (view_name)
        response = client.post(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def delete_zone(self, context, zone, view_name):
        client = self.get_client()
        data = {
            "current_user":self.cms_username
        }
        endpoint = "/views/%s/zones/%s" % (view_name,zone['name'][0:-1])
        response = client.delete(endpoint=endpoint,data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def update_zone(self, context, zone, view_name):
        # data ={
        #     "default_ttl":zone.ttl
        # }
        data = {
            "default_ttl": str(zone.ttl),
            "renewal":"yes",
            "current_user":self.cms_username
        }

        client = self.get_client()
        endpoint = "/views/%s/zones/%s" % (view_name,zone['name'][0:-1])
        response = client.update(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def create_record(self, context, zone, record, recordset, view_name):
        client = self.get_client()
        data = {
            "name":recordset.name,
            "type":recordset.type,
            "ttl":recordset.ttl,
            "rdata":record.data,
            "klass":"IN",
            "current_user":self.cms_username
        }
        endpoint = "/views/%s/zones/%s/rrs" % (
        view_name, zone.name)
        response = client.post(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def update_record(self, context, zone, record, recordset, view_name):
        client = self.get_client()
        data = {
            "ttl": record.ttl,
            "rdata": record.rdata,
            "current_user": self.cms_username
        }
        endpoint = "/views/%s/zones/%s/rrs/%s" % (
        view_name, zone.name, record.rr_id)
        response = client.update(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def delete_record(self, context, zone, rr_id, view_name):
        client = self.get_client()
        data = {"current_user":self.cms_username}
        endpoint = "/views/%s/zones/%s/rrs/%s" % (
        view_name, zone.name, rr_id)
        response = client.delete(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def create_view(self, context, view, acls):
        LOG.debug('Create view')
        data = {
            "name": view.name,
            "owners": self.cms_owners,
            "dns64s": [],
            "acls": acls,
            "fail_forwarder": '',
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/views"
        response = client.post(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def delete_view(self, context, view):
        LOG.debug('delete view')
        data = {
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/views/%s" % (view.name)
        response = client.delete(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def update_view(self, context, view, acls):
        LOG.debug('update view')
        data = {
            "dns64s": [],
            "acls":acls,
            "fail_forwarder": '',
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/views/%s" % (view.name)
        response = client.update(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def create_acl(self, context, acl):
        LOG.debug('Create acls')
        data = {
            "name": acl.name,
            "networks": acl.networks,
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/acls"
        response = client.post(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def delete_acl(self, context, acl):
        LOG.debug('delete acls')
        data = {
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/acls/%s" % (acl.name)
        response = client.delete(endpoint=endpoint, data=data)
        return self.check_response(response)

    @log_helpers.log_method_call
    def update_acl(self, context, acl):
        LOG.debug('update acls')
        data = {
            "networks": acl.networks,
            "current_user": self.cms_username}
        client = self.get_client()
        endpoint = "/acls/%s" % (acl.name)
        response = client.update(endpoint=endpoint, data=data)
        return self.check_response(response)

    def check_response(self, response):
        if response.get("error"):
            raise ZdnsErrMessage(response['error'])
        return response


class ZdnsClient(object):
    @log_helpers.log_method_call
    def __init__(self, cms_ip, cms_username, cms_password, cms_port):
        self.ip = cms_ip
        self.verify = False
        self.auth = (cms_username, cms_password)
        self.port = cms_port
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'}

    @log_helpers.log_method_call
    def post(self, endpoint, data):
        url = "https://" + self.ip + ":" + self.port + endpoint
        data = json.dumps(data)
        response = requests.post(url=url, data=data,
                      headers=self.headers, auth=self.auth, verify=self.verify)
        return response.json()

    @log_helpers.log_method_call
    def delete(self, endpoint, data):
        url = "https://" + self.ip +":" + self.port + endpoint
        data = json.dumps(data)
        response = requests.delete(url=url, data=data,
                      headers=self.headers, auth=self.auth, verify= self.verify)
        return response.json()

    @log_helpers.log_method_call
    def update(self, endpoint, data):
        url = "https://" + self.ip + ":" + self.port + endpoint
        data = json.dumps(data)
        response = requests.put(url=url, data=data,
                                headers=self.headers, auth=self.auth,
                                verify=self.verify)
        return response.json()

