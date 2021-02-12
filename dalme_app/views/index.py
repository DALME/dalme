from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ._common import DALMEContextMixin
from django.views.generic.base import TemplateView


@method_decorator(login_required, name='dispatch')
class Index(TemplateView, DALMEContextMixin):
    template_name = 'dalme_app/index.html'
    page_title = 'Dashboard'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cards'] = self.request.user.preferences['interface__homepage_cards']
        return context
