.. _create-zone:

Create a Zone
~~~~~~~~~~~~~

In environments that include the DNS service, you can create a DNS Zone.

#. Source the ``demo`` credentials to perform
   the following steps as a non-administrative project:

   .. code-block:: console

      $ . demo-openrc

#. Create a DNS Zone called ``example.com.``:

   .. code-block:: console

      $ openstack zone create --email dnsmaster@example.com example.com.
      +----------------+--------------------------------------+
      | Field          | Value                                |
      +----------------+--------------------------------------+
      | action         | CREATE                               |
      | attributes     | {}                                   |
      | created_at     | 2016-07-13T14:54:16.000000           |
      | description    | None                                 |
      | email          | dnsmaster@example.com                |
      | id             | 14093115-0f0f-497a-ac69-42235e46c26f |
      | masters        |                                      |
      | name           | example.com.                         |
      | pool_id        | 794ccc2c-d751-44fe-b57f-8894c9f5c842 |
      | project_id     | 656bc359067844fba6005d400f19df76     |
      | serial         | 1468421656                           |
      | status         | PENDING                              |
      | transferred_at | None                                 |
      | ttl            | 3600                                 |
      | type           | PRIMARY                              |
      | updated_at     | None                                 |
      | version        | 1                                    |
      +----------------+--------------------------------------+

#. After a short time, verify successful creation of the DNS Zone:

   .. code-block:: console

      $ openstack zone list
      +--------------------------------------+--------------+---------+------------+--------+--------+
      | id                                   | name         | type    |     serial | status | action |
      +--------------------------------------+--------------+---------+------------+--------+--------+
      | 14093115-0f0f-497a-ac69-42235e46c26f | example.com. | PRIMARY | 1468421656 | ACTIVE | NONE   |
      +--------------------------------------+--------------+---------+------------+--------+--------+

#. You can now create RecordSets in this DNS Zone:

   .. code-block:: console

      $ openstack recordset create --records '10.0.0.1' --type A example.com. www
      +-------------+--------------------------------------+
      | Field       | Value                                |
      +-------------+--------------------------------------+
      | action      | CREATE                               |
      | created_at  | 2016-07-13T14:59:32.000000           |
      | description | None                                 |
      | id          | 07e6f5af-783e-481f-b8df-5972a6174c94 |
      | name        | www.example.com.                     |
      | project_id  | 656bc359067844fba6005d400f19df76     |
      | records     | 10.0.0.1                             |
      | status      | PENDING                              |
      | ttl         | None                                 |
      | type        | A                                    |
      | updated_at  | None                                 |
      | version     | 1                                    |
      | zone_id     | 14093115-0f0f-497a-ac69-42235e46c26f |
      | zone_name   | example.com.                         |
      +-------------+--------------------------------------+

#. Delete the DNS Zone:

   .. code-block:: console

      $ openstack zone delete example.com.
