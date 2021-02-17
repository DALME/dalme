from rest_framework import viewsets
from rest_framework.response import Response
from dalme_api.serializers import CommentSerializer
from dalme_app.models import Comment
from dalme_api.access_policies import CommentAccessPolicy
from dalme_app.models import *


class Comments(viewsets.ModelViewSet):
    """ API endpoint for managing comments """
    permission_classes = (CommentAccessPolicy,)
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self, *args, **kwargs):
        if self.request.GET.get('model') is not None and self.request.GET.get('object') is not None:
            model = self.request.GET['model']
            object = self.request.GET['object']
            if type(object) is not str:
                object = str(object)
            obj_instance = eval(model+'.objects.get(pk="'+object+'")')
            queryset = obj_instance.comments.all()
        else:
            queryset = self.queryset
        return queryset

    def create(self, request, *args, **kwargs):
        result = {}
        data = request.data
        try:
            content_object = eval(data['model']+'.objects.get(pk="'+str(data['object'])+'")')
            new_comment = content_object.comments.create(body=data['body'])
            serializer = self.get_serializer(new_comment)
            result = serializer.data
            status = 201
        except Exception as e:
            result = str(e)
            status = 400
        return Response(result, status)
