from dalme_app.models import Comment
from rest_framework import serializers
from dalme_api.serializers.users import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    creation_user = UserSerializer(fields=['full_name', 'username', 'id', 'avatar'])

    class Meta:
        model = Comment
        fields = ('body', 'creation_timestamp', 'creation_user')

# class CommentSerializer(serializers.ModelSerializer):
#     creation_timestamp = serializers.DateTimeField(format='%-d-%b-%Y@%H:%M')
#
#     class Meta:
#         model = Comment
#         fields = ('body', 'creation_timestamp')
#
#     def to_representation(self, instance):
#         ret = super().to_representation(instance)
#         ret['user'] = '<a href="/users/{}">{}</a>'.format(instance.creation_user.username, instance.creation_user.profile.full_name)
#         if instance.creation_user.profile.profile_image is not None:
#             ret['avatar'] = '<img src="{}" class="img_avatar" alt="avatar">'.format(instance.creation_user.profile.profile_image)
#         else:
#             ret['avatar'] = '<i class="fa fa-user-alt-slash img_avatar mt-1 fa-2x"></i>'
#         return ret
