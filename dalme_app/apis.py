from django.contrib.auth.models import User
from django.db.models import Q, Count
import uuid
import datetime
import json
import ast
import operator
from functools import reduce
from rest_framework import viewsets
from dalme_app.serializers import (DTFieldsSerializer, DTListsSerializer, LanguageSerializer, WorksetSerializer,
                                   TaskSerializer, TaskListSerializer, PageSerializer, RSImageSerializer, TranscriptionSerializer,
                                   SourceSerializer, ProfileSerializer, AttributeTypeSerializer, ContentXAttributeSerializer,
                                   ContentTypeSerializer, ContentClassSerializer, AsyncTaskSerializer, SimpleAttributeSerializer,
                                   CountrySerializer, CitySerializer)
from rest_framework.response import Response
from rest_framework.decorators import action
from dalme_app.models import (Profile, Attribute_type, Content_class, Content_type, Content_attributes, DT_list,
                              DT_fields, Page, Source_pages, Source, Transcription, Language, Workset,
                              TaskList, Task, rs_resource, rs_collection, rs_collection_resource, rs_user, wiki_user,
                              wiki_user_groups, wp_users, wp_usermeta, Attribute, Country, City)
from django_celery_results.models import TaskResult
from django.db.models.expressions import RawSQL
from rest_framework.permissions import DjangoModelPermissions
from django.shortcuts import get_object_or_404
from passlib.apps import phpass_context
from dalme_app import functions


class DTViewSet(viewsets.ModelViewSet):
    """ Generic viewset for managing communication with DataTables.
    Should be subclassed for specific API endpoints. """
    permission_classes = (DjangoModelPermissions,)

    @action(detail=False)
    def get_workset(self, request, *args, **kwargs):
        data_dict = {}
        if request.GET.get('data') is not None:
            dt_data = json.loads(request.GET['data'])
            if hasattr(self, 'search_dict'):
                search_dict = self.search_dict
            else:
                search_dict = {}
            queryset = self.get_queryset()
            try:
                if dt_data['search']['value']:
                    queryset = self.filter_on_search(queryset=queryset, dt_data=dt_data, search_dict=search_dict)
                if request.GET.get('filters') is not None:
                    queryset = self.filter_on_filters(queryset=queryset, filters=ast.literal_eval(request.GET['filters']))
                queryset = self.get_ordered_queryset(queryset=queryset, dt_data=dt_data, search_dict=search_dict)
                count = 1
                resp_data = {}
                for obj in queryset:
                    obj_dict = {'pk': obj.pk}
                    resp_data[count] = obj_dict
                    count = count + 1
                data_dict['data'] = resp_data
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the data: ' + str(e)
        else:
            data_dict['error'] = 'There was no data in the request.'
        return Response(data_dict)

    def list(self, request, *args, **kwargs):
        data_dict = {}
        if request.GET.get('data') is not None:
            dt_data = json.loads(request.GET['data'])
            if hasattr(self, 'search_dict'):
                search_dict = self.search_dict
            else:
                search_dict = {}
            queryset = self.get_queryset()
            try:
                data_dict['draw'] = int(dt_data.get('draw'))  # cast return "draw" value as INT to prevent Cross Site Scripting (XSS) attacks
                if dt_data['search']['value']:
                    queryset = self.filter_on_search(queryset=queryset, dt_data=dt_data, search_dict=search_dict)
                if request.GET.get('filters') is not None:
                    queryset = self.filter_on_filters(queryset=queryset, filters=ast.literal_eval(request.GET['filters']))
                queryset = self.get_ordered_queryset(queryset=queryset, dt_data=dt_data, search_dict=search_dict)
                rec_count = queryset.count()
                data_dict['recordsTotal'] = rec_count
                data_dict['recordsFiltered'] = rec_count
                # filter the queryset for the current page
                queryset = queryset[dt_data.get('start'):dt_data.get('start')+dt_data.get('length')]
                serializer = self.get_serializer(queryset, many=True)
                data = serializer.data
                data_dict['data'] = data
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the data: ' + str(e)
        else:
            queryset = self.get_queryset()
            try:
                serializer = self.get_serializer(queryset, many=True)
                data = serializer.data
                data_dict['data'] = data
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the data: ' + str(e)
        return Response(data_dict)

    def retrieve(self, request, pk=None):
        object = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(object)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        result = {}
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        serializer = self.get_serializer(data=data_dict)
        if serializer.is_valid():
            try:
                serializer.save()
                result['data'] = serializer.data
                status = 201
            except Exception as e:
                result['error'] = 'The following error occured while trying to save the data: ' + str(e)
                status = 400
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if serializer.is_valid():
            serializer.save()
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)

    def destroy(self, request, *args, **kwargs):
        result = {}
        status = 0
        # object = self.get_object()
        if kwargs.get('pk') is not None:
            if ',' in str(kwargs.get('pk')):
                object_ids = kwargs.get('pk').split(',')
            else:
                object_ids = [kwargs.get('pk')]
            for obj in object_ids:
                object = get_object_or_404(self.queryset, pk=obj)
                try:
                    object.delete()
                    result['result'] = 'success'
                    status = 201
                except Exception as e:
                    result['result'] = 'error'
                    result['error'] = 'The following error occured while trying to delete the data: ' + str(e)
                    status = 400
        return Response(result, status)

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('filter') is not None:
            filter = self.request.GET['filter'].split(',')
            filter_q = Q(**{filter[0]: filter[1]})
            queryset = self.queryset.filter(filter_q).distinct()
        else:
            queryset = self.queryset
        return queryset

    def filter_on_search(self, *args, **kwargs):
        return filter_on_search(*args, **kwargs)

    def filter_on_filters(self, *args, **kwargs):
        return filter_on_filters(*args, **kwargs)

    def get_ordered_queryset(self, *args, **kwargs):
        return get_ordered_queryset(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)

    def get_serializer_class(self):
        return self.serializer_class

    def get_serializer_context(self):
        return {
            'request': self.request,
            'format': self.format_kwarg,
            'view': self
        }


class AsynchronousTasks(DTViewSet):
    """ API endpoint for managing asynchronous tasks """
    permission_classes = (DjangoModelPermissions,)
    queryset = TaskResult.objects.all()
    serializer_class = AsyncTaskSerializer


class Countries(DTViewSet):
    """ API endpoint for managing countries """
    permission_classes = (DjangoModelPermissions,)
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class Cities(DTViewSet):
    """ API endpoint for managing cities """
    permission_classes = (DjangoModelPermissions,)
    queryset = City.objects.all()
    serializer_class = CitySerializer


class AttributeTypes(DTViewSet):
    """ API endpoint for managing attribute types """
    permission_classes = (DjangoModelPermissions,)
    queryset = Attribute_type.objects.all()
    serializer_class = AttributeTypeSerializer

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('filter') is not None:
            filter = self.request.GET['filter'].split(',')
            filter_q = Q(**{filter[0]: filter[1]})
            queryset = Content_attributes.objects.filter(filter_q)
        else:
            queryset = Attribute_type.objects.all()
        return queryset

    def get_serializer_class(self):
        if self.request.GET.get('content_type') is not None:
            serializer = ContentXAttributeSerializer
        else:
            serializer = self.serializer_class
        return serializer


class Attributes(DTViewSet):
    """ API endpoint for managing attributes """
    permission_classes = (DjangoModelPermissions,)
    queryset = Attribute.objects.all().order_by('attribute_type')
    serializer_class = SimpleAttributeSerializer


class ContentClasses(DTViewSet):
    """ API endpoint for managing content classes """
    permission_classes = (DjangoModelPermissions,)
    queryset = Content_class.objects.all()
    serializer_class = ContentClassSerializer


class ContentTypes(DTViewSet):
    """ API endpoint for managing content types """
    permission_classes = (DjangoModelPermissions,)
    queryset = Content_type.objects.all()
    serializer_class = ContentTypeSerializer

    def create(self, request, format=None):
        result = {}
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        attribute_types = data_dict.pop('attribute_types', None)
        serializer = self.get_serializer(data=data_dict)
        if serializer.is_valid():
            new_obj = serializer.save()
            if attribute_types is not None:
                object = Content_type.objects.get(pk=new_obj.id)
                if ',' in str(attribute_types):
                    attribute_types = [int(i) for i in attribute_types.split(',')]
                else:
                    attribute_types = [attribute_types]
                for a in attribute_types:
                    atype = Attribute_type.objects.get(id=a)
                    new_record = Content_attributes()
                    new_record.content_type = object
                    new_record.attribute_type = atype
                    new_record.save()
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)

    def update(self, request, pk=None, format=None):
        result = {}
        object = get_object_or_404(self.queryset, pk=pk)
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        attribute_types = data_dict.pop('attribute_types', None)
        serializer = self.get_serializer(object, data=data_dict)
        if serializer.is_valid():
            if attribute_types is not None:
                if ',' in str(attribute_types):
                    attribute_types = [int(i) for i in attribute_types.split(',')]
                else:
                    attribute_types = [attribute_types]
                current_types = Content_attributes.objects.filter(content_type=object.id).values_list('attribute_type', flat=True)
                add_types = list(set(attribute_types) - set(current_types))
                remove_types = list(set(current_types) - set(attribute_types))
                if add_types:
                    for t in add_types:
                        new_type = Content_attributes()
                        new_type.content_type = object
                        new_type.attribute_type = Attribute_type.objects.get(id=t)
                        new_type.save()
                if remove_types:
                    q = Q(content_type=object.id)
                    for t in remove_types:
                        q &= Q(attribute_type=t)
                        Content_attributes.objects.filter(q).delete()
            serializer.save()
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)


class DTFields(DTViewSet):
    """ API endpoint for managing DataTables list field attributes """
    permission_classes = (DjangoModelPermissions,)
    queryset = DT_fields.objects.all()
    serializer_class = DTFieldsSerializer


class DTLists(DTViewSet):
    """ API endpoint for managing DataTables lists """
    permission_classes = (DjangoModelPermissions,)
    queryset = DT_list.objects.all()
    serializer_class = DTListsSerializer

    def create(self, request, *args, **kwargs):
        result = {}
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        fields = data_dict.pop('fields', None)
        content_types = data_dict.pop('content_types', None)
        serializer = self.get_serializer(data=data_dict)
        if serializer.is_valid():
            new_obj = serializer.save()
            if fields is not None:
                if ',' in str(fields):
                    fields = [int(i) for i in fields.split(',')]
                else:
                    fields = [fields]
                for f in fields:
                    new_field = DT_fields()
                    new_field.list = new_obj
                    new_field.field = Attribute_type.objects.get(pk=f)
                    new_field.save()
            if content_types is not None:
                if ',' in str(content_types):
                    content_types = [int(i) for i in content_types.split(',')]
                else:
                    content_types = [content_types]
                object = DT_list.objects.get(pk=new_obj.id)
                for ct in content_types:
                    ctype = Content_type.objects.get(id=ct)
                    object.content_types.add(ctype)
            object = DT_list.objects.get(pk=new_obj.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        fields = data_dict.pop('fields', None)
        content_types = data_dict.pop('content_types', None)
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if serializer.is_valid():
            if fields is not None:
                if ',' in str(fields):
                    fields = [int(i) for i in fields.split(',')]
                else:
                    fields = [fields]
                current_fields = DT_fields.objects.filter(list=object.id).values_list('field', flat=True)
                add_fields = list(set(fields) - set(current_fields))
                remove_fields = list(set(current_fields) - set(fields))
                if add_fields:
                    for f in add_fields:
                        try:
                            new_field = DT_fields()
                            new_field.list = object
                            new_field.field = Attribute_type.objects.get(pk=f)
                            new_field.save()
                        except Exception as e:
                            data_dict['error'] = 'The following error occured while trying to update the database: ' + str(e)
                if remove_fields:
                    q = Q(list=object.id)
                    for f in remove_fields:
                        q &= Q(field=f)
                        DT_fields.objects.filter(q).delete()
            if content_types is not None:
                if ',' in str(content_types):
                    content_types = [int(i) for i in content_types.split(',')]
                else:
                    content_types = [content_types]
                current_ct = object.content_types.all().values_list('id', flat=True)
                add_ct = list(set(content_types) - set(current_ct))
                remove_ct = list(set(current_ct) - set(content_types))
                if add_ct:
                    for ct in add_ct:
                        ctype = Content_type.objects.get(id=ct)
                        object.content_types.add(ctype)
                if remove_ct:
                    for ct in remove_ct:
                        ctype = Content_type.objects.get(id=ct)
                        object.content_types.remove(ctype)
            serializer.save()
            object = DT_list.objects.get(pk=object.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)


class Images(DTViewSet):
    """ API endpoint for managing DAM images """
    permission_classes = (DjangoModelPermissions,)
    queryset = rs_resource.objects.filter(resource_type=1, archive=0, ref__gte=0)
    serializer_class = RSImageSerializer
    search_dict = {'collections': 'collections__name'}

    @action(detail=True)
    def get_preview_url(self, request, pk=None):
        result = {}
        try:
            url = functions.get_dam_preview(pk)
            result['preview_url'] = url
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    @action(detail=False)
    def get_info_for_source(self, request):
        result = {}
        if self.request.GET.get('data') is not None:
            try:
                img_data = {}
                data = self.request.GET['data']
                id_list = data.split(',')
                search_q = Q()
                for i in id_list:
                    q = Q(**{'ref': i})
                    search_q |= q
                queryset = self.queryset.filter(search_q)
                collections_list = []
                for image in queryset:
                    dict = {i.resource_type_field.name: i.value for i in image.resource_data.all()
                            if i.resource_type_field.ref in [76, 77, 80, 99, 78, 3, 29]}
                    dict['title'] = image.field8
                    dict['folio'] = image.field79
                    collections = [i.name for i in image.collections.all() if i.name not in
                                   ['My Collection', 'Archivio Dummy', 'Archivio', 'All images']]
                    collections_list = collections_list + collections
                    dict['collections'] = ' | '.join(collections)
                    img_data[image.ref] = dict
                sug_name = None
                sug_short_name = None
                for col in collections_list:
                    if 'Inventory' in col:
                        sug_name = ''.join([i for i in col if not i.isdigit() and i not in ['(', ')', '[', ']']]).strip()
                        break
                for f, i in img_data.items():
                    if 'archivalsource' in i and 'Series' in i and 'shelfnumber' in i:
                        a_source = i['archivalsource'].split(',')[-1]
                        a_series = i['Series']
                        a_shelf = i['shelfnumber']
                        s_a_source = ''.join([c for c in a_source if c.isupper()])
                        if len(a_series) > 10:
                            s_a_series = ''.join([c for c in a_series if c.isupper()])
                        else:
                            s_a_series = a_series
                        sug_short_name = ' '.join([s_a_source, s_a_series, a_shelf]).strip()
                        break
                if sug_name is not None and sug_short_name is not None:
                    sur = sug_name.split(' ')[-1]
                    sug_name = sug_name + ' ('+sug_short_name+')'
                    sug_short_name = sug_short_name + ' ('+sur+')'
                    sug_dict = {
                        'name': sug_name,
                        'short_name': sug_short_name
                    }
                else:
                    sug_dict = {}
                result['data'] = {'suggested_fields': sug_dict, 'image_data': img_data}
                status = 201
            except Exception as e:
                result['error'] = str(e)
                status = 400
        else:
            result['error'] = 'A list of ids must be submitted with the request.'
            status = 400
        return Response(result, status)

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        collections = data_dict.pop('collections', None)
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if serializer.is_valid():
            if collections is not None:
                if ',' in str(collections):
                    collections = [int(i) for i in collections.split(',')]
                else:
                    collections = [collections]
                current_collections = rs_collection_resource.objects.filter(resource=object.ref).values_list('collection', flat=True)
                add_collections = list(set(collections) - set(current_collections))
                remove_collections = list(set(current_collections) - set(collections))
                if add_collections:
                    for c in add_collections:
                        new_col = rs_collection_resource()
                        new_col.resource = object
                        new_col.collection = rs_collection.objects.get(pk=c)
                        new_col.save()
                if remove_collections:
                    q = Q(list=object.ref)
                    for c in remove_collections:
                        q &= Q(collection=c)
                        rs_collection_resource.objects.filter(q).delete()
            serializer.save()
            object = rs_resource.objects.get(pk=object.ref)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)


class Languages(DTViewSet):
    """ API endpoint for managing languages """
    permission_classes = (DjangoModelPermissions,)
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class Options(viewsets.ViewSet):
    """ API endpoint for generating lists of options for DTE forms """
    permission_classes = (DjangoModelPermissions,)
    queryset = Workset.objects.none()

    def list(self, request, *args, **kwargs):
        data_dict = {}
        if self.request.GET.get('lists') is not None:
            lists = self.request.GET['lists'].split(',')
            try:
                for ls in lists:
                    tokens = ls.split('_')
                    if str(tokens[-1]).isdigit():
                        para = tokens.pop(-1)
                        ls = '_'.join(tokens)
                        options = eval('self.'+ls+'('+para+')')
                    else:
                        options = eval('self.'+ls+'()')
                    data_dict[ls] = options
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the options data: ' + str(e)
        else:
            data_dict['error'] = 'No options list/s were included in the request.'
        return Response(data_dict)

    def attribute_optexp(self, attribute_type=None, **kwargs):
        if attribute_type is not None:
            opt_exp = Attribute_type.objects.get(pk=attribute_type).options_list
            options_list = eval(opt_exp)
        else:
            options_list = [{'label': "", 'value': ""}]
        return options_list

    def attribute_types(self, content_type=None, **kwargs):
        if content_type is not None:
            qset = Content_attributes.objects.filter(content_type=content_type).order_by('attribute_type__short_name')
            opt_list = [{'label': i.attribute_type.name+' ('+i.attribute_type.short_name+')', 'value': i.attribute_type.id} for i in qset]
            if self.request.GET.get('extra') is not None:
                ref_dict = {i.attribute_type.id: [i.attribute_type.data_type, i.attribute_type.options_list] for i in qset}
                options_list = {'options': opt_list, 'ref': ref_dict}
            else:
                options_list = opt_list
        else:
            options_list = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Attribute_type.objects.all().order_by('name')]
        return options_list

    def active_staff(self, **kwargs):
        staff_options = [{'label': i.full_name, 'value': i.user_id} for i in Profile.objects.filter(user__is_active=1).order_by('user__username')]
        return staff_options

    def content_types(self, content_class=None, **kwargs):
        if content_class is not None:
            content_types = [{'label': i.name, 'value': i.id} for i in Content_type.objects.filter(content_class=content_class).order_by('name')]
        else:
            content_types = [{'label': i.name, 'value': i.id} for i in Content_type.objects.all().order_by('name')]
        return content_types

    def user_worksets(self, **kwargs):
        worksets_options = [{'label': i.name, 'value': i.id} for i in Workset.objects.filter(owner=str(self.request.user.id)).order_by('name')]
        return worksets_options

    def user_groups(self, **kwargs):
        user_groups = [{'label': i.name, 'value': i.id} for i in self.request.user.groups.all().order_by('name')]
        return user_groups

    def user_task_lists(self, **kwargs):
        groups = self.request.user.groups.all()
        all_lists = TaskList.objects.all().order_by('name')
        task_lists = []
        for list in all_lists:
            if list.group in groups:
                task_lists.append({'label': list.name+' ('+str(list.group)+')', 'value': list.id})
        return task_lists

    def content_classes(self, **kwargs):
        content_classes = [{'label': i.name, 'value': i.id} for i in Content_class.objects.all().order_by('name')]
        return content_classes

    def parent_sources(self, source_type=None, **kwargs):
        if source_type is not None:
            if source_type == 13:
                parent_sources = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Source.objects.filter(type=12).order_by('short_name')]
        else:
            parent_sources = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Source.objects.all().order_by('short_name')]
        return parent_sources


class Pages(DTViewSet):
    """ API endpoint for managing pages """
    permission_classes = (DjangoModelPermissions,)
    queryset = Page.objects.all()
    serializer_class = PageSerializer


class Sources(DTViewSet):
    """ API endpoint for managing sources """
    permission_classes = (DjangoModelPermissions,)
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    display_fields = ['name', 'type', 'parent']

    def create(self, request, *args, **kwargs):
        result = {}
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        validated_extra = self.validate_extra(data_dict.pop('attributes', None), data_dict.pop('pages', None))
        serializer = self.get_serializer(data=data_dict)
        if validated_extra['valid'] and serializer.is_valid():
            attributes = validated_extra['attributes']
            pages = validated_extra['pages']
            new_obj = serializer.save()
            object = Source.objects.get(pk=new_obj.id)
            if attributes is not None:
                create_attributes = []
                for a in attributes:
                    a_type = a.pop('attribute_type', None)
                    if a_type is not None:
                        a['attribute_type'] = Attribute_type.objects.get(pk=a_type)
                        create_attributes.append(a)
                if create_attributes:
                    for new_att in create_attributes:
                        object.attributes.create(**new_att)
            if pages is not None:
                create_pages = []
                for page in pages:
                    page.pop('id', None)
                    create_pages.append(page)
                if create_pages:
                    for new_page in create_pages:
                        object.pages.create(**new_page)
            result['data'] = serializer.data
            status = 201
        else:
            fieldErrors = []
            if validated_extra.get('fieldErrors') is not None:
                fieldErrors += validated_extra['fieldErrors']
            if not serializer.is_valid():
                fieldErrors += get_error_array(serializer.errors, self.display_fields)
            result['fieldErrors'] = fieldErrors
            status = 400
        return Response(result, status)

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        validated_extra = self.validate_extra(data_dict.pop('attributes', None), data_dict.pop('pages', None))
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if validated_extra['valid'] and serializer.is_valid():
            attributes = validated_extra['attributes']
            pages = validated_extra['pages']
            if attributes is not None:
                create_attributes = []
                update_attributes = {}
                for a in attributes:
                    a_id = a.pop('id', None)
                    a_type = a.pop('attribute_type', None)
                    if a_type is not None:
                        a['attribute_type'] = Attribute_type.objects.get(pk=a_type)
                        if a_id is not None:
                            update_attributes[a_id] = a
                        else:
                            create_attributes.append(a)
                if update_attributes:
                    old_attributes = object.attributes.all()
                    for att in old_attributes:
                        if str(att.id) in update_attributes:
                            up_att = update_attributes.get(str(att.id))
                            att_object = Attribute.objects.get(pk=att.id)
                            for attr, val in up_att.items():
                                setattr(att_object, attr, val)
                            att_object.save()
                        else:
                            # id = att.id
                            object.attributes.remove(att)
                            # Attribute.objects.get(pk=id).delete()
                if create_attributes:
                    for new_att in create_attributes:
                        object.attributes.create(**new_att)
            if pages is not None:
                create_pages = []
                update_pages = {}
                for page in pages:
                    p_id = page.pop('id', None)
                    if p_id is not None:
                        update_pages[p_id] = page
                    else:
                        create_pages.append(page)
                if update_pages:
                    old_pages = object.pages.all()
                    for pp in old_pages:
                        if str(pp.id) in update_pages:
                            up_page = update_pages.get(str(pp.id))
                            page_object = Page.objects.get(pk=pp.id)
                            for attr, val in up_page.items():
                                setattr(page_object, attr, val)
                            page_object.save()
                        else:
                            # id = att.id
                            object.pages.remove(pp)
                            # Attribute.objects.get(pk=id).delete()
                if create_pages:
                    for new_page in create_pages:
                        object.pages.create(**new_page)
            serializer.save()
            object = Source.objects.get(pk=object.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            fieldErrors = []
            if validated_extra.get('fieldErrors') is not None:
                fieldErrors += validated_extra['fieldErrors']
            if not serializer.is_valid():
                fieldErrors += get_error_array(serializer.errors, self.display_fields)
            result['fieldErrors'] = fieldErrors
            status = 400
        return Response(result, status)

    def validate_extra(self, attributes, pages):
        result = {}
        fieldErrors = []
        if attributes is not None:
            if 'attribute_type' in attributes:
                test_attributes = {'1': attributes}
                attributes = [attributes]
            else:
                test_attributes = attributes
                attributes = list(attributes.values())
            for key, value in test_attributes.items():
                if value['attribute_type'] is None:
                    fieldErrors.append({'name': 'attributes.'+str(key)+'.attribute_type', 'status': 'Attribute type must be selected.'})
        if pages is not None:
            if 'id' in pages:
                test_pages = {'1': pages}
                pages = [pages]
            else:
                test_pages = pages
                pages = list(pages.values())
            for key, value in test_pages.items():
                if value['order'] is None:
                    fieldErrors.append({'name': 'pages.'+str(key)+'.order', 'status': 'A value for order must be included.'})
                if value['name'] is None:
                    fieldErrors.append({'name': 'pages.'+str(key)+'.name', 'status': 'A name for the folio must be included.'})
        if fieldErrors:
            result['valid'] = False
            result['fieldErrors'] = fieldErrors
        else:
            result['valid'] = True
            result['attributes'] = attributes
            result['pages'] = pages
        return result

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('type') is not None:
            type = self.request.GET['type']
            queryset = self.queryset
            q_obj = Q()
            if type == 'inventories':
                q_obj &= Q(is_inventory=True)
                queryset = queryset.filter(q_obj).annotate(no_folios=Count('pages'))
            else:
                content_types = DT_list.objects.get(short_name=type).content_types.all()
                for i in content_types:
                    q_obj |= Q(type=i.pk)
                queryset = queryset.filter(q_obj)
        else:
            queryset = self.queryset
        return queryset

    def filter_on_search(self, *args, **kwargs):
        dt_data = kwargs['dt_data']
        search_string = dt_data['search']['value']
        queryset = kwargs['queryset']
        search_words = search_string.split()
        search_q = Q()
        for word in search_words:
            search_word = Q(name__icontains=word) | Q(type__name__icontains=word) | Q(parent__name__icontains=word) | Q(att_blob__icontains=word)
            search_q &= search_word
        queryset = queryset.annotate(att_blob=RawSQL('SELECT GROUP_CONCAT(dalme_app_attribute.value_STR SEPARATOR ",") FROM dalme_app_attribute JOIN dalme_app_source src2 ON dalme_app_attribute.object_id = src2.id WHERE src2.id = dalme_app_source.id', [])).filter(search_q)
        return queryset

    def filter_on_filters(self, *args, **kwargs):
        queryset = kwargs['queryset']
        filters = kwargs['filters']
        local_fields = ['id', 'type', 'name', 'short_name', 'parent', 'is_inventory', 'no_folios', 'tags']
        annotate_dict = {}
        if filters.get('and_list') is not None:
            for filter in filters['and_list']:
                annotate_dict = self.get_annotation(filter, local_fields, annotate_dict)
        if filters.get('or_list') is not None:
            for filter in filters['and_list']:
                annotate_dict = self.get_annotation(filter, local_fields, annotate_dict)
        queryset = queryset.annotate(**annotate_dict)
        if filters.get('and_list') is not None:
            queryset = queryset.filter(reduce(operator.and_, (Q(**q) for q in filters['and_list']))).distinct()
        if filters.get('or_list') is not None:
            queryset = queryset.filter(reduce(operator.or_, (Q(**q) for q in filters['or_list']))).distinct()
        return queryset

    def get_annotation(self, filter, local_fields, annotate_dict):
        (k, v), = filter.items()
        if '__' in k:
            field = k.split('__')[0]
        else:
            field = k
        if field not in local_fields:
            if Attribute_type.objects.filter(short_name=field).exists():
                att_type_id = Attribute_type.objects.get(short_name=field).id
                annotate_dict[field] = RawSQL('SELECT value_STR FROM dalme_app_attribute \
                                               JOIN dalme_app_source src2 ON dalme_app_attribute.object_id = src2.id \
                                               WHERE src2.id = dalme_app_source.id AND dalme_app_attribute.attribute_type = %s', [att_type_id])
        return annotate_dict

    def get_ordered_queryset(self, *args, **kwargs):
        queryset = kwargs['queryset']
        dt_data = kwargs['dt_data']
        order_column = dt_data['order'][0]['column']
        order_column_name_raw = dt_data['columns'][order_column]['data']
        if '.' in order_column_name_raw:
            field_list = order_column_name_raw.split('.')
            if field_list[0] in ['type', 'parent', 'name']:
                order_column_name = field_list[0]
            elif field_list[0] == 'attributes':
                order_column_name = field_list[1]
        elif ',' in order_column_name_raw:
            field_list = order_column_name_raw.split(',')
            order_column_name = field_list[0]
        else:
            order_column_name = order_column_name_raw
        order_dir = dt_data['order'][0]['dir']
        local_fields = ['id', 'type', 'name', 'short_name', 'parent', 'is_inventory', 'no_folios']
        if order_column_name not in local_fields:
            att_type = Attribute_type.objects.get(short_name=order_column_name)
            att_type_id = att_type.id
            att_dt = att_type.data_type
            if att_dt == 'DATE':
                queryset = queryset.annotate(value_DATE_d=RawSQL('SELECT value_DATE_d FROM dalme_app_attribute JOIN dalme_app_source src2 ON \
                                                            dalme_app_attribute.object_id = src2.id WHERE src2.id = dalme_app_source.id AND \
                                                            dalme_app_attribute.attribute_type = %s', [att_type_id]))
                queryset = queryset.annotate(value_DATE_m=RawSQL('SELECT value_DATE_m FROM dalme_app_attribute JOIN dalme_app_source src2 ON \
                                                            dalme_app_attribute.object_id = src2.id WHERE src2.id = dalme_app_source.id AND \
                                                            dalme_app_attribute.attribute_type = %s', [att_type_id]))
                queryset = queryset.annotate(value_DATE_y=RawSQL('SELECT value_DATE_y FROM dalme_app_attribute JOIN dalme_app_source src2 ON \
                                                            dalme_app_attribute.object_id = src2.id WHERE src2.id = dalme_app_source.id AND \
                                                            dalme_app_attribute.attribute_type = %s', [att_type_id]))
                if order_dir == 'desc':
                    queryset = queryset.order_by('-value_DATE_y', '-value_DATE_m', '-value_DATE_d')
                else:
                    queryset = queryset.order_by('value_DATE_y', 'value_DATE_m', 'value_DATE_d')
            else:
                target_field = 'value_' + att_dt
                queryset = queryset.annotate(ord_field=RawSQL('SELECT '+target_field+' FROM dalme_app_attribute JOIN dalme_app_source src2 ON \
                                                            dalme_app_attribute.object_id = src2.id WHERE src2.id = dalme_app_source.id AND \
                                                            dalme_app_attribute.attribute_type = %s', [att_type_id]))
                if order_dir == 'desc':
                    queryset = queryset.order_by('-ord_field')
                else:
                    queryset = queryset.order_by('ord_field')
        else:
            if order_dir == 'desc':
                order = '-'+order_column_name
            else:
                order = order_column_name
            queryset = queryset.order_by(order)
        return queryset

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.serializer_class
        if self.request.GET.get('type') is not None:
            type = self.request.GET['type']
        else:
            type = ''
        if type != 'inventories':
            kwargs['fields'] = ['no_folios']
        return serializer_class(*args, **kwargs)


class Tasks(DTViewSet):
    """ API endpoint for managing tasks """
    permission_classes = (DjangoModelPermissions,)
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True)
    def set_state(self, request, *args, **kwargs):
        result = {}
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        try:
            action = self.request.GET['action']
            if action == 'mark_done':
                object.completed = True
                object.save()
            elif action == 'mark_undone':
                object.completed = False
                object.save()
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)


class TaskLists(DTViewSet):
    """ API endpoint for managing tasks lists """
    permission_classes = (DjangoModelPermissions,)
    queryset = TaskList.objects.all().annotate(task_count=Count('task'))
    serializer_class = TaskListSerializer


class Transcriptions(viewsets.ModelViewSet):
    """ API endpoint for managing transcriptions """
    permission_classes = (DjangoModelPermissions,)
    queryset = Transcription.objects.all()
    serializer_class = TranscriptionSerializer

    def create(self, request, format=None):
        data = request.data
        s_data = {'version': data['version'], 'transcription': data['transcription']}
        serializer = TranscriptionSerializer(data=s_data)
        if serializer.is_valid():
            new_obj = serializer.save()
            object = Transcription.objects.get(pk=new_obj.id)
            sp = Source_pages.objects.get(source=data['source'], page=data['page'])
            sp.transcription = object
            sp.save()
            serializer = TranscriptionSerializer(object)
            result = serializer.data
            status = 201
        else:
            result = serializer.errors
            status = 400
        return Response(result, status)

    def update(self, request, pk=None, format=None):
        data = request.data
        object = self.get_object()
        if object.version:
            version = int(object.version)
        else:
            version = 0
        if int(data['version']) > version:
            serializer = TranscriptionSerializer(object, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                serializer = TranscriptionSerializer(object)
                result = serializer.data
                status = 201
            else:
                result = serializer.errors
                status = 400
        else:
            serializer = TranscriptionSerializer(object)
            result = serializer.data
            status = 201
        return Response(result, status)


class Users(DTViewSet):
    """ API endpoint for managing users """
    permission_classes = (DjangoModelPermissions,)
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def create(self, request, *args, **kwargs):
        result = {}
        display_fields = ['dam_usergroup', 'wp_role']
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        serializer = self.get_serializer(data=data_dict)
        if serializer.is_valid():
            # create wp user
            result = create_wp_user(data_dict)
            if result['status'] == 201:
                data_dict['wp_user'] = result['id']
            else:
                return Response(result['error'], result['status'])
            # create dam user
            result = create_dam_user(data_dict)
            if result['status'] == 201:
                data_dict['dam_user'] = result['id']
                data_dict.pop('dam_usergroup', None)
            else:
                return Response(result['error'], result['status'])
            # create wiki user
            result = create_wiki_user(data_dict)
            if result['status'] == 201:
                data_dict['wiki_user'] = result['id']
                data_dict.pop('wiki_groups', None)
            else:
                return Response(result['error'], result['status'])
            if data_dict['user'].get('groups') is not None and data_dict['user'].get('groups') != 0:
                groups = [i['id'] for i in data_dict['user']['groups']]
                serializer = self.get_serializer(data=data_dict, context={'groups': groups})
            else:
                serializer = self.get_serializer(data=data_dict)
            if serializer.is_valid():
                new_obj = serializer.save()
                object = Profile.objects.get(pk=new_obj.id)
                serializer = self.get_serializer(object)
                result['data'] = serializer.data
                status = 201
            else:
                result['fieldErrors'] = get_error_array(serializer.errors, display_fields)
                status = 400
        else:
            result['fieldErrors'] = get_error_array(serializer.errors, display_fields)
            status = 400
        return Response(result, status)

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        display_fields = ['dam_usergroup', 'wp_role']
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        dam_usergroup = data_dict.pop('dam_usergroup', None)
        if data_dict.get('wiki_groups') is not None and data_dict.get('wiki_groups') != 0:
            wiki_groups = [i['ug_group'] for i in data_dict.pop('wiki_groups', None)]
        else:
            wiki_groups = None
        wp_role = data_dict['wp_role']
        if data_dict['user'].get('groups') is not None and data_dict['user'].get('groups') != 0:
            groups = [i['id'] for i in data_dict['user'].pop('groups', None)]
            serializer = self.get_serializer(object, data=data_dict, partial=partial, context={'groups': groups})
        else:
            groups = None
            serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if serializer.is_valid():
            serializer.save()
            if dam_usergroup != '':
                rs_user.objects.filter(ref=object.dam_user).update(usergroup=dam_usergroup)
            if wp_role != '':
                wp_usermeta.objects.filter(user_id=object.wp_user, meta_key='wp_capabilities').update(meta_value=wp_role)
            if wiki_groups is not None:
                wiki_user_groups.objects.filter(ug_user=object.wiki_user).delete()
                for i in wiki_groups:
                    dict = {
                        'ug_user': object.wiki_user,
                        'ug_group': bytes(i, encoding='ascii')
                    }
                    wiki_user_groups(**dict).save()
            object = Profile.objects.get(pk=object.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors, display_fields)
            status = 400
        return Response(result, status)

    def destroy(self, request, pk=None, format=None):
        result = {}
        profile_id = self.kwargs.get('pk')
        object = Profile.objects.get(pk=profile_id)
        try:
            # django switch active to false
            User.objects.filter(id=object.user.pk).update(is_active=False)
            # resourcespace switch "approved" to false
            rs_user.objects.filter(ref=object.dam_user).update(approved=0)
            # wordpress change role to: -no role for this site- in meta, wp_capabilities = a:0:{}
            wp_usermeta.objects.filter(user_id=object.wp_user, meta_key='wp_capabilities').update(meta_value='a:0:{}')
            object = Profile.objects.get(pk=object.pk)
            serializer = ProfileSerializer(object)
            result['data'] = serializer.data
            status = 201
        except Exception as e:
            result['error'] = 'There was a problem deleting the user: ' + str(e)
            status = 400
        return Response(result, status)


class Worksets(DTViewSet):
    """ API endpoint for managing worksets """
    permission_classes = (DjangoModelPermissions,)
    queryset = Workset.objects.all()
    serializer_class = WorksetSerializer

    @action(detail=True)
    def set_state(self, request, *args, **kwargs):
        result = {}
        object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        try:
            action = self.request.GET['action']
            seq = self.request.GET['seq']
            if action == 'mark_done':
                qset = json.loads(object.qset)
                qset[str(seq)]['done'] = True
                object.current_record = int(seq) + 1
                object.qset = json.dumps(qset)
                object.save()
            elif action == 'mark_undone':
                qset = json.loads(object.qset)
                qset[str(seq)].pop('done')
                object.qset = json.dumps(qset)
                object.save()
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    def create(self, request, format=None):
        data = request.data
        data_dict = {
            'name': data['data[0][name]'],
            'description': data['data[0][description]'],
            'qset': data['qset'],
            'endpoint': data['endpoint'],
        }
        serializer = WorksetSerializer(data=data_dict)
        if serializer.is_valid():
            new_obj = Workset(**data_dict)
            new_obj.save()
            object = Workset.objects.get(pk=new_obj.id)
            serializer = WorksetSerializer(object)
            result = serializer.data
            status = 201
        else:
            result = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)


""" GENERALIZED FUNCTIONS """


def get_dte_data(request):
    dt_request = json.loads(request.data['data'])
    dt_request.pop('action', None)
    rows = dt_request['data']
    data_list = []
    for k, v in rows.items():
        row_values = {}
        for field, value in v.items():
            if 'many-count' not in field:
                if type(value) is list:
                    if len(value) == 1:
                        value = normalize_value(value[0])
                    elif len(value) == 0:
                        value = 0
                    else:
                        value = [normalize_value(i) for i in value]
                elif type(value) is dict:
                    # if len(value) == 1 and value.get('value') is not None:
                    if len(value) == 1:
                        # value = normalize_value(value['value'])
                        value = normalize_value(list(value.values())[0])
                    else:
                        value = {key: normalize_value(val) for key, val in value.items() if 'many-count' not in key}
                else:
                    value = normalize_value(value)
                row_values[field] = value
        data_list.append([k, row_values])
    return data_list


def normalize_value(value):
    if type(value) is list:
        if len(value) == 1:
            n_value = normalize_value(value[0])
        elif len(value) == 0:
            n_value = 0
        else:
            n_value = [normalize_value(i) for i in value]
    elif type(value) is dict:
        n_value = {key: normalize_value(val) for key, val in value.items() if 'many-count' not in key}
    elif type(value) is str and value.isdigit():
        n_value = int(value)
    else:
        if value != '' and value != 'none' and value != 'null' and value != 'Null':
            n_value = value
        else:
            n_value = None
    return n_value


def filter_on_search(*args, **kwargs):
    dt_data = kwargs['dt_data']
    search_string = dt_data['search']['value']
    queryset = kwargs['queryset']
    fields = get_searchable_fields(**kwargs)
    search_words = search_string.split()
    search_q = Q()
    for word in search_words:
        for f in fields:
            search_word = Q(**{'%s__icontains' % f: word})
            search_q |= search_word
    queryset = queryset.filter(search_q).distinct()
    return queryset


def filter_on_filters(*args, **kwargs):
    queryset = kwargs['queryset']
    filters = kwargs['filters']
    if 'and_list' in filters:
        queryset = queryset.filter(reduce(operator.and_, (Q(**q) for q in filters['and_list']))).distinct()
    if 'or_list' in filters:
        queryset = queryset.filter(reduce(operator.or_, (Q(**q) for q in filters['or_list']))).distinct()
    return queryset


def get_searchable_fields(**kwargs):
    dt_data = kwargs['dt_data']
    fields = []
    columns = dt_data['columns']
    for c in columns:
        if c['searchable'] is True:
            fields.append(get_clean_field_name(c['data'], **kwargs))
    return fields


def get_ordered_queryset(*args, **kwargs):
    queryset = kwargs['queryset']
    dt_data = kwargs['dt_data']
    order_column = dt_data['order'][0]['column']
    order_column_name = get_clean_field_name(dt_data['columns'][order_column]['data'], **kwargs)
    order_dir = dt_data['order'][0]['dir']
    if order_dir == 'desc':
        order = '-'+order_column_name
    else:
        order = order_column_name
    queryset = queryset.order_by(order)
    return queryset


def get_clean_field_name(field, **kwargs):
    if 'search_dict' in kwargs and field in kwargs['search_dict']:
        field = kwargs['search_dict'][field]
    elif '.' in field:
        field_list = field.split('.')
        field = '__'.join(field_list)
    return field


def get_error_array(errors, display_fields=[]):
    fieldErrors = []
    for k, v in errors.items():
        if type(v) is dict:
            for k2, v2 in v.items():
                field = k+'.'+k2
                fieldErrors.append({'name': field, 'status': str(v2[0])})
        else:
            if k in display_fields:
                field = k+'.value'
            else:
                field = k
            fieldErrors.append({'name': field, 'status': str(v[0])})
    return fieldErrors


""" USER MANAGEMENT FUNCTIONS """


def create_wp_user(data_dict):
    result = {}
    try:
        wp_dict = {
            'user_login': functions.get_unique_username(data_dict['user']['username'], 'wp'),
            'user_pass': phpass_context.hash(data_dict['user']['password']),
            'user_nicename': data_dict['user']['username'],
            'user_email': data_dict['user']['email'],
            'user_registered': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'display_name': data_dict['full_name']
            }
        wp_meta_list = [
            ['nickname', data_dict['user']['username']],
            ['first_name', data_dict['user']['first_name']],
            ['last_name', data_dict['user']['last_name']],
            ['wp_capabilities', data_dict['wp_role']]
        ]
        wp_user = wp_users(**wp_dict).save()
        wp_user = wp_users.objects.get(user_login=wp_dict['user_login'])
        for i in wp_meta_list:
            dict = {
                'user_id': wp_user.pk,
                'meta_key': i[0],
                'meta_value': i[1],
                }
            wp_usermeta(**dict).save()
        result['status'] = 201
        result['id'] = wp_user.pk
    except Exception as e:
        result['status'] = 400
        result['error'] = 'Failed to create WordPress user. Error: '+str(e)
    return result


def create_dam_user(data_dict):
    result = {}
    try:
        dam_dict = {
            'username': functions.get_unique_username(data_dict['user']['username'], 'dam'),
            'password': str(uuid.uuid4()),
            'fullname': data_dict['full_name'],
            'email': data_dict['user']['email'],
            'usergroup': data_dict['dam_usergroup'],
            'approved': 1,
        }
        dam_user = rs_user(**dam_dict).save()
        dam_user = rs_user.objects.get(username=dam_dict['username'])
        result['status'] = 201
        result['id'] = dam_user.pk
    except Exception as e:
        result['status'] = 400
        result['error'] = 'Failed to create DAM user. Error: '+str(e)
    return result


def create_wiki_user(data_dict):
    result = {}
    try:
        wiki_dict = {
            'user_name': bytes(functions.get_unique_username(data_dict['user']['username'], 'wiki'), encoding='ascii'),
            'user_real_name': bytes(data_dict['full_name'], encoding='ascii'),
            'user_password': bytes(str(uuid.uuid4().hex), encoding='ascii'),
            'user_email': bytes(data_dict['user']['email'], encoding='ascii'),
        }
        wiki_usr = wiki_user(**wiki_dict).save()
        wiki_usr = wiki_user.objects.get(user_name=wiki_dict['user_name'])
        wiki_groups = data_dict['wiki_groups']
        for i in wiki_groups:
            dict = {
                'ug_user': wiki_usr,
                'ug_group': bytes(i['ug_group'], encoding='ascii')
            }
            wiki_user_groups(**dict).save()
        result['status'] = 201
        result['id'] = wiki_usr.pk
    except Exception as e:
        result['status'] = 400
        result['error'] = 'Failed to create Wiki user. Error: '+str(e)
    return result
