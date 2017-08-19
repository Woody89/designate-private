# Copyright 2012 Managed I.T.
#
# Author: Kiall Mac Innes <kiall@managedit.ie>
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
import six


class Base(Exception):
    error_code = 500
    error_type = None
    error_message = None
    errors = None

    def __init__(self, *args, **kwargs):
        self.errors = kwargs.pop('errors', None)
        self.object = kwargs.pop('object', None)

        super(Base, self).__init__(*args, **kwargs)

        if len(args) > 0 and isinstance(args[0], six.string_types):
            self.error_message = args[0]


class Backend(Exception):
    pass


class RelationNotLoaded(Base):
    error_code = 500
    error_type = 'relation_not_loaded'

    def __init__(self, *args, **kwargs):

        self.relation = kwargs.pop('relation', None)

        super(RelationNotLoaded, self).__init__(*args, **kwargs)

        self.error_message = "%(relation)s is not loaded on %(object)s" % \
            {"relation": self.relation, "object": self.object.obj_name()}

    def __str__(self):
        return self.error_message


class AdapterNotFound(Base):
    error_code = 500
    error_type = 'adapter_not_found'


class NSD4SlaveBackendError(Backend):
    pass


class NotImplemented(Base, NotImplementedError):
    pass


class XFRFailure(Base):
    pass


class ConfigurationError(Base):
    error_type = 'configuration_error'


class UnknownFailure(Base):
    error_code = 500
    error_type = 'unknown_failure'


class CommunicationFailure(Base):
    error_code = 504
    error_type = 'communication_failure'


class NeutronCommunicationFailure(CommunicationFailure):
    """
    Raised in case one of the alleged Neutron endpoints fails.
    """
    error_type = 'neutron_communication_failure'


class NoFiltersConfigured(ConfigurationError):
    error_code = 500
    error_type = 'no_filters_configured'


class NoServersConfigured(ConfigurationError):
    error_code = 500
    error_type = 'no_servers_configured'


class MultiplePoolsFound(ConfigurationError):
    error_code = 500
    error_type = 'multiple_pools_found'


class NoPoolTargetsConfigured(ConfigurationError):
    error_code = 500
    error_type = 'no_pool_targets_configured'


class OverQuota(Base):
    error_code = 413
    error_type = 'over_quota'
    expected = True


class QuotaResourceUnknown(Base):
    error_type = 'quota_resource_unknown'


class InvalidObject(Base):
    error_code = 400
    error_type = 'invalid_object'
    expected = True


class BadRequest(Base):
    error_code = 400
    error_type = 'bad_request'
    expected = True


class EmptyRequestBody(BadRequest):
    error_type = 'empty_request_body'
    expected = True


class InvalidUUID(BadRequest):
    error_type = 'invalid_uuid'


class InvalidRecord(BadRequest):
    error_type = 'invalid_record'


class NetworkEndpointNotFound(BadRequest):
    error_type = 'no_endpoint'
    error_code = 403


class MarkerNotFound(BadRequest):
    error_type = 'marker_not_found'


class NotEqual(Base):
    error_type = 'udn_record_count not equals record in db'


class NoChange(Base):
    error_type = 'No changes'


class ValueError(BadRequest):
    error_type = 'value_error'


class InvalidMarker(BadRequest):
    error_type = 'invalid_marker'


class InvalidSortDir(BadRequest):
    error_type = 'invalid_sort_dir'


class InvalidLimit(BadRequest):
    error_type = 'invalid_limit'


class InvalidSortKey(BadRequest):
    error_type = 'invalid_sort_key'


class InvalidJson(BadRequest):
    error_type = 'invalid_json'

class NoneIpAddress(BadRequest):
    error_type = 'none_ip_address'

class InvalidOperation(BadRequest):
    error_code = 400
    error_type = 'invalid_operation'


class UnsupportedAccept(BadRequest):
    error_code = 406
    error_type = 'unsupported_accept'


class UnsupportedContentType(BadRequest):
    error_code = 415
    error_type = 'unsupported_content_type'


class InvalidZoneName(Base):
    error_code = 400
    error_type = 'invalid_zone_name'
    expected = True

class InvalidAclName(Base):
    error_code = 400
    error_type = 'invalid_acl_name'
    expected = True

class InvalidRecordSetName(Base):
    error_code = 400
    error_type = 'invalid_recordset_name'
    expected = True


class InvalidRecordSetLocation(Base):
    error_code = 400
    error_type = 'invalid_recordset_location'
    expected = True


class InvaildZoneTransfer(Base):
    error_code = 400
    error_type = 'invalid_zone_transfer_request'


class InvalidTTL(Base):
    error_code = 400
    error_type = 'invalid_ttl'


class ZoneHasSubZone(Base):
    error_code = 400
    error_type = 'zone_has_sub_zone'


class Forbidden(Base):
    error_code = 403
    error_type = 'forbidden'
    expected = True


class IllegalChildZone(Forbidden):
    error_type = 'illegal_child'


class IllegalParentZone(Forbidden):
    error_type = 'illegal_parent'


class IncorrectZoneTransferKey(Forbidden):
    error_type = 'invalid_key'


class Duplicate(Base):
    expected = True
    error_code = 409
    error_type = 'duplicate'


class DuplicateServiceStatus(Duplicate):
    error_type = 'duplicate_service_status'


class DuplicateQuota(Duplicate):
    error_type = 'duplicate_quota'


class DuplicateServer(Duplicate):
    error_type = 'duplicate_server'


class DuplicateTsigKey(Duplicate):
    error_type = 'duplicate_tsigkey'


class DuplicateZone(Duplicate):
    error_type = 'duplicate_zone'

class DuplicateAcl(Duplicate):
    error_type = 'duplicate_acl'

class DuplicateTld(Duplicate):
    error_type = 'duplicate_tld'


class DuplicateRecordSet(Duplicate):
    error_type = 'duplicate_recordset'


class DuplicateRecord(Duplicate):
    error_type = 'duplicate_record'


class DuplicateBlacklist(Duplicate):
    error_type = 'duplicate_blacklist'


class DuplicatePoolManagerStatus(Duplicate):
    error_type = 'duplication_pool_manager_status'


class DuplicatePool(Duplicate):
    error_type = 'duplicate_pool'


class DuplicatePoolAttribute(Duplicate):
    error_type = 'duplicate_pool_attribute'


class DuplicatePoolNsRecord(Duplicate):
    error_type = 'duplicate_pool_ns_record'


class DuplicatePoolNameserver(Duplicate):
    error_type = 'duplicate_pool_nameserver'


class DuplicatePoolTarget(Duplicate):
    error_type = 'duplicate_pool_target'


class DuplicatePoolTargetOption(Duplicate):
    error_type = 'duplicate_pool_target_option'


class DuplicatePoolTargetMaster(Duplicate):
    error_type = 'duplicate_pool_target_master'


class DuplicatePoolAlsoNotify(Duplicate):
    error_type = 'duplicate_pool_also_notify'


class DuplicateZoneImport(Duplicate):
    error_type = 'duplicate_zone_import'


class DuplicateZoneExport(Duplicate):
    error_type = 'duplicate_zone_export'
    
    
class DuplicateViewDuplicate(Duplicate):
    error_type = 'duplicate_view_export'

class DuplicateZdnsViewInfo(Duplicate):
    error_type = 'duplicate_zdns_view_info'


class DuplicateViewZdnsView(Duplicate):
    error_type = 'duplicate_view_zdns_view_association'

class DuplicateView(Duplicate):
    error_type = 'duplicate_view'

class NeedView(BadRequest):
    error_type = 'attributes_need_view'

class MethodNotAllowed(Base):
    expected = True
    error_code = 405
    error_type = 'method_not_allowed'


class DuplicateZoneTransferRequest(Duplicate):
    error_type = 'duplicate_zone_transfer_request'


class DuplicateZoneTransferAccept(Duplicate):
    error_type = 'duplicate_zone_transfer_accept'


class DuplicateZoneAttribute(Duplicate):
    error_type = 'duplicate_zone_attribute'


class DuplicateZoneMaster(Duplicate):
    error_type = 'duplicate_zone_attribute'


class NotFound(Base):
    expected = True
    error_code = 404
    error_type = 'not_found'


class Failed(Base):
    expected = True
    error_code = 500
    error_type = 'create_failed'


class ServiceStatusNotFound(NotFound):
    error_type = 'service_status_not_found'


class QuotaNotFound(NotFound):
    error_type = 'quota_not_found'


class ServerNotFound(NotFound):
    error_type = 'server_not_found'


class TsigKeyNotFound(NotFound):
    error_type = 'tsigkey_not_found'


class BlacklistNotFound(NotFound):
    error_type = 'blacklist_not_found'


class ZoneNotFound(NotFound):
    error_type = 'zone_not_found'

class AclNotFound(NotFound):
    error_type = 'acl_not_found'

class ZoneMasterNotFound(NotFound):
    error_type = 'zone_master_not_found'


class ZoneAttributeNotFound(NotFound):
    error_type = 'zone_attribute_not_found'


class TldNotFound(NotFound):
    error_type = 'tld_not_found'


class RecordSetNotFound(NotFound):
    error_type = 'recordset_not_found'


class RecordNotFound(NotFound):
    error_type = 'record_not_found'


class AllFailed(Failed):
    error_type = 'all record-create failed'


class PartlyFailed(Failed):
    error_type = 'some record-create failed'


class ReportNotFound(NotFound):
    error_type = 'report_not_found'


class PoolManagerStatusNotFound(NotFound):
    error_type = 'pool_manager_status_not_found'


class PoolNotFound(NotFound):
    error_type = 'pool_not_found'


class NoValidPoolFound(NotFound):
    error_type = 'no_valid_pool_found'


class PoolAttributeNotFound(NotFound):
    error_type = 'pool_attribute_not_found'


class PoolNsRecordNotFound(NotFound):
    error_type = 'pool_ns_record_not_found'


class PoolNameserverNotFound(NotFound):
    error_type = 'pool_nameserver_not_found'


class PoolTargetNotFound(NotFound):
    error_type = 'pool_target_not_found'


class PoolTargetOptionNotFound(NotFound):
    error_type = 'pool_target_option_not_found'


class PoolTargetMasterNotFound(NotFound):
    error_type = 'pool_target_master_not_found'


class PoolAlsoNotifyNotFound(NotFound):
    error_type = 'pool_also_notify_not_found'


class ZoneTransferRequestNotFound(NotFound):
    error_type = 'zone_transfer_request_not_found'


class ZoneTransferAcceptNotFound(NotFound):
    error_type = 'zone_transfer_accept_not_found'


class ZoneImportNotFound(NotFound):
    error_type = 'zone_import_not_found'


class ZoneExportNotFound(NotFound):
    error_type = 'zone_export_not_found'
    
    
class ViewNotFound(NotFound):
    error_type = 'view_not_found'


class ViewAclNotFound(NotFound):
    error_type = 'view_acl_not_found'


class AclsIsNone(NotFound):
    error_type = 'acl_ids_is_none'


class ParamsIsNotLegal(NotFound):
    error_type = 'params_is_not_legal'


class AclidsMustBeList(NotFound):
    error_type = 'acl_ids_must_be_list'


class CreateViewFailed(NotFound):
    error_type = 'create_view_failed'


class LastServerDeleteNotAllowed(BadRequest):
    error_type = 'last_server_delete_not_allowed'



EZDNS = {
        "1": "any or none acl is read only",
        "2": "acl already exists",
        "3": "operate non-exist acl",
        "4": "dns64 prefix should be a ipv6 addr",
        "5": "invalid dns64 prefix netmask",
        "6": "suffix is needed if netmask of prefix smaller than 96",
        "7": "DNS64 setting already exists",
        "8": "operate non-exist DNS64 setting",
        "9": "tsig key already exists",
        "10": "delete acl is using by view",
        "11": "operate non-exist zone",
        "12": "cache file not exist",
        "13": "cache size too large",
        "14": "operate non-exist view",
        "15": "get zone from backend server failed",
        "16": "zone already exists",
        "17": "unsupported meta data type",
        "18": "view already exists",
        "19": "delete default view",
        "20": "cann't modify acl of default view",
        "21": "operate non-exist rr",
        "22": "conflict key secret",
        "23": "not supported zone type",
        "24": "operate non-exist shared rr",
        "25": "cann't delete the last shared rr",
        "26": "operate non-exist tsig key",
        "27": "reconfig dns server failed",
        "28": "no rndc-confgen installed",
        "29": "lack/white list already exists",
        "30": "operate non-exist back/white list",
        "31": "zone owner doesn't has view owner",
        "32": "unsupport acl action",
        "33": "no pine-control installed",
        "34": "server already started",
        "35": "RR format error",
        "36": "zone transfer failed",
        "37": "more than one ad zone owner",
        "38": "update zone failed",
        "39": "shared rr already exists",
        "40": "add duplicate rr",
        "41": "add exclusive rr",
        "42": "short of glue rr",
        "43": "conflict with exists cname",
        "44": "delete unknown rr",
        "45": "can't delete soa rr",
        "46": "no ns left after delete",
        "47": "delete glue needed by other rr",
        "48": "reverse zone doesn't exist",
        "49": "rdata is valid",
        "50": "rr is out of zone",
        "51": "onfigure value isn't valid",
        "52": "unknown forward style",
        "53": "duplicate zone master",
        "54": "forwarder exists",
        "55": "operate non-exist forwarder",
        "56": "operate non-exist view on node",
        "57": "already exists root zone",
        "58": "only A/AAAA NS is allowed in hint zone",
        "59": "already has root configuration",
        "60": "rr type isn't supported",
        "61": "can't update slave zone",
        "62": "duplicate local domain policy",
        "63": "zone name isn't valid",
        "64": "add duplicate host",
        "65": "soa serial number degraded",
        "66": "root isn't support in local policy",
        "67": "auth zone with same name already exists",
        "68": "stub zone with same name already exists",
        "69": "forward zone with same name already exists",
        "70": "acl is used by view",
        "71": "acl is used by AD zone",
        "72": "rrl policy already exist",
        "73": "non-exist rrl policy",
        "74": "delete monitor strategy in use",
        "75": "monitor strategy already exist",
        "76": "non exist monitor strategy",
        "77": "node's view querysource already exists",
        "78": "node's view querysource not exist",
        "79": "too much rrls(over 999)",
        "100": "version is unknown",
        "101": "patch file broken",
        "102": "source code isn't a release version",
        "103": "binding different iface with same ip address",
        "104": "ntp interval out of range",
        "105": "send a test mail failed, check the configuration",
        "300": "invalid ip address",
        "301": "no dns server installed",
        "302": "not enough params",
        "303": "not supported backup method",
        "304": "not supported command method",
        "305": "service hasn't been init",
        "306": "not supported ha type",
        "307": "member is not accessible",
        "308": "wrong username and password",
        "309": "nic config failed",
        "310": "service hasn't been started",
        "311": "init params is required",
        "312": "invalid port",
        "313": "verify node failed",
        "314": "request body json format error",
        "315": "connect backup server timeout",
        "316": "data recovery failed",
        "317": "data backup failed",
        "318": "lower limit bigger than upper limit",
        "319": "execute command timeout",
        "320": "password/role failed",
        "404": "Wrong url, please check it",
        "421": "Equipment internal error !",
        "600": "operate non-exist group",
        "601": "member with same ip alreasy exists",
        "602": "member with same name alreasy exists",
        "603": "operate non-exist member",
        "604": "not supported service type",
        "605": "member command queue is full",
        "606": "member is performing data recovery",
        "607": "group already exists",
        "608": "cann't operate local group",
        "609": "user already exists",
        "610": "operate non-exist user",
        "611": "init member service failed",
        "612": "owners is required",
        "613": "cann't delete the last owner for resource",
        "614": "add duplicate owners",
        "615": "old password is wrong",
        "616": "cann't delete local group",
        "617": "cann't delete local member",
        "618": "permission denied",
        "619": "unkown authority rule",
        "620": "authority rule already exist",
        "621": "invalid backup data",
        "622": "device already under management",
        "623": "some devices don't exist any more",
        "624": "cann't operation inactive cloud",
        "625": "cann't add multi backup devices",
        "626": "no backup device",
        "627": "not master device",
        "628": "not backup device",
        "629": "not slave device",
        "630": "hasn't managed by cloud yet",
        "631": "node can't communicate with master",
        "632": "invalid exception handle method",
        "800": "time out while sending alarm msg"
}


class ZdnsErrMessage(Base):
    error_type = "Equipment Internal Error"
    expected = True

    def __init__(self,*args,**kwargs):
        self.errors = kwargs.pop('errors', None)
        self.object = kwargs.pop('object', None)
        super(Base, self).__init__(*args, **kwargs)
        if len(args) > 0 and isinstance(args[0], six.string_types):
            self.error_message = str(args[0]) + ": " + EZDNS[args[0]]


    # @staticmethod
    # def getmsg(cord):
    #     msg = str(cord) + ": " + EZDNS[cord]
    #     return msg



class AclUsedByView(Base):
    error_type = 'acl used by view'