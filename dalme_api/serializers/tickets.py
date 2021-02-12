from dalme_app.models import Ticket
from rest_framework import serializers
from dalme_api.serializers.others import TagSerializer


class TicketSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, required=False)
    creation_timestamp = serializers.DateTimeField(format='%d-%b-%Y@%H:%M', required=False)

    class Meta:
        model = Ticket
        fields = ('id', 'subject', 'description', 'status', 'tags', 'url', 'file',
                  'creation_user', 'creation_timestamp')
        extra_kwargs = {
            'tags': {'required': False}
            }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['comment_count'] = instance.comments.count()
        ticket = '<div class="d-flex align-items-center"><i class="fa fa-exclamation-circle ticket-status-{} fa-fw"></i>'.format(ret['status'])
        ticket += '<a href="/tickets/'+str(ret['id'])+'" class="ticket_subject">'+ret['subject']+'</a>'
        if ret['comment_count'] > 0:
            ticket += '<i class="fas fa-comment fa-lg icon-badge ml-2"></i><span class="icon-badge-count">{}</span></div>'.format(ret['comment_count'])
        ret['ticket'] = ticket
        attachments = ''
        if ret['url'] is not None:
            attachments += '<a href="{}" class="task-attachment">URL</a>'.format(ret['url'])
        if ret['file'] is not None:
            attachments += '<a href="/download/{}" class="task-attachment">File</a>'.format(instance.file.file)
        ret['attachments'] = attachments
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
