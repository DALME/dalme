from django.contrib.auth.models import User, Group
from dalme_app.models import Agent, Profile
from rest_framework import serializers
from ._common import DynamicSerializer
from dalme_app.serializers.others import GroupSerializer, ProfileSerializer


class UserSerializer(DynamicSerializer):
    """ Serializes user and profile data """
    groups = GroupSerializer(many=True, required=False)
    profile = ProfileSerializer()
    full_name = serializers.CharField(max_length=255, source='profile.full_name', required=False)

    class Meta:
        model = User
        fields = ('id', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'full_name',
                  'email', 'is_staff', 'is_active', 'date_joined', 'groups', 'profile', 'password')
        extra_kwargs = {
            'username': {'validators': []},
            'password': {'write_only': True, 'required': False}
            }

    def to_internal_value(self, data):
        if type(data) is int:
            user = User.objects.get(pk=data)
            data = {
                'id': user.id,
                'username': user.username
                }
        if data.get('groups') is not None:
            self.context['groups'] = data.pop('groups')

        if data.get('profile') is not None:
            self.context['profile'] = data.pop('profile')

        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        if self.context.get('profile') is not None:
            profile_data = self.context.get('profile')
            profile = Profile.objects.get_or_create(user=instance)
            if type(profile) is tuple:
                profile = profile[0]
            if profile_data.get('primary_group') is not None and type(profile_data.get('primary_group')) is int:
                profile_data['primary_group'] = Group.objects.get(pk=profile_data['primary_group'])
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        if self.context.get('groups') is not None:
            group_data = [i['id'] for i in self.context['groups']]
            instance.groups.set(group_data)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        profile_data = validated_data.pop('profile')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user, **profile_data)
        if self.context.get('groups') is not None:
            group_data = [i['id'] for i in self.context['groups']]
            user.groups.set(group_data)
        Agent.objects.create(standard_name=user.profile.full_name, type=1, user=user)
        return user