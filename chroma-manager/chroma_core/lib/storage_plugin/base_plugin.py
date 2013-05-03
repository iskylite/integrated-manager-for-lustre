#
# ========================================================
# Copyright (c) 2012 Whamcloud, Inc.  All rights reserved.
# ========================================================


import os
import logging
import settings
import threading

from chroma_core.lib.storage_plugin.base_resource import BaseStorageResource
from chroma_core.services.stats import StatsQueue


class ResourceNotFound(Exception):
    pass


class ResourceIndex(object):
    def __init__(self):
        # Map (local_id) to resource
        self._local_id_to_resource = {}

        # Map (id_tuple, klass) to resource
        self._resource_id_to_resource = {}

    def add(self, resource):
        self._local_id_to_resource[resource._handle] = resource

        # Why don't we need a scope resource in here?
        # Because if it's a ScopedId then only items for that
        # scannable will be in this ResourceIndex (index is per
        # plugin instance), and if it's a GlobalId then it doesn't
        # have a scope.
        resource_id = (resource.id_tuple(), resource.__class__)
        if resource_id in self._resource_id_to_resource:
            raise RuntimeError("Duplicate resource added to index")
        self._resource_id_to_resource[resource_id] = resource

    def remove(self, resource):
        resource_id = (resource.id_tuple(), resource.__class__)
        if not resource_id in self._resource_id_to_resource:
            raise RuntimeError("Remove non-existent resource")

        del self._local_id_to_resource[resource._handle]
        del self._resource_id_to_resource[resource_id]

    def get(self, klass, **attrs):
        id_tuple = klass(**attrs).id_tuple()
        try:
            return self._resource_id_to_resource[(id_tuple, klass)]
        except KeyError:
            raise ResourceNotFound()

    def all(self):
        return self._local_id_to_resource.values()


class BaseStoragePlugin(object):
    #: Set to true for plugins which should not be shown in the user interface
    internal = False

    _log = None
    _log_format = None

    @property
    def log(self):
        if not self._log.handlers:
            handler = logging.handlers.WatchedFileHandler(os.path.join(settings.LOG_PATH, 'storage_plugin.log'))
            handler.setFormatter(logging.Formatter(self._log_format, '%d/%b/%Y:%H:%M:%S'))
            self._log.addHandler(handler)
        return self._log

    # TODO: need to document that initial_scan may not kick off async operations, because
    # the caller looks at overall resource state at exit of function.  If they eg
    # want to kick off an async update thread they should do it at the first
    # call to update_scan, or maybe we could give them a separate function for that.
    def initial_scan(self, root_resource):
        """Identify all resources
           present at this time and call register_resource on them.

           If you return from this function you must have succeeded
           in communicating with the scannable resource.  Any
           resources which were present previously and are absent
           when initial_scan returns are assumed to be
           permanently absent and are deleted.  If for any reason
           you cannot return all resources (for example, communication
           failure with a controller), you must raise an exception."""
        raise NotImplementedError

    def update_scan(self, root_resource):
        """Perform any required
           periodic refresh of data and update any resource instances.
           Guaranteed that initial_scan will have been called before this."""
        pass

    def agent_session_start(self, host_id, data):
        """Start a session based on information sent from an agent plugin.

        :param host_id: ID of the host from which the agent information was sent -- this is
          a database identifier which is mainly useful for constructing DeviceNode
          resources.
        :param data: Arbitrary JSON-serializable data sent by plugin.
        :rtype: None
        """
        pass

    def agent_session_continue(self, host_id, data):
        """Continue a session using information sent from an agent plugin.

        This will only ever be called on Plugin instances where `agent_session_start` has
        already been called.

        :param host_id: ID of the host from which the agent information was sent -- this is
          a database identifier which is mainly useful for constructing DeviceNode
          resources.
        :param data: Arbitrary JSON-serializable data sent by plugin.
        :rtype: None
        """
        pass

    def teardown(self):
        """Optional.  Perform any teardown
           required before terminating.  Guaranteed not to be called
           concurrently with initial_scan or update_scan.  Guaranteed
           that initial_scan or update_scan will not be called after this.
           Guaranteed that once initial_scan has been entered this function will
           later be called unless the whole process terminates
           prematurely.  This function will be called even if initial_scan
           or update_scan raises an exception."""
        pass

    def generate_handle(self):
        with self._handle_lock:
            self._handle_counter += 1
            handle = self._handle_counter
            return handle

    def __init__(self, resource_manager, scannable_id = None):
        from chroma_core.lib.storage_plugin.manager import storage_plugin_manager
        storage_plugin_manager.register_plugin(self)
        self._initialized = False
        self._resource_manager = resource_manager

        self._handle_lock = threading.Lock()
        self._instance_lock = threading.Lock()
        self._handle_counter = 0

        self._index = ResourceIndex()
        self._scannable_id = scannable_id

        self._resource_lock = threading.Lock()
        self._delta_new_resources = []
        self._delta_delete_resources = []

        self._alerts_lock = threading.Lock()
        self._delta_alerts = set()
        self._alerts = {}

        self._session_open = False

        self.update_period = settings.PLUGIN_DEFAULT_UPDATE_PERIOD

        from chroma_core.lib.storage_plugin.query import ResourceQuery
        root_resource = ResourceQuery().get_resource(scannable_id)
        root_resource._handle = self.generate_handle()
        root_resource._handle_global = False
        self._root_resource = root_resource

    def do_agent_session_start(self, data):
        self._initial_populate(self.agent_session_start, self._root_resource.host_id, data)

    def do_agent_session_continue(self, data):
        self._update(self.agent_session_continue, self._root_resource.host_id, data)

    def do_initial_scan(self):
        self._initial_populate(self.initial_scan, self._root_resource)

    def do_periodic_update(self):
        self._update(self.update_scan, self._root_resource)

    def _initial_populate(self, fn, *args):
        if self._initialized:
            raise RuntimeError("Tried to initialize %s twice!" % self)
        self._initialized = True

        self._index.add(self._root_resource)

        fn(*args)

        self._resource_manager.session_open(
                self._scannable_id,
                self._index.all(),
                self.update_period)
        self._session_open = True
        self._delta_new_resources = []

        # Creates, deletes, attrs, parents are all handled in session_open
        # the rest we do manually.
        self.commit_resource_statistics()
        self.check_alert_conditions()
        self.commit_alerts()

    def _update(self, fn, *args):
        fn(*args)

        # Resources created since last update
        with self._resource_lock:
            self.commit_resource_creates()
            self.commit_resource_deletes()
            self.commit_resource_updates()
            self.commit_resource_statistics()
            self.check_alert_conditions()
            self.commit_alerts()

    def check_alert_conditions(self):
        for resource in self._index.all():
            # Check if any AlertConditions are matched
            for ac in resource._meta.alert_conditions:
                alert_list = ac.test(resource)
                for name, attribute, active in alert_list:
                    self.notify_alert(active, resource, name, attribute)

    def do_teardown(self):
        self.teardown()
        if self._session_open:
            self._resource_manager.session_close(self._scannable_id)
            self._session_open = False

    def commit_resource_creates(self):
        if len(self._delta_new_resources) > 0:
            self._resource_manager.session_add_resources(self._scannable_id, self._delta_new_resources)
        self._delta_new_resources = []

    def commit_resource_deletes(self):
        # Resources deleted since last update
        if len(self._delta_delete_resources) > 0:
            self._resource_manager.session_remove_resources(self._scannable_id, self._delta_delete_resources)
        self._delta_delete_resources = []

    def commit_resource_updates(self):
        # Resources with changed attributes
        for resource in self._index.all():
            deltas = resource.flush_deltas()
            # If there were changes to attributes
            if len(deltas['attributes']) > 0:
                self._resource_manager.session_update_resource(
                        self._scannable_id, resource._handle, deltas['attributes'])

            # If there were parents added or removed
            if len(deltas['parents']) > 0:
                for parent_resource in deltas['parents']:
                    if parent_resource in resource._parents:
                        # If it's in the parents of the resource then it's an add
                        self._resource_manager.session_resource_add_parent(
                                self._scannable_id, resource._handle,
                                parent_resource._handle)
                    else:
                        # Else if's a remove
                        self._resource_manager.session_resource_remove_parent(
                                self._scannable_id, resource._handle,
                                parent_resource._handle)

    def commit_alerts(self):
        with self._alerts_lock:
            for (resource, attribute, alert_class) in self._delta_alerts:
                active = self._alerts[(resource, attribute, alert_class)]
                self._resource_manager.session_notify_alert(
                        self._scannable_id, resource._handle,
                        active, alert_class, attribute)
            self._delta_alerts.clear()

    def commit_resource_statistics(self):
        samples = []
        for resource in self._index.all():
            r_stats = resource.flush_stats()
            if r_stats and settings.STORAGE_PLUGIN_ENABLE_STATS:
                samples += self._resource_manager.session_get_stats(self._scannable_id, resource._handle, r_stats)
        if samples:
            StatsQueue().put(samples)
        return len(samples)

    def update_or_create(self, klass, parents = [], **attrs):
        """Report a storage resource.  If it already exists then
        it will be updated, otherwise it will be created.  The resulting
        resource instance is returned.

        Note that the 'created' return value indicates whether this
        is the first report of the resource within this plugin session,
        not whether it is the first report of the resource ever (e.g.
        from a different or previous plugin session).

        :returns: (resource, created) -- the storage resource and a boolean
                  indicating whether this was the first report this session.
        """
        with self._resource_lock:
            try:
                existing = self._index.get(klass, **attrs)
                for k, v in attrs.items():
                    setattr(existing, k, v)
                for p in parents:
                    existing.add_parent(p)
                for p in parents:
                    assert p._handle != existing._handle
                return existing, False
            except ResourceNotFound:
                resource = klass(parents = parents, **attrs)
                self._register_resource(resource)
                for p in parents:
                    assert p._handle != resource._handle
                return resource, True

    def remove(self, resource):
        """Note: this does not immediately unregister the resource, but rather marks it
        for removal at the next periodic update"""
        with self._resource_lock:
            self._index.remove(resource)
            self._delta_delete_resources.append(resource)
            # TODO: it would be useful if local resource instances had a
            # way to invalidate their handles to detect buggy plugins

    def notify_alert(self, active, resource, alert_name, attribute = None):
        # This will be flushed through to the database by update_scan
        key = (resource, attribute, alert_name)
        value = active
        with self._alerts_lock:
            try:
                existing = self._alerts[key]
                if existing == value:
                    return
            except KeyError:
                pass

            self._alerts[key] = value
            self._delta_alerts.add(key)

    def _register_resource(self, resource):
        """Register a newly created resource:
        * Assign it a local ID
        * Add it to the local indices
        * Mark it for inclusion in the next update to global state"""
        assert(isinstance(resource, BaseStorageResource))
        assert(not resource._handle)

        resource.validate()

        resource._handle = self.generate_handle()
        resource._handle_global = False

        self._index.add(resource)
        self._delta_new_resources.append(resource)
