from dalme_app.models import Ticket
from rest_framework import serializers
from dalme_api.serializers.others import TagSerializer
from dalme_api.serializers.users import UserSerializer
from dalme_api.serializers.comments import CommentSerializer


class TicketSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    creation_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'])
    modification_user = UserSerializer(fields=['full_name', 'username', 'id'])

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
    creation_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'])
    modification_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'])
    comments = CommentSerializer(many=True, required=False)

    class Meta:
        model = Ticket
        fields = ('id', 'subject', 'description', 'status', 'tags', 'url', 'file', 'comments',
                  'creation_user', 'creation_timestamp', 'modification_user', 'modification_timestamp')
        extra_kwargs = {
            'tags': {'required': False}
            }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['comment_count'] = instance.comments.count()
        return ret
