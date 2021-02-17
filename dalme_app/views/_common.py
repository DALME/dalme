from django.views.generic.base import TemplateView, ContextMixin
from django.views.generic import DetailView
from django.conf import settings
from dalme_app.forms import SearchForm
from django.forms import formset_factory
import os
import json


class DALMEContextMixin(ContextMixin):
    breadcrumb = None
    page_title = None
    comments = False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        main_menu, secondary_menu = self.get_menus()
        context.update({
            'api_endpoint': settings.API_ENDPOINT,
            'db_endpoint': settings.DB_ENDPOINT,
            'page_title': self.get_page_title(),
            'comments': self.comments,
            'form': formset_factory(SearchForm),
            'preferences': self.get_preferences(),
            'page_context': {
                'breadcrumb': self.get_breadcrumb(),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.profile.full_name,
                    'avatar': user.profile.profile_image,
                    'groups': [g.name for g in user.groups.all()]
                },
                'preferences': self.get_preferences(),
                'main_menu': main_menu,
                'secondary_menu': secondary_menu
            }
        })
        return context

    def get_page_title(self):
        return self.page_title

    def get_breadcrumb(self):
        return self.breadcrumb

    def get_preferences(self):
        return {
            'remember_columns': self.request.session.get('remember_columns', self.request.user.preferences['interface__remember_column_visibility']),
            'list_scope': self.request.session.get('list_scope', self.request.user.preferences['interface__records_list_scope'])
        }

    def get_menus(self):
        menus = ['main_menu', 'secondary_menu']
        results = []
        for file in menus:
            data = self.get_json_config(file)
            menu = []
            for item in data:
                if item.get('children') is not None:
                    children = []
                    for child in item['children']:
                        if child.get('permissions') is not None:
                            if self.show_item(child):
                                children.append(child)
                        else:
                            children.append(child)

                    item['children'] = children

                if item.get('permissions') is not None:
                    if self.show_item(item):
                        menu.append(item)
                else:
                    menu.append(item)

            results.append(menu)

        return results

    @staticmethod
    def get_json_config(filename):
        file = os.path.join('dalme_app', 'config', filename + '.json')
        with open(file, 'r') as fp:
            return json.load(fp)

    def show_item(self, item):
        if item.get('permissions') is not None:
            user_groups = [i.name for i in self.request.user.groups.all()]
            result = [i for i in user_groups if i in item['permissions']]
            if result or self.request.user.is_superuser:
                return True
            else:
                return False
        else:
            return True


class DALMEDetailView(DetailView, DALMEContextMixin):
    template_name = 'dalme_app/generic_detail.html'

    def get_page_title(self):
        return '{}: {}'.format(self.page_title, self.object.name) if self.page_title else self.object.name


class DALMEListView(TemplateView, DALMEContextMixin):
    template_name = 'dalme_app/list-views.html'
    page_title = None
    dt_config = None
    breadcrumb = None
    helpers = None
    includes = None
    editor = 'true'
    form_template = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context.update({
            'config': self.get_dt_config(),
            'helpers': self.helpers,
            'includes': self.includes,
            'form_template': self.form_template,
            'editor': self.editor,
        })

        return context

    def get_dt_config(self):
        return self.dt_config


def get_page_chain(breadcrumb, current=None):
    i_count = len(breadcrumb)
    title = ''
    if current and current != breadcrumb[i_count-1][0]:
        if len(current) > 55:
            current = current[:55] + ' <i class="fa fa-plus-circle fa-fw" data-toggle="tooltip" data-placement="bottom" title="{}"></i> '.format(current)
        for i in breadcrumb:
            if i[1] != '':
                title += '<a href="{}" class="title_link">{}</a>'.format(i[1], i[0])
            else:
                title += i[0]
            title += ' <i class="fa fa-caret-right fa-fw"></i> '
        title += '<span class="title_current">{}</span>'.format(current)
    else:
        c = 0
        while c <= i_count - 1:
            if c == i_count - 1:
                title += '<span class="title_current">{}</span>'.format(breadcrumb[c][0])
            else:
                title += breadcrumb[c][0] + ' <i class="fa fa-caret-right fa-fw"></i> '
            c = c + 1
    return title
