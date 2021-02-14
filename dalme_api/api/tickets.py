from rest_framework.response import Response
from rest_framework.decorators import action
from dalme_api.serializers import TicketSerializer, TicketDetailSerializer
from dalme_app.models import Ticket
from dalme_api.access_policies import TicketAccessPolicy
from dalme_api.filters import TicketFilter
from ._common import DALMEModelViewSet


class Tickets(DALMEModelViewSet):
    """ API endpoint for managing issue tickets """
    permission_classes = (TicketAccessPolicy,)
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
    serializer_class_detail = TicketDetailSerializer
    filterset_class = TicketFilter
    ordering = ['status', 'id']
    search_fields = ['id', 'subject', 'description', 'tags__tag', 'comments__body', 'creation_user__username', 'creation_user__profile__full_name']
    ordering_fields = ['id', 'status', 'creation_user', 'creation_timestamp', 'no_comments']
    ordering_aggregates = {
        'no_comments': {
            'function': 'Count',
            'expression': 'comments'
        },
    }

    @action(detail=True, methods=['patch'])
    def set_state(self, request, *args, **kwargs):
        object = self.get_object()
        try:
            action = self.request.data['action']
            if action == 'Close':
                object.status = 1
                object.save(update_fields=['status', 'modification_user', 'modification_timestamp'])
            elif action == 'Open':
                object.status = 0
                object.save(update_fields=['status', 'modification_user', 'modification_timestamp'])
            result = {'username': self.request.user.username}
            status = 201
        except Exception as e:
            result = {'error': str(e)}
            status = 400
        return Response(result, status)

    def get_metadata(self, queryset):
        return {
            'open': queryset.filter(status=0).count(),
            'closed': queryset.filter(status=1).count(),
            'authors': [dict(tup) for tup in {tuple(pair.items()) for pair in Ticket.objects.values('creation_user__id', 'creation_user__profile__full_name')}]
        }
