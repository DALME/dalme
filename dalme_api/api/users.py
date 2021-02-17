from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordResetForm
from django.http import HttpRequest
from django.conf import settings
from rest_framework.response import Response
from rest_framework.decorators import action
from dalme_api.serializers import UserSerializer
from dalme_api.access_policies import UserAccessPolicy
from ._common import DALMEBaseViewSet
from dalme_api.filters import UserFilter


class Users(DALMEBaseViewSet):
    """ API endpoint for managing users """
    permission_classes = (UserAccessPolicy,)
    queryset = User.objects.all()
    serializer_class = UserSerializer
    filterset_class = UserFilter
    search_fields = ['username', 'email', 'profile__full_name', 'first_name', 'last_name']
    ordering_fields = ['id', 'username', 'email', 'profile__full_name', 'last_login', 'date_joined', 'is_staff', 'is_active', 'is_superuser', 'first_name']
    ordering = ['id']

    @action(detail=True, methods=['post'])
    def reset_password(self, request, *args, **kwargs):
        object = self.get_object()
        try:
            form = PasswordResetForm({'email': object.email})
            assert form.is_valid()
            request = HttpRequest()
            request.META['SERVER_NAME'] = 'db.dalme.org'
            request.META['SERVER_PORT'] = '443'
            form.save(
                request=request,
                use_https=True,
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='registration/password_reset_email.html'
            )
            result = {'data': 'Email sent'}
            status = 201
        except Exception as e:
            result = {'error': str(e)}
            status = 400
        return Response(result, status)

    def update(self, request, *args, **kwargs):
        partial = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial, fields=['id', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'groups', 'profile'])
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)
