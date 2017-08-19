====================
DNS service overview
====================

The DNS service provides DNS Zone and RecordSet management for OpenStack
clouds. The DNS Service includes a REST API, a command-line client, and a
Horizon Dashboard plugin.

The DNS service consists of the following components:

``openstack`` command-line client plugin
  A plugin for the OpenStack Client CLI that communicates with the REST API

``designate-api`` component
  An OpenStack-native REST API that processes API requests by sending
  them to the ``designate-central`` over Remote Procedure Call (RPC).

``designate-central`` component
  Orchestrates the creation, deletion and update of Zones and RecordSets, and
  delegates work to ``designate-pool-manager`` for interaction with the DNS
  servers

``designate-producer`` component
  Orchestrates periodic tasks that are run by designate.

``designate-worker`` component
  Is a generic task runner, that runs both zone create / update and deletes,
  and periodic tasks, from ``designate-producer``

``designate-mdns`` component
  A small DNS Server that is responsible for pushing DNS Zone information to
  the customer facing DNS Servers. Can also pull in DNS information about
  DNS Zones hosted outside of the Designate infrastructure

``designate-agent`` component
  A small python daemon that can be used for a limited sub set of DNS Servers
  Some DNS Servers requrire commands be run locally, and to do this we use
  this component.

  .. note:: The majority of the DNS service installs will not need this
     component.

``Customer Facing DNS Servers``
  Serves DNS requests to end users. They are orchestreated by the
  ``designate-worker``, and the supported list is maintained `here`_


  .. _here: http://docs.openstack.org/developer/designate/support-matrix.html

