from django.contrib.auth.models import User
from django.db.models import Q, Count
import uuid
import datetime
import json
import ast
import operator
import os
from functools import reduce
from rest_framework import viewsets
from dalme_app.serializers import (DTFieldsSerializer, DTListsSerializer, LanguageSerializer, TaskSerializer,
                                   TaskListSerializer, PageSerializer, RSImageSerializer, TranscriptionSerializer,
                                   SourceSerializer, ProfileSerializer, AttributeTypeSerializer, ContentXAttributeSerializer,
                                   ContentTypeSerializer, ContentClassSerializer, AsyncTaskSerializer, SimpleAttributeSerializer,
                                   CountrySerializer, CitySerializer, AttachmentSerializer, TicketSerializer, CommentSerializer, WorkflowSerializer,
                                   SetSerializer, RightsSerializer)
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import FileUploadParser, FormParser, MultiPartParser
from dalme_app.models import (Profile, Attribute_type, Content_class, Content_type, Content_attributes, DT_list,
                              DT_fields, Page, Source_pages, Source, Transcription, LanguageReference,
                              TaskList, Task, rs_resource, rs_collection, rs_collection_resource, rs_user, wiki_user,
                              wiki_user_groups, wp_users, wp_usermeta, Attribute, CountryReference, CityReference, Attachment, Ticket, Tag,
                              Comment, Workflow, Set, Set_x_content, RightsPolicy)
from django_celery_results.models import TaskResult
from django.db.models.expressions import RawSQL
from rest_framework.permissions import DjangoModelPermissions
from django.shortcuts import get_object_or_404
from passlib.apps import phpass_context
from dalme_app import functions
from django.utils import timezone
from dalme_app.access_policies import SourceAccessPolicy
from dalme_app.utils import IsOwnerOrReadOnly


class CityList(viewsets.ModelViewSet):
    """ API endpoint for managing cities """
    queryset = CityReference.objects.all()
    serializer_class = CitySerializer
    dt_fields = [
        {'header': "ID", 'field': "id"},
        {'header': "City Name", 'field': "name"},
        {'header': "Administrative Region", 'field': "administrative_region"},
        {'header': "Country", 'field': "country.name"}
    ]

    def list(self, request, *args, **kwargs):
        response = super().list(request, args, kwargs)
        response.data['headers'] = self.dt_fields
        return response

    def get_queryset(self, *args, **kwargs):
        sort_field = self.request.GET.get('sortBy', False)
        sort_desc = self.request.GET.get('sortDesc', False)
        search = self.request.GET.get('search', False)
        queryset = self.queryset

        # fields = ['name', 'administrative_region', 'country__name']
        # fields = CitySerializer.Meta.fields
        fields = [i['field'] for i in self.dt_fields if i['field'] not in ['id']]

        if search:
            if '+' in search:
                search = search.split('+')
            else:
                search = [search]
            search_q = Q()
            for s in search:
                for f in fields:
                    search_word = Q(**{'%s__icontains' % f: s})
                    search_q |= search_word
            # queryset = queryset.filter(search_q).distinct()
            queryset = queryset.filter(search_q)

        if sort_field:
            if ',' in sort_field:
                sort_field = sort_field.split(',')
                sort_desc = sort_desc.split(',')
            else:
                sort_field = [sort_field]
                sort_desc = [sort_desc]

            filters = ['-' + f if sort_desc[i] == 'true' else f for i, f in enumerate(sort_field)]

            queryset = queryset.order_by(*filters)

        return queryset


class Datasets(viewsets.ViewSet):
    """ API endpoint for generating lists of options for DTE forms """
    permission_classes = (DjangoModelPermissions,)
    queryset = Workflow.objects.all()

    def list(self, request, *args, **kwargs):
        data_dict = {}
        if self.request.GET.get('id') is not None:
            try:
                ds_id = self.request.GET['id']
                if ds_id == '1':
                    data_dict = {
                        'chart': {'type': 'bar'},
                        'title': {'text': 'Sources worked on per period and per processing stage'},
                        'yAxis': {'min': 0, 'title': {'text': 'Number of sources'}},
                        'legend': {'reversed': 'true'},
                        'plotOptions': {'series': {'stacking': 'normal'}},
                        'series': []
                    }
                    x_dict = {
                        'Past week': 'timedelta|7',
                        'Past month': 'timedelta|30',
                        'Past three months': 'timedelta|90',
                        'Past year': 'timedelta|365',
                        'Earlier': 'timedelta|older'
                    }
                    y_dict = {
                        1: 'ingestion',
                        2: 'transcription',
                        3: 'markup',
                        4: 'review',
                        5: 'parsing',
                    }
                    categories = [label for label, query in x_dict.items()]
                    for stage, name in y_dict.items():
                        queryset = Source.objects.filter(has_inventory=True, workflow__stage=stage)
                        src_counts = []
                        for label, query in x_dict.items():
                            src_counts.append(filter_on_workflow(queryset=queryset, wf_query=query).count())
                        data_dict['series'].append({'name': name, 'data': src_counts})
                    data_dict['xAxis'] = {'categories': categories}
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the dataset: ' + str(e)
        else:
            data_dict['error'] = 'No dataset id was included in the request.'
        return Response(data_dict)


class WorkflowManager(viewsets.ModelViewSet):
    """ API endpoint for managing the project's workflow """
    permission_classes = (DjangoModelPermissions,)
    queryset = Workflow.objects.all()
    serializer_class = WorkflowSerializer

    @action(detail=True, methods=['patch'])
    def change_state(self, request, *args, **kwargs):
        result = {}
        #object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        #self.check_object_permissions(request, object)
        object = self.get_object()
        try:
            action = self.request.POST['action']
            stage_dict = dict(Workflow.PROCESSING_STAGES)
            status_dict = dict(Workflow.WORKFLOW_STATUS)
            if action == 'stage_done':
                stage = int(self.request.POST['code'])
                stage_name = stage_dict[stage]
                setattr(object, stage_name + '_done', True)
                object.last_user = request.user
                object.last_modified = timezone.now()
                object.save()
                functions.update_log(object, stage_name + ': marked as done')
                next_stage = stage + 1
                result['prev_stage_name'] = stage_name
                result['mod_html'] = '<i class="far fa-history fa-fw"></i> Now | <a href="/users/' + request.user.username + '">' + request.user.profile.full_name + '</a>'
                if stage == 4:
                    result['status_html'] = '<div class="wf-manager-status tag-wf-awaiting">awaiting parsing</div>'
                else:
                    result['status_html'] = '<button class="wf-manager-status_btn tag-wf-awaiting" role="button" onclick="update_workflow(\'begin_stage\',' + str(next_stage) + ')">\
                    begin ' + stage_dict[next_stage] + '</button>'
            elif action == 'begin_stage':
                stage = int(self.request.POST['code'])
                stage_name = stage_dict[stage]
                object.stage = stage
                object.last_user = request.user
                object.last_modified = timezone.now()
                object.save()
                functions.update_log(object, stage_name + ': work commenced')
                result['stage_name'] = stage_name
                result['mod_html'] = '<i class="far fa-history fa-fw"></i> Now | <a href="/users/' + request.user.username + '">' + request.user.profile.full_name + '</a>'
                result['status_html'] = '<div class="wf-manager-status tag-wf-in_progress">' + stage_name + ' in progress</div>\
                <button class="wf-manager-status_btn tag-wf-in_progress" role="button" onclick="update_workflow(\'stage_done\', ' + str(stage) + ')">\
                <i class="far fa-check-square fa-fw"></i> DONE</button>'
            elif action == 'toggle_help':
                if object.help_flag:
                    object.help_flag = False
                else:
                    object.help_flag = True
                object.last_user = request.user
                object.last_modified = timezone.now()
                object.save()
                functions.update_log(object, 'help flag set to ' + str(object.help_flag))
            elif action == 'toggle_public':
                if object.is_public:
                    object.is_public = False
                else:
                    object.is_public = True
                object.last_user = request.user
                object.last_modified = timezone.now()
                object.save()
                functions.update_log(object, 'public flag set to ' + str(object.is_public))
            elif action == 'change_status':
                status = int(self.request.POST['code'])
                prev_status = object.wf_status
                object.wf_status = status
                object.last_user = request.user
                object.last_modified = timezone.now()
                object.save()
                functions.update_log(object, 'status changed from "' + status_dict[prev_status] + '" to "' + status_dict[status] + '"')
                status_name = status_dict[status]
                result['mod_html'] = '<i class="far fa-history fa-fw"></i> Now | <a href="/users/' + request.user.username + '">' + request.user.profile.full_name + '</a>'
                if status != 2:
                    result['status_html'] = '<div class="wf-manager-status tag-wf-' + status_name + '">' + status_name + '</div>'
                else:
                    stage = object.stage
                    stage_name = stage_dict[stage]
                    if getattr(object, stage_name + '_done'):
                        if stage == 4:
                            result['status_html'] = '<div class="wf-manager-status tag-wf-awaiting">awaiting parsing</div>'
                        else:
                            next_stage = stage + 1
                            result['status_html'] = '<button class="wf-manager-status_btn tag-wf-awaiting" role="button" onclick="update_workflow(\'begin_stage\', ' + str(next_stage) + ')">\
                            begin ' + stage_dict[next_stage] + '</button>'
                    else:
                        result['status_html'] = '<div class="wf-manager-status tag-wf-in_progress">' + stage_name + ' in progress</div>\
                        <button class="wf-manager-status_btn tag-wf-in_progress" role="button" onclick="update_workflow(\'stage_done\', ' + str(stage) + ')">\
                        <i class="far fa-check-square fa-fw"></i> DONE</button>'
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)


class DTViewSet(viewsets.ModelViewSet):
    """ Generic viewset for managing communication with DataTables.
    Should be subclassed for specific API endpoints. """

    @action(detail=True, methods=['post'])
    def has_permission(self, request, pk=None):
        object = self.get_object()
        self.check_object_permissions(self.request, object)
        return Response(200)

    @action(detail=False)
    def get_set(self, request, *args, **kwargs):
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
                query_list = list(queryset.values_list('id', flat=True))
                data_dict['data'] = query_list
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to fetch the set: ' + str(e)
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
            # try:
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
            # except Exception as e:
            #     data_dict['error'] = 'The following error occured while trying to fetch the data: ' + str(e)
        else:
            queryset = self.get_queryset()
            try:
                serializer = self.get_serializer(queryset, many=True)
                data = serializer.data
                data_dict['data'] = data
            except Exception as e:
                data_dict['error'] = 'The following error occured while trying to serialize the data: ' + str(e)
        return Response(data_dict)

    # def retrieve(self, request, pk=None):
    #     object = get_object_or_404(self.queryset, pk=pk)
    #     serializer = self.get_serializer(object)
    #     return Response(serializer.data)

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
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
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
                self.check_object_permissions(request, object)
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
        elif self.request.GET.get('workset') is not None:
            ws_id = self.request.GET['workset']
            queryset = self.queryset.filter(sets__set_id=ws_id)
        else:
            queryset = self.queryset
        return queryset

    def filter_on_search(self, *args, **kwargs):
        return filter_on_search(*args, **kwargs)

    def filter_on_filters(self, *args, **kwargs):
        return filter_on_filters(*args, **kwargs)

    def filter_on_workflow(self, *args, **kwargs):
        return filter_on_workflow(*args, **kwargs)

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
    queryset = TaskResult.objects.all()
    serializer_class = AsyncTaskSerializer


class Countries(DTViewSet):
    """ API endpoint for managing countries """
    queryset = CountryReference.objects.all()
    serializer_class = CountrySerializer


class Cities(DTViewSet):
    """ API endpoint for managing cities """
    queryset = CityReference.objects.all()
    serializer_class = CitySerializer


class Rights(DTViewSet):
    """ API endpoint for managing rights policies """
    queryset = RightsPolicy.objects.all()
    serializer_class = RightsSerializer


class AttributeTypes(DTViewSet):
    """ API endpoint for managing attribute types """
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
        if self.request.GET.get('filter') is not None and self.request.GET['filter'].split(',')[0] == 'content_type':
            serializer = ContentXAttributeSerializer
        else:
            serializer = self.serializer_class
        return serializer


class Attributes(DTViewSet):
    """ API endpoint for managing attributes """
    queryset = Attribute.objects.all().order_by('attribute_type')
    serializer_class = SimpleAttributeSerializer


class ContentClasses(DTViewSet):
    """ API endpoint for managing content classes """
    queryset = Content_class.objects.all()
    serializer_class = ContentClassSerializer


class ContentTypes(DTViewSet):
    """ API endpoint for managing content types """
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
            object = Content_type.objects.get(pk=new_obj.id)
            if attribute_types is not None:
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

    def update(self, request, *args, **kwargs):
        result = {}
        partial = kwargs.pop('partial', False)
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        attribute_types = data_dict.pop('attribute_types', None)
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
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
    queryset = DT_fields.objects.all()
    serializer_class = DTFieldsSerializer


class DTLists(DTViewSet):
    """ API endpoint for managing DataTables lists """
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
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
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
                data = self.request.GET['data']
                id_list = data.split(',')
                search_q = Q()
                for i in id_list:
                    q = Q(**{'ref': i})
                    search_q |= q
                queryset = self.queryset.filter(search_q)
                # collections_list = []
                folios = {}
                source_data = {}
                for image in queryset:
                    folios[image.ref] = image.field79
                    img_data = {i.resource_type_field.name: i.value for i in image.resource_data.all()
                                if i.resource_type_field.ref in [12, 29, 76, 77, 78, 80, 99]}
                    img_data['title'] = image.field8
                    img_data['country'] = image.field3
                    theme2 = image.collections.filter(theme2__isnull=False)
                    if theme2.exists() and 'archive' not in source_data:
                        img_data['archive'] = theme2[0].theme2
                    if 'city' not in source_data and img_data.get('archivalsource', '') != '' and ',' in img_data.get('archivalsource', ''):
                        img_data['city'] = img_data.get('archivalsource').split(',')[0]
                        img_data['archive'] = img_data.get('archivalsource').split(',')[1]
                    if 'collection_title' not in source_data and 'city' in img_data:
                        collections = image.collections.filter(theme=img_data['city']).exclude(name__icontains='images')
                        if collections.count() == 1:
                            img_data['collection_title'] = collections[0].name
                    for k, v in img_data.items():
                        if k not in source_data and v not in ['', ' ', None]:
                            source_data[k] = v
                short_archive = '<ARCHIVE>'
                short_series = '<SERIES>'
                if 'archive' in source_data:
                    archive = Source.objects.filter(name=source_data['archive'])
                    if archive.exists():
                        short_archive = archive[0].short_name
                if 'Series' in source_data:
                    short_series = ''.join([c for c in source_data['Series'] if c.isupper()])
                if 'person' in source_data:
                    src_title = 'Inventory of ' + source_data['person']
                    src_title_short = source_data['person'].split()[-1]
                elif 'collection_title' in source_data:
                    src_title = source_data['collection_title']
                    src_title_short = source_data['collection_title'].split()[-1]
                elif 'title' in source_data:
                    src_title = source_data['title']
                    src_title_short = source_data['title'].split()[-1]
                else:
                    src_title = ''
                    src_title_short = ''
                shelf_number = source_data.get('shelfnumber', '')
                source_data['name'] = '{} ({} {} {})'.format(src_title, short_archive, short_series, shelf_number)
                source_data['short_name'] = '{} {} {} ({})'.format(short_archive, short_series, shelf_number, src_title_short)
                result['data'] = {'source_fields': source_data, 'folios': folios}
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
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
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
    queryset = LanguageReference.objects.all()
    serializer_class = LanguageSerializer


class Options(viewsets.ViewSet):
    """ API endpoint for generating data for options in the UI """
    queryset = Set.objects.none()

    def list(self, request, *args, **kwargs):
        data_dict = {}
        if self.request.GET.get('target') is not None:
            target = self.request.GET['target'].split(',')
            try:
                for ls in target:
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
            data_dict['error'] = 'No target was included in the request.'
        return Response(data_dict)

    def json_file(self, **kwargs):
        if self.request.GET.get('name') is not None:
            filename = self.request.GET['name']
            file = os.path.join('dalme_app', 'templates', 'json', filename + '.json')
        with open(file, 'r') as fp:
            output = json.load(fp)
        return output

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
            # opt_list = [{'label': i.attribute_type.name+' ('+i.attribute_type.short_name+')', 'value': i.attribute_type.id} for i in qset]
            opt_list = [{'label': i.attribute_type.name, 'value': i.attribute_type.id} for i in qset]
            if self.request.GET.get('extra') is not None:
                ref_dict = {i.attribute_type.id: [i.attribute_type.data_type, i.attribute_type.options_list] for i in qset}
                options_list = {'options': opt_list, 'ref': ref_dict}
            else:
                options_list = opt_list
        else:
            # options_list = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Attribute_type.objects.all().order_by('name')]
            options_list = [{'label': i.name, 'value': i.id} for i in Attribute_type.objects.all().order_by('name')]
        return options_list

    def active_staff(self, **kwargs):
        staff_options = [{'label': i.full_name, 'value': i.user_id} for i in Profile.objects.filter(user__is_active=1).order_by('user__username')]
        return staff_options

    def content_types(self, content_class=None, **kwargs):
        if content_class is not None and content_class != 0:
            content_types = [{'label': i.name, 'value': i.id} for i in Content_type.objects.filter(content_class=content_class).order_by('name')]
        elif content_class == 0:
            content_types = [{'label': i.name, 'value': i.id} for i in Content_type.objects.filter(content_class=1, has_pages=True).order_by('name')]
        else:
            content_types = [{'label': i.name, 'value': i.id} for i in Content_type.objects.all().order_by('name')]
        return content_types

    def content_types_opt(self, **kwargs):
        content_types = {i.id: {'pages': i.has_pages, 'inv': i.has_inventory} for i in Content_type.objects.all()}
        return content_types

    def user_worksets(self, **kwargs):
        worksets_options = [{'label': i.name, 'value': i.id} for i in Set.objects.filter(owner=str(self.request.user.id)).order_by('name')]
        return worksets_options

    def available_sets(self, **kwargs):
        filters = Q(owner=str(self.request.user.id))
        filters |= Q(set_permissions__in=[3, 4])
        sets = [{'label': '{} ({})'.format(i.name, i.get_set_type_display()), 'value': i.id} for i in Set.objects.filter(filters).distinct().order_by('name')]
        return sets

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
            parent_types = Content_type.objects.get(pk=source_type).parents
            if parent_types is not None and ',' in parent_types:
                list_ids = parent_types.split(',')
                parent_sources = []
                for sid in list_ids:
                    parent_sources += [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Source.objects.filter(type=sid).order_by('short_name')]
            elif parent_types is not None:
                parent_sources = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Source.objects.filter(type=parent_types).order_by('short_name')]
            else:
                parent_sources = 'n/a'
        else:
            parent_sources = [{'label': i.name+' ('+i.short_name+')', 'value': i.id} for i in Source.objects.all().order_by('short_name')]
        return parent_sources


class Pages(DTViewSet):
    """ API endpoint for managing pages """
    queryset = Page.objects.all()
    serializer_class = PageSerializer

    @action(detail=True, methods=['post', 'get'])
    def get_rights(self, request, *args, **kwargs):
        result = {}
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        try:
            result['rights'] = object.get_rights()
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)


class Sources(DTViewSet):
    """ API endpoint for managing sources """
    permission_classes = (SourceAccessPolicy, IsOwnerOrReadOnly,)
    queryset = Source.objects.all()
    serializer_class = SourceSerializer
    display_fields = ['name', 'type', 'parent']

    @action(detail=True, methods=['patch'])
    def change_description(self, request, *args, **kwargs):
        result = {}
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        try:
            action = self.request.POST['action']
            desc_text = self.request.POST['description']
            desc_att_obj = Attribute_type.objects.get(pk=79)
            if action == 'update':
                att_obj = Attribute.objects.filter(object_id=object.id, attribute_type=desc_att_obj)[0]
                att_obj.value_TXT = desc_text
                att_obj.save(update_fields=['value_TXT', 'modification_username', 'modification_timestamp'])
            elif action == 'create':
                object.attributes.create(attribute_type=desc_att_obj, value_TXT=desc_text)
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    # @action(detail=True, methods=['post'])
    # def add_identity_phrase(self, request, *args, **kwargs):
    #     result = {}
    #     object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
    #     try:

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
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
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
                        if new_att.get('value_UUID', None) is not None:
                            new_att['value_STR'] = new_att.pop('value_UUID')
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
            content_types = DT_list.objects.get(short_name=type).content_types.all()
            for i in content_types:
                q_obj |= Q(type=i.pk)
            if type == 'records':
                # queryset = queryset.filter(q_obj).annotate(no_folios=Count('pages'))
                queryset = queryset.filter(q_obj).annotate(no_folios=Count('pages', filter=Q(pages__source__isnull=False)))
            else:
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
        local_fields = ['id', 'type', 'name', 'short_name', 'parent', 'has_inventory', 'no_folios', 'tags', 'workflow']
        annotate_dict = {}
        if filters.get('and_list') is not None:
            for filter in filters['and_list']:
                annotate_dict = self.get_annotation(filter, local_fields, annotate_dict)
        if filters.get('or_list') is not None:
            for filter in filters['or_list']:
                annotate_dict = self.get_annotation(filter, local_fields, annotate_dict)
        queryset = queryset.annotate(**annotate_dict)
        if filters.get('and_list') is not None:
            for i, f in enumerate(filters['and_list']):
                (key, val), = f.items()
                if 'timedelta' in str(val):
                    cut_off = timezone.now().date() - datetime.timedelta(**{'days': int(val.split('-')[1])})
                    filters['and_list'][i][key] = cut_off
            qf = reduce(operator.and_, (Q(**q) for q in filters['and_list']))
        if filters.get('or_list') is not None:
            qf |= reduce(operator.or_, (Q(**q) for q in filters['or_list']))
        queryset = queryset.filter(qf).distinct()
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
        local_fields = ['id', 'type', 'name', 'short_name', 'parent', 'has_inventory', 'no_folios']
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
        if type != 'records':
            kwargs['fields'] = ['no_folios', 'workflow']
        return serializer_class(*args, **kwargs)


class Tasks(DTViewSet):
    """ API endpoint for managing tasks """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer

    @action(detail=True, methods=['patch'])
    def set_state(self, request, *args, **kwargs):
        result = {}
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        try:
            action = self.request.POST['action']
            if action == 'mark_done':
                object.completed = True
                object.save(update_fields=['completed', 'modification_username', 'modification_timestamp'])
            elif action == 'mark_undone':
                object.completed = False
                object.save(update_fields=['completed', 'modification_username', 'modification_timestamp'])
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)


class Comments(viewsets.ModelViewSet):
    """ API endpoint for managing comments """
    permission_classes = (DjangoModelPermissions,)
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('model') is not None and self.request.GET.get('object') is not None:
            model = self.request.GET['model']
            object = self.request.GET['object']
            if type(object) is not str:
                object = str(object)
            obj_instance = eval(model+'.objects.get(pk="'+object+'")')
            queryset = obj_instance.comments.all()
        else:
            queryset = self.queryset
            # raise ValueError('A model and object must be provided to filter the comments dataset.')
        return queryset

    def create(self, request, *args, **kwargs):
        result = {}
        data = request.data
        try:
            content_object = eval(data['model']+'.objects.get(pk="'+data['object']+'")')
            new_comment = content_object.comments.create(body=data['body'])
            serializer = self.get_serializer(new_comment)
            result = serializer.data
            status = 201
        except Exception as e:
            result = str(e)
            status = 400
        return Response(result, status)


class Tickets(DTViewSet):
    """ API endpoint for managing issue tickets """
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    @action(detail=True, methods=['patch'])
    def set_state(self, request, *args, **kwargs):
        result = {}
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        try:
            action = self.request.POST['action']
            if action == 'Close':
                object.status = 1
                object.save(update_fields=['status', 'modification_username', 'modification_timestamp'])
            elif action == 'Open':
                object.status = 0
                object.save(update_fields=['status', 'modification_username', 'modification_timestamp'])
            result['username'] = self.request.user.username
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    def create(self, request, *args, **kwargs):
        result = {}
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        tags = data_dict.pop('tags', None)
        serializer = self.get_serializer(data=data_dict)
        if serializer.is_valid():
            new_obj = serializer.save()
            if tags is not None:
                if type(tags) is not list:
                    tags = [tags]
                for tag in tags:
                    tag_dict = {
                            'content_object': new_obj,
                            'tag_type': 'T',
                            'tag': tag
                        }
                    Tag.objects.create(**tag_dict)
                    # new_tag = Tag(**tag_dict)
                    # new_tag.save()
            object = Ticket.objects.get(pk=new_obj.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            status = 201
        else:
            result['fieldErrors'] = get_error_array(serializer.errors)
            status = 400
        return Response(result, status)


class TaskLists(DTViewSet):
    """ API endpoint for managing tasks lists """
    queryset = TaskList.objects.all().annotate(task_count=Count('task'))
    serializer_class = TaskListSerializer


class Attachments(viewsets.ModelViewSet):
    """ API endpoint for managing attachments """
    permission_classes = (DjangoModelPermissions,)
    parser_classes = (MultiPartParser, FormParser, FileUploadParser,)
    queryset = Attachment.objects.all()
    serializer_class = AttachmentSerializer

    def create(self, request, format=None):
        result = {}
        try:
            new_obj = Attachment()
            new_obj.file = request.data['upload']
            new_obj.save()
            result['upload'] = {'id': new_obj.id}
            result['files'] = {'Attachment': {str(new_obj.id): {
                'filename': str(new_obj.filename),
                'web_path': str(new_obj.file)
            }}}
            status = 201
        except Exception as e:
            result['error'] = 'There was an error processing the file: '+str(e)
            status = 400
        return Response(result, status)


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
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def create(self, request, *args, **kwargs):
        result = {}
        display_fields = ['dam_usergroup', 'wp_role']
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        if data_dict['user'].get('groups', None) is not None and type(data_dict['user']['groups']) is not list:
            data_dict['user']['groups'] = [data_dict['user']['groups']]
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
        # object = get_object_or_404(self.queryset, pk=kwargs.get('pk'))
        # self.check_object_permissions(request, object)
        object = self.get_object()
        display_fields = ['dam_usergroup', 'wp_role']
        data_dict = get_dte_data(request)
        data_dict = data_dict[0][1]
        dam_usergroup = data_dict.pop('dam_usergroup', None)
        if data_dict.get('wiki_groups') is not None and data_dict.get('wiki_groups') != 0:
            if type(data_dict['wiki_groups']) is list:
                wiki_groups = [i['ug_group'] for i in data_dict.pop('wiki_groups', None)]
            else:
                wiki_groups = [data_dict.pop('wiki_groups')['ug_group']]
        else:
            wiki_groups = None
        wp_role = data_dict['wp_role']
        groups = data_dict['user'].pop('groups', None)
        if groups is not None:
            if type(groups) is list:
                groups = [i['id'] for i in groups]
            else:
                groups = [groups['id']]
        data_dict['groups'] = groups
        serializer = self.get_serializer(object, data=data_dict, partial=partial)
        if serializer.is_valid():
            serializer.save()
            if dam_usergroup != '':
                rs_user.objects.filter(ref=object.dam_user).update(usergroup=dam_usergroup)
            if wp_role != '':
                wp_usermeta.objects.filter(user_id=object.wp_user, meta_key='wp_capabilities').update(meta_value=wp_role)
            if wiki_groups is not None:
                wiki_user_groups.objects.filter(ug_user=object.wiki_user).delete()
                usr = wiki_user.objects.get(user_id=object.wiki_user)
                for i in wiki_groups:
                    dict = {
                        'ug_user': usr,
                        'ug_group': bytes(i, encoding='ascii')
                    }
                    wiki_user_groups(**dict).save()
            object = Profile.objects.get(pk=object.id)
            serializer = self.get_serializer(object)
            result['data'] = serializer.data
            result['data_dict'] = data_dict
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


class Sets(DTViewSet):
    """ API endpoint for managing sets """
    queryset = Set.objects.all()
    serializer_class = SetSerializer

    @action(detail=False, methods=['post'])
    def add_members(self, request, *args, **kwargs):
        result = {}
        try:
            data = request.data
            members = json.loads(data['qset'])
            set_id = data['data[0][set]']
            object = self.queryset.get(pk=set_id)
            new_members = []
            for i in members:
                source_object = Source.objects.get(pk=i)
                if not Set_x_content.objects.filter(set_id=set_id, object_id=source_object).exists():
                    new_entry = Set_x_content()
                    new_entry.set_id = object
                    new_entry.content_object = source_object
                    new_members.append(new_entry)
            Set_x_content.objects.bulk_create(new_members)
            result['message'] = 'Action succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    @action(detail=True, methods=['patch'])
    def remove_members(self, request, *args, **kwargs):
        result = {}
        try:
            set_id = kwargs.get('pk')
            members = json.loads(self.request.POST['members'])
            member_objects = Set_x_content.objects.filter(set_id=set_id, object_id__in=members)
            member_objects.delete()
            result['message'] = 'Action succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    @action(detail=True, methods=['patch'])
    def workset_state(self, request, *args, **kwargs):
        result = {}
        try:
            action = self.request.POST['action']
            target = self.request.POST['target']
            set_id = kwargs.get('pk')
            object = Set_x_content.objects.get(set_id=set_id, object_id=target)
            if action == 'mark_done':
                mark = True
            elif action == 'mark_undone':
                mark = False
            object.workset_done = mark
            object.save(update_fields=['workset_done', 'modification_username', 'modification_timestamp'])
            result['message'] = 'Update succesful.'
            status = 201
        except Exception as e:
            result['error'] = str(e)
            status = 400
        return Response(result, status)

    def create(self, request, format=None):
        data = request.data
        member_list = json.loads(data['qset'])
        set_para = {
            'name': data['data[0][name]'],
            'description': data['data[0][description]'],
            'set_permissions': data['data[0][set_permissions]'],
            'set_type': data['data[0][set_type]'],
            'endpoint': data['endpoint']
        }
        serializer = SetSerializer(data=set_para)
        if serializer.is_valid():
            new_set = Set(**set_para)
            new_set.save()
            set_object = Set.objects.get(pk=new_set.id)
            new_members = []
            for i in member_list:
                source_object = Source.objects.get(pk=i)
                new_entry = Set_x_content()
                new_entry.set_id = set_object
                new_entry.content_object = source_object
                new_members.append(new_entry)
            Set_x_content.objects.bulk_create(new_members)
            serializer = SetSerializer(set_object)
            result = serializer.data
            status = 201
        else:
            result = get_error_array(serializer.errors)
            status = 400

        return Response(result, status)

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('type') is not None:
            type = int(self.request.GET['type'])
            queryset = self.queryset.filter(set_type=type)
        else:
            queryset = self.queryset
        return queryset


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


def filter_on_workflow(*args, **kwargs):
    queryset = kwargs['queryset']
    wf_query = kwargs['wf_query']
    query_list = wf_query.split('|')
    if query_list[0] == 'special':
        status_list = [1, 2, 3]
        q_dict = {'workflow__wf_status__in': status_list}
    elif query_list[0] == 'timedelta':
        if query_list[1] != 'older':
            timedelta_dict = {'days': int(query_list[1])}
            cut_off = timezone.now().date() - datetime.timedelta(**timedelta_dict)
            q_dict = {'workflow__last_modified__gte': cut_off}
        else:
            cut_off = timezone.now().date() - datetime.timedelta(days=365)
            q_dict = {'workflow__last_modified__lte': cut_off}
    elif query_list[0] == 'status':
        stage_dict = dict(Workflow.PROCESSING_STAGES)
        if query_list[1] == 'awaiting':
            q_dict = {
                'workflow__stage': int(query_list[2]) - 1,
                'workflow__' + stage_dict[int(query_list[2]) - 1] + '_done': True,
            }
        elif query_list[1] == 'in_progress':
            q_dict = {
                'workflow__stage': int(query_list[2]),
                'workflow__' + stage_dict[int(query_list[2])] + '_done': False,
            }
        elif query_list[1] == 'done':
            q_dict = {
                'workflow__' + stage_dict[int(query_list[2])] + '_done': True,
            }
        elif query_list[1] == 'not_done':
            q_dict = {
                'workflow__' + stage_dict[int(query_list[2])] + '_done': False,
            }
    else:
        if query_list[1].isdigit():
            value = int(query_list[1])
        else:
            value = query_list[1]
        q_dict = {'workflow__' + query_list[0]: value}
    return queryset.filter(Q(**q_dict))


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
                try:
                    fieldErrors.append({'name': field, 'status': str(v2[0])})
                except KeyError:
                    fieldErrors.append({'name': field, 'status': errors})
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
        wiki_user(**wiki_dict).save()
        new_user = wiki_user.objects.get(user_name=wiki_dict.get('user_name'))
        wiki_groups = data_dict.get('wiki_groups', None)
        if type(wiki_groups) is not list:
            wiki_groups = [wiki_groups]
        if wiki_groups is not None:
            for i in wiki_groups:
                dict = {
                    'ug_user': new_user,
                    'ug_group': bytes(i['ug_group'], encoding='ascii')
                }
                wiki_user_groups(**dict).save()
        result['status'] = 201
        result['id'] = new_user.pk
    except Exception as e:
        result['status'] = 400
        result['error'] = 'Failed to create Wiki user. Error: '+str(e)
    return result
