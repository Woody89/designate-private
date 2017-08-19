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
import time
import hashlib

from oslo_config import cfg
from oslo_log import log as logging
from oslo_db import options
from sqlalchemy import select, distinct, func
from sqlalchemy.sql.expression import or_
from oslo_db import exception as oslo_db_exception

from designate import exceptions
from designate import objects
from designate.i18n import _LI
from designate.sqlalchemy import base as sqlalchemy_base
from designate.storage import base as storage_base
from designate.storage.impl_sqlalchemy import tables
from oslo_db import exception as oslo_db_exception
from designate.sqlalchemy import utils


LOG = logging.getLogger(__name__)

MAXIMUM_SUBZONE_DEPTH = 128

cfg.CONF.register_group(cfg.OptGroup(
    name='storage:sqlalchemy', title="Configuration for SQLAlchemy Storage"
))

cfg.CONF.register_opts(options.database_opts, group='storage:sqlalchemy')


class SQLAlchemyStorage(sqlalchemy_base.SQLAlchemy, storage_base.Storage):
    """SQLAlchemy connection"""
    __plugin_name__ = 'sqlalchemy'

    def __init__(self):
        super(SQLAlchemyStorage, self).__init__()

    def get_name(self):
        return self.name

    # CRUD for our resources (quota, server, tsigkey, tenant, zone & record)
    # R - get_*, find_*s
    #
    # Standard Arguments
    # self      - python object for the class
    # context   - a dictionary of details about the request (http etc),
    #             provided by flask.
    # criterion - dictionary of filters to be applied
    #

    # Quota Methods
    def _find_quotas(self, context, criterion, one=False, marker=None,
                     limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.quotas, objects.Quota, objects.QuotaList,
            exceptions.QuotaNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_quota(self, context, quota):
        if not isinstance(quota, objects.Quota):
            # TODO(kiall): Quotas should always use Objects
            quota = objects.Quota(**quota)

        return self._create(
            tables.quotas, quota, exceptions.DuplicateQuota)

    def get_quota(self, context, quota_id):
        return self._find_quotas(context, {'id': quota_id}, one=True)

    def find_quotas(self, context, criterion=None, marker=None, limit=None,
                    sort_key=None, sort_dir=None):
        return self._find_quotas(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir)

    def find_quota(self, context, criterion):
        return self._find_quotas(context, criterion, one=True)

    def update_quota(self, context, quota):
        return self._update(
            context, tables.quotas, quota, exceptions.DuplicateQuota,
            exceptions.QuotaNotFound)

    def delete_quota(self, context, quota_id):
        # Fetch the existing quota, we'll need to return it.
        quota = self._find_quotas(context, {'id': quota_id}, one=True)
        return self._delete(context, tables.quotas, quota,
                            exceptions.QuotaNotFound)

    # TLD Methods
    def _find_tlds(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tlds, objects.Tld, objects.TldList,
            exceptions.TldNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tld(self, context, tld):
        return self._create(
            tables.tlds, tld, exceptions.DuplicateTld)

    def get_tld(self, context, tld_id):
        return self._find_tlds(context, {'id': tld_id}, one=True)

    def find_tlds(self, context, criterion=None, marker=None, limit=None,
                  sort_key=None, sort_dir=None):
        return self._find_tlds(context, criterion, marker=marker, limit=limit,
                               sort_key=sort_key, sort_dir=sort_dir)

    def find_tld(self, context, criterion):
        return self._find_tlds(context, criterion, one=True)

    def update_tld(self, context, tld):
        return self._update(
            context, tables.tlds, tld, exceptions.DuplicateTld,
            exceptions.TldNotFound)

    def delete_tld(self, context, tld_id):
        # Fetch the existing tld, we'll need to return it.
        tld = self._find_tlds(context, {'id': tld_id}, one=True)
        return self._delete(context, tables.tlds, tld, exceptions.TldNotFound)

    # TSIG Key Methods
    def _find_tsigkeys(self, context, criterion, one=False, marker=None,
                       limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.tsigkeys, objects.TsigKey, objects.TsigKeyList,
            exceptions.TsigKeyNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def create_tsigkey(self, context, tsigkey):
        return self._create(
            tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey)

    def get_tsigkey(self, context, tsigkey_id):
        return self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)

    def find_tsigkeys(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        return self._find_tsigkeys(context, criterion, marker=marker,
                                   limit=limit, sort_key=sort_key,
                                   sort_dir=sort_dir)

    def find_tsigkey(self, context, criterion):
        return self._find_tsigkeys(context, criterion, one=True)

    def update_tsigkey(self, context, tsigkey):
        return self._update(
            context, tables.tsigkeys, tsigkey, exceptions.DuplicateTsigKey,
            exceptions.TsigKeyNotFound)

    def delete_tsigkey(self, context, tsigkey_id):
        # Fetch the existing tsigkey, we'll need to return it.
        tsigkey = self._find_tsigkeys(context, {'id': tsigkey_id}, one=True)
        return self._delete(context, tables.tsigkeys, tsigkey,
                            exceptions.TsigKeyNotFound)

    ##
    # Tenant Methods
    ##
    def find_tenants(self, context):
        # returns an array of tenant_id & count of their zones
        query = select([tables.zones.c.tenant_id,
                        func.count(tables.zones.c.id)])
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)
        query = query.group_by(tables.zones.c.tenant_id)

        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        tenant_list = objects.TenantList(
            objects=[objects.Tenant(id=t[0], zone_count=t[1]) for t in
                     results])

        tenant_list.obj_reset_changes()

        return tenant_list

    def get_tenant(self, context, tenant_id):
        # get list list & count of all zones owned by given tenant_id
        query = select([tables.zones.c.name])
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)
        query = query.where(tables.zones.c.tenant_id == tenant_id)

        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()

        return objects.Tenant(
            id=tenant_id,
            zone_count=len(results),
            zones=[r[0] for r in results])

    def count_tenants(self, context):
        # tenants are the owner of zones, count the number of unique tenants
        # select count(distinct tenant_id) from zones
        query = select([func.count(distinct(tables.zones.c.tenant_id))])
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    ##
    # Zone Methods
    ##
    def _find_zones(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        zones = self._find(
            context, tables.zones, objects.Zone, objects.ZoneList,
            exceptions.ZoneNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

        def _load_relations(zone):
            if zone.type == 'SECONDARY':
                zone.masters = self._find_zone_masters(
                    context, {'zone_id': zone.id})
            else:
                # This avoids an extra DB call per primary zone. This will
                # always have 0 results for a PRIMARY zone.
                zone.masters = objects.ZoneMasterList()

            zone.attributes = self._find_zone_attributes(
                context, {'zone_id': zone.id, "key": "!master"})

            zone.obj_reset_changes(['masters', 'attributes'])

        # TODO(Federico) refactor part of _find_zones into _find_zone, move
        # _load_relations out

        if one:
            _load_relations(zones)
        else:
            zones.total_count = self.count_zones(context, criterion)
            for d in zones:
                _load_relations(d)

        if one:
            LOG.debug("Fetched zone %s", zones)
        return zones

    def get_zone_asso(self,context,value):
        return self._find_asso( context,tables.zone_associations,
                                "zone_id", value.id, exceptions.ZoneNotFound)

    def create_acl(self, context, acl):
        # Don't handle recordsets for now
        if not acl.get("tenant_id"):
            acl.tenant_id = context.tenant
        acl = self._create(
            tables.acls, acl, exceptions.DuplicateAcl)
        return acl

    def update_acl(self, context, acl):
        return self._update(
            context, tables.acls, acl, exceptions.DuplicateAcl,
            exceptions.AclNotFound)

    def _find_acls(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.acls, objects.Acl, objects.AclList,
            exceptions.AclNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def find_acls(self, context, criterion=None, marker=None, limit=None,
                      sort_key=None, sort_dir=None):
        return self._find_acls(context, criterion, marker=marker,
                                   limit=limit, sort_key=sort_key,
                                   sort_dir=sort_dir)

    def find_acl(self, context, criterion):
        return self._find_acls(context, criterion, one=True)

    def get_acl(self, context, acl_id):
        return self._find_acls(context, {'id': acl_id}, one=True)

    def delete_acl(self, context, acl_id):
        # Fetch the existing acl, we'll need to return it.
        acl = self._find_acls(context, {'id': acl_id}, one=True)
        return self._delete(context, tables.acls, acl,
                            exceptions.AclNotFound)

    def create_zdns_acl(self, context, acl):
        # Patch in the reverse_name column

        # Don't handle recordsets for now\
        self._create_zdns_acl(
            tables.zdns_acls, acl, exceptions.DuplicateAcl,)

    def create_acl_asso(self, context, acl):
        # Patch in the reverse_name column

        # Don't handle recordsets for now\
        self._create_acl_asso(
            tables.acl_associations, acl, exceptions.DuplicateAcl)

    def delete_zdns_acl(self, context, acl):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._delete_zdns_acl(context,
                              tables.zdns_acls, acl, exceptions.DuplicateAcl, )

    def delete_acl_asso(self, context, acl):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._delete_acl_asso(context,
                               tables.acl_associations, acl, exceptions.DuplicateAcl)



    def update_zdns_acl(self, context, acl, values):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._update_zdns_acl(context,
                              tables.zdns_acls, acl, values, exceptions.DuplicateAcl)

    def get_acl_asso(self, context, value):
        return self._find_asso(context, tables.acl_associations, "acl_id", value.id, exceptions.AclNotFound)

    def get_acl_view_asso(self, context, value):
        return self._find_asso(context, tables.view_acl, "acl_id", value, exceptions.AclNotFound)

    def create_zone(self, context, zone):
        # Patch in the reverse_name column
        extra_values = {"reverse_name": zone.name[::-1]}

        # Don't handle recordsets for now
        zone = self._create(
            tables.zones, zone, exceptions.DuplicateZone,
            ['attributes', 'recordsets', 'masters'],
            extra_values=extra_values)

        if zone.obj_attr_is_set('attributes'):
            for attrib in zone.attributes:
                self.create_zone_attribute(context, zone.id, attrib)
        else:
            zone.attributes = objects.ZoneAttributeList()
        if zone.obj_attr_is_set('masters'):
            for master in zone.masters:
                self.create_zone_master(context, zone.id, master)
        else:
            zone.masters = objects.ZoneMasterList()
        zone.obj_reset_changes(['masters', 'attributes'])

        return zone

    def get_zone(self, context, zone_id):
        zone = self._find_zones(context, {'id': zone_id}, one=True)
        return zone

    def find_zones(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        zones = self._find_zones(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir)
        return zones

    def find_zone(self, context, criterion):
        zone = self._find_zones(context, criterion, one=True)
        return zone

    def update_zone(self, context, zone):
        tenant_id_changed = False
        if 'tenant_id' in zone.obj_what_changed():
            tenant_id_changed = True

        # Don't handle recordsets for now
        LOG.debug("Updating zone %s", zone)
        updated_zone = self._update(
            context, tables.zones, zone, exceptions.DuplicateZone,
            exceptions.ZoneNotFound,
            ['attributes', 'recordsets', 'masters'])

        if zone.obj_attr_is_set('attributes'):
            # Gather the Attribute ID's we have
            have = set([r.id for r in self._find_zone_attributes(
                context, {'zone_id': zone.id})])

            # Prep some lists of changes
            keep = set([])
            create = []
            update = []

            # Determine what to change
            for i in zone.attributes:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "zone.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_zone_attributes(
                    context, {'id': i_id}, one=True)
                self.delete_zone_attribute(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_zone_attribute(context, i)

            # Create Attributes
            for attr in create:
                attr.zone_id = zone.id
                self.create_zone_attribute(context, zone.id, attr)

        if zone.obj_attr_is_set('masters'):
            # Gather the Attribute ID's we have
            have = set([r.id for r in self._find_zone_masters(
                context, {'zone_id': zone.id})])

            # Prep some lists of changes
            keep = set([])
            create = []
            update = []

            # Determine what to change
            for i in zone.masters:
                keep.add(i.id)
                try:
                    i.obj_get_original_value('id')
                except KeyError:
                    create.append(i)
                else:
                    update.append(i)

            # NOTE: Since we're dealing with mutable objects, the return value
            #       of create/update/delete attribute is not needed.
            #       The original item will be mutated in place on the input
            #       "zone.attributes" list.

            # Delete Attributes
            for i_id in have - keep:
                attr = self._find_zone_masters(
                    context, {'id': i_id}, one=True)
                self.delete_zone_master(context, attr.id)

            # Update Attributes
            for i in update:
                self.update_zone_master(context, i)

            # Create Attributes
            for attr in create:
                attr.zone_id = zone.id
                self.create_zone_master(context, zone.id, attr)

        if zone.obj_attr_is_set('recordsets'):
            existing = self.find_recordsets(context, {'zone_id': zone.id})

            data = {}
            for rrset in existing:
                data[rrset.name, rrset.type] = rrset

            keep = set()
            for rrset in zone.recordsets:
                current = data.get((rrset.name, rrset.type))

                if current:
                    current.update(rrset)
                    current.records = rrset.records
                    self.update_recordset(context, current)
                    keep.add(current.id)
                else:
                    self.create_recordset(context, zone.id, rrset)
                    keep.add(rrset.id)

            if zone.type == 'SECONDARY':
                # Purge anything that shouldn't be there :P
                for i in set([i.id for i in data.values()]) - keep:
                    self.delete_recordset(context, i)

        if tenant_id_changed:
            recordsets_query = tables.recordsets.update().\
                where(tables.recordsets.c.zone_id == zone.id)\
                .values({'tenant_id': zone.tenant_id})

            records_query = tables.records.update().\
                where(tables.records.c.zone_id == zone.id).\
                values({'tenant_id': zone.tenant_id})

            self.session.execute(records_query)
            self.session.execute(recordsets_query)

        return updated_zone

    def delete_zone(self, context, zone_id):
        """
        """
        # Fetch the existing zone, we'll need to return it.
        zone = self._find_zones(context, {'id': zone_id}, one=True)
        return self._delete(context, tables.zones, zone,
                            exceptions.ZoneNotFound)

    def purge_zone(self, context, zone):
        """Effectively remove a zone database record.
        """
        return self._delete(context, tables.zones, zone,
                            exceptions.ZoneNotFound, hard_delete=True)

    def _walk_up_zones(self, current, zones_by_id):
        """Walk upwards in a zone hierarchy until we find a parent zone
        that does not belong to "zones_by_id"
        :returns: parent zone ID or None
        """
        max_steps = MAXIMUM_SUBZONE_DEPTH
        while current.parent_zone_id in zones_by_id:
            current = zones_by_id[current.parent_zone_id]
            max_steps -= 1
            if max_steps == 0:
                raise exceptions.IllegalParentZone("Loop detected in the"
                                                   " zone hierarchy")

        return current.parent_zone_id

    def purge_zones(self, context, criterion, limit):
        """Purge deleted zones.
        Reparent orphan childrens, if any.
        Transactions/locks are not needed.
        :returns: number of purged zones
        """
        if 'deleted' in criterion:
            context.show_deleted = True

        zones = self.find_zones(
            context=context,
            criterion=criterion,
            limit=limit,
        )
        if not zones:
            LOG.info(_LI("No zones to be purged"))
            return

        LOG.debug(_LI("Purging %d zones"), len(zones))

        zones_by_id = {z.id: z for z in zones}

        for zone in zones:

            # Reparent child zones, if any.
            surviving_parent_id = self._walk_up_zones(zone, zones_by_id)
            query = tables.zones.update().\
                where(tables.zones.c.parent_zone_id == zone.id).\
                values(parent_zone_id=surviving_parent_id)

            resultproxy = self.session.execute(query)
            LOG.debug(_LI("%d child zones updated"), resultproxy.rowcount)

            self.purge_zone(context, zone)

        LOG.info(_LI("Purged %d zones"), len(zones))
        return len(zones)

    def count_zones(self, context, criterion=None):
        query = select([func.count(tables.zones.c.id)])
        query = self._apply_criterion(tables.zones, query, criterion)
        query = self._apply_tenant_criteria(context, tables.zones, query)
        query = self._apply_deleted_criteria(context, tables.zones, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Zone attribute methods
    def _find_zone_attributes(self, context, criterion, one=False,
                              marker=None, limit=None, sort_key=None,
                              sort_dir=None):
        return self._find(context, tables.zone_attributes,
                          objects.ZoneAttribute, objects.ZoneAttributeList,
                          exceptions.ZoneAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_zone_attribute(self, context, zone_id, zone_attribute):
        zone_attribute.zone_id = zone_id
        return self._create(tables.zone_attributes, zone_attribute,
                            exceptions.DuplicateZoneAttribute)

    def get_zone_attributes(self, context, zone_attribute_id):
        return self._find_zone_attributes(
            context, {'id': zone_attribute_id}, one=True)

    def find_zone_attributes(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_attributes(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_zone_attribute(self, context, criterion):
        return self._find_zone_attributes(context, criterion, one=True)

    def update_zone_attribute(self, context, zone_attribute):
        return self._update(context, tables.zone_attributes,
                            zone_attribute,
                            exceptions.DuplicateZoneAttribute,
                            exceptions.ZoneAttributeNotFound)

    def delete_zone_attribute(self, context, zone_attribute_id):
        zone_attribute = self._find_zone_attributes(
            context, {'id': zone_attribute_id}, one=True)
        deleted_zone_attribute = self._delete(
            context, tables.zone_attributes, zone_attribute,
            exceptions.ZoneAttributeNotFound)

        return deleted_zone_attribute

    # Zone master methods
    def _find_zone_masters(self, context, criterion, one=False,
                           marker=None, limit=None, sort_key=None,
                           sort_dir=None):

        return self._find(context, tables.zone_masters,
                          objects.ZoneMaster, objects.ZoneMasterList,
                          exceptions.ZoneMasterNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_zone_master(self, context, zone_id, zone_master):

        zone_master.zone_id = zone_id
        return self._create(tables.zone_masters, zone_master,
                            exceptions.DuplicateZoneMaster)

    def get_zone_masters(self, context, zone_attribute_id):
        return self._find_zone_masters(
            context, {'id': zone_attribute_id}, one=True)

    def find_zone_masters(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_masters(context, criterion, marker=marker,
                                       limit=limit, sort_key=sort_key,
                                       sort_dir=sort_dir)

    def find_zone_master(self, context, criterion):
        return self._find_zone_master(context, criterion, one=True)

    def update_zone_master(self, context, zone_master):

        return self._update(context, tables.zone_masters,
                            zone_master,
                            exceptions.DuplicateZoneMaster,
                            exceptions.ZoneMasterNotFound)

    def delete_zone_master(self, context, zone_master_id):
        zone_master = self._find_zone_masters(
            context, {'id': zone_master_id}, one=True)
        deleted_zone_master = self._delete(
            context, tables.zone_masters, zone_master,
            exceptions.ZoneMasterNotFound)

        return deleted_zone_master

    # RecordSet Methods
    def _find_recordsets(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None,
                         force_index=False):

        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        if criterion is not None \
                and not criterion.get('zones_deleted', True):
            # remove 'zones_deleted' from the criterion, as _apply_criterion
            # assumes each key in criterion to be a column name.
            del criterion['zones_deleted']

        if one:
            rjoin = tables.recordsets.join(
                tables.zones,
                tables.recordsets.c.zone_id == tables.zones.c.id)
            query = select([tables.recordsets]).select_from(rjoin).\
                where(tables.zones.c.deleted == '0')

            recordsets = self._find(
                context, tables.recordsets, objects.RecordSet,
                objects.RecordSetList, exceptions.RecordSetNotFound, criterion,
                one, marker, limit, sort_key, sort_dir, query)

            recordsets.records = self._find_records(
                context, {'recordset_id': recordsets.id})

            recordsets.obj_reset_changes(['records'])

        else:
            tc, recordsets = self._find_recordsets_with_records(
                    context, criterion, tables.zones, tables.recordsets,
                    tables.records, limit=limit, marker=marker,
                    sort_key=sort_key, sort_dir=sort_dir,
                    force_index=force_index)

            recordsets.total_count = tc

        return recordsets

    def find_recordsets_axfr(self, context, criterion=None):
        query = None

        # Check to see if the criterion can use the reverse_name column
        criterion = self._rname_check(criterion)

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = select([tables.recordsets.c.id, tables.recordsets.c.type,
                        tables.recordsets.c.ttl, tables.recordsets.c.name,
                        tables.records.c.data, tables.records.c.action]).\
            select_from(rjoin).where(tables.records.c.action != 'DELETE')

        query = query.order_by(tables.recordsets.c.id)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def create_recordset(self, context, zone_id, recordset):
        # Fetch the zone as we need the tenant_id
        zone = self._find_zones(context, {'id': zone_id}, one=True)

        recordset.tenant_id = zone.tenant_id
        recordset.zone_id = zone_id

        # Patch in the reverse_name column
        extra_values = {"reverse_name": recordset.name[::-1]}

        recordset = self._create(
            tables.recordsets, recordset, exceptions.DuplicateRecordSet,
            ['records'], extra_values=extra_values)

        return recordset

    def create_zdns_record(self, context, zdns_record):
        return self._create_zdns_record(
            tables.zdns_record, zdns_record, exceptions.Duplicate)

    def _create_zdns_record(self, table, obj, exc_dup, skip_values=None,
                            extra_values=None):
        query = table.insert()
        try:
            self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = 'Duplicate %s' % obj.obj_name()
            raise exc_dup(msg)

    def create_record_association(self, context, record_association):
        return self._create_record_association(
            tables.record_association, record_association, exceptions.Duplicate)

    def _create_record_association(
            self, table, obj, exc_dup, skip_values=None, extra_values=None):
        query = table.insert()
        try:
            self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = 'Duplicate %s' % obj.obj_name()
            raise exc_dup(msg)

    def find_recordsets_export(self, context, criterion=None):
        query = None

        rjoin = tables.records.join(
            tables.recordsets,
            tables.records.c.recordset_id == tables.recordsets.c.id)

        query = select([tables.recordsets.c.name, tables.recordsets.c.ttl,
                        tables.recordsets.c.type, tables.records.c.data]).\
            select_from(rjoin)

        query = query.order_by(tables.recordsets.c.created_at)

        raw_rows = self._select_raw(
            context, tables.recordsets, criterion, query)

        return raw_rows

    def get_recordset(self, context, recordset_id):
        return self._find_recordsets(context, {'id': recordset_id.replace('-', '')}, one=True)

    def find_recordsets(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None, force_index=False):
        return self._find_recordsets(context, criterion, marker=marker,
                                     sort_dir=sort_dir, sort_key=sort_key,
                                     limit=limit, force_index=force_index)

    def find_recordset(self, context, criterion):
        return self._find_recordsets(context, criterion, one=True)

    def update_zdns_record_in_storage(self, context, zdns_record):
        zdns_record = self._update(context, tables.zdns_record,
                                   zdns_record, exceptions.DuplicateRecordSet,
                                   exceptions.RecordSetNotFound)
        return zdns_record

    def update_recordset(self, context, recordset):
        recordset = self._update(
            context, tables.recordsets, recordset,
            exceptions.DuplicateRecordSet, exceptions.RecordSetNotFound,
            ['records'])

#         if recordset.obj_attr_is_set('records'):
#             # Gather the Record ID's we have
#             have_records = set([r.id for r in self._find_records(
#                 context, {'recordset_id': recordset.id})])
#
#             # Prep some lists of changes
#             keep_records = set([])
#             create_records = []
#             update_records = []
#
#             # Determine what to change
#             for record in recordset.records:
#                 keep_records.add(record.id)
#                 try:
#                     record.obj_get_original_value('id')
#                 except KeyError:
#                     create_records.append(record)
#                 else:
#                     update_records.append(record)
#
#             # NOTE: Since we're dealing with mutable objects, the return value
#             #       of create/update/delete record is not needed. The original
#             #       item will be mutated in place on the input
#             #       "recordset.records" list.
#
#             # Delete Records
#             for record_id in have_records - keep_records:
#                 self.delete_record(context, record_id)
#
#             # Update Records
#             for record in update_records:
#                 self.update_record(context, record)
#
#             # Create Records
#             for record in create_records:
#                 self.create_record(
#                     context, recordset.zone_id, recordset.id, record)

        return recordset

    def delete_recordset(self, context, recordset_id):
        # Fetch the existing recordset, we'll need to return it.
        recordset = self._find_recordsets(
            context, {'id': recordset_id}, one=True)

        return self._delete(context, tables.recordsets, recordset,
                            exceptions.RecordSetNotFound)

    def count_recordsets(self, context, criterion=None):
        # Ensure that we return only active recordsets
        rjoin = tables.recordsets.join(
            tables.zones,
            tables.recordsets.c.zone_id == tables.zones.c.id)

        query = select([func.count(tables.recordsets.c.id)]).\
            select_from(rjoin).\
            where(tables.zones.c.deleted == '0')

        query = self._apply_criterion(tables.recordsets, query, criterion)
        query = self._apply_tenant_criteria(context, tables.recordsets, query)
        query = self._apply_deleted_criteria(context, tables.recordsets, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Record Methods
    def _find_records(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.records, objects.Record, objects.RecordList,
            exceptions.RecordNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def _find_zdns_record(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.zdns_record, objects.ZdnsRecord, objects.ZdnsRecordList,
            exceptions.RecordNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def _find_record_association(self, context, criterion, one=False, marker=None,
                      limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.record_association, objects.RecordAssociation, objects.RecordAssociationList,
            exceptions.RecordNotFound, criterion, one, marker, limit,
            sort_key, sort_dir)

    def _recalculate_record_hash(self, record):
        """
        Calculates the hash of the record, used to ensure record uniqueness.
        """
        md5 = hashlib.md5()
        md5.update(("%s:%s" % (record.recordset_id,
                               record.data)).encode('utf-8'))

        return md5.hexdigest()

    def create_record(self, context, zone_id, recordset_id, record):
        # Fetch the zone as we need the tenant_id
        zone = self._find_zones(context, {'id': zone_id}, one=True)

        record.tenant_id = zone.tenant_id
        record.zone_id = zone_id
        record.recordset_id = recordset_id
        record.hash = self._recalculate_record_hash(record)

        return self._create(
            tables.records, record, exceptions.DuplicateRecord)

    def get_record(self, context, record_id):
        return self._find_records(context, {'id': record_id}, one=True)

    def get_record_association(self, context, record_id):
        return self._find_record_association(context, {'record_id': record_id.replace('-', '')}, one=True)

    def get_zdns_record(self, context, zdns_record_id):
        return self._find_zdns_record(context, {'id': zdns_record_id
                                                }, one=True)

    def find_records(self, context, criterion=None, marker=None, limit=None,
                     sort_key=None, sort_dir=None):
        return self._find_records(context, criterion, marker=marker,
                                  limit=limit, sort_key=sort_key,
                                  sort_dir=sort_dir)

    def find_record(self, context, criterion):
        return self._find_records(context, criterion, one=True)

    def update_record(self, context, record):
        if record.obj_what_changed():
            record.hash = self._recalculate_record_hash(record)

        return self._update(
            context, tables.records, record, exceptions.DuplicateRecord,
            exceptions.RecordNotFound)

    def delete_record(self, context, record_id):
        # Fetch the existing record, we'll need to return it.
        record = self._find_records(context, {'id': record_id}, one=True)
        return self._delete(context, tables.records, record,
                            exceptions.RecordNotFound)

    def delete_zdns_record(self, context, id):
        zdns_record = self._find_zdns_record(context, {'id': id}, one=True)
        return self._delete(context, tables.zdns_record, zdns_record,
                            exceptions.RecordNotFound)

    def delete_record_association(self, context, record_id):
        # Fetch the existing record, we'll need to return it.
        record_association = self._find_record_association(
            context, {'record_id': record_id}, one=True)
        return self._delete(context, tables.record_association, record_association,
                            exceptions.RecordNotFound)

    def count_records(self, context, criterion=None):
        # Ensure that we return only active records
        rjoin = tables.records.join(
            tables.zones,
            tables.records.c.zone_id == tables.zones.c.id)

        query = select([func.count(tables.records.c.id)]).\
            select_from(rjoin).\
            where(tables.zones.c.deleted == '0')

        query = self._apply_criterion(tables.records, query, criterion)
        query = self._apply_tenant_criteria(context, tables.records, query)
        query = self._apply_deleted_criteria(context, tables.records, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Blacklist Methods
    def _find_blacklists(self, context, criterion, one=False, marker=None,
                         limit=None, sort_key=None, sort_dir=None):
        return self._find(
            context, tables.blacklists, objects.Blacklist,
            objects.BlacklistList, exceptions.BlacklistNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

    def create_blacklist(self, context, blacklist):
        return self._create(
            tables.blacklists, blacklist, exceptions.DuplicateBlacklist)

    def get_blacklist(self, context, blacklist_id):
        return self._find_blacklists(context, {'id': blacklist_id}, one=True)

    def find_blacklists(self, context, criterion=None, marker=None, limit=None,
                        sort_key=None, sort_dir=None):
        return self._find_blacklists(context, criterion, marker=marker,
                                     limit=limit, sort_key=sort_key,
                                     sort_dir=sort_dir)

    def find_blacklist(self, context, criterion):
        return self._find_blacklists(context, criterion, one=True)

    def update_blacklist(self, context, blacklist):
        return self._update(
            context, tables.blacklists, blacklist,
            exceptions.DuplicateBlacklist, exceptions.BlacklistNotFound)

    def delete_blacklist(self, context, blacklist_id):
        # Fetch the existing blacklist, we'll need to return it.
        blacklist = self._find_blacklists(
            context, {'id': blacklist_id}, one=True)

        return self._delete(context, tables.blacklists, blacklist,
                            exceptions.BlacklistNotFound)

    # Pool methods
    def _find_pools(self, context, criterion, one=False, marker=None,
                    limit=None, sort_key=None, sort_dir=None):
        pools = self._find(context, tables.pools, objects.Pool,
                           objects.PoolList, exceptions.PoolNotFound,
                           criterion, one, marker, limit, sort_key,
                           sort_dir)

        # Load Relations
        def _load_relations(pool):
            pool.attributes = self._find_pool_attributes(
                context, {'pool_id': pool.id})

            pool.ns_records = self._find_pool_ns_records(
                context, {'pool_id': pool.id})

            pool.nameservers = self._find_pool_nameservers(
                context, {'pool_id': pool.id})

            pool.targets = self._find_pool_targets(
                context, {'pool_id': pool.id})

            pool.also_notifies = self._find_pool_also_notifies(
                context, {'pool_id': pool.id})

            pool.obj_reset_changes(['attributes', 'ns_records', 'nameservers',
                                    'targets', 'also_notifies'])

        if one:
            _load_relations(pools)
        else:
            for pool in pools:
                _load_relations(pool)

        return pools

    def create_pool(self, context, pool):
        pool = self._create(
            tables.pools, pool, exceptions.DuplicatePool,
            ['attributes', 'ns_records', 'nameservers', 'targets',
             'also_notifies'])

        if pool.obj_attr_is_set('attributes'):
            for pool_attribute in pool.attributes:
                self.create_pool_attribute(context, pool.id, pool_attribute)
        else:
            pool.attributes = objects.PoolAttributeList()

        if pool.obj_attr_is_set('ns_records'):
            for ns_record in pool.ns_records:
                self.create_pool_ns_record(context, pool.id, ns_record)
        else:
            pool.ns_records = objects.PoolNsRecordList()

        if pool.obj_attr_is_set('nameservers'):
            for nameserver in pool.nameservers:
                self.create_pool_nameserver(context, pool.id, nameserver)
        else:
            pool.nameservers = objects.PoolNameserverList()

        if pool.obj_attr_is_set('targets'):
            for target in pool.targets:
                self.create_pool_target(context, pool.id, target)
        else:
            pool.targets = objects.PoolTargetList()

        if pool.obj_attr_is_set('also_notifies'):
            for also_notify in pool.also_notifies:
                self.create_pool_also_notify(context, pool.id, also_notify)
        else:
            pool.also_notifies = objects.PoolAlsoNotifyList()

        pool.obj_reset_changes(['attributes', 'ns_records', 'nameservers',
                                'targets', 'also_notifies'])

        return pool

    def get_pool(self, context, pool_id):
        return self._find_pools(context, {'id': pool_id}, one=True)

    def find_pools(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pools(context, criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool(self, context, criterion):
        return self._find_pools(context, criterion, one=True)

    def update_pool(self, context, pool):
        pool = self._update(context, tables.pools, pool,
                            exceptions.DuplicatePool, exceptions.PoolNotFound,
                            ['attributes', 'ns_records', 'nameservers',
                             'targets', 'also_notifies'])

        for attribute_name in ('attributes', 'ns_records', 'nameservers',
                               'targets', 'also_notifies'):
            if pool.obj_attr_is_set(attribute_name):
                self._update_pool_items(context, pool, attribute_name)

        # Call get_pool to get the ids of all the attributes/ns_records
        # refreshed in the pool object
        updated_pool = self.get_pool(context, pool.id)

        return updated_pool

    def delete_pool(self, context, pool_id):
        pool = self._find_pools(context, {'id': pool_id}, one=True)

        return self._delete(context, tables.pools, pool,
                            exceptions.PoolNotFound)

    # Pool attribute methods
    def _find_pool_attributes(self, context, criterion, one=False, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_attributes,
                          objects.PoolAttribute, objects.PoolAttributeList,
                          exceptions.PoolAttributeNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_attribute(self, context, pool_id, pool_attribute):
        pool_attribute.pool_id = pool_id

        return self._create(tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute)

    def get_pool_attribute(self, context, pool_attribute_id):
        return self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)

    def find_pool_attributes(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_attributes(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_attribute(self, context, criterion):
        return self._find_pool_attributes(context, criterion, one=True)

    def update_pool_attribute(self, context, pool_attribute):
        return self._update(context, tables.pool_attributes, pool_attribute,
                            exceptions.DuplicatePoolAttribute,
                            exceptions.PoolAttributeNotFound)

    def delete_pool_attribute(self, context, pool_attribute_id):
        pool_attribute = self._find_pool_attributes(
            context, {'id': pool_attribute_id}, one=True)
        deleted_pool_attribute = self._delete(
            context, tables.pool_attributes, pool_attribute,
            exceptions.PoolAttributeNotFound)

        return deleted_pool_attribute

    # Pool ns_record methods
    def _find_pool_ns_records(self, context, criterion, one=False, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find(context, tables.pool_ns_records,
                          objects.PoolNsRecord, objects.PoolNsRecordList,
                          exceptions.PoolNsRecordNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_ns_record(self, context, pool_id, pool_ns_record):
        pool_ns_record.pool_id = pool_id

        return self._create(tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord)

    def get_pool_ns_record(self, context, pool_ns_record_id):
        return self._find_pool_ns_records(
            context, {'id': pool_ns_record_id}, one=True)

    def find_pool_ns_records(self, context, criterion=None, marker=None,
                             limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_ns_records(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_ns_record(self, context, criterion):
        return self._find_pool_ns_records(context, criterion, one=True)

    def update_pool_ns_record(self, context, pool_ns_record):
        return self._update(context, tables.pool_ns_records, pool_ns_record,
                            exceptions.DuplicatePoolNsRecord,
                            exceptions.PoolNsRecordNotFound)

    def delete_pool_ns_record(self, context, pool_ns_record_id):
        pool_ns_record = self._find_pool_ns_records(
            context, {'id': pool_ns_record_id}, one=True)
        deleted_pool_ns_record = self._delete(
            context, tables.pool_ns_records, pool_ns_record,
            exceptions.PoolNsRecordNotFound)

        return deleted_pool_ns_record

    # PoolNameserver methods
    def _find_pool_nameservers(self, context, criterion, one=False,
                               marker=None, limit=None, sort_key=None,
                               sort_dir=None):
        return self._find(context, tables.pool_nameservers,
                          objects.PoolNameserver, objects.PoolNameserverList,
                          exceptions.PoolNameserverNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_nameserver(self, context, pool_id, pool_nameserver):
        pool_nameserver.pool_id = pool_id

        return self._create(tables.pool_nameservers, pool_nameserver,
                            exceptions.DuplicatePoolNameserver)

    def get_pool_nameserver(self, context, pool_nameserver_id):
        return self._find_pool_nameservers(
            context, {'id': pool_nameserver_id}, one=True)

    def find_pool_nameservers(self, context, criterion=None, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_nameservers(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_nameserver(self, context, criterion):
        return self._find_pool_nameservers(context, criterion, one=True)

    def update_pool_nameserver(self, context, pool_nameserver):
        return self._update(context, tables.pool_nameservers, pool_nameserver,
                            exceptions.DuplicatePoolNameserver,
                            exceptions.PoolNameserverNotFound)

    def delete_pool_nameserver(self, context, pool_nameserver_id):
        pool_nameserver = self._find_pool_nameservers(
            context, {'id': pool_nameserver_id}, one=True)
        deleted_pool_nameserver = self._delete(
            context, tables.pool_nameservers, pool_nameserver,
            exceptions.PoolNameserverNotFound)

        return deleted_pool_nameserver

    # PoolTarget methods
    def _find_pool_targets(self, context, criterion, one=False, marker=None,
                           limit=None, sort_key=None, sort_dir=None):
        pool_targets = self._find(
            context, tables.pool_targets, objects.PoolTarget,
            objects.PoolTargetList, exceptions.PoolTargetNotFound,
            criterion, one, marker, limit, sort_key,
            sort_dir)

        # Load Relations
        def _load_relations(pool_target):
            pool_target.options = self._find_pool_target_options(
                context, {'pool_target_id': pool_target.id})

            pool_target.masters = self._find_pool_target_masters(
                context, {'pool_target_id': pool_target.id})

            pool_target.obj_reset_changes(['options', 'masters'])

        if one:
            _load_relations(pool_targets)
        else:
            for pool_target in pool_targets:
                _load_relations(pool_target)

        return pool_targets

    def create_pool_target(self, context, pool_id, pool_target):
        pool_target.pool_id = pool_id

        pool_target = self._create(
            tables.pool_targets, pool_target, exceptions.DuplicatePoolTarget,
            ['options', 'masters'])

        if pool_target.obj_attr_is_set('options'):
            for pool_target_option in pool_target.options:
                self.create_pool_target_option(
                    context, pool_target.id, pool_target_option)
        else:
            pool_target.options = objects.PoolTargetOptionList()

        if pool_target.obj_attr_is_set('masters'):
            for pool_target_master in pool_target.masters:
                self.create_pool_target_master(
                    context, pool_target.id, pool_target_master)
        else:
            pool_target.masters = objects.PoolTargetMasterList()

        pool_target.obj_reset_changes(['options', 'masters'])

        return pool_target

    def get_pool_target(self, context, pool_target_id):
        return self._find_pool_targets(
            context, {'id': pool_target_id}, one=True)

    def find_pool_targets(self, context, criterion=None, marker=None,
                          limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_targets(context, criterion, marker=marker,
                                limit=limit, sort_key=sort_key,
                                sort_dir=sort_dir)

    def find_pool_target(self, context, criterion):
        return self._find_pool_targets(context, criterion, one=True)

    def _update_pool_items(self, context, pool, attribute_name):
        """Update attributes beloging to a pool
        """
        assert attribute_name in ('attributes', 'ns_records', 'nameservers',
                                  'targets', 'also_notifies')

        # Gather the pool ID's we have
        finder = getattr(self, "_find_pool_%s" % attribute_name)
        have_items = set()
        for r in finder(context, {'pool_id': pool.id}):
            have_items.add(r.id)

        # Prep some lists of changes
        keep_items = set([])
        create_items = []
        update_items = []

        items = []
        if pool.obj_attr_is_set(attribute_name):
            for r in getattr(pool, attribute_name).objects:
                items.append(r)

        # Determine what to change
        for item in items:
            keep_items.add(item.id)
            try:
                item.obj_get_original_value('id')
            except KeyError:
                create_items.append(item)
            else:
                update_items.append(item)

        # NOTE: Since we're dealing with mutable objects, the return value
        #       of create/update/delete option is not needed. The
        #       original item will be mutated in place on the input
        #       "pool.options" list.

        # singular: attributes -> attribute, 'notify' is as a corner case
        if attribute_name == 'also_notifies':
            singular = 'also_notify'
        else:
            singular = attribute_name[:-1]

        # Delete items
        fn = getattr(self, "delete_pool_%s" % singular)
        for item_id in have_items - keep_items:
            fn(context, item_id)

        # Update items
        fn = getattr(self, "update_pool_%s" % singular)
        for item in update_items:
            fn(context, item)

        # Create items
        fn = getattr(self, "create_pool_%s" % singular)
        for item in create_items:
            fn(context, pool.id, item)

    def _update_pool_target_items(self, context, pool_target, attribute_name):
        """Update attributes beloging to a pool target
        """
        assert attribute_name in ('options', 'masters')

        # Gather the pool ID's we have
        finder = getattr(self, "_find_pool_target_%s" % attribute_name)
        have_items = set()
        for r in finder(context, {'pool_target_id': pool_target.id}):
            have_items.add(r.id)

        # Prep some lists of changes
        keep_items = set([])
        create_items = []
        update_items = []

        items = []
        if pool_target.obj_attr_is_set(attribute_name):
            for r in getattr(pool_target, attribute_name).objects:
                items.append(r)

        # Determine what to change
        for item in items:
            keep_items.add(item.id)
            try:
                item.obj_get_original_value('id')
            except KeyError:
                create_items.append(item)
            else:
                update_items.append(item)

        # NOTE: Since we're dealing with mutable objects, the return value
        #       of create/update/delete option is not needed. The
        #       original item will be mutated in place on the input
        #       "pool.options" list.

        # singular: options -> option
        singular = attribute_name[:-1]

        # Delete items
        fn = getattr(self, "delete_pool_target_%s" % singular)
        for item_id in have_items - keep_items:
            fn(context, item_id)

        # Update items
        fn = getattr(self, "update_pool_target_%s" % singular)
        for item in update_items:
            fn(context, item)

        # Create items
        fn = getattr(self, "create_pool_target_%s" % singular)
        for item in create_items:
            fn(context, pool_target.id, item)

    def update_pool_target(self, context, pool_target):
        pool_target = self._update(
            context, tables.pool_targets, pool_target,
            exceptions.DuplicatePoolTarget, exceptions.PoolTargetNotFound,
            ['options', 'masters'])

        for attribute_name in ('options', 'masters'):
            if pool_target.obj_attr_is_set(attribute_name):
                self._update_pool_target_items(context, pool_target,
                                               attribute_name)

        # Call get_pool to get the ids of all the attributes/ns_records
        # refreshed in the pool object
        updated_pool_target = self.get_pool_target(context, pool_target.id)

        return updated_pool_target

    def delete_pool_target(self, context, pool_target_id):
        pool_target = self._find_pool_targets(
            context, {'id': pool_target_id}, one=True)

        return self._delete(context, tables.pool_targets, pool_target,
                            exceptions.PoolTargetNotFound)

    # PoolTargetOption methods
    def _find_pool_target_options(self, context, criterion, one=False,
                                  marker=None, limit=None, sort_key=None,
                                  sort_dir=None):
        return self._find(
            context, tables.pool_target_options,
            objects.PoolTargetOption, objects.PoolTargetOptionList,
            exceptions.PoolTargetOptionNotFound, criterion, one,
            marker, limit, sort_key, sort_dir)

    def create_pool_target_option(self, context, pool_target_id,
                                  pool_target_option):
        pool_target_option.pool_target_id = pool_target_id

        return self._create(tables.pool_target_options, pool_target_option,
                            exceptions.DuplicatePoolTargetOption)

    def get_pool_target_option(self, context, pool_target_option_id):
        return self._find_pool_target_options(
            context, {'id': pool_target_option_id}, one=True)

    def find_pool_target_options(self, context, criterion=None, marker=None,
                                 limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_target_options(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def find_pool_target_option(self, context, criterion):
        return self._find_pool_target_options(context, criterion, one=True)

    def update_pool_target_option(self, context, pool_target_option):
        return self._update(
            context, tables.pool_target_options, pool_target_option,
            exceptions.DuplicatePoolTargetOption,
            exceptions.PoolTargetOptionNotFound)

    def delete_pool_target_option(self, context, pool_target_option_id):
        pool_target_option = self._find_pool_target_options(
            context, {'id': pool_target_option_id}, one=True)
        deleted_pool_target_option = self._delete(
            context, tables.pool_target_options, pool_target_option,
            exceptions.PoolTargetOptionNotFound)

        return deleted_pool_target_option

    # PoolTargetMaster methods
    def _find_pool_target_masters(self, context, criterion, one=False,
                                  marker=None, limit=None, sort_key=None,
                                  sort_dir=None):
        return self._find(
            context, tables.pool_target_masters,
            objects.PoolTargetMaster, objects.PoolTargetMasterList,
            exceptions.PoolTargetMasterNotFound, criterion, one,
            marker, limit, sort_key, sort_dir)

    def create_pool_target_master(self, context, pool_target_id,
                                  pool_target_master):
        pool_target_master.pool_target_id = pool_target_id

        return self._create(tables.pool_target_masters, pool_target_master,
                            exceptions.DuplicatePoolTargetMaster)

    def get_pool_target_master(self, context, pool_target_master_id):
        return self._find_pool_target_masters(
            context, {'id': pool_target_master_id}, one=True)

    def find_pool_target_masters(self, context, criterion=None, marker=None,
                                 limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_target_masters(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def find_pool_target_master(self, context, criterion):
        return self._find_pool_target_masters(context, criterion, one=True)

    def update_pool_target_master(self, context, pool_target_master):
        return self._update(
            context, tables.pool_target_masters, pool_target_master,
            exceptions.DuplicatePoolTargetMaster,
            exceptions.PoolTargetMasterNotFound)

    def delete_pool_target_master(self, context, pool_target_master_id):
        pool_target_master = self._find_pool_target_masters(
            context, {'id': pool_target_master_id}, one=True)
        deleted_pool_target_master = self._delete(
            context, tables.pool_target_masters, pool_target_master,
            exceptions.PoolTargetMasterNotFound)

        return deleted_pool_target_master

    # PoolAlsoNotify methods
    def _find_pool_also_notifies(self, context, criterion, one=False,
                                 marker=None, limit=None, sort_key=None,
                                 sort_dir=None):
        return self._find(context, tables.pool_also_notifies,
                          objects.PoolAlsoNotify, objects.PoolAlsoNotifyList,
                          exceptions.PoolAlsoNotifyNotFound, criterion, one,
                          marker, limit, sort_key, sort_dir)

    def create_pool_also_notify(self, context, pool_id, pool_also_notify):
        pool_also_notify.pool_id = pool_id

        return self._create(tables.pool_also_notifies, pool_also_notify,
                            exceptions.DuplicatePoolAlsoNotify)

    def get_pool_also_notify(self, context, pool_also_notify_id):
        return self._find_pool_also_notifies(
            context, {'id': pool_also_notify_id}, one=True)

    def find_pool_also_notifies(self, context, criterion=None, marker=None,
                                limit=None, sort_key=None, sort_dir=None):
        return self._find_pool_also_notifies(context, criterion, marker=marker,
                                          limit=limit, sort_key=sort_key,
                                          sort_dir=sort_dir)

    def find_pool_also_notify(self, context, criterion):
        return self._find_pool_also_notifies(context, criterion, one=True)

    def update_pool_also_notify(self, context, pool_also_notify):
        return self._update(
            context, tables.pool_also_notifies, pool_also_notify,
            exceptions.DuplicatePoolAlsoNotify,
            exceptions.PoolAlsoNotifyNotFound)

    def delete_pool_also_notify(self, context, pool_also_notify_id):
        pool_also_notify = self._find_pool_also_notifies(
            context, {'id': pool_also_notify_id}, one=True)
        deleted_pool_also_notify = self._delete(
            context, tables.pool_also_notifies, pool_also_notify,
            exceptions.PoolAlsoNotifyNotFound)

        return deleted_pool_also_notify

    # Zone Transfer Methods
    def _find_zone_transfer_requests(self, context, criterion, one=False,
                                     marker=None, limit=None, sort_key=None,
                                     sort_dir=None):

        table = tables.zone_transfer_requests

        ljoin = tables.zone_transfer_requests.join(
            tables.zones,
            tables.zone_transfer_requests.c.zone_id == tables.zones.c.id)

        query = select(
            [table, tables.zones.c.name.label("zone_name")]
        ).select_from(ljoin)

        if not context.all_tenants:
            query = query.where(or_(
                table.c.tenant_id == context.tenant,
                table.c.target_tenant_id == context.tenant))

        return self._find(
            context, table, objects.ZoneTransferRequest,
            objects.ZoneTransferRequestList,
            exceptions.ZoneTransferRequestNotFound,
            criterion,
            one=one, marker=marker, limit=limit, sort_dir=sort_dir,
            sort_key=sort_key, query=query, apply_tenant_criteria=False
        )

    def create_zone_transfer_request(self, context, zone_transfer_request):

        try:
            criterion = {"zone_id": zone_transfer_request.zone_id,
                         "status": "ACTIVE"}
            self.find_zone_transfer_request(
                context, criterion)
        except exceptions.ZoneTransferRequestNotFound:
            return self._create(
                tables.zone_transfer_requests,
                zone_transfer_request,
                exceptions.DuplicateZoneTransferRequest)
        else:
            raise exceptions.DuplicateZoneTransferRequest()

    def find_zone_transfer_requests(self, context, criterion=None,
                                    marker=None, limit=None, sort_key=None,
                                    sort_dir=None):

        return self._find_zone_transfer_requests(
            context, criterion, marker=marker,
            limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_request(self, context, zone_transfer_request_id):
        request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return request

    def find_zone_transfer_request(self, context, criterion):

        return self._find_zone_transfer_requests(context, criterion, one=True)

    def update_zone_transfer_request(self, context, zone_transfer_request):

        zone_transfer_request.obj_reset_changes(('zone_name'))

        updated_zt_request = self._update(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.DuplicateZoneTransferRequest,
            exceptions.ZoneTransferRequestNotFound,
            skip_values=['zone_name'])

        return updated_zt_request

    def delete_zone_transfer_request(self, context, zone_transfer_request_id):

        zone_transfer_request = self._find_zone_transfer_requests(
            context,
            {'id': zone_transfer_request_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_requests,
            zone_transfer_request,
            exceptions.ZoneTransferRequestNotFound)

    def count_zone_transfer_accept(self, context, criterion=None):
        query = select([func.count(tables.zone_transfer_accepts.c.id)])
        query = self._apply_criterion(tables.zone_transfer_accepts,
                    query, criterion)
        query = self._apply_deleted_criteria(context,
                    tables.zone_transfer_accepts, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    def _find_zone_transfer_accept(self, context, criterion, one=False,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):

        zone_transfer_accept = self._find(
            context, tables.zone_transfer_accepts,
            objects.ZoneTransferAccept,
            objects.ZoneTransferAcceptList,
            exceptions.ZoneTransferAcceptNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

        if not one:
            zone_transfer_accept.total_count = self.count_zone_transfer_accept(
                context, criterion)

        return zone_transfer_accept

    def create_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._create(
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept)

    def find_zone_transfer_accepts(self, context, criterion=None,
                                   marker=None, limit=None, sort_key=None,
                                   sort_dir=None):
        return self._find_zone_transfer_accept(
            context, criterion, marker=marker, limit=limit, sort_key=sort_key,
            sort_dir=sort_dir)

    def get_zone_transfer_accept(self, context, zone_transfer_accept_id):
        return self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

    def find_zone_transfer_accept(self, context, criterion):
        return self._find_zone_transfer_accept(
            context,
            criterion,
            one=True)

    def update_zone_transfer_accept(self, context, zone_transfer_accept):

        return self._update(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.DuplicateZoneTransferAccept,
            exceptions.ZoneTransferAcceptNotFound)

    def delete_zone_transfer_accept(self, context, zone_transfer_accept_id):

        zone_transfer_accept = self._find_zone_transfer_accept(
            context,
            {'id': zone_transfer_accept_id},
            one=True)

        return self._delete(
            context,
            tables.zone_transfer_accepts,
            zone_transfer_accept,
            exceptions.ZoneTransferAcceptNotFound)

    # Zone Import Methods
    def _find_zone_imports(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'IMPORT'
        zone_imports = self._find(
            context, tables.zone_tasks, objects.ZoneImport,
            objects.ZoneImportList, exceptions.ZoneImportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

        if not one:
            zone_imports.total_count = self.count_zone_tasks(
                context, criterion)

        return zone_imports

    def create_zone_import(self, context, zone_import):
        return self._create(
            tables.zone_tasks, zone_import, exceptions.DuplicateZoneImport)

    def get_zone_import(self, context, zone_import_id):
        return self._find_zone_imports(context, {'id': zone_import_id},
                                     one=True)

    def find_zone_imports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_imports(context, criterion, marker=marker,
                               limit=limit, sort_key=sort_key,
                               sort_dir=sort_dir)

    def find_zone_import(self, context, criterion):
        return self._find_zone_imports(context, criterion, one=True)

    def update_zone_import(self, context, zone_import):
        return self._update(
            context, tables.zone_tasks, zone_import,
            exceptions.DuplicateZoneImport, exceptions.ZoneImportNotFound)

    def delete_zone_import(self, context, zone_import_id):
        # Fetch the existing zone_import, we'll need to return it.
        zone_import = self._find_zone_imports(context, {'id': zone_import_id},
                                one=True)
        return self._delete(context, tables.zone_tasks, zone_import,
                    exceptions.ZoneImportNotFound)

    # Zone Export Methods
    def _find_zone_exports(self, context, criterion, one=False, marker=None,
                   limit=None, sort_key=None, sort_dir=None):
        if not criterion:
            criterion = {}
        criterion['task_type'] = 'EXPORT'
        zone_exports = self._find(
            context, tables.zone_tasks, objects.ZoneExport,
            objects.ZoneExportList, exceptions.ZoneExportNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)
        if not one:
            zone_exports.total_count = self.count_zone_tasks(
                context, criterion)

        return zone_exports

    def create_zone_export(self, context, zone_export):
        return self._create(
            tables.zone_tasks, zone_export, exceptions.DuplicateZoneExport)

    def get_zone_export(self, context, zone_export_id):
        return self._find_zone_exports(context, {'id': zone_export_id},
                                     one=True)

    def find_zone_exports(self, context, criterion=None, marker=None,
                  limit=None, sort_key=None, sort_dir=None):
        return self._find_zone_exports(context, criterion, marker=marker,
                               limit=limit, sort_key=sort_key,
                               sort_dir=sort_dir)

    def find_zone_export(self, context, criterion):
        return self._find_zone_exports(context, criterion, one=True)

    def update_zone_export(self, context, zone_export):
        return self._update(
            context, tables.zone_tasks, zone_export,
            exceptions.DuplicateZoneExport, exceptions.ZoneExportNotFound)

    def delete_zone_export(self, context, zone_export_id):
        # Fetch the existing zone_export, we'll need to return it.
        zone_export = self._find_zone_exports(context, {'id': zone_export_id},
                                one=True)
        return self._delete(context, tables.zone_tasks, zone_export,
                    exceptions.ZoneExportNotFound)

    def count_zone_tasks(self, context, criterion=None):
        query = select([func.count(tables.zone_tasks.c.id)])
        query = self._apply_criterion(tables.zone_tasks, query, criterion)
        query = self._apply_tenant_criteria(context, tables.zone_tasks, query)
        query = self._apply_deleted_criteria(context, tables.zone_tasks, query)

        resultproxy = self.session.execute(query)
        result = resultproxy.fetchone()

        if result is None:
            return 0

        return result[0]

    # Service Status Methods
    def _find_service_statuses(self, context, criterion, one=False,
                               marker=None, limit=None, sort_key=None,
                               sort_dir=None):
        return self._find(
            context, tables.service_status, objects.ServiceStatus,
            objects.ServiceStatusList, exceptions.ServiceStatusNotFound,
            criterion, one, marker, limit, sort_key, sort_dir)

    def find_service_status(self, context, criterion):
        return self._find_service_statuses(context, criterion, one=True)

    def find_service_statuses(self, context, criterion=None, marker=None,
                              limit=None, sort_key=None, sort_dir=None):
        return self._find_service_statuses(context, criterion, marker=marker,
                                           limit=limit, sort_key=sort_key,
                                           sort_dir=sort_dir)

    def create_service_status(self, context, service_status):
        return self._create(
            tables.service_status, service_status,
            exceptions.DuplicateServiceStatus)

    def update_service_status(self, context, service_status):
        return self._update(
            context, tables.service_status, service_status,
            exceptions.DuplicateServiceStatus,
            exceptions.ServiceStatusNotFound)
    
    #view methods    
    def create_view(self, context,view):
        return self._create(tables.view, view, 
                            exceptions.DuplicateViewDuplicate)

    def delete_view(self, context, view_id):
        """
        """
#         view_id = view_id.replace('-', '')
        view = self._find_views(context, {'id': view_id}, one=True)
        return self._delete(context, tables.view, view,
                            exceptions.ViewNotFound)

    def get_view(self, context, view_id):
        view_id = view_id.replace('-', '')
        return self._find_views(context, {'id': view_id},
                                       one=True)

    def find_views(self, context, criterion=None, marker=None, limit=None,
                   sort_key=None, sort_dir=None):
        views = self._find_views(context, criterion, marker=marker,
                                 limit=limit, sort_key=sort_key,
                                 sort_dir=sort_dir)
        return views

    def _find_views(self, context, criterion, one=False,marker=None,
                   limit=None, sort_key=None,sort_dir=None):
        views = self._find(
            context, tables.view,
            objects.View,
            objects.ViewList,
            exceptions.ViewNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)

        return views

    def update_view(self, context, view):
        LOG.debug("Updating view %s", view)
        view = self._update(
            context, tables.view, view, exceptions.DuplicateZone,
            exceptions.ViewNotFound)
        
        return view
    
    def create_zdns_view_info(self, context, zdns_view_info, view):
        for item in zdns_view_info.keys():
            if type(zdns_view_info[item]) == list:
                zdns_view_info[item] = ','.join(zdns_view_info[item]) 
        self._create_zdns_view(tables.zdns_view_info_t, zdns_view_info, 
                              exceptions.DuplicateZdnsViewInfo)
    def create_view_zdns_view(self, context, view_zdns_view):
        self._create_zdns_view(tables.view_zdns_view_associations, 
                              view_zdns_view,
                              exceptions.DuplicateViewZdnsView)
    
    def update_zdns_view_info(self, context, obj, zdns_view_info):
        self._update_zdns_view(context,
                              tables.zdns_view_info_t, obj, zdns_view_info,
                              exceptions.DuplicateViewZdnsView)
        
    def find_view_zdns_view(self, context, view):
        return self._find_zdns_view(context,
                                   tables.view_zdns_view_associations, 
                                   "view_id", view.id, 
                                   exceptions.ViewNotFound)
        
    def delete_view_zdns_view(self, context, view):
        self._delete_zdns_view_asso(context, 
                                    tables.view_zdns_view_associations,
                                    view,
                                    exceptions.DuplicateViewZdnsView)
        
    def get_zdns_view_info(self, context, id):
        return self._find_zdns_view(context,
                                   tables.zdns_view_info_t,
                                   "id", id,
                                   exceptions.ViewNotFound)

    def delete_zdns_view_info(self, context, zdns_view_info):
        self._delete_zdns_view(context, tables.zdns_view_info_t, 
                                zdns_view_info, 
                                exceptions.DuplicateZdnsViewInfo)
    
    def create_view_acl(self, context, view_acl):
        self._create_zdns_view(tables.view_acl, view_acl, 
                              exceptions.DuplicateZdnsViewInfo)  
        
    def find_view_acls(self, context, view_id): 
        view_acls = self._find_view_acls(context, tables.view_acl, "view_id",
                                        view_id,
                                        exceptions.ViewAclNotFound)
        return view_acls
        
    def delete_view_acl(self, context, view_acl):
        self._delete_zdns_view(context, tables.view_acl, 
                               {'id' : view_acl['id']}, 
                               exceptions.ViewAclNotFound)
        
        
    def _create_zdns_view(self, table, obj, exc_dup, skip_values=None,
                          extra_values=None):
        query = table.insert()
        try:
            resultproxy = self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)
    
    def _delete_zdns_view_asso(self, context, table, obj, exc_notfound, hard_delete=False):
        query = table.delete().where(table.c.view_id == obj["id"])
        resultproxy = self.session.execute(query)
        return resultproxy
    
    def _delete_zdns_view(self, context, table, obj, exc_notfound, hard_delete=False):
        query = table.delete().where(table.c.id == obj["id"])
        resultproxy = self.session.execute(query)
        return resultproxy
    
    def _update_zdns_view(self, context, table, obj, values, exc_dup,
                         skip_values=None):
        query = table.update()\
                     .where(table.c.id == obj["id"])\
                     .values(**values)
        try:
            resultproxy = self.session.execute(query)
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)
    
    def _find_zdns_view(self, context, table, column_name, value, exc_notfound):
        query = select([table])
        column = getattr(table.c, column_name)

        # Wildcard value: '%'
        query = query.where(column == value)
        query = utils.paginate_query(
            query, table, 1,
            [])
        try:
            resultproxy = self.session.execute(query)
            results = resultproxy.fetchall()
        except Exception as e:
            raise
        return results[0]
    
    def find_zdns_view_infos(self, context, criterion=None, marker=None, limit=None,
                             sort_key=None, sort_dir=None):
        sort_key = 'priority'
        views = self._find_zdns_view_infos(context, criterion, marker=marker,
                                           limit=limit, sort_key=sort_key,
                                           sort_dir=sort_dir)
        return views

    def _find_zdns_view_infos(self, context, criterion, one=False,marker=None,
                   limit=None, sort_key=None,sort_dir=None):
        zdns_view_infos = self._find(
            context, tables.zdns_view_info_t,
            objects.ZdnsViewInfo,
            objects.ZdnsViewInfoList,
            exceptions.ViewNotFound, criterion,
            one, marker, limit, sort_key, sort_dir)
        return zdns_view_infos

    def _find_view_acls(self, context, table, column_name, value, exc_notfound):
        query = select([table])
        column = getattr(table.c, column_name)

        query = query.where(column == value)
        query = utils.paginate_query(
            query, table, None,
            [])
        try:
            resultproxy = self.session.execute(query)
            results = resultproxy.fetchall()
        except Exception as e:
            raise
        return results
    
    # diagnostics
    def ping(self, context):
        start_time = time.time()

        try:
            result = self.engine.execute('SELECT 1').first()
        except Exception:
            status = False
        else:
            status = True if result[0] == 1 else False

        return {
            'status': status,
            'rtt': "%f" % (time.time() - start_time)
        }

    # Reverse Name utils
    def _rname_check(self, criterion):
        # If the criterion has 'name' in it, switch it out for reverse_name
        if criterion is not None and criterion.get('name', "").startswith('*'):
                criterion['reverse_name'] = criterion.pop('name')[::-1]
        return criterion

    def create_zdns_zone(self, context, zone):
        # Patch in the reverse_name column

        # Don't handle recordsets for now\
        return self._create_zdns_zone(
            tables.zdns_zones, zone,
            exceptions.DuplicateZone,)

    def create_zone_asso(self, context, zone):
        # Patch in the reverse_name column

        # Don't handle recordsets for now\
        self._create_zone_asso(
            tables.zone_associations, zone,
            exceptions.DuplicateZone)

    def delete_zdns_zone(self, context, zone):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._delete_zdns_zone(context,
                               tables.zdns_zones, zone,
                               exceptions.DuplicateZone)

    def delete_zone_asso(self, context, zone):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._delete_zone_asso(context,
                               tables.zone_associations, zone,
                               exceptions.DuplicateZone)

    def update_zdns_zone(self, context, zone, values):
        # Patch in the reverse_name column

        # Don't handle recordsets for now
        self._update_zdns_zone(context,
                               tables.zdns_zones, zone, values,
                               exceptions.DuplicateZone)

    def _create_zdns_zone(self, table, obj, exc_dup, skip_values=None,
                          extra_values=None):
        #create zdns_zone_info_t infos where
        """
        :param table: zdns_zone_info_t
        :param obj: equipment response
        :param exc_dup:
        :param skip_values: not use
        :param extra_values: not user
        :return:
        """
        query = table.insert()
        try:
            resultproxy = self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

    def _create_zone_asso(self, table, obj, exc_dup, skip_values=None,
                          extra_values=None):
        # create zdns_zone_info_t and zones table associations
        """
        :param table: zones_zdns_associations_t
        :param obj: dict{"zone_id","zdns_zone_id"}
        :param exc_dup:
        :param skip_values:
        :param extra_values:
        :return:
        """
        query = table.insert()
        try:
            resultproxy = self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

    def _find_asso(self, context, table, column_name, value, exc_notfound):
        """
        find associations from association tables;
        :param context:
        :param table: zone_znds_associations_t or view_zdns_associations_t
        or acl_zdns_assciations_t
        :param column_name:  Used to determine delete by what column
        :param value: colunm value , single
        :param exc_notfound:
        :return:
        """
        query = select([table])
        column = getattr(table.c, column_name)

        # Wildcard value: '%'
        query = query.where(column == value)
        query = utils.paginate_query(
            query, table, 1,
            [])
        try:
            resultproxy = self.session.execute(query)
            results = resultproxy.fetchall()
        except Exception as e:
            raise
        if len(results) == 0:
            return results
        return results[0]

    def _delete_zdns_zone(self, context, table, obj, exc_notfound, hard_delete=False):
        """
        delete zdns_zone_info_t
        :param context:
        :param table:  zdns_zone_info_t
        :param obj:  zones obj, we user zone.id
        :param exc_notfound:
        :param hard_delete:
        :return:
        """
        query = table.delete().where(table.c.id == obj['id'])
        resultproxy = self.session.execute(query)
        return resultproxy

    def _delete_zone_asso(self, context, table, obj, exc_notfound, hard_delete=False):
        """
        delete zones table and zdns_zone_info_t table associations in zone_zdns_associations_t
        :param context:
        :param table: zone_zdns_associations_t
        :param obj:  zones obj , we use zone.id
        :param exc_notfound:
        :param hard_delete:
        :return:
        """
        query = table.delete().where(table.c.zone_id == obj["id"])
        resultproxy = self.session.execute(query)
        return resultproxy

    def _update_zdns_zone(self, context, table, obj, values, exc_dup,
                          skip_values=None):
        # refresh update zdns_zone_info_t
        """
        :param context:
        :param table:  zdns_zone_info_t
        :param obj:  zones obj , we use zone.id
        :param values:  equipment_response
        :param exc_dup:
        :param skip_values:
        :return:
        """
        query = table.update()\
                     .where(table.c.id == obj["id"])\
                     .values(**values)
        try:
            resultproxy = self.session.execute(query)
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

    def _update_zdns_acl(self, context, table, obj, values, exc_dup,
                         skip_values=None):
        query = table.update()\
                     .where(table.c.id == obj["id"])\
                     .values(**values)
        try:
            resultproxy = self.session.execute(query)
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

    def _delete_zdns_acl(self, context, table, obj, exc_notfound, hard_delete=False):
        query = table.delete().where(table.c.id == obj.get("id"))
        resultproxy = self.session.execute(query)
        return resultproxy

    def _delete_acl_asso(self, context, table, obj, exc_notfound, hard_delete=False):
        """
        delete zones table and zdns_zone_info_t table associations in zone_zdns_associations_t
        :param context:
        :param table: zone_zdns_associations_t
        :param obj:  zones obj , we use zone.id
        :param exc_notfound:
        :param hard_delete:
        :return:
        """
        query = table.delete().where(table.c.acl_id == obj.id)
        resultproxy = self.session.execute(query)
        return resultproxy

    def _create_zdns_acl(self, table, obj, exc_dup, skip_values=None,
                          extra_values=None):
        #create zdns_acl_info_t infos where
        """
        :param table: zdns_acl_info_t
        :param obj: equipment response
        :param exc_dup:
        :param skip_values: not use
        :param extra_values: not user
        :return:
        """
        query = table.insert()
        try:
            resultproxy = self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)

    def _create_acl_asso(self, table, obj, exc_dup, skip_values=None,
                          extra_values=None):
        # create zdns_zone_info_t and zones table associations
        """
        :param table: zones_zdns_associations_t
        :param obj: dict{"zone_id","zdns_zone_id"}
        :param exc_dup:
        :param skip_values:
        :param extra_values:
        :return:
        """
        query = table.insert()
        try:
            resultproxy = self.session.execute(query, [obj])
        except oslo_db_exception.DBDuplicateEntry:
            msg = "Duplicate %s" % obj.obj_name()
            raise exc_dup(msg)


    def get_records_by_zone_id(self, context, zone_id):
        return self._get_records_by_zone_id(context, tables.records, zone_id)

    def _get_records_by_zone_id(self, context, table, zone_id, exc_dup = None, skip_values=None,
                                extra_values=None):
        # get recordsets by zone _id
        """
        :param table: zones_zdns_associations_t
        :param id = zone_id
        :param exc_dup:
        :param skip_values:
        :param extra_values:
        :return:
        """
        query = select([table])
        column = getattr(table.c, "zone_id")
        query = query.where(column==zone_id)
        query = utils.paginate_query(query, table, None, [])
        resultproxy = self.session.execute(query)
        results = resultproxy.fetchall()
        return results