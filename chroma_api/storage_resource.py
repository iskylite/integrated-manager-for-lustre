#
# ==============================
# Copyright 2011 Whamcloud, Inc.
# ==============================

from django.contrib.contenttypes.models import ContentType

from chroma_core.models import StorageResourceRecord, StorageResourceStatistic

from tastypie.authorization import DjangoAuthorization
from chroma_api.authentication import AnonymousAuthentication
from tastypie.resources import ModelResource
from tastypie import fields
from chroma_core.lib.storage_plugin.query import ResourceQuery

from tastypie.exceptions import NotFound, ImmediateHttpResponse
from tastypie import http
from django.core.exceptions import ObjectDoesNotExist
from chroma_core.lib.storage_plugin.daemon import StorageDaemon


class StorageResourceResource(ModelResource):
    content_type_id = fields.IntegerField()
    attributes = fields.DictField()
    alias = fields.CharField()

    alerts = fields.ListField()
    stats = fields.DictField()
    charts = fields.ListField()
    propagated_alerts = fields.ListField()

    default_alias = fields.CharField()

    plugin_name = fields.CharField(attribute='resource_class__storage_plugin__module_name')
    class_name = fields.CharField(attribute='resource_class__class_name')

    deletable = fields.BooleanField()

    def dehydrate_propagated_alerts(self, bundle):
        return [a.to_dict() for a in ResourceQuery().resource_get_propagated_alerts(bundle.obj.to_resource())]

    def dehydrate_stats(self, bundle):
        stats = {}
        for s in StorageResourceStatistic.objects.filter(storage_resource = bundle.obj):
            stats[s.name] = s.to_dict()
        return stats

    def dehydrate_charts(self, bundle):
        return bundle.obj.to_resource().get_charts()

    def dehydrate_deletable(self, bundle):
        return bundle.obj.resource_class.user_creatable

    def dehydrate_default_alias(self, bundle):
        return bundle.obj.to_resource().get_label()

    def dehydrate_alias(self, bundle):
        resource = bundle.obj.to_resource()
        return bundle.obj.alias_or_name(resource)

    def dehydrate_alerts(self, bundle):
        return [a.to_dict() for a in ResourceQuery().resource_get_alerts(bundle.obj.to_resource())]

    def dehydrate_content_type_id(self, bundle):
        return ContentType.objects.get_for_model(bundle.obj.__class__).pk

    def dehydrate_attributes(self, bundle):
        return bundle.obj.to_resource().get_attribute_items()

    class Meta:
        queryset = StorageResourceRecord.objects.all()
        resource_name = 'storage_resource'
        #filtering = {'storage_plugin__module_name': ['exact'], 'class_name': ['exact']}
        filtering = {'class_name': ['exact'], 'plugin_name': ['exact']}
        authorization = DjangoAuthorization()
        authentication = AnonymousAuthentication()
        #ordering = ['lun_name']

    def obj_delete(self, request = None, **kwargs):
        try:
            obj = self.obj_get(request, **kwargs)
        except ObjectDoesNotExist:
            raise NotFound("A model instance matching the provided arguments could not be found.")
        StorageDaemon.request_remove_resource(obj.id)
        raise ImmediateHttpResponse(http.HttpAccepted())

    def obj_create(self, bundle, request = None, **kwargs):
        # Note: not importing this at module scope so that this module can
        # be imported without loading plugins (useful at installation)
        from chroma_core.lib.storage_plugin.manager import storage_plugin_manager
        record = storage_plugin_manager.create_root_resource(bundle.data['plugin_name'], bundle.data['class_name'], **bundle.data['attrs'])
        bundle.obj = record

        return bundle

    def obj_update(self, bundle, request = None, **kwargs):
        bundle.obj = self.cached_obj_get(request = request, **self.remove_api_resource_names(kwargs))
        # We only support updating the 'alias' field
        if not 'alias' in bundle.data:
            raise ImmediateHttpResponse(http.HttpBadRequest())

        # FIXME: sanitize input for alias (it gets echoed back as markup)
        alias = bundle.data['alias']
        record = bundle.obj
        if alias == "":
            record.alias = None
        else:
            record.alias = alias
        record.save()

        return bundle

    def override_urls(self):
        from django.conf.urls.defaults import url
        return [
            url(r"^(?P<resource_name>%s)/(?P<plugin_name>\w+)/(?P<class_name>\w+)/$" % self._meta.resource_name, self.wrap_view('dispatch_list'), name="dispatch_list"),
]
