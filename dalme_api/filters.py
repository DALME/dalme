from django_filters import rest_framework as filters
from dalme_app.models import Source, Set, Content_type, Ticket


class ContenTypeFilter(filters.FilterSet):
    id__lt = filters.NumberFilter(field_name='id', lookup_expr='lt')

    class Meta:
        model = Content_type
        fields = ['id']


class SourceFilter(filters.FilterSet):
    wf_status = filters.NumberFilter(field_name='workflow__wf_status', lookup_expr='iexact')
    wf_stage = filters.NumberFilter(field_name='workflow__stage', lookup_expr='iexact')
    help_flag = filters.BooleanFilter(field_name='workflow__help_flag')
    is_public = filters.BooleanFilter(field_name='workflow__is_public')
    ingestion_done = filters.BooleanFilter(field_name='workflow__ingestion_done')
    transcription_done = filters.BooleanFilter(field_name='workflow__transcription_done')
    markup_done = filters.BooleanFilter(field_name='workflow__markup_done')
    review_done = filters.BooleanFilter(field_name='workflow__review_done')
    parsing_done = filters.BooleanFilter(field_name='workflow__parsing_done')
    type__in = filters.NumberFilter(field_name='type', lookup_expr='in')
    type__lt = filters.NumberFilter(field_name='type', lookup_expr='lt')
    pd_null = filters.BooleanFilter(field_name='primary_dataset', lookup_expr='isnull')

    class Meta:
        model = Source
        fields = ['type', 'type__name', 'type__in', 'name', 'short_name', 'owner',
                  'primary_dataset', 'parent', 'has_inventory', 'is_private']

    @property
    def qs(self):
        parent = super().qs
        if self.request.GET.get('mode') is not None:
            mode = self.request.GET['mode']
            if mode == 'team':
                dataset = Set.objects.get(dataset_usergroup=self.request.user.profile.primary_group)
                return parent.filter(primary_dataset=dataset.id)
            elif mode == 'all':
                return parent.filter(is_private=False)
            else:
                return parent.filter(owner=self.request.user)
        else:
            return parent


class SetFilter(filters.FilterSet):

    class Meta:
        model = Set
        fields = ['set_type', 'name', 'is_public', 'has_landing', 'endpoint',
                  'permissions', 'description', 'dataset_usergroup', 'dataset_usergroup__name']

    @property
    def qs(self):
        parent = super().qs
        # change general qs based on superadmin status
        if self.request.GET.get('mode') is not None:
            mode = self.request.GET['mode']
            if mode == 'group':
                return parent
            elif mode == 'all':
                return parent.filter(set_type=4)
            else:
                return parent.filter(owner=self.request.user)
        else:
            return parent


class TicketFilter(filters.FilterSet):
    tags = filters.CharFilter(field_name='tags__tag', lookup_expr='icontains')

    class Meta:
        model = Ticket
        fields = ['id', 'subject', 'description', 'status', 'tags', 'url', 'file',
                  'creation_user', 'creation_timestamp']
