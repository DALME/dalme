from dalme_app.models import Ticket, Tag
from rest_framework import serializers
from dalme_api.serializers.others import TagSerializer, AttachmentSerializer
from dalme_api.serializers.users import UserSerializer
from dalme_api.serializers.comments import CommentSerializer
from django.contrib.auth.models import User
from rest_framework.utils import model_meta
from django_currentuser.middleware import get_current_user


class TicketSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    creation_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'], required=False)
    modification_user = UserSerializer(fields=['full_name', 'username', 'id'], required=False)

    class Meta:
        model = Ticket
        fields = ('id', 'subject', 'description', 'status', 'tags', 'url', 'file',
                  'creation_user', 'creation_timestamp', 'modification_user', 'modification_timestamp')
        extra_kwargs = {
            'tags': {'required': False}
            }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['comment_count'] = instance.comments.count()
        return ret

    def to_internal_value(self, data):
        if data.get('tags') is not None:
            self.context['tags'] = data.pop('tags')
        return super().to_internal_value(data)

    def create(self, validated_data):
        tags = self.context.get('tags')
        ticket = Ticket.objects.create(**validated_data)
        if tags:
            for tag in tags:
                obj = {'tag_type': 'T', 'tag': tag['value']}
                ticket.tags.create(**obj)
        return ticket


class TicketDetailSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    file = AttachmentSerializer(required=False)
    creation_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'], required=False)
    modification_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'], required=False)
    comments = CommentSerializer(many=True, required=False)
    assigned_to = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'], required=False)

    class Meta:
        model = Ticket
        fields = ('id', 'subject', 'description', 'status', 'tags', 'url', 'file', 'comments',
                  'creation_user', 'creation_timestamp', 'modification_user', 'modification_timestamp', 'assigned_to')
        extra_kwargs = {
            'tags': {'required': False}
            }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['comment_count'] = instance.comments.count()
        return ret

    def to_internal_value(self, data):
        if data.get('tags') is not None:
            self.context['tags'] = data.pop('tags')
        if data.get('assigned_to') is not None:
            self.context['assigned_to'] = data.pop('assigned_to')
        return super().to_internal_value(data)

    def update(self, instance, validated_data):
        serializers.raise_errors_on_nested_writes('update', self, validated_data)
        info = model_meta.get_field_info(instance)
        assigned_to = self.context.get('assigned_to')
        tags = self.context.get('tags')
        fields = ['modification_user', 'modification_timestamp']
        m2m_fields = []
        validated_data['modification_user'] = get_current_user()

        if assigned_to:
            validated_data['assigned_to'] = User.objects.get(id=assigned_to)

        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                fields.append(attr)
                setattr(instance, attr, value)

        instance.save(update_fields=fields)

        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        if tags:
            if instance.tags.all().exists():
                new_tags = []
                current_tags = dict((i.tag, i.id) for i in instance.tags.all())
                for tag in tags:
                    if current_tags.get(tag) is None:
                        new_tags.append(tag)
                    else:
                        current_tags.pop(tag)

                if len(current_tags) > 0:
                    for tag in current_tags.values():
                        Tag.objects.get(id=tag).delete()
            else:
                new_tags = tags

            if new_tags:
                for tag in new_tags:
                    instance.tags.create(**{'tag': tag})

        return super().update(instance, validated_data)
