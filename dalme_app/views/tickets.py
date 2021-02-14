from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils.decorators import method_decorator
from dalme_app.models import Ticket
from django.core.exceptions import ObjectDoesNotExist
from ._common import DALMEListView, DALMEDetailView


@method_decorator(login_required, name='dispatch')
class TicketDetail(DALMEDetailView):
    model = Ticket
    template_name = 'dalme_app/detail_views/ticket.html'
    breadcrumb = [('Project', ''), ('Issue Tickets', '/tickets')]

    def get_page_title(self):
        return 'Ticket #{}'.format(str(self.object.id))

    def get_object(self):
        try:
            object = super().get_object()
            return object
        except ObjectDoesNotExist:
            raise Http404


@method_decorator(login_required, name='dispatch')
class TicketList(DALMEListView):
    template_name = 'dalme_app/list_views/tickets.html'
    page_title = 'Issue Tickets'
    dt_config = 'tickets'
    breadcrumb = [('Project', ''), ('Issue Tickets', '/tickets')]
