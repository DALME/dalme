"""dalme URL Configuration"""
from django.urls import path, re_path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import HttpResponse
# from allaccess.views import OAuthRedirect
from rest_framework import routers
from dalme_app import apis
from dalme_app import web_apis

router = routers.DefaultRouter()
router.register(r'sources', apis.Sources, basename='sources')
router.register(r'users', apis.Users, basename='users')
router.register(r'transcriptions', apis.Transcriptions, basename='transcriptions')
router.register(r'images', apis.Images, basename='images')
router.register(r'pages', apis.Pages, basename='pages')
router.register(r'tasks', apis.Tasks, basename='tasks')
router.register(r'tasklists', apis.TaskLists, basename='tasklists')
router.register(r'sets', apis.Sets, basename='sets')
router.register(r'options', apis.Options, basename='options')
router.register(r'dt_lists', apis.DTLists, basename='dt_lists')
router.register(r'dt_fields', apis.DTFields, basename='dt_fields')
router.register(r'attribute_types', apis.AttributeTypes, basename='attribute_types')
router.register(r'content_types', apis.ContentTypes, basename='content_types')
router.register(r'content_classes', apis.ContentClasses, basename='content_classes')
router.register(r'languages', apis.Languages, basename='languages')
router.register(r'async_tasks', apis.AsynchronousTasks, basename='async_tasks')
router.register(r'attributes', apis.Attributes, basename='attributes')
router.register(r'countries', apis.Countries, basename='countries')
router.register(r'cities', apis.CityList, basename='cities')
router.register(r'attachments', apis.Attachments, basename='attachments')
router.register(r'tickets', apis.Tickets, basename='tickets')
router.register(r'comments', apis.Comments, basename='comments')
# router.register(r'userinfo', apis.OauthUser, basename='userinfo')
router.register(r'workflow', apis.WorkflowManager, basename='workflow')
router.register(r'datasets', apis.Datasets, basename='datasets')
router.register(r'rights', apis.Rights, basename='rights')

web_router = routers.DefaultRouter()
web_router.register(r'records', web_apis.Records, basename='records')
web_router.register(r'collections', web_apis.Collections, basename='collections')

urlpatterns = [
    # path('oauth/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    path('api/', include(router.urls)),
    path('web-api/', include(web_router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('idp/', include('djangosaml2idp.urls', namespace='identity_provider')),
    # path('openid/', include('oidc_provider.urls', namespace='oidc_provider')),
    # re_path(r'^accounts/login/dalme_wp/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('django_admin/', admin.site.urls),
    re_path(r'^\.well-known/acme-challenge/DWY9GSDZjOsijpklS3RIAuBvZt2PThO7ameePcaIHm8/', lambda request: HttpResponse('DWY9GSDZjOsijpklS3RIAuBvZt2PThO7ameePcaIHm8.LbUmj5n5DqTPM7bapjsa-DennAErlpafYkGP-9eZzzo'), name='hello_world'),
    re_path(r'^', include('dalme_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns = [
#         path('__debug__/', include(debug_toolbar.urls)),
#     ] + urlpatterns
